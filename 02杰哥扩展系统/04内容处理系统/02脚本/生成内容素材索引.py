"""
名称：生成内容素材索引.py
作用：扫描内容处理系统素材入口目录，生成素材类型、大小、哈希和处理状态索引。
触发方式：python 生成内容素材索引.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/04内容处理系统
安全边界：只读取素材入口目录，只写入本模块索引目录；不修改、不删除、不移动素材。
创建/修改记录：2026-04-27 创建内容素材索引脚本。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_suffix(suffix: str, type_map: dict[str, list[str]]) -> str:
    lower = suffix.lower()
    for type_name, suffixes in type_map.items():
        if lower in [item.lower() for item in suffixes]:
            return type_name
    return "未知"


def build_index() -> dict[str, Any]:
    root = module_root()
    config = load_json(root / "01配置" / "内容处理配置.json")
    source_dir = root / "03数据" / "01素材入口"
    output_dir = root / "03数据" / "02登记索引"
    source_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    type_map = config.get("素材类型", {})

    items = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file():
            continue
        file_type = classify_suffix(path.suffix, type_map)
        items.append(
            {
                "文件名": path.name,
                "路径": str(path),
                "扩展名": path.suffix.lower(),
                "素材类型": file_type,
                "大小字节": path.stat().st_size,
                "sha256": sha256(path),
                "可进入批处理计划": file_type != "未知",
                "允许改写原文件": False,
                "允许删除原文件": False,
                "允许移动原文件": False,
            }
        )

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "素材入口": str(source_dir),
        "素材数量": len(items),
        "素材": items,
        "统计": {
            "文档": sum(1 for item in items if item["素材类型"] == "文档"),
            "表格": sum(1 for item in items if item["素材类型"] == "表格"),
            "图片": sum(1 for item in items if item["素材类型"] == "图片"),
            "音频": sum(1 for item in items if item["素材类型"] == "音频"),
            "视频": sum(1 for item in items if item["素材类型"] == "视频"),
            "未知": sum(1 for item in items if item["素材类型"] == "未知"),
        },
        "安全说明": "素材索引只登记文件信息，不对原文件做任何改动。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"内容素材索引_{timestamp}.json"
    latest = output_dir / "内容素材索引_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"asset_count": len(items), "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_index()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
