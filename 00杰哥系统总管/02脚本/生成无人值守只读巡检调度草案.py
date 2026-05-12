# -*- coding: utf-8 -*-
"""
名称：生成无人值守只读巡检调度草案.py
作用：扫描00总管验证脚本标识，生成无人值守只读巡检调度清单草案。
触发方式：python 生成无人值守只读巡检调度草案.py
依赖：Python标准库；无人值守只读巡检调度草案规则.json。
所属系统：00杰哥系统总管
安全边界：只生成调度草案；不创建系统计划任务；不触发n8n；不执行巡检脚本；不联网；不发送企业微信；不写正式库；不写旧系统。
创建/修改记录：2026-04-28 创建无人值守只读巡检调度草案脚本。
标识：unattended-readonly-patrol-schedule-draft-report
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def find_marker(script_dir: Path, marker: str) -> str:
    for path in sorted(script_dir.glob("*.py")):
        try:
            if marker in path.read_text(encoding="utf-8-sig", errors="replace"):
                return str(path)
        except OSError:
            continue
    return ""


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    script_dir = manager / "02脚本"
    rule_path = manager / "01配置" / "无人值守只读巡检调度草案规则.json"
    rules = load_json(rule_path)
    patrol_items = []
    for item in rules.get("巡检项", []):
        marker = item.get("脚本标识", "")
        script_path = find_marker(script_dir, marker)
        patrol_items.append({
            **item,
            "脚本路径": script_path,
            "脚本是否存在": bool(script_path),
            "是否创建系统计划任务": False,
            "是否触发n8n": False,
            "是否实际执行巡检": False,
            "是否真实联网": False,
            "是否真实发送": False,
            "是否写正式库": False,
            "是否写旧系统": False
        })
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "规则文件": str(rule_path),
        "默认开关": rules.get("默认开关", {}),
        "巡检调度草案": patrol_items,
        "汇总": {
            "巡检项数量": len(patrol_items),
            "脚本存在数量": sum(1 for item in patrol_items if item["脚本是否存在"]),
            "脚本缺失数量": sum(1 for item in patrol_items if not item["脚本是否存在"]),
            "创建系统计划任务数量": sum(1 for item in patrol_items if item["是否创建系统计划任务"]),
            "触发n8n数量": sum(1 for item in patrol_items if item["是否触发n8n"]),
            "实际执行巡检数量": sum(1 for item in patrol_items if item["是否实际执行巡检"]),
            "真实联网数量": sum(1 for item in patrol_items if item["是否真实联网"]),
            "真实发送数量": sum(1 for item in patrol_items if item["是否真实发送"]),
            "写正式库数量": sum(1 for item in patrol_items if item["是否写正式库"]),
            "写旧系统数量": sum(1 for item in patrol_items if item["是否写旧系统"])
        },
        "当前结论": "无人值守只读巡检调度草案已生成；当前只登记巡检清单，不创建计划任务、不执行巡检、不触发n8n。"
    }
    output_dir = manager / "03数据" / "无人值守守护"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "无人值守只读巡检调度草案_最新.json"
    latest = output_dir / "无人值守只读巡检调度草案_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"巡检项数量": len(patrol_items), "脚本缺失数量": report["汇总"]["脚本缺失数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
