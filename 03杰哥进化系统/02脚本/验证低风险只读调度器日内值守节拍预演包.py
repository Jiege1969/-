# -*- coding: utf-8 -*-
"""验证低风险只读调度器日内值守节拍预演包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "108低风险只读调度器日内值守节拍预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器日内值守节拍预演包验收"

CONFIG_JSON = DATA_DIR / "日内值守节拍配置_最新.json"
CONFIG_MD = DATA_DIR / "日内值守节拍配置_最新.md"
PREVIEW_RESULT_JSON = DATA_DIR / "值守节拍预演结果_最新.json"
PREVIEW_RESULT_MD = DATA_DIR / "值守节拍预演结果_最新.md"
CONFLICT_JSON = DATA_DIR / "节拍冲突检查_最新.json"
CONFLICT_MD = DATA_DIR / "节拍冲突检查_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器日内值守节拍预演包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器日内值守节拍预演包_最新.md"
VERIFY_JSON = LOG_DIR / "low-risk-readonly-scheduler-daily-rhythm-preview-verify-最新.json"


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
    ]:
        require_false(errors, data, key, scope)


def main() -> int:
    errors: list[str] = []
    required_files = [
        CONFIG_JSON,
        CONFIG_MD,
        PREVIEW_RESULT_JSON,
        PREVIEW_RESULT_MD,
        CONFLICT_JSON,
        CONFLICT_MD,
        PACKAGE_JSON,
        PACKAGE_MD,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件: {path}")

    config = read_json(CONFIG_JSON) if CONFIG_JSON.exists() else {"rhythms": [], "hard_red_line_confirmation": {}}
    preview = read_json(PREVIEW_RESULT_JSON) if PREVIEW_RESULT_JSON.exists() else {"rhythms": [], "hard_red_line_confirmation": {}}
    conflict = read_json(CONFLICT_JSON) if CONFLICT_JSON.exists() else {"hard_red_line_confirmation": {}}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {"hard_red_line_confirmation": {}}

    required_names = {"早间巡检", "午间快照", "收盘复核", "晚间归档", "异常复验"}
    config_names = {item.get("rhythm_name") for item in config.get("rhythms", [])}
    missing_names = sorted(required_names - config_names)
    if missing_names:
        errors.append(f"节拍配置缺少必需节拍: {missing_names}")

    rhythm_count = len(config.get("rhythms", []))
    if rhythm_count < 5:
        errors.append("rhythm_count 必须不少于 5")
    if config.get("rhythm_count") != rhythm_count:
        errors.append("config.rhythm_count 必须等于 rhythms 数量")
    if preview.get("rhythm_count") != rhythm_count:
        errors.append("preview.rhythm_count 必须等于 config.rhythm_count")
    if package.get("rhythm_count") != rhythm_count:
        errors.append("package.rhythm_count 必须等于 config.rhythm_count")

    require_boundary(errors, config, "config")
    require_boundary(errors, preview, "preview")
    require_boundary(errors, conflict, "conflict")
    require_boundary(errors, package, "package")
    require_boundary(errors, config.get("hard_red_line_confirmation", {}), "config.hard_red_line_confirmation")
    require_boundary(errors, preview.get("hard_red_line_confirmation", {}), "preview.hard_red_line_confirmation")
    require_boundary(errors, conflict.get("hard_red_line_confirmation", {}), "conflict.hard_red_line_confirmation")
    require_boundary(errors, package.get("hard_red_line_confirmation", {}), "package.hard_red_line_confirmation")

    for item in config.get("rhythms", []):
        scope = f"config.{item.get('rhythm_id', '<missing>')}"
        require_boundary(errors, item, scope)
        if item.get("plan_only") is not True:
            errors.append(f"{scope}.plan_only 必须为 true")
        if item.get("execution_adapter") != "none":
            errors.append(f"{scope}.execution_adapter 必须为 none")
        if item.get("script_to_execute") is not None:
            errors.append(f"{scope}.script_to_execute 必须为 null")
        if not item.get("dependencies"):
            errors.append(f"{scope}.dependencies 不得为空")
        if not item.get("evidence_path"):
            errors.append(f"{scope}.evidence_path 不得为空")

    for item in preview.get("rhythms", []):
        scope = f"preview.{item.get('rhythm_id', '<missing>')}"
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
        if not item.get("dependencies"):
            errors.append(f"{scope}.dependencies 不得为空")
        if not item.get("evidence_path"):
            errors.append(f"{scope}.evidence_path 不得为空")

    if conflict.get("no_overlap") is not True:
        errors.append("conflict.no_overlap 必须为 true")
    if conflict.get("redline_blocked") is not True:
        errors.append("conflict.redline_blocked 必须为 true")
    if conflict.get("service_reload_required") is not False:
        errors.append("conflict.service_reload_required 必须为 false")
    if conflict.get("overlap_count") != 0:
        errors.append("conflict.overlap_count 必须为 0")

    verification = {
        "name": "低风险只读调度器日内值守节拍预演包验收",
        "generated_at": now(),
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "fixed_log_path": str(VERIFY_JSON),
        "required_file_count": len(required_files),
        "existing_file_count": sum(1 for path in required_files if path.exists()),
        "rhythm_count": rhythm_count,
        "auto_schedule": False,
        "actual_execution": False,
        "external_call": False,
        "reload_service": False,
        "preview_only": True,
        "no_overlap": conflict.get("no_overlap") is True,
        "redline_blocked": conflict.get("redline_blocked") is True,
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
        },
    }
    write_json(VERIFY_JSON, verification)
    print(
        json.dumps(
            {
                "pass": verification["pass"],
                "error_count": verification["error_count"],
                "rhythm_count": verification["rhythm_count"],
                "auto_schedule": verification["auto_schedule"],
                "actual_execution": verification["actual_execution"],
                "external_call": verification["external_call"],
                "reload_service": verification["reload_service"],
                "log": str(VERIFY_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if verification["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
