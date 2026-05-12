# -*- coding: utf-8 -*-
"""执行低风险只读调度运行台账归档预演。

这里的“执行”只表示读取生成包并登记预演结果；不真实执行任务、不调用外部接口、
不复制或移动业务证据、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "100低风险只读调度运行台账与证据归档预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度运行台账与证据归档预演包验收"

FIELD_DEFINITION_JSON = DATA_DIR / "运行台账字段定义_最新.json"
LEDGER_JSON = DATA_DIR / "调度预演台账_最新.json"
ARCHIVE_REPORT_JSON = DATA_DIR / "证据归档预演报告_最新.json"
RUN_REPORT_JSON = DATA_DIR / "调度运行台账归档预演执行报告_最新.json"
RUN_REPORT_MD = DATA_DIR / "调度运行台账归档预演执行报告_最新.md"
RUN_LOG = LOG_DIR / "low-risk-readonly-scheduler-ledger-evidence-preview-run-最新.json"


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


def require_false(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not False:
        errors.append(f"{scope}.{key} 必须为 false")


def build_report_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['task_id']} | {item['preview_status']} | {item['actual_execution']} | {item['copy_source_files']} | {item['move_source_files']} | {item['registered_result']} |"
        for item in report["registered_results"]
    ]
    return "\n".join(
        [
            "# 调度运行台账归档预演执行报告",
            "",
            f"- 生成时间：{report['generated_at']}",
            f"- pass: {report['pass']}",
            f"- error_count: {report['error_count']}",
            "- 执行范围：只登记计划结果和归档清单预演结果，不执行真实任务。",
            "",
            "| task_id | preview_status | actual_execution | copy_source_files | move_source_files | registered_result |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def main() -> int:
    generated_at = now()
    errors: list[str] = []
    for path in [FIELD_DEFINITION_JSON, LEDGER_JSON, ARCHIVE_REPORT_JSON]:
        if not path.exists():
            errors.append(f"缺少输入文件：{path}")

    field_definition = read_json(FIELD_DEFINITION_JSON) if FIELD_DEFINITION_JSON.exists() else {}
    ledger = read_json(LEDGER_JSON) if LEDGER_JSON.exists() else {"records": []}
    archive_report = read_json(ARCHIVE_REPORT_JSON) if ARCHIVE_REPORT_JSON.exists() else {"archive_items": []}

    for scope, data in [
        ("field_definition", field_definition),
        ("ledger", ledger),
        ("archive_report", archive_report),
    ]:
        for key in ["actual_execution", "copy_source_files", "move_source_files", "external_call", "reload_service"]:
            require_false(errors, data.get("defaults", data), key, scope)

    archive_by_task = {item.get("task_id"): item for item in archive_report.get("archive_items", [])}
    registered_results: list[dict[str, Any]] = []
    for record in ledger.get("records", []):
        task_id = record.get("task_id", "<missing>")
        archive_item = archive_by_task.get(task_id)
        if archive_item is None:
            errors.append(f"{task_id} 缺少归档清单项")
        for key in ["actual_execution", "copy_source_files", "move_source_files", "external_call", "reload_service"]:
            require_false(errors, record, key, task_id)
        if record.get("preview_status") != "not_executed":
            errors.append(f"{task_id}.preview_status 必须为 not_executed")
        registered_results.append(
            {
                "task_id": task_id,
                "task_name": record.get("task_name"),
                "plan_time": record.get("plan_time"),
                "preview_status": "not_executed",
                "registered_result": "planned_result_registered_only",
                "evidence_path": record.get("evidence_path"),
                "archive_item_id": archive_item.get("archive_item_id") if archive_item else None,
                "actual_execution": False,
                "copy_source_files": False,
                "move_source_files": False,
                "external_call": False,
                "reload_service": False,
            }
        )

    report = {
        "name": "低风险只读调度运行台账归档预演执行报告",
        "generated_at": generated_at,
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "record_count": len(ledger.get("records", [])),
        "archive_item_count": len(archive_report.get("archive_items", [])),
        "registered_results": registered_results,
        "actual_execution": False,
        "copy_source_files": False,
        "move_source_files": False,
        "external_call": False,
        "reload_service": False,
        "scope_statement": "只登记计划结果，不执行真实任务，不复制或移动业务证据。",
    }

    write_json(RUN_REPORT_JSON, report)
    write_text(RUN_REPORT_MD, build_report_md(report))
    write_json(RUN_LOG, report)
    print(json.dumps({"pass": report["pass"], "error_count": report["error_count"], "output": str(RUN_REPORT_JSON)}, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
