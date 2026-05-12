# -*- coding: utf-8 -*-
"""验证低风险只读调度器跨日值守接续预演包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "116低风险只读调度器跨日值守接续预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器跨日值守接续预演包验收"

CONFIG_JSON = DATA_DIR / "跨日值守接续配置_最新.json"
CONFIG_MD = DATA_DIR / "跨日值守接续配置_最新.md"
PREVIEW_RESULT_JSON = DATA_DIR / "跨日值守接续预演结果_最新.json"
PREVIEW_RESULT_MD = DATA_DIR / "跨日值守接续预演结果_最新.md"
NEXT_DAY_QUEUE_JSON = DATA_DIR / "次日只读候选队列_最新.json"
NEXT_DAY_QUEUE_MD = DATA_DIR / "次日只读候选队列_最新.md"
HANDOFF_CHECK_JSON = DATA_DIR / "跨日接续一致性检查_最新.json"
HANDOFF_CHECK_MD = DATA_DIR / "跨日接续一致性检查_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器跨日值守接续预演包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器跨日值守接续预演包_最新.md"
VERIFY_JSON = LOG_DIR / "low-risk-readonly-scheduler-cross-day-handoff-verify-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def require_true(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not True:
        errors.append(f"{scope}.{key} 必须为 true")


def require_false(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not False:
        errors.append(f"{scope}.{key} 必须为 false")


def require_boundary(errors: list[str], data: dict[str, Any], scope: str) -> None:
    require_true(errors, data, "preview_only", scope)
    for key in [
        "auto_schedule",
        "auto_execute",
        "actual_execution",
        "external_call",
        "real_wecom_send",
        "connect_n8n",
        "trigger_n8n",
        "broker_connection",
        "trade_order",
        "tax_bureau_login",
        "finance_tax_software_connection",
        "write_formal_rule",
        "auto_promote_formal_rule",
        "modify_supervisor_panel",
        "modify_one_click_continuation_package",
        "register_system_scheduled_task",
        "reload_service",
        "delete_business_artifact",
    ]:
        require_false(errors, data, key, scope)


def main() -> int:
    errors: list[str] = []
    required_files = [
        CONFIG_JSON,
        CONFIG_MD,
        PREVIEW_RESULT_JSON,
        PREVIEW_RESULT_MD,
        NEXT_DAY_QUEUE_JSON,
        NEXT_DAY_QUEUE_MD,
        HANDOFF_CHECK_JSON,
        HANDOFF_CHECK_MD,
        PACKAGE_JSON,
        PACKAGE_MD,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件: {path}")

    config = read_json(CONFIG_JSON) if CONFIG_JSON.exists() else {"handoff_steps": [], "hard_red_line_confirmation": {}}
    preview = read_json(PREVIEW_RESULT_JSON) if PREVIEW_RESULT_JSON.exists() else {"handoff_steps": [], "hard_red_line_confirmation": {}}
    queue = read_json(NEXT_DAY_QUEUE_JSON) if NEXT_DAY_QUEUE_JSON.exists() else {"items": [], "hard_red_line_confirmation": {}}
    handoff_check = read_json(HANDOFF_CHECK_JSON) if HANDOFF_CHECK_JSON.exists() else {"hard_red_line_confirmation": {}}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {"hard_red_line_confirmation": {}}

    data_dir_text = str(DATA_DIR)
    if "116低风险只读调度器跨日值守接续预演包" not in data_dir_text:
        errors.append("验收数据目录必须为116低风险只读调度器跨日值守接续预演包")
    if "112" in data_dir_text:
        errors.append("验收数据目录不得包含112")
    for path in required_files:
        if "112" in str(path):
            errors.append(f"输出文件路径不得包含112: {path}")

    required_names = {"日终只读收束", "未完成项继承", "异常升级草案挂起", "次日只读开局计划", "跨日一致性复核"}
    config_names = {item.get("handoff_name") for item in config.get("handoff_steps", [])}
    missing_names = sorted(required_names - config_names)
    if missing_names:
        errors.append(f"接续配置缺少必需步骤: {missing_names}")

    step_count = len(config.get("handoff_steps", []))
    if step_count < 5:
        errors.append("handoff_step_count 必须不少于 5")
    if config.get("handoff_step_count") != step_count:
        errors.append("config.handoff_step_count 必须等于 handoff_steps 数量")
    if preview.get("handoff_step_count") != step_count:
        errors.append("preview.handoff_step_count 必须等于 config.handoff_step_count")
    if package.get("handoff_step_count") != step_count:
        errors.append("package.handoff_step_count 必须等于 config.handoff_step_count")
    if queue.get("queue_count") != step_count:
        errors.append("queue.queue_count 必须等于 config.handoff_step_count")

    require_boundary(errors, config, "config")
    require_boundary(errors, preview, "preview")
    require_boundary(errors, queue, "queue")
    require_boundary(errors, handoff_check, "handoff_check")
    require_boundary(errors, package, "package")
    require_boundary(errors, config.get("hard_red_line_confirmation", {}), "config.hard_red_line_confirmation")
    require_boundary(errors, preview.get("hard_red_line_confirmation", {}), "preview.hard_red_line_confirmation")
    require_boundary(errors, queue.get("hard_red_line_confirmation", {}), "queue.hard_red_line_confirmation")
    require_boundary(errors, handoff_check.get("hard_red_line_confirmation", {}), "handoff_check.hard_red_line_confirmation")
    require_boundary(errors, package.get("hard_red_line_confirmation", {}), "package.hard_red_line_confirmation")

    for item in config.get("handoff_steps", []):
        scope = f"config.{item.get('handoff_id', '<missing>')}"
        require_boundary(errors, item, scope)
        if item.get("plan_only") is not True:
            errors.append(f"{scope}.plan_only 必须为 true")
        if item.get("execution_adapter") != "none":
            errors.append(f"{scope}.execution_adapter 必须为 none")
        if item.get("script_to_execute") is not None:
            errors.append(f"{scope}.script_to_execute 必须为 null")
        if not item.get("dependency_keys"):
            errors.append(f"{scope}.dependency_keys 不得为空")
        if "116低风险只读调度器跨日值守接续预演包" not in item.get("evidence_path", ""):
            errors.append(f"{scope}.evidence_path 必须落在116目录")

    for item in preview.get("handoff_steps", []):
        scope = f"preview.{item.get('handoff_id', '<missing>')}"
        require_boundary(errors, item, scope)
        if item.get("preview_status") != "planned_not_executed":
            errors.append(f"{scope}.preview_status 必须为 planned_not_executed")
        if item.get("script_to_execute") is not None:
            errors.append(f"{scope}.script_to_execute 必须为 null")
        plan = item.get("plan", {})
        if plan.get("script_execution") is not False:
            errors.append(f"{scope}.plan.script_execution 必须为 false")
        if plan.get("system_schedule_registration") is not False:
            errors.append(f"{scope}.plan.system_schedule_registration 必须为 false")
        if plan.get("resume_task_execution") is not False:
            errors.append(f"{scope}.plan.resume_task_execution 必须为 false")
        if "116低风险只读调度器跨日值守接续预演包" not in item.get("evidence_path", ""):
            errors.append(f"{scope}.evidence_path 必须落在116目录")

    for item in queue.get("items", []):
        scope = f"queue.{item.get('queue_id', '<missing>')}"
        require_boundary(errors, item, scope)
        if item.get("auto_resume") is not False:
            errors.append(f"{scope}.auto_resume 必须为 false")
        if item.get("auto_execute") is not False:
            errors.append(f"{scope}.auto_execute 必须为 false")
        if item.get("status") != "candidate_only":
            errors.append(f"{scope}.status 必须为 candidate_only")

    if handoff_check.get("pass") is not True:
        errors.append("handoff_check.pass 必须为 true")
    if handoff_check.get("error_count") != 0:
        errors.append("handoff_check.error_count 必须为 0")
    if handoff_check.get("data_dir_is_116") is not True:
        errors.append("handoff_check.data_dir_is_116 必须为 true")
    if handoff_check.get("data_dir_is_not_112") is not True:
        errors.append("handoff_check.data_dir_is_not_112 必须为 true")
    if handoff_check.get("redline_blocked") is not True:
        errors.append("handoff_check.redline_blocked 必须为 true")
    if handoff_check.get("service_reload_required") is not False:
        errors.append("handoff_check.service_reload_required 必须为 false")

    verification = {
        "name": "低风险只读调度器跨日值守接续预演包验收",
        "generated_at": now(),
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "fixed_log_path": str(VERIFY_JSON),
        "data_dir": str(DATA_DIR),
        "data_dir_is_116": "116低风险只读调度器跨日值守接续预演包" in data_dir_text,
        "data_dir_is_not_112": "112" not in data_dir_text,
        "required_file_count": len(required_files),
        "existing_file_count": sum(1 for path in required_files if path.exists()),
        "handoff_step_count": step_count,
        "queue_count": queue.get("queue_count", 0),
        "auto_schedule": False,
        "actual_execution": False,
        "external_call": False,
        "reload_service": False,
        "preview_only": True,
        "redline_blocked": handoff_check.get("redline_blocked") is True,
        "service_reload_required": False,
        "register_system_scheduled_task": False,
        "hard_red_line_confirmation": {
            "real_wecom_send": False,
            "connect_n8n": False,
            "trigger_n8n": False,
            "broker_connection": False,
            "trade_order": False,
            "tax_bureau_login": False,
            "finance_tax_software_connection": False,
            "write_formal_rule": False,
            "auto_promote_formal_rule": False,
            "modify_supervisor_panel": False,
            "modify_one_click_continuation_package": False,
            "register_system_scheduled_task": False,
            "reload_service": False,
            "delete_business_artifact": False,
        },
    }
    write_json(VERIFY_JSON, verification)
    print(
        json.dumps(
            {
                "pass": verification["pass"],
                "error_count": verification["error_count"],
                "handoff_step_count": verification["handoff_step_count"],
                "queue_count": verification["queue_count"],
                "data_dir": verification["data_dir"],
                "data_dir_is_116": verification["data_dir_is_116"],
                "data_dir_is_not_112": verification["data_dir_is_not_112"],
                "log": str(VERIFY_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if verification["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
