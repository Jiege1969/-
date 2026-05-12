# -*- coding: utf-8 -*-
"""验证低风险自主任务本地只读调度预演包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "96低风险自主任务本地只读调度预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险自主任务本地只读调度预演包验收"

RULES_JSON = DATA_DIR / "调度预演规则_最新.json"
RULES_MD = DATA_DIR / "调度预演规则_最新.md"
SCHEDULE_JSON = DATA_DIR / "本地只读调度计划_最新.json"
SCHEDULE_MD = DATA_DIR / "本地只读调度计划_最新.md"
REPORT_JSON = DATA_DIR / "调度预演报告_最新.json"
REPORT_MD = DATA_DIR / "调度预演报告_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险自主任务本地只读调度预演包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险自主任务本地只读调度预演包_最新.md"

VERIFY_JSON = LOG_DIR / "low-risk-autonomous-local-scheduler-preview-verify-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def require_false(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not False:
        errors.append(f"{scope}.{key} 必须为 false")


def require_true(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not True:
        errors.append(f"{scope}.{key} 必须为 true")


def main() -> int:
    generated_at = now()
    errors: list[str] = []
    required_files = [
        RULES_JSON,
        RULES_MD,
        SCHEDULE_JSON,
        SCHEDULE_MD,
        REPORT_JSON,
        REPORT_MD,
        PACKAGE_JSON,
        PACKAGE_MD,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件：{path}")

    rules = read_json(RULES_JSON) if RULES_JSON.exists() else {}
    schedule = read_json(SCHEDULE_JSON) if SCHEDULE_JSON.exists() else {"tasks": []}
    report = read_json(REPORT_JSON) if REPORT_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}

    for field in ["cron_like_preview", "manual_trigger_preview", "pause_gate_check", "evidence_required"]:
        if field not in rules:
            errors.append(f"调度预演规则缺少字段：{field}")
    require_false(errors, rules.get("cron_like_preview", {}), "enabled", "rules.cron_like_preview")
    require_false(errors, rules.get("cron_like_preview", {}), "scheduled", "rules.cron_like_preview")
    require_false(errors, rules.get("manual_trigger_preview", {}), "enabled", "rules.manual_trigger_preview")
    require_true(errors, rules.get("pause_gate_check", {}), "enabled", "rules.pause_gate_check")
    require_true(errors, rules.get("evidence_required", {}), "enabled", "rules.evidence_required")

    tasks = schedule.get("tasks", [])
    if len(tasks) < 8:
        errors.append("本地只读调度计划任务数不足 8 个")
    schedule_defaults = schedule.get("defaults", {})
    require_false(errors, schedule_defaults, "scheduled", "schedule.defaults")
    require_false(errors, schedule_defaults, "auto_execute", "schedule.defaults")
    require_true(errors, schedule_defaults, "dry_run_only", "schedule.defaults")
    require_false(errors, schedule_defaults, "external_call", "schedule.defaults")

    seen_ids = set()
    for task in tasks:
        task_id = task.get("id", "<missing>")
        if task_id in seen_ids:
            errors.append(f"{task_id} 重复")
        seen_ids.add(task_id)
        require_false(errors, task, "scheduled", task_id)
        require_false(errors, task, "auto_execute", task_id)
        require_true(errors, task, "dry_run_only", task_id)
        require_false(errors, task, "external_call", task_id)
        require_false(errors, task, "real_send", task_id)
        require_false(errors, task, "reload_service", task_id)
        require_false(errors, task, "write_formal_rule", task_id)
        require_false(errors, task, "task_executed", task_id)
        if task.get("execution_adapter") != "none":
            errors.append(f"{task_id}.execution_adapter 必须为 none")
        if not isinstance(task.get("depends_on", []), list):
            errors.append(f"{task_id}.depends_on 必须为列表")

    if report.get("pass") is not True:
        errors.append("调度预演报告必须 pass=true")
    if report.get("error_count") != 0:
        errors.append("调度预演报告 error_count 必须为 0")
    require_true(errors, report, "preview_only", "report")
    require_true(errors, report, "sort_preview_only", "report")
    require_true(errors, report, "dependency_preview_only", "report")
    require_false(errors, report, "tasks_executed", "report")
    if report.get("executed_task_count") != 0:
        errors.append("report.executed_task_count 必须为 0")

    for scope, data in [("rules.hard_red_line_confirmation", rules.get("hard_red_line_confirmation", {})), ("schedule.hard_red_line_confirmation", schedule.get("hard_red_line_confirmation", {})), ("package", package), ("report", report)]:
        for key in ["auto_execute", "external_call", "real_send", "reload_service", "write_formal_rule"]:
            require_false(errors, data, key, scope)

    verification = {
        "name": "低风险自主任务本地只读调度预演包验收",
        "generated_at": generated_at,
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "fixed_log_path": str(VERIFY_JSON),
        "required_file_count": len(required_files),
        "existing_file_count": sum(1 for path in required_files if path.exists()),
        "task_count": len(tasks),
        "auto_execute": False,
        "external_call": False,
        "real_send": False,
        "reload_service": False,
        "write_formal_rule": False,
        "hard_red_line_confirmation": {
            "real_wecom_send": False,
            "trigger_n8n": False,
            "broker_connection": False,
            "trade_order": False,
            "tax_bureau_login": False,
            "finance_tax_software_connection": False,
            "write_formal_rule": False,
            "reload_service": False,
            "modify_supervisor_panel": False,
            "modify_one_click_continuation_package": False,
        },
        "scope_statement": "只预演本地排序和依赖，未执行任务，未调用业务接口。",
    }
    write_json(VERIFY_JSON, verification)
    print(json.dumps({"pass": verification["pass"], "error_count": verification["error_count"], "log": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if verification["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
