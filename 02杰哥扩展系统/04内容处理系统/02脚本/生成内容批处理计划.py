"""
名称：生成内容批处理计划.py
作用：根据内容素材索引和批处理规则，生成可人工确认的批处理计划。
触发方式：python 生成内容批处理计划.py
依赖：Python 标准库；需先生成内容素材索引。
所属系统：02杰哥扩展系统/04内容处理系统
安全边界：只读取索引和规则，只写入计划目录；不改写、不删除、不移动素材。
创建/修改记录：2026-04-27 创建内容批处理计划脚本。
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_index(root: Path) -> Path:
    latest = root / "03数据" / "02登记索引" / "内容素材索引_最新.json"
    if latest.exists():
        return latest
    script = root / "02脚本" / "生成内容素材索引.py"
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    return latest


def build_plan() -> dict[str, Any]:
    root = module_root()
    rules = load_json(root / "01配置" / "内容批处理规则.json")
    index_path = ensure_index(root)
    index = load_json(index_path)
    output_dir = root / "03数据" / "03批处理计划"
    output_dir.mkdir(parents=True, exist_ok=True)
    task_rules = rules.get("任务类型", [])
    tasks = []

    for asset in index.get("素材", []):
        matched_rules = [rule for rule in task_rules if asset.get("素材类型") in rule.get("适用类型", [])]
        if not matched_rules:
            tasks.append(
                {
                    "文件名": asset.get("文件名"),
                    "路径": asset.get("路径"),
                    "素材类型": asset.get("素材类型"),
                    "任务类型": "只登记",
                    "预演动作": ["等待人工分类"],
                    "是否阻断": True,
                    "阻断原因": "未知素材类型或无匹配规则",
                    "允许真实处理": False,
                }
            )
            continue
        for rule in matched_rules:
            tasks.append(
                {
                    "文件名": asset.get("文件名"),
                    "路径": asset.get("路径"),
                    "素材类型": asset.get("素材类型"),
                    "任务类型": rule.get("名称"),
                    "预演动作": rule.get("预演动作", []),
                    "是否阻断": False,
                    "阻断原因": "",
                    "允许真实处理": False,
                }
            )

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "索引来源": str(index_path),
        "任务数量": len(tasks),
        "任务": tasks,
        "阻断规则": rules.get("阻断规则", []),
        "跨系统复用": rules.get("跨系统复用", {}),
        "是否允许真实处理": False,
        "安全说明": "批处理计划只用于人工确认和流程预演，当前不执行真实改写、转码、移动或删除。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"内容批处理计划_{timestamp}.json"
    latest = output_dir / "内容批处理计划_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"task_count": len(tasks), "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_plan()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
