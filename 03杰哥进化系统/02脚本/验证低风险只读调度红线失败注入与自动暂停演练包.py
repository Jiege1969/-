# -*- coding: utf-8 -*-
"""验证低风险只读调度红线失败注入与自动暂停演练包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "106低风险只读调度红线失败注入与自动暂停演练包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度红线失败注入与自动暂停演练包验收"

INJECTION_JSON = DATA_DIR / "失败注入样例_最新.json"
INJECTION_MD = DATA_DIR / "失败注入样例_最新.md"
REPORT_JSON = DATA_DIR / "自动暂停演练报告_最新.json"
REPORT_MD = DATA_DIR / "自动暂停演练报告_最新.md"
SUPERVISOR_JSON = DATA_DIR / "总管确认事项清单_最新.json"
SUPERVISOR_MD = DATA_DIR / "总管确认事项清单_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度红线失败注入与自动暂停演练包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度红线失败注入与自动暂停演练包_最新.md"

VERIFY_JSON = LOG_DIR / "low-risk-readonly-redline-injection-pause-verify-最新.json"


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


def require_safety_false(errors: list[str], data: dict[str, Any], scope: str) -> None:
    for key in [
        "commands_executed",
        "external_call",
        "reload_service",
        "real_wecom_send",
        "connect_n8n",
        "connect_broker",
        "trade",
        "login_tax_bureau",
        "connect_finance_tax_software",
        "write_formal_rule",
        "promote_to_formal_rule",
        "real_video_publish",
    ]:
        require_false(errors, data, key, scope)


def main() -> int:
    errors: list[str] = []
    required_files = [
        INJECTION_JSON,
        INJECTION_MD,
        REPORT_JSON,
        REPORT_MD,
        SUPERVISOR_JSON,
        SUPERVISOR_MD,
        PACKAGE_JSON,
        PACKAGE_MD,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件: {path}")

    injections = read_json(INJECTION_JSON) if INJECTION_JSON.exists() else {"samples": [], "safety_confirmation": {}}
    report = read_json(REPORT_JSON) if REPORT_JSON.exists() else {"results": [], "safety_confirmation": {}}
    supervisor = read_json(SUPERVISOR_JSON) if SUPERVISOR_JSON.exists() else {"items": [], "safety_confirmation": {}}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {"safety_confirmation": {}}

    samples = injections.get("samples", [])
    results = report.get("results", [])
    supervisor_items = supervisor.get("items", [])
    required_types = {"企业微信真实发送", "n8n webhook", "19310重载", "正式规则写入", "视频真实发布", "券商交易"}
    existing_types = {item.get("redline_type") for item in samples}
    missing_types = sorted(required_types - existing_types)
    if missing_types:
        errors.append(f"失败注入样例缺少红线类型: {missing_types}")
    if len(samples) < 6:
        errors.append("injection_count 必须不少于 6")
    if len(results) != len(samples):
        errors.append("自动暂停演练结果数量必须等于失败注入样例数量")
    if len(supervisor_items) != len(samples):
        errors.append("总管确认事项数量必须等于失败注入样例数量")

    for sample in samples:
        scope = f"injection.{sample.get('id', '<missing>')}"
        require_true(errors, sample, "pause_required", scope)
        require_false(errors, sample, "continue_allowed", scope)
        require_true(errors, sample, "requires_supervisor_confirmation", scope)
        require_false(errors, sample, "executed", scope)
        require_false(errors, sample, "commands_executed", scope)
        require_false(errors, sample, "external_call", scope)
        require_false(errors, sample, "reload_service", scope)

    for result in results:
        scope = f"report.{result.get('injection_id', '<missing>')}"
        require_true(errors, result, "pause_required", scope)
        require_false(errors, result, "continue_allowed", scope)
        require_true(errors, result, "requires_supervisor_confirmation", scope)
        require_false(errors, result, "executed", scope)
        require_false(errors, result, "commands_executed", scope)
        require_false(errors, result, "external_call", scope)
        require_false(errors, result, "reload_service", scope)

    for item in supervisor_items:
        scope = f"supervisor.{item.get('id', '<missing>')}"
        if item.get("status") != "需总管确认":
            errors.append(f"{scope}.status 必须为 需总管确认")
        require_false(errors, item, "executed", scope)
        require_false(errors, item, "continue_allowed", scope)
        require_true(errors, item, "requires_supervisor_confirmation", scope)
        require_false(errors, item, "commands_executed", scope)
        require_false(errors, item, "external_call", scope)
        require_false(errors, item, "reload_service", scope)

    if report.get("pass") is not True:
        errors.append("自动暂停演练报告 pass 必须为 true")
    if report.get("error_count") != 0:
        errors.append("自动暂停演练报告 error_count 必须为 0")
    require_safety_false(errors, injections.get("safety_confirmation", {}), "injections.safety_confirmation")
    require_safety_false(errors, report.get("safety_confirmation", {}), "report.safety_confirmation")
    require_safety_false(errors, supervisor.get("safety_confirmation", {}), "supervisor.safety_confirmation")
    require_safety_false(errors, package.get("safety_confirmation", {}), "package.safety_confirmation")

    verification = {
        "name": "低风险只读调度红线失败注入与自动暂停演练包验收",
        "generated_at": now(),
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "injection_count": len(samples),
        "pause_required_count": sum(1 for item in results if item.get("pause_required") is True),
        "supervisor_confirmation_count": sum(
            1 for item in results if item.get("requires_supervisor_confirmation") is True
        ),
        "commands_executed": False,
        "external_call": False,
        "reload_service": False,
        "continue_allowed_count": sum(1 for item in results if item.get("continue_allowed") is True),
        "required_redline_types": sorted(required_types),
        "covered_redline_types": sorted(existing_types),
        "metrics": {
            "required_file_count": len(required_files),
            "existing_file_count": sum(1 for path in required_files if path.exists()),
            "injection_count": len(samples),
            "pause_required_count": sum(1 for item in results if item.get("pause_required") is True),
            "supervisor_item_count": len(supervisor_items),
        },
        "fixed_log_path": str(VERIFY_JSON),
        "hard_red_line_confirmation": {
            "real_wecom_send": False,
            "connect_n8n": False,
            "connect_broker": False,
            "trade": False,
            "login_tax_bureau": False,
            "connect_finance_tax_software": False,
            "write_formal_rule": False,
            "promote_to_formal_rule": False,
            "real_video_publish": False,
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
                "injection_count": verification["injection_count"],
                "pause_required_count": verification["pause_required_count"],
                "commands_executed": verification["commands_executed"],
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
