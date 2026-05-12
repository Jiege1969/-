# -*- coding: utf-8 -*-
"""验证低风险自主任务失败暂停与恢复演练包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "97低风险自主任务失败暂停与恢复演练包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险自主任务失败暂停与恢复演练包验收"

SCENARIO_JSON = DATA_DIR / "失败暂停场景矩阵_最新.json"
SCENARIO_MD = DATA_DIR / "失败暂停场景矩阵_最新.md"
RECOVERY_JSON = DATA_DIR / "恢复申请模板_最新.json"
RECOVERY_MD = DATA_DIR / "恢复申请模板_最新.md"
REPORT_JSON = DATA_DIR / "只读暂停演练报告_最新.json"
REPORT_MD = DATA_DIR / "只读暂停演练报告_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险自主任务失败暂停与恢复演练包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险自主任务失败暂停与恢复演练包_最新.md"

VERIFY_JSON = LOG_DIR / "low-risk-autonomous-failure-pause-recovery-verify-最新.json"


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
    errors: list[str] = []
    required_files = [
        SCENARIO_JSON,
        SCENARIO_MD,
        RECOVERY_JSON,
        RECOVERY_MD,
        REPORT_JSON,
        REPORT_MD,
        PACKAGE_JSON,
        PACKAGE_MD,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件：{path}")

    matrix = read_json(SCENARIO_JSON) if SCENARIO_JSON.exists() else {"scenarios": []}
    template = read_json(RECOVERY_JSON) if RECOVERY_JSON.exists() else {}
    report = read_json(REPORT_JSON) if REPORT_JSON.exists() else {"drill_results": []}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}

    scenarios = matrix.get("scenarios", [])
    scenario_names = {item.get("scenario") for item in scenarios}
    required_scenarios = {"验收失败", "证据缺失", "红线词命中", "需服务重载", "正式规则影响", "外部接口需求"}
    missing = sorted(required_scenarios - scenario_names)
    if missing:
        errors.append(f"失败暂停场景矩阵缺少场景：{missing}")
    if len(scenarios) < 6:
        errors.append("失败暂停场景矩阵至少需要 6 个场景")

    for item in scenarios:
        item_id = item.get("id", "<missing>")
        require_true(errors, item, "pause_required", item_id)
        require_false(errors, item, "auto_continue_after_failure", item_id)
        require_false(errors, item, "continue_dispatch_allowed", item_id)
        require_false(errors, item, "recovery_requested", item_id)
        require_false(errors, item, "recovery_executed", item_id)
        require_false(errors, item, "external_call", item_id)
        require_false(errors, item, "reload_service", item_id)
        require_true(errors, item, "requires_supervisor_confirmation", item_id)

    require_false(errors, template, "recovery_requested", "recovery_template")
    require_false(errors, template, "recovery_executed", "recovery_template")
    require_true(errors, template, "requires_supervisor_confirmation", "recovery_template")
    require_false(errors, template, "auto_continue_after_failure", "recovery_template")
    require_false(errors, template, "external_call", "recovery_template")
    require_false(errors, template, "reload_service", "recovery_template")

    if report.get("pass") is not True:
        errors.append("只读暂停演练报告必须 pass=true")
    if report.get("error_count") != 0:
        errors.append("只读暂停演练报告 error_count 必须为 0")
    drill_results = report.get("drill_results", [])
    if len(drill_results) != len(scenarios):
        errors.append("只读暂停演练报告结果数量必须等于场景数量")
    for item in drill_results:
        item_id = item.get("scenario_id", "<missing>")
        require_true(errors, item, "pause_required", f"drill.{item_id}")
        require_false(errors, item, "would_continue_dispatch", f"drill.{item_id}")
        require_false(errors, item, "auto_continue_after_failure", f"drill.{item_id}")
        require_false(errors, item, "recovery_requested", f"drill.{item_id}")
        require_false(errors, item, "recovery_executed", f"drill.{item_id}")
        require_false(errors, item, "external_call", f"drill.{item_id}")
        require_false(errors, item, "reload_service", f"drill.{item_id}")

    for key in [
        "auto_continue_after_failure",
        "recovery_executed",
        "external_call",
        "reload_service",
        "real_wecom_send",
        "connect_n8n",
        "connect_broker",
        "trade",
        "login_tax_bureau",
        "connect_finance_tax_software",
        "promote_to_formal_rule",
        "modify_master_panel",
        "modify_one_click_continuation_package",
    ]:
        require_false(errors, matrix.get("global_policy", {}), key, "matrix.global_policy")
        require_false(errors, report.get("safety_confirmation", {}), key, "report.safety_confirmation")
        require_false(errors, package.get("safety_confirmation", {}), key, "package.safety_confirmation")

    verification = {
        "name": "低风险自主任务失败暂停与恢复演练包验收",
        "generated_at": now(),
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "auto_continue_after_failure": False,
        "recovery_executed": False,
        "external_call": False,
        "reload_service": False,
        "metrics": {
            "required_file_count": len(required_files),
            "existing_file_count": sum(1 for path in required_files if path.exists()),
            "scenario_count": len(scenarios),
            "pause_required_count": sum(1 for item in scenarios if item.get("pause_required") is True),
            "drill_result_count": len(drill_results),
            "paused_without_continue_count": sum(
                1 for item in drill_results if item.get("pause_required") is True and item.get("would_continue_dispatch") is False
            ),
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
            "modify_master_panel": False,
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
                "auto_continue_after_failure": verification["auto_continue_after_failure"],
                "recovery_executed": verification["recovery_executed"],
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
