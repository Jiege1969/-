# -*- coding: utf-8 -*-
"""
名称：验证轻量任务契约规则沉淀.py
作用：只读解析03进化系统本地规则卡、审计清单和证据JSON，确认轻量任务契约边界未突破。
安全边界：不触发n8n，不发送企业微信，不写正式库，不调用券商接口，不自动交易，不发起外部网络调用。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "03数据" / "28轻量任务契约规则沉淀"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"检查项": name, "通过": bool(passed), "详情": detail})


def all_false(mapping: dict[str, Any]) -> bool:
    return all(value is False for value in mapping.values())


def main() -> int:
    rule_path = DATA_DIR / "轻量任务契约规则卡_最新.json"
    audit_path = DATA_DIR / "轻量任务契约审计清单_最新.json"
    evidence_path = DATA_DIR / "轻量任务契约规则沉淀证据_最新.json"
    checks: list[dict[str, Any]] = []

    add_check(checks, "规则卡JSON存在", rule_path.exists(), str(rule_path))
    add_check(checks, "审计清单JSON存在", audit_path.exists(), str(audit_path))
    add_check(checks, "证据JSON存在", evidence_path.exists(), str(evidence_path))
    if not all(item["通过"] for item in checks):
        print(json.dumps({"通过": 0, "失败": len(checks), "检查项": checks}, ensure_ascii=False, indent=2))
        return 1

    rule_card = load_json(rule_path)
    audit = load_json(audit_path)
    evidence = load_json(evidence_path)

    rules = rule_card.get("核心规则", [])
    rule_ids = {item.get("规则ID") for item in rules}
    expected_rule_ids = {f"LTC-{index:03d}" for index in range(1, 8)}
    audit_items = audit.get("检查项", [])
    audit_ids = [item.get("检查项ID") for item in audit_items]
    shadow = evidence.get("影子链路声明", {})
    task_order = shadow.get("task_order_json", {})
    safety = evidence.get("安全边界", {})
    card_safety = rule_card.get("安全边界", {})

    required_fields = {
        "task_id",
        "source_system",
        "target_system",
        "intent",
        "scope",
        "inputs",
        "expected_outputs",
        "safety_boundary",
        "dry_run",
        "real_action_requested",
        "acceptance",
    }

    add_check(checks, "规则ID完整", expected_rule_ids.issubset(rule_ids), sorted(rule_ids))
    add_check(checks, "规则卡覆盖不新增第二中枢", rule_card.get("总体原则", {}).get("不新增第二中枢") is True, rule_card.get("总体原则"))
    add_check(checks, "规则卡覆盖SQLite影子权威台账", rule_card.get("总体原则", {}).get("SQLite影子权威台账") is True, rule_card.get("总体原则"))
    add_check(checks, "规则卡覆盖Redis影子映射增强", rule_card.get("总体原则", {}).get("Redis影子映射增强") is True, rule_card.get("总体原则"))
    add_check(checks, "规则卡覆盖n8n干跑", rule_card.get("总体原则", {}).get("n8n干跑") is True, rule_card.get("总体原则"))
    add_check(checks, "规则卡覆盖真实动作单线闸门", rule_card.get("总体原则", {}).get("真实动作单线闸门") is True, rule_card.get("总体原则"))
    add_check(checks, "规则卡覆盖股票分析only", rule_card.get("总体原则", {}).get("股票分析only") is True, rule_card.get("总体原则"))
    add_check(checks, "标准任务单JSON必填字段完整", required_fields.issubset(set(task_order.get("required_fields", []))), task_order)
    add_check(checks, "任务单保持干跑且无真实动作请求", task_order.get("dry_run") is True and task_order.get("real_action_requested") is False, task_order)
    add_check(checks, "不新增第二中枢证据成立", shadow.get("center_role") == "rule_deposit_only" and shadow.get("second_center_created") is False, shadow)
    add_check(checks, "SQLite仅为影子权威台账", shadow.get("sqlite", {}).get("role") == "shadow_authoritative_ledger" and shadow.get("sqlite", {}).get("official_db_write") is False and shadow.get("sqlite", {}).get("drives_real_action") is False, shadow.get("sqlite"))
    add_check(checks, "Redis仅为影子映射增强", shadow.get("redis", {}).get("role") == "shadow_mapping_enhancement" and shadow.get("redis", {}).get("real_action_queue") is False and shadow.get("redis", {}).get("permission_release") is False, shadow.get("redis"))
    add_check(checks, "n8n仅干跑且未触发", shadow.get("n8n", {}).get("mode") == "dry_run_only" and shadow.get("n8n", {}).get("triggered") is False and shadow.get("n8n", {}).get("webhook_called") is False and shadow.get("n8n", {}).get("workflow_enabled") is False, shadow.get("n8n"))
    add_check(checks, "真实动作单线闸门关闭", shadow.get("gate", {}).get("real_actions_enabled") is False and shadow.get("gate", {}).get("mode") == "single_line_manual_gate" and shadow.get("gate", {}).get("multi_gate_release") is False, shadow.get("gate"))
    add_check(checks, "股票范围为分析only", shadow.get("stock_scope") == "analysis_only", shadow.get("stock_scope"))
    add_check(checks, "审计检查项数量为8", len(audit_items) == 8, len(audit_items))
    add_check(checks, "审计检查项ID唯一", len(set(audit_ids)) == len(audit_ids), audit_ids)
    add_check(checks, "审计检查项均为阻断项", all(item.get("阻断项") is True for item in audit_items), audit_items)
    add_check(checks, "证据安全边界全关闭", all_false(safety), safety)
    add_check(checks, "规则卡安全边界全关闭", all_false(card_safety), card_safety)

    failed_items = [item for item in checks if not item["通过"]]
    result = {
        "验证对象": str(DATA_DIR),
        "验证方式": "只读本地JSON解析",
        "通过": len(checks) - len(failed_items),
        "失败": len(failed_items),
        "阻断项": len(failed_items),
        "检查项": checks,
        "安全声明": "未触发n8n、企业微信、正式库、券商接口或自动交易",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failed_items else 1


if __name__ == "__main__":
    raise SystemExit(main())
