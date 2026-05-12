# -*- coding: utf-8 -*-
"""验证低风险只读调度运行台账与证据归档预演包。"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "100低风险只读调度运行台账与证据归档预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度运行台账与证据归档预演包验收"

FIELD_DEFINITION_JSON = DATA_DIR / "运行台账字段定义_最新.json"
FIELD_DEFINITION_MD = DATA_DIR / "运行台账字段定义_最新.md"
LEDGER_JSON = DATA_DIR / "调度预演台账_最新.json"
LEDGER_MD = DATA_DIR / "调度预演台账_最新.md"
ARCHIVE_REPORT_JSON = DATA_DIR / "证据归档预演报告_最新.json"
ARCHIVE_REPORT_MD = DATA_DIR / "证据归档预演报告_最新.md"
RUN_REPORT_JSON = DATA_DIR / "调度运行台账归档预演执行报告_最新.json"
RUN_REPORT_MD = DATA_DIR / "调度运行台账归档预演执行报告_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度运行台账与证据归档预演包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度运行台账与证据归档预演包_最新.md"

VERIFY_JSON = LOG_DIR / "low-risk-readonly-scheduler-ledger-evidence-preview-verify-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def stable_hash(data: dict[str, Any]) -> str:
    payload = {key: value for key, value in data.items() if key != "hash"}
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
        FIELD_DEFINITION_JSON,
        FIELD_DEFINITION_MD,
        LEDGER_JSON,
        LEDGER_MD,
        ARCHIVE_REPORT_JSON,
        ARCHIVE_REPORT_MD,
        RUN_REPORT_JSON,
        RUN_REPORT_MD,
        PACKAGE_JSON,
        PACKAGE_MD,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件：{path}")

    field_definition = read_json(FIELD_DEFINITION_JSON) if FIELD_DEFINITION_JSON.exists() else {}
    ledger = read_json(LEDGER_JSON) if LEDGER_JSON.exists() else {"records": []}
    archive_report = read_json(ARCHIVE_REPORT_JSON) if ARCHIVE_REPORT_JSON.exists() else {"archive_items": []}
    run_report = read_json(RUN_REPORT_JSON) if RUN_REPORT_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}

    minimum_fields = {
        "task_id",
        "task_name",
        "plan_time",
        "preview_status",
        "pause_required",
        "evidence_path",
        "hash",
        "operator_mode",
    }
    defined_fields = {item.get("name") for item in field_definition.get("fields", [])}
    missing_fields = sorted(minimum_fields - defined_fields)
    if missing_fields:
        errors.append(f"字段定义缺少必需字段：{missing_fields}")

    records = ledger.get("records", [])
    if len(records) < 8:
        errors.append("调度预演台账记录数必须不少于 8 条")
    if ledger.get("preview_status_default") != "not_executed":
        errors.append("ledger.preview_status_default 必须为 not_executed")

    seen_task_ids: set[str] = set()
    for record in records:
        task_id = record.get("task_id", "<missing>")
        if task_id in seen_task_ids:
            errors.append(f"{task_id} 重复")
        seen_task_ids.add(task_id)
        missing_record_fields = sorted(field for field in minimum_fields if field not in record)
        if missing_record_fields:
            errors.append(f"{task_id} 缺少字段：{missing_record_fields}")
        if record.get("preview_status") != "not_executed":
            errors.append(f"{task_id}.preview_status 必须为 not_executed")
        if record.get("operator_mode") != "readonly_preview":
            errors.append(f"{task_id}.operator_mode 必须为 readonly_preview")
        if record.get("hash") != stable_hash(record):
            errors.append(f"{task_id}.hash 不匹配")
        require_false(errors, record, "actual_execution", task_id)
        require_false(errors, record, "copy_source_files", task_id)
        require_false(errors, record, "move_source_files", task_id)
        require_false(errors, record, "external_call", task_id)
        require_false(errors, record, "reload_service", task_id)
        require_true(errors, record, "planned_result_only", task_id)

    archive_items = archive_report.get("archive_items", [])
    archive_task_ids = {item.get("task_id") for item in archive_items}
    if len(archive_items) < len(records):
        errors.append("证据归档预演报告清单条目数不得少于台账记录数")
    for task_id in seen_task_ids:
        if task_id not in archive_task_ids:
            errors.append(f"{task_id} 缺少证据归档预演清单")
    for item in archive_items:
        scope = item.get("archive_item_id", "<missing_archive_item>")
        if item.get("archive_action") != "list_only_no_copy_no_move":
            errors.append(f"{scope}.archive_action 必须为 list_only_no_copy_no_move")
        require_false(errors, item, "actual_execution", scope)
        require_false(errors, item, "copy_source_files", scope)
        require_false(errors, item, "move_source_files", scope)
        require_false(errors, item, "external_call", scope)

    for scope, data in [
        ("field_definition.defaults", field_definition.get("defaults", {})),
        ("ledger", ledger),
        ("archive_report", archive_report),
        ("run_report", run_report),
        ("package", package),
    ]:
        require_false(errors, data, "actual_execution", scope)
        require_false(errors, data, "copy_source_files", scope)
        require_false(errors, data, "move_source_files", scope)
        require_false(errors, data, "external_call", scope)
        require_false(errors, data, "reload_service", scope)

    if run_report.get("pass") is not True:
        errors.append("执行预演报告必须 pass=true")
    if run_report.get("error_count") != 0:
        errors.append("执行预演报告 error_count 必须为 0")
    if package.get("pass") is not True:
        errors.append("预演包必须 pass=true")
    if package.get("error_count") != 0:
        errors.append("预演包 error_count 必须为 0")

    verification = {
        "name": "低风险只读调度运行台账与证据归档预演包验收",
        "generated_at": generated_at,
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "fixed_log_path": str(VERIFY_JSON),
        "required_file_count": len(required_files),
        "existing_file_count": sum(1 for path in required_files if path.exists()),
        "ledger_record_count": len(records),
        "archive_item_count": len(archive_items),
        "actual_execution": False,
        "copy_source_files": False,
        "move_source_files": False,
        "external_call": False,
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
        "scope_statement": "只登记计划结果，只生成证据归档清单，不执行真实任务，不复制或移动业务源文件。",
    }
    write_json(VERIFY_JSON, verification)
    print(json.dumps({"pass": verification["pass"], "error_count": verification["error_count"], "log": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if verification["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
