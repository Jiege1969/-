# -*- coding: utf-8 -*-
"""
名称：生成无人值守任务执行器骨架报告.py
作用：基于无人值守任务队列种子、状态机和权限分级，生成只计划不执行的任务执行器骨架报告。
触发方式：python 生成无人值守任务执行器骨架报告.py
依赖：Python标准库；无人值守任务执行器骨架规则.json；无人值守任务队列种子_最新.json。
所属系统：00杰哥系统总管
安全边界：只生成任务计划报告；不调用任务执行器；不触发n8n；不联网；不发送企业微信；不写正式库；不写旧系统。
创建/修改记录：2026-04-28 创建无人值守任务执行器骨架报告脚本。
标识：unattended-task-executor-skeleton-report
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


def decide_task(task: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    name = task.get("任务名称", "")
    risk = task.get("风险等级", "")
    marker = task.get("执行器标识", "")
    switches = rules.get("默认开关", {})
    blockers = rules.get("强制阻断关键词", [])
    allowed_risks = set(rules.get("自动计划允许等级", []))
    hit_blockers = [word for word in blockers if word in name]

    if hit_blockers or risk.startswith("L3") or marker == "无":
        plan_state = "禁止执行"
        plan_action = "阻断"
        reason = "命中高风险、无执行器或强制阻断关键词"
    elif risk in allowed_risks and switches.get("允许实际调用执行器") is False:
        plan_state = "待处理"
        plan_action = "仅生成计划"
        reason = "风险等级允许计划，但执行器总开关关闭"
    elif risk in allowed_risks:
        plan_state = "执行中候选"
        plan_action = "候选"
        reason = "风险等级允许，但仍需后续闸口复核"
    else:
        plan_state = "待人工确认"
        plan_action = "等待许可令"
        reason = "风险等级需要人工确认"

    return {
        "任务编号": task.get("任务编号"),
        "任务名称": name,
        "所属模块": task.get("所属模块"),
        "风险等级": risk,
        "原状态": task.get("当前状态"),
        "计划状态": plan_state,
        "计划动作": plan_action,
        "执行器标识": marker,
        "命中阻断词": hit_blockers,
        "是否实际调用执行器": False,
        "是否触发n8n": False,
        "是否真实联网": False,
        "是否真实发送": False,
        "是否写正式库": False,
        "是否写旧系统": False,
        "原因": reason
    }


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    rule_path = manager / "01配置" / "无人值守任务执行器骨架规则.json"
    queue_path = manager / "03数据" / "无人值守守护" / "无人值守任务队列种子_最新.json"
    state_rule_path = manager / "01配置" / "无人值守任务状态机规则.json"
    permission_rule_path = manager / "01配置" / "无人值守守护权限分级规则.json"
    rules = load_json(rule_path)
    queue = load_json(queue_path)
    state_rules = load_json(state_rule_path)
    permission_rules = load_json(permission_rule_path)
    tasks = queue.get("任务队列", [])
    plans = [decide_task(task, rules) for task in tasks]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "执行模式": rules.get("执行模式"),
        "规则文件": str(rule_path),
        "队列文件": str(queue_path),
        "状态机文件": str(state_rule_path),
        "权限分级文件": str(permission_rule_path),
        "默认开关": rules.get("默认开关", {}),
        "允许状态": state_rules.get("允许状态", []),
        "权限等级": permission_rules.get("权限等级", {}),
        "任务计划": plans,
        "汇总": {
            "任务数量": len(plans),
            "仅生成计划数量": sum(1 for item in plans if item["计划动作"] == "仅生成计划"),
            "阻断数量": sum(1 for item in plans if item["计划动作"] == "阻断"),
            "待人工确认数量": sum(1 for item in plans if item["计划动作"] == "等待许可令"),
            "实际调用执行器数量": sum(1 for item in plans if item["是否实际调用执行器"]),
            "触发n8n数量": sum(1 for item in plans if item["是否触发n8n"]),
            "真实联网数量": sum(1 for item in plans if item["是否真实联网"]),
            "真实发送数量": sum(1 for item in plans if item["是否真实发送"]),
            "写正式库数量": sum(1 for item in plans if item["是否写正式库"]),
            "写旧系统数量": sum(1 for item in plans if item["是否写旧系统"])
        },
        "当前结论": "无人值守任务执行器骨架已生成；当前只做计划和阻断判断，不实际调用任何执行器。"
    }
    output_dir = manager / "03数据" / "无人值守守护"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "无人值守任务执行器骨架报告_最新.json"
    latest = output_dir / "无人值守任务执行器骨架报告_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"任务数量": len(plans), "阻断数量": report["汇总"]["阻断数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
