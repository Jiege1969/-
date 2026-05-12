# -*- coding: utf-8 -*-
"""验证低风险只读调度干跑结果漂移复核与幂等校验包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "105低风险只读调度干跑结果漂移复核与幂等校验包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度干跑结果漂移复核与幂等校验包验收"

RULES_JSON = DATA_DIR / "漂移规则_最新.json"
RULES_MD = DATA_DIR / "漂移规则_最新.md"
IDEMPOTENCY_JSON = DATA_DIR / "幂等校验报告_最新.json"
IDEMPOTENCY_MD = DATA_DIR / "幂等校验报告_最新.md"
DRIFT_JSON = DATA_DIR / "漂移复核报告_最新.json"
DRIFT_MD = DATA_DIR / "漂移复核报告_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度干跑结果漂移复核与幂等校验包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度干跑结果漂移复核与幂等校验包_最新.md"

VERIFY_JSON = LOG_DIR / "low-risk-readonly-scheduler-drift-idempotency-verify-最新.json"


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
        RULES_JSON,
        RULES_MD,
        IDEMPOTENCY_JSON,
        IDEMPOTENCY_MD,
        DRIFT_JSON,
        DRIFT_MD,
        PACKAGE_JSON,
        PACKAGE_MD,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件：{path}")

    rules = read_json(RULES_JSON) if RULES_JSON.exists() else {}
    idempotency = read_json(IDEMPOTENCY_JSON) if IDEMPOTENCY_JSON.exists() else {}
    drift = read_json(DRIFT_JSON) if DRIFT_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}

    if len(rules.get("checks", [])) < 5:
        errors.append("漂移规则必须覆盖任务数量、任务顺序、红线扫描摘要、安全边界字段、台账字段")
    expected_rule_ids = {"task_count", "task_order", "redline_scan_summary", "safety_boundary_fields", "ledger_fields"}
    actual_rule_ids = {item.get("id") for item in rules.get("checks", []) if isinstance(item, dict)}
    missing_rule_ids = sorted(expected_rule_ids - actual_rule_ids)
    if missing_rule_ids:
        errors.append(f"漂移规则缺少检查项：{missing_rule_ids}")

    require_true(errors, idempotency, "repeated_preview_same_plan", "idempotency")
    require_false(errors, idempotency, "source_files_modified", "idempotency")
    require_false(errors, idempotency, "external_call", "idempotency")
    require_false(errors, idempotency, "actual_execution", "idempotency")
    if idempotency.get("diff_count") != 0:
        errors.append("idempotency.diff_count 必须为 0")
    if idempotency.get("error_count") != 0:
        errors.append("idempotency.error_count 必须为 0")

    if drift.get("drift_count") != 0:
        errors.append("drift.drift_count 必须为 0")
    if drift.get("missing_count") != 0:
        errors.append("drift.missing_count 必须为 0")
    if drift.get("redline_regression_count") != 0:
        errors.append("drift.redline_regression_count 必须为 0")
    if drift.get("error_count") != 0:
        errors.append("drift.error_count 必须为 0")
    require_false(errors, drift, "source_files_modified", "drift")
    require_false(errors, drift, "external_call", "drift")
    require_false(errors, drift, "actual_execution", "drift")

    for scope, data in [("package", package), ("rules", rules)]:
        require_false(errors, data, "external_call", scope)
        require_false(errors, data, "reload_service", scope)

    verification = {
        "name": "低风险只读调度干跑结果漂移复核与幂等校验包验收",
        "generated_at": now(),
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "fixed_log_path": str(VERIFY_JSON),
        "required_file_count": len(required_files),
        "existing_file_count": sum(1 for path in required_files if path.exists()),
        "repeated_preview_same_plan": idempotency.get("repeated_preview_same_plan") is True,
        "source_files_modified": idempotency.get("source_files_modified") is True,
        "diff_count": idempotency.get("diff_count", -1),
        "drift_count": drift.get("drift_count", -1),
        "missing_count": drift.get("missing_count", -1),
        "redline_regression_count": drift.get("redline_regression_count", -1),
        "external_call": False,
        "actual_execution": False,
        "copy_source_files": False,
        "move_source_files": False,
        "reload_service": False,
        "hard_red_line_confirmation": {
            "real_wecom_send": False,
            "trigger_n8n": False,
            "broker_connection": False,
            "trade_order": False,
            "tax_bureau_login": False,
            "finance_tax_software_connection": False,
            "auto_promote_formal_rule": False,
            "modify_supervisor_panel": False,
            "modify_one_click_continuation_package": False,
            "reload_service": False,
        },
        "scope_statement": "只读比对三轮干跑结果，不改源产物，不调用外部接口。",
    }
    write_json(VERIFY_JSON, verification)
    print(json.dumps({"pass": verification["pass"], "error_count": verification["error_count"], "drift_count": verification["drift_count"], "diff_count": verification["diff_count"], "source_files_modified": verification["source_files_modified"], "external_call": verification["external_call"], "log": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if verification["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
