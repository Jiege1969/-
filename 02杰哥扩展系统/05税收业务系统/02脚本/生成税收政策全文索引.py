"""
名称：生成税收政策全文索引.py
作用：解析税收业务系统本地政策文件，生成清洗文本和全文分块索引，并记录元数据有效状态。
触发方式：python 生成税收政策全文索引.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只读取本模块政策文件目录，只写入本模块清洗文本和分类索引；不抓取政策、不替代正式税务判断。
创建/修改记录：2026-04-26 创建税收政策全文解析与索引脚本。
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def policy_rules() -> dict[str, Any]:
    return load_json(module_root() / "01配置" / "税收政策入库规则.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metadata_path_for(path: Path) -> Path:
    return path.with_name(f"{path.name}.元数据.json")


def read_text_with_fallback(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


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


def parse_document(path: Path, direct_ext: set[str]) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix not in direct_ext:
        return "", "仅登记，暂未解析"
    try:
        if suffix in {".md", ".txt"}:
            return read_text_with_fallback(path), "已解析"
        if suffix == ".json":
            return json.dumps(load_json(path), ensure_ascii=False, indent=2), "已解析"
        if suffix == ".docx":
            return parse_docx(path), "已解析"
        return "", "仅登记，暂未解析"
    except Exception as exc:
        return "", f"解析失败：{exc}"


def clean_text(text: str, max_chars: int) -> str:
    text = re.sub(r"[ \t]+", " ", text.replace("\ufeff", ""))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:max_chars] if len(text) > max_chars else text


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


def load_metadata(path: Path) -> tuple[dict[str, Any], str]:
    meta_path = metadata_path_for(path)
    if not meta_path.exists():
        return {}, "缺失"
    try:
        return load_json(meta_path), "正常"
    except Exception as exc:
        return {"错误": str(exc)}, "异常"


def build_policy_fulltext_index() -> dict[str, Any]:
    root = module_root()
    rules = policy_rules()
    strategy = rules.get("全文解析策略", {})
    direct_ext = {item.lower() for item in strategy.get("直接解析扩展名", [])}
    allowed = {item.lower() for item in rules.get("允许文件类型", [])}
    chunk_size = int(strategy.get("分块字符数", 900))
    overlap = int(strategy.get("分块重叠字符数", 150))
    max_chars = int(strategy.get("最大单文件字符数", 200000))
    policy_dir = root / "03数据" / "01政策文件"
    clean_dir = root / "03数据" / "05清洗文本"
    index_dir = root / "03数据" / "02分类索引"
    clean_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    policies = []
    chunks = []
    for path in sorted(policy_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name.endswith(".元数据.json"):
            continue
        if path.suffix.lower() not in allowed:
            continue
        digest = sha256(path)
        metadata, metadata_status = load_metadata(path)
        text, parse_status = parse_document(path, direct_ext)
        text = clean_text(text, max_chars)
        clean_path = ""
        doc_chunks = []
        if text:
            clean_target = clean_dir / f"{path.stem}_{digest[:12]}.txt"
            clean_target.write_text(text, encoding="utf-8")
            clean_path = str(clean_target)
            doc_chunks = chunk_text(text, chunk_size, overlap)
        doc_id = digest[:16]
        can_be_basis = metadata_status == "正常" and metadata.get("有效状态") != "待核实" and bool(metadata.get("来源链接"))
        for index, chunk in enumerate(doc_chunks, start=1):
            chunks.append(
                {
                    "政策ID": doc_id,
                    "分块序号": index,
                    "标题": metadata.get("标题", path.name),
                    "文号": metadata.get("文号", ""),
                    "有效状态": metadata.get("有效状态", "待核实"),
                    "可作为正式依据": can_be_basis,
                    "文件名": path.name,
                    "路径": str(path),
                    "内容": chunk,
                    "清洗文本路径": clean_path,
                }
            )
        policies.append(
            {
                "政策ID": doc_id,
                "文件名": path.name,
                "路径": str(path),
                "sha256": digest,
                "解析状态": parse_status,
                "元数据状态": metadata_status,
                "标题": metadata.get("标题", path.name),
                "文号": metadata.get("文号", ""),
                "有效状态": metadata.get("有效状态", "待核实"),
                "来源链接": metadata.get("来源链接", ""),
                "可作为正式依据": can_be_basis,
                "清洗文本路径": clean_path,
                "分块数量": len(doc_chunks),
            }
        )

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "政策文件目录": str(policy_dir),
        "清洗文本目录": str(clean_dir),
        "政策数量": len(policies),
        "分块数量": len(chunks),
        "政策文件": policies,
        "分块": chunks,
        "安全说明": "待核实或无官方来源的政策资料不得作为最终税务处理依据。",
    }
    output = index_dir / f"税收政策全文索引_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    latest = index_dir / "税收政策全文索引_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"政策数量": len(policies), "分块数量": len(chunks), "输出": str(output)}, ensure_ascii=False))
    return report


def main() -> int:
    build_policy_fulltext_index()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
