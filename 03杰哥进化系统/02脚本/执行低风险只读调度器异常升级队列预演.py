# -*- coding: utf-8 -*-
"""执行低风险只读调度器异常升级队列预演。

执行含义仅为读取本地草案与队列，生成暂停判定报告；不执行任何升级动作。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "110低风险只读调度器异常升级草案与总管确认队列包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器异常升级草案与总管确认队列包验收"

RULE_JSON = DATA_DIR / "异常升级规则_最新.json"
QUEUE_JSON = DATA_DIR / "总管确认队列_最新.json"
REPORT_JSON = DATA_DIR / "升级队列预演报告_最新.json"
REPORT_MD = DATA_DIR / "升级队列预演报告_最新.md"
RUN_LOG = LOG_DIR / "low-risk-readonly-scheduler-escalation-confirmation-queue-run-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safety_flags() -> dict[str, bool]:
    return {
        "executed": False,
        "auto_resume": False,
        "commands_executed": False,
        "external_call": False,
        "reload_service": False,
        "real_wecom_send": False,
        "connect_n8n": False,
        "connect_broker": False,
        "trade": False,
        "login_tax_bureau": False,
        "connect_finance_tax_software": False,
        "promote_to_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
    }


def simulate_queue_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "queue_id": item.get("id"),
        "category": item.get("category"),
        "status": item.get("status"),
        "pause_required": True,
        "continue_allowed": False,
        "requires_supervisor_confirmation": True,
        "scheduler_decision": "paused_waiting_supervisor_confirmation",
        "executed": False,
        "auto_resume": False,
        "external_call": False,
        "reload_service": False,
        "decision_note": "只读预演确认进入总管确认队列，不执行升级动作。",
    }


def report_md(report: dict[str, Any]) -> str:
    rows = [
        "| {queue_id} | {category} | {status} | {pause_required} | {continue_allowed} | {requires_supervisor_confirmation} | {executed} | {auto_resume} |".format(**item)
        for item in report["results"]
    ]
    return "\n".join(
        [
            "# 升级队列预演报告",
            "",
            f"- 生成时间: {report['generated_at']}",
            f"- pass: {report['pass']}",
            f"- error_count: {report['error_count']}",
            f"- queue_count: {report['queue_count']}",
            "- pause_required: true",
            "- continue_allowed: false",
            "- requires_supervisor_confirmation: true",
            "- executed: false",
            "- auto_resume: false",
            "- external_call: false",
            "- reload_service: false",
            "",
            "| 队列ID | 类别 | status | pause_required | continue_allowed | requires_supervisor_confirmation | executed | auto_resume |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def main() -> int:
    errors: list[str] = []
    if not RULE_JSON.exists():
        errors.append(f"缺少异常升级规则: {RULE_JSON}")
    if not QUEUE_JSON.exists():
        errors.append(f"缺少总管确认队列: {QUEUE_JSON}")

    rules = read_json(RULE_JSON) if RULE_JSON.exists() else {"rules": []}
    queue = read_json(QUEUE_JSON) if QUEUE_JSON.exists() else {"items": []}
    items = queue.get("items", [])
    results = [simulate_queue_item(item) for item in items]

    if len(rules.get("rules", [])) < 6:
        errors.append("异常升级规则数量必须不少于6")
    if len(items) < 6:
        errors.append("总管确认队列数量必须不少于6")

    for item in items:
        if item.get("status") != "需总管确认":
            errors.append(f"{item.get('id')} status 必须为 需总管确认")
        for key in ["executed", "auto_resume", "external_call", "reload_service"]:
            if item.get(key) is not False:
                errors.append(f"{item.get('id')} {key} 必须为 false")

    for result in results:
        if result["pause_required"] is not True:
            errors.append(f"{result['queue_id']} pause_required 必须为 true")
        if result["continue_allowed"] is not False:
            errors.append(f"{result['queue_id']} continue_allowed 必须为 false")
        if result["requires_supervisor_confirmation"] is not True:
            errors.append(f"{result['queue_id']} requires_supervisor_confirmation 必须为 true")

    report = {
        "name": "低风险只读调度器异常升级队列预演报告",
        "generated_at": now(),
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "readonly_draft_only": True,
        "queue_count": len(items),
        "rule_count": len(rules.get("rules", [])),
        "pause_required": True,
        "continue_allowed": False,
        "requires_supervisor_confirmation": True,
        "executed": False,
        "auto_resume": False,
        "external_call": False,
        "reload_service": False,
        "safety_confirmation": safety_flags(),
        "results": results,
    }
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, report_md(report))
    write_json(RUN_LOG, report)
    print(json.dumps({"pass": report["pass"], "error_count": report["error_count"], "queue_count": report["queue_count"], "pause_required": True, "continue_allowed": False, "requires_supervisor_confirmation": True}, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
