# -*- coding: utf-8 -*-
"""
名称：生成无人值守只读巡检运行记录模板.py
作用：根据无人值守只读巡检调度草案生成未来巡检运行记录模板。
触发方式：python 生成无人值守只读巡检运行记录模板.py
依赖：Python标准库；无人值守只读巡检运行记录规则.json；无人值守只读巡检调度草案_最新.json。
所属系统：00杰哥系统总管
安全边界：只生成运行记录模板；不执行巡检；不创建系统计划任务；不触发n8n；不联网；不发送企业微信；不写正式库；不写旧系统；不自动修复。
创建/修改记录：2026-04-28 创建无人值守只读巡检运行记录模板脚本。
标识：unattended-readonly-patrol-run-record-template-report
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


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    rule_path = manager / "01配置" / "无人值守只读巡检运行记录规则.json"
    schedule_path = manager / "03数据" / "无人值守守护" / "无人值守只读巡检调度草案_最新.json"
    rules = load_json(rule_path)
    schedule = load_json(schedule_path)
    records = []
    for item in schedule.get("巡检调度草案", []):
        records.append({
            "运行编号": f"RUN-{item.get('编号')}-TEMPLATE",
            "巡检编号": item.get("编号"),
            "巡检名称": item.get("名称"),
            "脚本标识": item.get("脚本标识"),
            "计划频率": item.get("建议频率"),
            "开始时间": "未执行",
            "结束时间": "未执行",
            "退出码": None,
            "结果": "未执行",
            "摘要": "模板记录，尚未运行巡检。",
            "日志路径": "",
            "是否触发修复": False,
            "是否进入诊断": False,
            "是否进入经验提炼": False,
            "是否实际执行巡检": False,
            "是否触发n8n": False,
            "是否真实联网": False,
            "是否写正式库": False,
            "是否写旧系统": False
        })
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "规则文件": str(rule_path),
        "调度草案": str(schedule_path),
        "默认开关": rules.get("默认开关", {}),
        "运行记录字段": rules.get("运行记录字段", []),
        "经验沉淀规则": rules.get("经验沉淀规则", {}),
        "运行记录模板": records,
        "汇总": {
            "模板数量": len(records),
            "未执行数量": sum(1 for item in records if item["结果"] == "未执行"),
            "实际执行巡检数量": sum(1 for item in records if item["是否实际执行巡检"]),
            "触发修复数量": sum(1 for item in records if item["是否触发修复"]),
            "进入诊断数量": sum(1 for item in records if item["是否进入诊断"]),
            "进入经验提炼数量": sum(1 for item in records if item["是否进入经验提炼"]),
            "触发n8n数量": sum(1 for item in records if item["是否触发n8n"]),
            "真实联网数量": sum(1 for item in records if item["是否真实联网"]),
            "写正式库数量": sum(1 for item in records if item["是否写正式库"]),
            "写旧系统数量": sum(1 for item in records if item["是否写旧系统"])
        },
        "当前结论": "无人值守只读巡检运行记录模板已生成；当前所有巡检均未执行，只登记未来运行记录结构。"
    }
    output_dir = manager / "03数据" / "无人值守守护"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "无人值守只读巡检运行记录模板_最新.json"
    latest = output_dir / "无人值守只读巡检运行记录模板_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"模板数量": len(records), "实际执行巡检数量": report["汇总"]["实际执行巡检数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
