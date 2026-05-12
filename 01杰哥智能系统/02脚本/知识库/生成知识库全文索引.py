"""
名称：生成知识库全文索引.py
作用：解析 v3 知识库原始文档目录中的本地文本资料，生成清洗文本和全文分块索引。
触发方式：python 生成知识库全文索引.py
依赖：Python 标准库。
所属系统：01杰哥智能系统
安全边界：只读取 v3 知识库原始文档目录，只写入清洗文本和索引清单；不读取旧系统资料，不删除或移动原始文档，不写入向量数据库。
创建/修改记录：2026-04-26 创建知识库全文解析与轻量索引脚本；排除元数据伴随文件。
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


def v3_root() -> Path:
    return Path(__file__).resolve().parents[3]


def config_path() -> Path:
    return v3_root() / "01杰哥智能系统" / "01配置" / "知识库配置.json"


def load_config() -> dict[str, Any]:
    return json.loads(config_path().read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text_with_fallback(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def parse_json(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(data, ensure_ascii=False, indent=2)


def parse_csv(path: Path) -> str:
    text = read_text_with_fallback(path)
    rows = []
    for row in csv.reader(text.splitlines()):
        rows.append(" | ".join(cell.strip() for cell in row))
    return "\n".join(rows)


def parse_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml_bytes = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml_bytes)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for paragraph in root.findall(".//w:p", namespace):
        texts = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
        line = "".join(texts).strip()
        if line:
            paragraphs.append(line)
    return "\n".join(paragraphs)


def clean_text(text: str, limit: int) -> str:
    text = text.replace("\ufeff", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    if len(text) > limit:
        return text[:limit]
    return text


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if not text:
        return []
    chunks = []
    start = 0
    safe_overlap = max(0, min(overlap, chunk_size // 2))
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - safe_overlap, start + 1)
    return [item for item in chunks if item]


def parse_document(path: Path, direct_ext: set[str], max_chars: int) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix not in direct_ext:
        return "", "仅登记，暂未解析"
    try:
        if suffix in {".md", ".txt"}:
            text = read_text_with_fallback(path)
        elif suffix == ".json":
            text = parse_json(path)
        elif suffix == ".csv":
            text = parse_csv(path)
        elif suffix == ".docx":
            text = parse_docx(path)
        else:
            return "", "仅登记，暂未解析"
        return clean_text(text, max_chars), "已解析"
    except Exception as exc:
        return "", f"解析失败：{exc}"


def build_fulltext_index() -> dict[str, Any]:
    config = load_config()
    raw_dir = Path(config["数据目录"]["原始文档"])
    clean_dir = Path(config["数据目录"]["清洗文本"])
    index_dir = Path(config["数据目录"]["索引清单"])
    log_dir = v3_root() / "01杰哥智能系统" / "04日志" / "知识库"
    clean_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    supported = {item.lower() for item in config.get("支持扩展名", [])}
    strategy = config.get("全文解析策略", {})
    direct_ext = {item.lower() for item in strategy.get("直接解析扩展名", [])}
    chunk_size = int(strategy.get("分块字符数", 800))
    overlap = int(strategy.get("分块重叠字符数", 120))
    max_chars = int(strategy.get("最大单文件字符数", 200000))

    documents = []
    chunks = []
    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in supported:
            continue
        if path.name.endswith(".元数据.json"):
            continue
        sha256 = file_sha256(path)
        text, status = parse_document(path, direct_ext, max_chars)
        clean_path = ""
        doc_chunks = []
        if text:
            clean_file = f"{path.stem}_{sha256[:12]}.txt"
            clean_target = clean_dir / clean_file
            clean_target.write_text(text, encoding="utf-8")
            clean_path = str(clean_target)
            doc_chunks = chunk_text(text, chunk_size, overlap)

        doc_id = sha256[:16]
        for index, chunk in enumerate(doc_chunks, start=1):
            chunks.append(
                {
                    "文档ID": doc_id,
                    "分块序号": index,
                    "文件名": path.name,
                    "路径": str(path),
                    "清洗文本路径": clean_path,
                    "内容": chunk,
                    "字符数": len(chunk),
                }
            )

        documents.append(
            {
                "文档ID": doc_id,
                "文件名": path.name,
                "路径": str(path),
                "扩展名": path.suffix.lower(),
                "大小字节": path.stat().st_size,
                "sha256": sha256,
                "解析状态": status,
                "清洗文本路径": clean_path,
                "分块数量": len(doc_chunks),
            }
        )

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "原始文档目录": str(raw_dir),
        "清洗文本目录": str(clean_dir),
        "解析扩展名": sorted(direct_ext),
        "文档数量": len(documents),
        "分块数量": len(chunks),
        "文档": documents,
        "分块": chunks,
        "说明": "轻量全文索引仅用于本地检索；后续向量化前仍需按保密等级复核。",
    }
    output = index_dir / f"知识库全文索引_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = index_dir / "知识库全文索引_最新.json"
    latest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"文档数量": len(documents), "分块数量": len(chunks), "输出": str(output)}, ensure_ascii=False))
    return report


def main() -> int:
    build_fulltext_index()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
