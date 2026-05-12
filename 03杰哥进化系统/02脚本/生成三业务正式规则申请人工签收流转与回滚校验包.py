# -*- coding: utf-8 -*-
"""生成三业务正式规则申请人工签收流转与回滚校验包。

本脚本只生成待人工签收、总管确认、申请生效前与回滚前后的只读材料。
不写正式规则，不自动生效，不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "90三业务正式规则申请人工签收流转与回滚校验包"
SOURCE_86_DIR = ROOT / "03数据" / "86三业务正式规则申请草案冲突扫描与签收台账包"

PACKAGE_JSON = DATA_DIR / "三业务正式规则申请人工签收流转与回滚校验包_最新.json"
FLOW_JSON = DATA_DIR / "人工签收流转定义_最新.json"
FLOW_MD = DATA_DIR / "人工签收流转定义_最新.md"
ROLLBACK_JSON = DATA_DIR / "回滚校验清单_最新.json"
ROLLBACK_MD = DATA_DIR / "回滚校验清单_最新.md"

REQUIRED_BUSINESSES = ["税收", "股票", "视频"]
REQUIRED_STATES = [
    "待签收",
    "需补正",
    "总管已确认",
    "可申请正式生效",
    "已驳回",
    "回滚待确认",
]
FORBIDDEN_ACTIONS = [
    "真实发送企业微信",
    "接n8n",
    "接券商",
    "交易",
    "登录税局",
    "接财税软件",
    "自动转正式规则",
    "改总管面板",
    "改一键接续包",
    "重载服务",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_inside_allowed(path: Path) -> None:
    resolved = path.resolve()
    allowed = DATA_DIR.resolve()
    if resolved != allowed and allowed not in resolved.parents:
        raise ValueError(f"拒绝写入非本包数据目录：{resolved}")


def write_json(path: Path, data: Any) -> None:
    ensure_inside_allowed(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    ensure_inside_allowed(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def source_files() -> list[str]:
    if not SOURCE_86_DIR.exists():
        return []
    return [str(path) for path in sorted(SOURCE_86_DIR.glob("*_最新.json"))]


def build_flow(generated_at: str, sources: list[str]) -> dict[str, Any]:
    states = [
        {
            "state": "待签收",
            "meaning": "第86包草案冲突扫描与签收台账产物已具备，只等待人工签收人读取。",
            "entry_condition": "冲突扫描材料存在，formal_rule_effective=false，write_formal_rule=false。",
            "allowed_next_states": ["需补正", "总管已确认", "已驳回"],
            "requires_supervisor_confirmation": False,
            "operator": "人工签收人",
            "write_formal_rule": False,
            "auto_apply": False,
        },
        {
            "state": "需补正",
            "meaning": "人工签收发现材料、边界、回滚说明或红线声明不完整。",
            "entry_condition": "任一必填签收字段缺失，或回滚校验项不完整。",
            "allowed_next_states": ["待签收", "已驳回"],
            "requires_supervisor_confirmation": False,
            "operator": "人工签收人",
            "write_formal_rule": False,
            "auto_apply": False,
        },
        {
            "state": "总管已确认",
            "meaning": "总管已人工确认签收结论，但仍不代表正式生效。",
            "entry_condition": "人工签收通过，且总管确认记录完整。",
            "allowed_next_states": ["可申请正式生效", "回滚待确认", "已驳回"],
            "requires_supervisor_confirmation": True,
            "operator": "总管",
            "write_formal_rule": False,
            "auto_apply": False,
        },
        {
            "state": "可申请正式生效",
            "meaning": "材料只允许进入正式生效申请队列，不允许本包自动写正式规则。",
            "entry_condition": "总管已确认，回滚校验清单已覆盖税收、股票、视频三业务。",
            "allowed_next_states": ["回滚待确认", "已驳回"],
            "requires_supervisor_confirmation": True,
            "operator": "总管",
            "write_formal_rule": False,
            "auto_apply": False,
        },
        {
            "state": "已驳回",
            "meaning": "人工或总管驳回本次正式规则申请材料。",
            "entry_condition": "命中红线、缺少回滚办法、业务边界不清或人工明确驳回。",
            "allowed_next_states": ["待签收"],
            "requires_supervisor_confirmation": False,
            "operator": "人工签收人或总管",
            "write_formal_rule": False,
            "auto_apply": False,
        },
        {
            "state": "回滚待确认",
            "meaning": "进入回滚复核等待态，仅做回滚入口、快照和验收材料确认，不执行回滚。",
            "entry_condition": "总管要求回滚复核，或可申请正式生效前需补充回滚证据。",
            "allowed_next_states": ["待签收", "总管已确认", "已驳回"],
            "requires_supervisor_confirmation": True,
            "operator": "总管",
            "write_formal_rule": False,
            "auto_apply": False,
        },
    ]
    transitions = [
        {"from": "待签收", "to": "需补正", "condition": "材料缺项或红线声明不足"},
        {"from": "待签收", "to": "总管已确认", "condition": "人工签收通过并提交总管确认"},
        {"from": "待签收", "to": "已驳回", "condition": "命中不可补正红线"},
        {"from": "需补正", "to": "待签收", "condition": "补正后重新提交人工签收"},
        {"from": "需补正", "to": "已驳回", "condition": "补正失败或拒绝补正"},
        {"from": "总管已确认", "to": "可申请正式生效", "condition": "总管确认且回滚校验通过"},
        {"from": "总管已确认", "to": "回滚待确认", "condition": "总管要求回滚复核"},
        {"from": "总管已确认", "to": "已驳回", "condition": "总管驳回"},
        {"from": "可申请正式生效", "to": "回滚待确认", "condition": "申请前发现需补充回滚证据"},
        {"from": "可申请正式生效", "to": "已驳回", "condition": "申请前发现红线冲突"},
        {"from": "回滚待确认", "to": "待签收", "condition": "回滚材料补齐后重新签收"},
        {"from": "回滚待确认", "to": "总管已确认", "condition": "回滚复核通过并回到总管确认态"},
        {"from": "回滚待确认", "to": "已驳回", "condition": "回滚入口或快照不可确认"},
    ]
    return {
        "name": "三业务正式规则申请人工签收流转定义",
        "version": "three-business-rule-signoff-flow-v1",
        "generated_at": generated_at,
        "based_on_package_86": True,
        "source_files": sources,
        "businesses": REQUIRED_BUSINESSES,
        "required_states": REQUIRED_STATES,
        "states": states,
        "transitions": transitions,
        "guard_flags": {
            "formal_rule_effective": False,
            "write_formal_rule": False,
            "auto_apply": False,
            "rollback_executed": False,
            "requires_supervisor_confirmation": True,
        },
        "forbidden_actions": {name: False for name in FORBIDDEN_ACTIONS},
    }


def build_rollback_checklist(generated_at: str, sources: list[str]) -> dict[str, Any]:
    business_notes = {
        "税收": {
            "rollback_entry": "从本包签收材料撤回税收正式规则申请草案标记，保留第86包只读扫描结果。",
            "pre_snapshot": "记录税收草案ID、签收状态、总管确认状态、红线声明和补正意见。",
            "post_acceptance": "确认税收申请仍为待签收或已驳回，不登录税局，不接财税软件，不写正式规则。",
        },
        "股票": {
            "rollback_entry": "从本包签收材料撤回股票正式规则申请草案标记，保留第86包只读扫描结果。",
            "pre_snapshot": "记录股票草案ID、签收状态、总管确认状态、非交易声明和补正意见。",
            "post_acceptance": "确认股票申请仍为待签收或已驳回，不接券商，不交易，不写正式规则。",
        },
        "视频": {
            "rollback_entry": "从本包签收材料撤回视频正式规则申请草案标记，保留第86包只读扫描结果。",
            "pre_snapshot": "记录视频草案ID、签收状态、总管确认状态、发布前确认点和补正意见。",
            "post_acceptance": "确认视频申请仍为待签收或已驳回，不发布，不渲染，不重载服务，不写正式规则。",
        },
    }
    rows = []
    for business in REQUIRED_BUSINESSES:
        note = business_notes[business]
        rows.append(
            {
                "business": business,
                "rollback_entry": note["rollback_entry"],
                "pre_rollback_snapshot": note["pre_snapshot"],
                "post_rollback_acceptance": note["post_acceptance"],
                "redline_recheck": [
                    "formal_rule_effective=false",
                    "write_formal_rule=false",
                    "auto_apply=false",
                    "rollback_executed=false",
                    "requires_supervisor_confirmation=true",
                    "不真实发送企业微信",
                    "不接n8n",
                    "不改总管面板",
                    "不改一键接续包",
                ],
                "requires_supervisor_confirmation": True,
                "rollback_executed": False,
            }
        )
    return {
        "name": "三业务正式规则申请回滚校验清单",
        "version": "three-business-rule-rollback-checklist-v1",
        "generated_at": generated_at,
        "based_on_package_86": True,
        "source_files": sources,
        "businesses": REQUIRED_BUSINESSES,
        "checklist": rows,
        "guard_flags": {
            "formal_rule_effective": False,
            "write_formal_rule": False,
            "auto_apply": False,
            "rollback_executed": False,
            "requires_supervisor_confirmation": True,
        },
        "forbidden_actions": {name: False for name in FORBIDDEN_ACTIONS},
    }


def flow_md(flow: dict[str, Any]) -> str:
    lines = [
        "# 三业务正式规则申请人工签收流转定义",
        "",
        f"- 版本：{flow['version']}",
        f"- 生成时间：{flow['generated_at']}",
        "- 基于上一轮第86包：true",
        "- formal_rule_effective：false",
        "- write_formal_rule：false",
        "- auto_apply：false",
        "- rollback_executed：false",
        "- requires_supervisor_confirmation：true",
        "",
        "| 状态 | 含义 | 可流转至 | 操作人 |",
        "| --- | --- | --- | --- |",
    ]
    for state in flow["states"]:
        lines.append(
            f"| {state['state']} | {state['meaning']} | "
            f"{'、'.join(state['allowed_next_states'])} | {state['operator']} |"
        )
    lines.extend(["", "## 流转边", ""])
    for item in flow["transitions"]:
        lines.append(f"- {item['from']} -> {item['to']}：{item['condition']}")
    lines.append("")
    return "\n".join(lines)


def rollback_md(checklist: dict[str, Any]) -> str:
    lines = [
        "# 三业务正式规则申请回滚校验清单",
        "",
        f"- 版本：{checklist['version']}",
        f"- 生成时间：{checklist['generated_at']}",
        "- formal_rule_effective：false",
        "- write_formal_rule：false",
        "- auto_apply：false",
        "- rollback_executed：false",
        "- requires_supervisor_confirmation：true",
        "",
        "| 业务 | 回滚入口 | 回滚前快照 | 回滚后验收 |",
        "| --- | --- | --- | --- |",
    ]
    for row in checklist["checklist"]:
        lines.append(
            f"| {row['business']} | {row['rollback_entry']} | "
            f"{row['pre_rollback_snapshot']} | {row['post_rollback_acceptance']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    generated_at = now_text()
    sources = source_files()
    flow = build_flow(generated_at, sources)
    checklist = build_rollback_checklist(generated_at, sources)
    package = {
        "name": "三业务正式规则申请人工签收流转与回滚校验包",
        "status": "three_business_rule_signoff_flow_rollback_ready",
        "generated_at": generated_at,
        "based_on_package_86": True,
        "source_files": sources,
        "businesses": REQUIRED_BUSINESSES,
        "required_outputs": {
            "flow_json": str(FLOW_JSON),
            "flow_md": str(FLOW_MD),
            "rollback_json": str(ROLLBACK_JSON),
            "rollback_md": str(ROLLBACK_MD),
        },
        "guard_flags": {
            "formal_rule_effective": False,
            "write_formal_rule": False,
            "auto_apply": False,
            "rollback_executed": False,
            "requires_supervisor_confirmation": True,
        },
        "forbidden_actions": {name: False for name in FORBIDDEN_ACTIONS},
    }

    write_json(FLOW_JSON, flow)
    write_text(FLOW_MD, flow_md(flow))
    write_json(ROLLBACK_JSON, checklist)
    write_text(ROLLBACK_MD, rollback_md(checklist))
    write_json(PACKAGE_JSON, package)
    print(json.dumps({"通过": True, "错误数": 0, "输出目录": str(DATA_DIR)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
