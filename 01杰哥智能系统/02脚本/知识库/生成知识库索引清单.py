"""
名称：生成知识库索引清单.py
作用：扫描 v3 知识库原始文档目录，生成只读文档索引清单。
触发方式：python 生成知识库索引清单.py
依赖：Python 标准库。
所属系统：01杰哥智能系统
安全边界：只读取知识库原始文档目录，只写入 v3 索引清单和日志，不移动、不删除、不修改原始文档。
创建/修改记录：2026-04-26 创建第一阶段知识库索引脚本；排除元数据伴随文件。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


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


def scan_documents() -> dict[str, Any]:
    config = load_config()
    raw_dir = Path(config["数据目录"]["原始文档"])
    index_dir = Path(config["数据目录"]["索引清单"])
    log_dir = v3_root() / "01杰哥智能系统" / "04日志" / "知识库"
    index_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    supported = {item.lower() for item in config.get("支持扩展名", [])}
    documents = []
    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name.endswith(".元数据.json"):
            continue
        if path.suffix.lower() not in supported:
            continue
        stat = path.stat()
        documents.append(
            {
                "文件名": path.name,
                "路径": str(path),
                "扩展名": path.suffix.lower(),
                "大小字节": stat.st_size,
                "修改时间": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "sha256": file_sha256(path),
                "入库状态": "未入库",
                "文档类型": "待分类",
            }
        )

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "原始文档目录": str(raw_dir),
        "支持扩展名": sorted(supported),
        "文档数量": len(documents),
        "文档": documents,
    }
    output = index_dir / f"知识库索引清单_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = index_dir / "知识库索引清单_最新.json"
    latest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"文档数量": len(documents), "输出": str(output)}, ensure_ascii=False))
    return report


def main() -> int:
    scan_documents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
