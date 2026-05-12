"""
名称：生成视频素材候选.py
作用：读取内容处理系统素材索引，筛选可用于视频制作的素材候选。
触发方式：python 生成视频素材候选.py
依赖：Python 标准库；需已有内容处理系统素材索引。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：只读取内容处理索引，只写入视频制作系统素材候选目录；不复制、不移动、不删除、不转码素材。
创建/修改记录：2026-04-27 创建视频素材候选桥接脚本。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def v3_root() -> Path:
    return module_root().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_content_index(root: Path) -> Path:
    content_root = root / "02杰哥扩展系统" / "04内容处理系统"
    latest = content_root / "03数据" / "02登记索引" / "内容素材索引_最新.json"
    if latest.exists():
        return latest
    script = content_root / "02脚本" / "生成内容素材索引.py"
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    return latest


def build_candidates() -> dict[str, Any]:
    root = module_root()
    rules = load_json(root / "01配置" / "视频素材桥接规则.json")
    content_index_path = ensure_content_index(v3_root())
    content_index = load_json(content_index_path)
    output_dir = root / "03数据" / "05素材候选"
    output_dir.mkdir(parents=True, exist_ok=True)
    allowed_types = set(rules.get("桥接范围", {}).get("允许素材类型", []))
    priority_types = set(rules.get("桥接范围", {}).get("优先素材类型", []))

    candidates = []
    blocked = []
    for item in content_index.get("素材", []):
        asset_type = item.get("素材类型", "未知")
        candidate = {
            "文件名": item.get("文件名"),
            "路径": item.get("路径"),
            "素材类型": asset_type,
            "大小字节": item.get("大小字节"),
            "sha256": item.get("sha256"),
            "来源系统": "04内容处理系统",
            "授权状态": "待人工确认",
            "是否优先素材": asset_type in priority_types,
            "允许复制": False,
            "允许移动": False,
            "允许删除": False,
            "允许转码": False,
            "允许发布": False,
        }
        if asset_type in allowed_types:
            candidates.append(candidate)
        else:
            candidate["阻断原因"] = "素材类型不在视频桥接允许范围"
            blocked.append(candidate)

    candidates = sorted(candidates, key=lambda item: (not item["是否优先素材"], item["文件名"] or ""))
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "内容索引来源": str(content_index_path),
        "候选数量": len(candidates),
        "阻断数量": len(blocked),
        "素材候选": candidates,
        "阻断素材": blocked,
        "安全边界": rules.get("安全边界", {}),
        "安全说明": "视频素材候选只登记可复用素材，不复制、不移动、不转码、不发布。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"视频素材候选_{timestamp}.json"
    latest = output_dir / "视频素材候选_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"candidate_count": len(candidates), "blocked_count": len(blocked), "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_candidates()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
