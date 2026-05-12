# -*- coding: utf-8 -*-
"""验证低风险只读调度器周周期值守样本预演包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "120低风险只读调度器周周期值守样本预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器周周期值守样本预演包验收"

RULE_JSON = DATA_DIR / "周周期值守规则_最新.json"
RULE_MD = DATA_DIR / "周周期值守规则_最新.md"
SAMPLE_JSON = DATA_DIR / "周周期样本_最新.json"
SAMPLE_MD = DATA_DIR / "周周期样本_最新.md"
REPORT_JSON = DATA_DIR / "周周期预演报告_最新.json"
REPORT_MD = DATA_DIR / "周周期预演报告_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器周周期值守样本预演包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器周周期值守样本预演包_最新.md"
VERIFY_JSON = LOG_DIR / "low-risk-readonly-scheduler-week-cycle-sample-verify-最新.json"


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
    required_files = [RULE_JSON, RULE_MD, SAMPLE_JSON, SAMPLE_MD, REPORT_JSON, REPORT_MD, PACKAGE_JSON, PACKAGE_MD]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件: {path}")

    rule = read_json(RULE_JSON) if RULE_JSON.exists() else {"rules": [], "hard_red_line_confirmation": {}}
    sample = read_json(SAMPLE_JSON) if SAMPLE_JSON.exists() else {"days": [], "hard_red_line_confirmation": {}}
    report = read_json(REPORT_JSON) if REPORT_JSON.exists() else {"hard_red_line_confirmation": {}}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {"hard_red_line_confirmation": {}}

    data_dir_text = str(DATA_DIR)
    if "120低风险只读调度器周周期值守样本预演包" not in data_dir_text:
        errors.append("验收数据目录必须为120低风险只读调度器周周期值守样本预演包")

    required_phases = {"周一启动", "工作日巡检", "周中复核", "周五归档", "周末不执行/只保留待办"}
    rule_phases = {item.get("phase") for item in rule.get("rules", [])}
    sample_phases = {item.get("phase") for item in sample.get("days", [])}
    for scope, phases in [("rule", rule_phases), ("sample", sample_phases)]:
        missing = sorted(required_phases - phases)
        if missing:
            errors.append(f"{scope} 缺少周周期阶段: {missing}")

    day_count = len(sample.get("days", []))
    if day_count < 7:
        errors.append("day_count 必须不少于7")
    if sample.get("day_count") != day_count:
        errors.append("sample.day_count 必须等于 days 数量")
    if report.get("day_count") != day_count:
        errors.append("report.day_count 必须等于 sample.day_count")
    if package.get("day_count", 0) < 7:
        errors.append("package.day_count 必须不少于7")

    if report.get("pass") is not True:
        errors.append("report.pass 必须为 true")
    if report.get("error_count") != 0:
        errors.append("report.error_count 必须为 0")
    if report.get("weekday_queue_created") is not True:
        errors.append("report.weekday_queue_created 必须为 true")
    if report.get("weekend_execute") is not False:
        errors.append("report.weekend_execute 必须为 false")

    require_boundary(errors, rule, "rule")
    require_boundary(errors, sample, "sample")
    require_boundary(errors, report, "report")
    require_boundary(errors, package, "package")
    require_boundary(errors, rule.get("hard_red_line_confirmation", {}), "rule.hard_red_line_confirmation")
    require_boundary(errors, sample.get("hard_red_line_confirmation", {}), "sample.hard_red_line_confirmation")
    require_boundary(errors, report.get("hard_red_line_confirmation", {}), "report.hard_red_line_confirmation")
    require_boundary(errors, package.get("hard_red_line_confirmation", {}), "package.hard_red_line_confirmation")

    for item in rule.get("rules", []):
        scope = f"rule.{item.get('rule_id', '<missing>')}"
        require_boundary(errors, item, scope)
        if item.get("execution_adapter") != "none":
            errors.append(f"{scope}.execution_adapter 必须为 none")
        if item.get("script_to_execute") is not None:
            errors.append(f"{scope}.script_to_execute 必须为 null")
        if item.get("system_schedule_name") is not None:
            errors.append(f"{scope}.system_schedule_name 必须为 null")
    for item in sample.get("days", []):
        scope = f"sample.{item.get('day_index', '<missing>')}"
        require_boundary(errors, item, scope)
        if item.get("execution_adapter") != "none":
            errors.append(f"{scope}.execution_adapter 必须为 none")
        if item.get("script_to_execute") is not None:
            errors.append(f"{scope}.script_to_execute 必须为 null")
        if item.get("system_schedule_name") is not None:
            errors.append(f"{scope}.system_schedule_name 必须为 null")
        if item.get("day_type") == "weekend" and item.get("weekend_execute") is not False:
            errors.append(f"{scope}.weekend_execute 必须为 false")

    verification = {
        "name": "低风险只读调度器周周期值守样本预演包验收",
        "generated_at": now(),
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "fixed_log_path": str(VERIFY_JSON),
        "data_dir": str(DATA_DIR),
        "required_file_count": len(required_files),
        "existing_file_count": sum(1 for path in required_files if path.exists()),
        "day_count": day_count,
        "weekday_queue_created": report.get("weekday_queue_created") is True,
        "weekend_execute": False,
        "auto_schedule": False,
        "actual_execution": False,
        "external_call": False,
        "reload_service": False,
        "preview_only": True,
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
                "day_count": verification["day_count"],
                "weekday_queue_created": verification["weekday_queue_created"],
                "weekend_execute": verification["weekend_execute"],
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
