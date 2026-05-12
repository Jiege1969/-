# -*- coding: utf-8 -*-
"""验证低风险只读调度器异常升级草案与总管确认队列包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "110低风险只读调度器异常升级草案与总管确认队列包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器异常升级草案与总管确认队列包验收"

RULE_JSON = DATA_DIR / "异常升级规则_最新.json"
RULE_MD = DATA_DIR / "异常升级规则_最新.md"
QUEUE_JSON = DATA_DIR / "总管确认队列_最新.json"
QUEUE_MD = DATA_DIR / "总管确认队列_最新.md"
REPORT_JSON = DATA_DIR / "升级队列预演报告_最新.json"
REPORT_MD = DATA_DIR / "升级队列预演报告_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器异常升级草案与总管确认队列包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器异常升级草案与总管确认队列包_最新.md"

VERIFY_JSON = LOG_DIR / "low-risk-readonly-scheduler-escalation-confirmation-queue-verify-最新.json"


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


def require_safety_false(errors: list[str], data: dict[str, Any], scope: str) -> None:
    for key in [
        "executed",
        "auto_resume",
        "commands_executed",
        "external_call",
        "reload_service",
        "real_wecom_send",
        "connect_n8n",
        "connect_broker",
        "trade",
        "login_tax_bureau",
        "connect_finance_tax_software",
        "promote_to_formal_rule",
        "modify_supervisor_panel",
        "modify_one_click_continuation_package",
    ]:
        require_false(errors, data, key, scope)


def main() -> int:
    errors: list[str] = []
    required_files = [RULE_JSON, RULE_MD, QUEUE_JSON, QUEUE_MD, REPORT_JSON, REPORT_MD, PACKAGE_JSON, PACKAGE_MD]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件: {path}")

    rules = read_json(RULE_JSON) if RULE_JSON.exists() else {"rules": [], "safety_confirmation": {}}
    queue = read_json(QUEUE_JSON) if QUEUE_JSON.exists() else {"items": [], "safety_confirmation": {}}
    report = read_json(REPORT_JSON) if REPORT_JSON.exists() else {"results": [], "safety_confirmation": {}}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {"safety_confirmation": {}}

    rule_items = rules.get("rules", [])
    queue_items = queue.get("items", [])
    report_results = report.get("results", [])
    required_categories = {"红线命中", "服务重载需求", "正式规则影响", "外部接口需求", "证据缺失", "连续失败"}
    covered_categories = {item.get("category") for item in rule_items}
    missing_categories = sorted(required_categories - covered_categories)
    if missing_categories:
        errors.append(f"异常升级规则缺少覆盖类别: {missing_categories}")
    if len(rule_items) < 6:
        errors.append("rule_count 必须不少于6")
    if len(queue_items) < 6:
        errors.append("queue_count 必须不少于6")
    if len(report_results) != len(queue_items):
        errors.append("升级预演报告结果数量必须等于队列数量")

    for rule in rule_items:
        scope = f"rule.{rule.get('id', '<missing>')}"
        require_true(errors, rule, "pause_required", scope)
        require_false(errors, rule, "continue_allowed", scope)
        require_true(errors, rule, "requires_supervisor_confirmation", scope)
        require_false(errors, rule, "executed", scope)
        require_false(errors, rule, "auto_resume", scope)
        require_false(errors, rule, "external_call", scope)
        require_false(errors, rule, "reload_service", scope)

    for item in queue_items:
        scope = f"queue.{item.get('id', '<missing>')}"
        if item.get("status") != "需总管确认":
            errors.append(f"{scope}.status 必须为 需总管确认")
        require_true(errors, item, "pause_required", scope)
        require_false(errors, item, "continue_allowed", scope)
        require_true(errors, item, "requires_supervisor_confirmation", scope)
        require_false(errors, item, "executed", scope)
        require_false(errors, item, "auto_resume", scope)
        require_false(errors, item, "external_call", scope)
        require_false(errors, item, "reload_service", scope)

    for result in report_results:
        scope = f"report.{result.get('queue_id', '<missing>')}"
        require_true(errors, result, "pause_required", scope)
        require_false(errors, result, "continue_allowed", scope)
        require_true(errors, result, "requires_supervisor_confirmation", scope)
        require_false(errors, result, "executed", scope)
        require_false(errors, result, "auto_resume", scope)
        require_false(errors, result, "external_call", scope)
        require_false(errors, result, "reload_service", scope)

    if report.get("pass") is not True:
        errors.append("升级队列预演报告 pass 必须为 true")
    if report.get("error_count") != 0:
        errors.append("升级队列预演报告 error_count 必须为 0")
    require_true(errors, report, "pause_required", "report")
    require_false(errors, report, "continue_allowed", "report")
    require_true(errors, report, "requires_supervisor_confirmation", "report")
    require_false(errors, report, "executed", "report")
    require_false(errors, report, "auto_resume", "report")
    require_false(errors, report, "external_call", "report")
    require_false(errors, report, "reload_service", "report")

    require_safety_false(errors, rules.get("safety_confirmation", {}), "rules.safety_confirmation")
    require_safety_false(errors, queue.get("safety_confirmation", {}), "queue.safety_confirmation")
    require_safety_false(errors, report.get("safety_confirmation", {}), "report.safety_confirmation")
    require_safety_false(errors, package.get("safety_confirmation", {}), "package.safety_confirmation")

    verification = {
        "name": "低风险只读调度器异常升级草案与总管确认队列包验收",
        "generated_at": now(),
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "rule_count": len(rule_items),
        "queue_count": len(queue_items),
        "pause_required": report.get("pause_required") is True,
        "continue_allowed": False,
        "requires_supervisor_confirmation": report.get("requires_supervisor_confirmation") is True,
        "executed": False,
        "auto_resume": False,
        "external_call": False,
        "reload_service": False,
        "covered_categories": sorted(covered_categories),
        "required_categories": sorted(required_categories),
        "metrics": {
            "required_file_count": len(required_files),
            "existing_file_count": sum(1 for path in required_files if path.exists()),
            "rule_count": len(rule_items),
            "queue_count": len(queue_items),
            "report_result_count": len(report_results),
        },
        "fixed_log_path": str(VERIFY_JSON),
        "hard_red_line_confirmation": {
            "real_wecom_send": False,
            "connect_n8n": False,
            "connect_broker": False,
            "trade": False,
            "login_tax_bureau": False,
            "connect_finance_tax_software": False,
            "promote_to_formal_rule": False,
            "modify_supervisor_panel": False,
            "modify_one_click_continuation_package": False,
            "reload_service": False,
        },
    }
    write_json(VERIFY_JSON, verification)
    print(
        json.dumps(
            {
                "pass": verification["pass"],
                "error_count": verification["error_count"],
                "queue_count": verification["queue_count"],
                "executed": verification["executed"],
                "auto_resume": verification["auto_resume"],
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
