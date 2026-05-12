import json
import sys
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\03数据\13可用入口清单操作卡包")
PACKAGE_PATH = BASE_DIR / "可用入口清单操作卡包_20260505_N.json"
MARKDOWN_PATH = BASE_DIR / "可用入口清单操作卡包_20260505_N.md"

EXPECTED_ENTRIES = {
    "stock_analysis",
    "enterprise_wechat_assistant",
    "knowledge_base_readonly_qa",
    "content_office_draft",
    "video_production_preplan",
    "tax_readonly_evidence_chain",
}

REQUIRED_FORBIDDEN = {
    "trigger_n8n_workflow",
    "call_n8n_webhook",
    "send_enterprise_wechat_real_message",
    "call_enterprise_wechat_response_url",
    "call_enterprise_wechat_group_robot_webhook",
    "write_production_database",
    "write_formal_knowledge_base",
    "write_vector_database",
    "convert_real_media",
    "make_formal_tax_judgement",
    "call_external_tax_api",
    "call_broker_interface",
    "place_order",
    "automatic_trading",
    "touch_main_work_system",
}

REQUIRED_ENTRY_FIELDS = {
    "entry_id",
    "entry_name",
    "entry_path",
    "entry_status",
    "availability",
    "use_method",
    "dry_run_status",
    "real_status",
    "rollback",
    "forbidden_actions",
    "operation_card",
}

LINE_FORBIDDEN_MINIMUMS = {
    "stock_analysis": {"call_broker_interface", "place_order", "automatic_trading"},
    "enterprise_wechat_assistant": {
        "send_enterprise_wechat_real_message",
        "call_enterprise_wechat_response_url",
        "call_enterprise_wechat_group_robot_webhook",
    },
    "knowledge_base_readonly_qa": {"write_formal_knowledge_base", "write_vector_database"},
    "content_office_draft": {"write_production_content_database", "publish_content"},
    "video_production_preplan": {"convert_real_media", "transcode_video", "render_final_video"},
    "tax_readonly_evidence_chain": {
        "make_formal_tax_judgement",
        "submit_tax_filing",
        "call_external_tax_api",
    },
}


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def all_boolean_values_false(mapping):
    return all(value is False for value in mapping.values() if isinstance(value, bool))


def main():
    failures = []
    package = load_json(PACKAGE_PATH)
    markdown = MARKDOWN_PATH.read_text(encoding="utf-8")

    if package.get("status") != "definition_and_readonly_validation_only":
        failures.append("package status must be definition_and_readonly_validation_only")

    boundary = package.get("work_system_boundary", {})
    if boundary.get("status") != "paused" or boundary.get("touched") is not False:
        failures.append("work system boundary must be paused and untouched")

    non_execution = package.get("non_execution_guarantee", {})
    if non_execution.get("real_actions_triggered") != 0:
        failures.append("real_actions_triggered must be 0")
    if not all_boolean_values_false(non_execution):
        failures.append("all non-execution boolean flags must remain false")

    policy = package.get("global_policy", {})
    if policy.get("dry_run_default") is not True:
        failures.append("global dry_run_default must be true")
    if policy.get("real_action_authorized") is not False:
        failures.append("real_action_authorized must be false")

    forbidden = set(policy.get("always_forbidden_actions", []))
    missing_forbidden = sorted(REQUIRED_FORBIDDEN - forbidden)
    if missing_forbidden:
        failures.append(f"missing global forbidden actions: {missing_forbidden}")

    entries = package.get("entries", [])
    entry_ids = {entry.get("entry_id") for entry in entries}
    if entry_ids != EXPECTED_ENTRIES:
        failures.append(f"entry id mismatch: {sorted(entry_ids)}")

    for entry in entries:
        entry_id = entry.get("entry_id", "<unknown>")
        missing_fields = sorted(REQUIRED_ENTRY_FIELDS - set(entry))
        if missing_fields:
            failures.append(f"{entry_id} missing fields: {missing_fields}")
            continue

        if not entry.get("use_method"):
            failures.append(f"{entry_id} use_method is empty")
        if entry.get("dry_run_status", {}).get("default") is not True:
            failures.append(f"{entry_id} dry_run default must be true")

        real_status = entry.get("real_status", {})
        if real_status.get("enabled") is not False or real_status.get("authorized") is not False:
            failures.append(f"{entry_id} real status must be disabled and unauthorized")

        rollback = entry.get("rollback", {})
        if not rollback.get("rollback_ref") or not rollback.get("steps"):
            failures.append(f"{entry_id} rollback ref and steps are required")

        line_forbidden = set(entry.get("forbidden_actions", []))
        missing_line_forbidden = sorted(LINE_FORBIDDEN_MINIMUMS.get(entry_id, set()) - line_forbidden)
        if missing_line_forbidden:
            failures.append(f"{entry_id} missing line forbidden actions: {missing_line_forbidden}")

        card = entry.get("operation_card", {})
        for field in ("title", "open_with", "do", "do_not", "acceptance"):
            if not card.get(field):
                failures.append(f"{entry_id} operation_card.{field} is required")

    acceptance = package.get("acceptance_criteria", {})
    if acceptance.get("entry_count") != 6:
        failures.append("acceptance entry_count must be 6")
    if acceptance.get("real_actions_triggered") != 0:
        failures.append("acceptance real_actions_triggered must be 0")
    if acceptance.get("work_system_untouched") is not True:
        failures.append("acceptance work_system_untouched must be true")

    validation = package.get("validation", {})
    if validation.get("readonly") is not True:
        failures.append("validation.readonly must be true")
    if validation.get("network_required") is not False:
        failures.append("validation.network_required must be false")
    if validation.get("writes_files") is not False:
        failures.append("validation.writes_files must be false")

    required_markdown_terms = [
        "股票分析",
        "企业微信助手",
        "知识库只读问答",
        "内容办公草稿",
        "视频制作预案",
        "税收只读证据链",
        "严禁触发",
        "本职工作系统：暂停",
    ]
    for term in required_markdown_terms:
        if term not in markdown:
            failures.append(f"markdown missing term: {term}")

    result = {
        "package_path": str(PACKAGE_PATH),
        "markdown_path": str(MARKDOWN_PATH),
        "checked_entries": sorted(entry_ids),
        "checked_entry_count": len(entry_ids),
        "checked_required_global_forbidden_actions": sorted(REQUIRED_FORBIDDEN),
        "real_actions_triggered": 0,
        "work_system_touched": False,
        "readonly_validation": True,
        "network_required": False,
        "writes_files": False,
        "passed": not failures,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
