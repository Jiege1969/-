# -*- coding: utf-8 -*-
"""生成低风险只读调度运行台账与证据归档预演包。

本脚本只生成本地 JSON/MD 预演材料：登记计划结果、字段定义和证据归档清单。
不真实发送企业微信、不接 n8n、不接券商、不交易、不登录税局、不接财税软件、
不自动转正式规则、不改总管面板、不改一键接续包、不重载服务。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
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
PACKAGE_JSON = DATA_DIR / "低风险只读调度运行台账与证据归档预演包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度运行台账与证据归档预演包_最新.md"
GENERATE_LOG = LOG_DIR / "low-risk-readonly-scheduler-ledger-evidence-preview-generate-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_hash(data: dict[str, Any]) -> str:
    payload = {key: value for key, value in data.items() if key != "hash"}
    return sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def safety_flags() -> dict[str, bool]:
    return {
        "actual_execution": False,
        "copy_source_files": False,
        "move_source_files": False,
        "external_call": False,
        "reload_service": False,
        "real_wecom_send": False,
        "trigger_n8n": False,
        "broker_connection": False,
        "trade_order": False,
        "tax_bureau_login": False,
        "finance_tax_software_connection": False,
        "auto_promote_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
    }


def build_field_definition(generated_at: str) -> dict[str, Any]:
    fields = [
        ("task_id", "string", True, "预演任务唯一编号。"),
        ("task_name", "string", True, "预演任务名称。"),
        ("plan_time", "string", True, "计划登记时间，仅用于预演排序，不注册调度。"),
        ("preview_status", "string", True, "固定默认为 not_executed。"),
        ("pause_required", "boolean", True, "是否需要人工暂停复核；预演只登记，不执行。"),
        ("evidence_path", "string", True, "预演证据归档目标路径，仅登记清单，不复制/移动源文件。"),
        ("hash", "string", True, "台账记录规范化内容的 sha256。"),
        ("operator_mode", "string", True, "固定 readonly_preview。"),
        ("actual_execution", "boolean", True, "固定 false，确认未真实执行。"),
        ("copy_source_files", "boolean", True, "固定 false，确认未复制业务源文件。"),
        ("move_source_files", "boolean", True, "固定 false，确认未移动业务源文件。"),
        ("external_call", "boolean", True, "固定 false，确认未调用外部接口。"),
        ("reload_service", "boolean", True, "固定 false，确认未重载服务。"),
    ]
    return {
        "name": "低风险只读调度运行台账字段定义",
        "generated_at": generated_at,
        "scope": "readonly_scheduler_ledger_and_evidence_archive_preview_only",
        "required_minimum_fields": [
            "task_id",
            "task_name",
            "plan_time",
            "preview_status",
            "pause_required",
            "evidence_path",
            "hash",
            "operator_mode",
        ],
        "field_count": len(fields),
        "fields": [
            {
                "name": name,
                "type": field_type,
                "required": required,
                "description": description,
            }
            for name, field_type, required, description in fields
        ],
        "defaults": {
            "preview_status": "not_executed",
            "operator_mode": "readonly_preview",
            **safety_flags(),
        },
        "hard_red_line_confirmation": safety_flags(),
    }


def build_ledger(generated_at: str) -> dict[str, Any]:
    base_time = datetime.now().replace(second=0, microsecond=0)
    task_specs = [
        ("LRSL-001", "读取低风险只读调度入口清单快照", False),
        ("LRSL-002", "登记计划时间与人工暂停标记", False),
        ("LRSL-003", "生成证据路径占位与哈希", False),
        ("LRSL-004", "预演日常运行台账待登记项", False),
        ("LRSL-005", "预演跨业务证据引用清单", False),
        ("LRSL-006", "预演异常暂停待复核记录", True),
        ("LRSL-007", "预演只读归档索引行", False),
        ("LRSL-008", "汇总验收日志输入项", False),
    ]
    records: list[dict[str, Any]] = []
    for index, (task_id, task_name, pause_required) in enumerate(task_specs, start=1):
        evidence_path = str(DATA_DIR / "evidence_preview" / f"{task_id}.placeholder.json")
        record = {
            "task_id": task_id,
            "task_name": task_name,
            "plan_time": (base_time + timedelta(minutes=15 * index)).strftime("%Y-%m-%d %H:%M:%S"),
            "preview_status": "not_executed",
            "pause_required": pause_required,
            "evidence_path": evidence_path,
            "hash": "",
            "operator_mode": "readonly_preview",
            "actual_execution": False,
            "copy_source_files": False,
            "move_source_files": False,
            "external_call": False,
            "reload_service": False,
            "source_file_touched": False,
            "planned_result_only": True,
            "notes": "仅登记计划结果，不执行真实任务，不复制或移动业务证据。",
        }
        record["hash"] = stable_hash(record)
        records.append(record)
    return {
        "name": "低风险只读调度预演台账",
        "generated_at": generated_at,
        "preview_status_default": "not_executed",
        "actual_execution": False,
        "copy_source_files": False,
        "move_source_files": False,
        "external_call": False,
        "reload_service": False,
        "record_count": len(records),
        "records": records,
        "hard_red_line_confirmation": safety_flags(),
    }


def build_archive_report(generated_at: str, ledger: dict[str, Any]) -> dict[str, Any]:
    archive_items: list[dict[str, Any]] = []
    for record in ledger["records"]:
        source_reference = f"readonly-source-reference://{record['task_id']}"
        archive_item = {
            "archive_item_id": f"ARCH-{record['task_id']}",
            "task_id": record["task_id"],
            "task_name": record["task_name"],
            "source_reference": source_reference,
            "planned_archive_path": record["evidence_path"],
            "source_hash_preview": sha256_text(source_reference),
            "copy_source_files": False,
            "move_source_files": False,
            "actual_execution": False,
            "external_call": False,
            "archive_action": "list_only_no_copy_no_move",
            "preview_status": "not_executed",
        }
        archive_items.append(archive_item)
    return {
        "name": "低风险只读调度证据归档预演报告",
        "generated_at": generated_at,
        "summary": "只生成归档清单，不复制、不移动业务源文件。",
        "archive_item_count": len(archive_items),
        "actual_execution": False,
        "copy_source_files": False,
        "move_source_files": False,
        "external_call": False,
        "reload_service": False,
        "archive_items": archive_items,
        "hard_red_line_confirmation": safety_flags(),
    }


def field_definition_md(data: dict[str, Any]) -> str:
    rows = [
        f"| {field['name']} | {field['type']} | {field['required']} | {field['description']} |"
        for field in data["fields"]
    ]
    return "\n".join(
        [
            "# 运行台账字段定义",
            "",
            f"- 生成时间：{data['generated_at']}",
            f"- 范围：{data['scope']}",
            "- 默认：preview_status=not_executed，operator_mode=readonly_preview。",
            "",
            "| 字段 | 类型 | 必填 | 说明 |",
            "| --- | --- | --- | --- |",
            *rows,
        ]
    )


def ledger_md(data: dict[str, Any]) -> str:
    rows = [
        f"| {item['task_id']} | {item['task_name']} | {item['plan_time']} | {item['preview_status']} | {item['pause_required']} | {item['actual_execution']} | {item['operator_mode']} |"
        for item in data["records"]
    ]
    return "\n".join(
        [
            "# 调度预演台账",
            "",
            f"- 生成时间：{data['generated_at']}",
            "- 确认：只登记计划结果，actual_execution=false。",
            "",
            "| task_id | task_name | plan_time | preview_status | pause_required | actual_execution | operator_mode |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def archive_report_md(data: dict[str, Any]) -> str:
    rows = [
        f"| {item['archive_item_id']} | {item['task_id']} | {item['planned_archive_path']} | {item['copy_source_files']} | {item['move_source_files']} | {item['actual_execution']} |"
        for item in data["archive_items"]
    ]
    return "\n".join(
        [
            "# 证据归档预演报告",
            "",
            f"- 生成时间：{data['generated_at']}",
            "- 归档动作：只生成清单，不复制、不移动业务源文件。",
            f"- archive_item_count: {data['archive_item_count']}",
            "",
            "| archive_item_id | task_id | planned_archive_path | copy_source_files | move_source_files | actual_execution |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def package_md(data: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 低风险只读调度运行台账与证据归档预演包",
            "",
            f"- 生成时间：{data['generated_at']}",
            f"- pass: {data['pass']}",
            f"- record_count: {data['ledger']['record_count']}",
            f"- archive_item_count: {data['archive_report']['archive_item_count']}",
            "- 硬红线：不真实发送企业微信、不接 n8n、不接券商、不交易、不登录税局、不接财税软件、不自动转正式规则、不改总管面板、不改一键接续包、不重载服务。",
            "- 本包只登记计划结果与归档清单，不执行真实任务，不移动业务证据。",
        ]
    )


def main() -> int:
    generated_at = now()
    field_definition = build_field_definition(generated_at)
    ledger = build_ledger(generated_at)
    archive_report = build_archive_report(generated_at, ledger)
    package = {
        "name": "低风险只读调度运行台账与证据归档预演包",
        "generated_at": generated_at,
        "pass": True,
        "error_count": 0,
        "field_definition": field_definition,
        "ledger": ledger,
        "archive_report": archive_report,
        "actual_execution": False,
        "copy_source_files": False,
        "move_source_files": False,
        "external_call": False,
        "reload_service": False,
        "hard_red_line_confirmation": safety_flags(),
    }

    write_json(FIELD_DEFINITION_JSON, field_definition)
    write_text(FIELD_DEFINITION_MD, field_definition_md(field_definition))
    write_json(LEDGER_JSON, ledger)
    write_text(LEDGER_MD, ledger_md(ledger))
    write_json(ARCHIVE_REPORT_JSON, archive_report)
    write_text(ARCHIVE_REPORT_MD, archive_report_md(archive_report))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))
    write_json(GENERATE_LOG, package)

    print(json.dumps({"pass": True, "error_count": 0, "output": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
