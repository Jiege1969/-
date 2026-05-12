# -*- coding: utf-8 -*-
"""执行低风险只读调度器证据留存到期检查与不删除预演。
执行含义仅为读取 118 包内策略和队列，生成不删除预演报告；不删除、不移动、不触发外部动作。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "118低风险只读调度器证据留存到期检查与不删除预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器证据留存到期检查与不删除预演包验收"

POLICY_JSON = DATA_DIR / "证据留存到期检查策略_最新.json"
INVENTORY_JSON = DATA_DIR / "证据留存样本清单_最新.json"
QUEUE_JSON = DATA_DIR / "到期不删除处理队列_最新.json"
REPORT_JSON = DATA_DIR / "不删除预演报告_最新.json"
REPORT_MD = DATA_DIR / "不删除预演报告_最新.md"
RUN_LOG = LOG_DIR / "low-risk-readonly-scheduler-evidence-retention-expiry-run-最新.json"


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
        "read_only": True,
        "delete_file": False,
        "remove_directory": False,
        "move_history_package": False,
        "overwrite_history_package": False,
        "external_call": False,
        "send_notification": False,
        "connect_n8n": False,
        "reload_service": False,
        "promote_to_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
        "write_scope_is_118_only": True,
    }


def report_md(report: dict[str, Any]) -> str:
    lines = [
        "# 不删除预演报告",
        "",
        f"- 生成时间: {report['generated_at']}",
        f"- pass: {report['pass']}",
        f"- error_count: {report['error_count']}",
        "- delete_allowed: false",
        "- dry_run_only: true",
        "- history_content_untouched: true",
        "",
        "| 队列ID | 样本ID | 决策 | delete_allowed | evidence_retained | history_content_untouched |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["results"]:
        lines.append(
            f"| {item['queue_id']} | {item['sample_id']} | {item['decision']} | {item['delete_allowed']} | {item['evidence_retained']} | {item['history_content_untouched']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    errors: list[str] = []
    for path in [POLICY_JSON, INVENTORY_JSON, QUEUE_JSON]:
        if not path.exists():
            errors.append(f"缺少输入文件: {path}")
    policy = read_json(POLICY_JSON) if POLICY_JSON.exists() else {"rules": []}
    inventory = read_json(INVENTORY_JSON) if INVENTORY_JSON.exists() else {"samples": []}
    queue = read_json(QUEUE_JSON) if QUEUE_JSON.exists() else {"items": []}

    results = []
    for item in queue.get("items", []):
        if item.get("delete_allowed") is not False:
            errors.append(f"{item.get('id')} delete_allowed 必须为 false")
        results.append(
            {
                "queue_id": item.get("id"),
                "sample_id": item.get("sample_id"),
                "decision": "不删除",
                "delete_allowed": False,
                "dry_run_only": True,
                "requires_supervisor_confirmation": True,
                "evidence_retained": True,
                "history_content_untouched": True,
                "actual_delete_performed": False,
                "actual_move_performed": False,
                "external_call": False,
            }
        )
    if len(policy.get("rules", [])) < 5:
        errors.append("策略规则数必须不少于 5")
    if len(inventory.get("samples", [])) < 4:
        errors.append("证据样本数必须不少于 4")
    if len(results) != len(queue.get("items", [])):
        errors.append("预演结果数必须等于队列数")

    report = {
        "name": "低风险只读调度器证据留存到期检查与不删除预演报告",
        "generated_at": now(),
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "readonly_dry_run_only": True,
        "delete_allowed": False,
        "dry_run_only": True,
        "history_content_untouched": True,
        "write_scope_is_118_only": True,
        "policy_rule_count": len(policy.get("rules", [])),
        "inventory_sample_count": len(inventory.get("samples", [])),
        "queue_count": len(queue.get("items", [])),
        "result_count": len(results),
        "results": results,
        "safety_confirmation": safety_flags(),
    }
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, report_md(report))
    write_json(RUN_LOG, report)
    print(json.dumps({"pass": report["pass"], "error_count": report["error_count"], "queue_count": report["queue_count"], "delete_allowed": False}, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
