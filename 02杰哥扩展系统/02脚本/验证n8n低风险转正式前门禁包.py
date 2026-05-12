import json
import sys
from pathlib import Path


PACKAGE_PATH = Path(
    r"D:\杰哥智能化系统\02杰哥扩展系统\03数据\11n8n低风险转正式前门禁包\n8n低风险转正式前门禁包_20260505_F.json"
)

EXPECTED_LINES = {
    "enterprise_wechat",
    "knowledge_base",
    "content_processing",
    "video_production",
    "tax_readonly",
}

REQUIRED_AUDIT_FIELDS = {
    "gate_package_id",
    "business_line",
    "requested_action",
    "dry_run_before_state",
    "target_low_risk_state",
    "approval_ticket",
    "operator",
    "reviewer",
    "allowlist_ref",
    "rollback_ref",
    "kill_switch_ref",
    "n8n_workflow_id",
    "n8n_workflow_active_before",
    "n8n_workflow_active_after",
    "real_action_enabled",
    "production_write_enabled",
    "external_call_enabled",
    "blocked_actions",
    "receipt_id",
    "evidence_ref",
    "timestamp_utc8",
}

GLOBAL_FALSE_FLAGS = {
    "workflow_import",
    "workflow_enable",
    "workflow_trigger",
    "workflow_activation",
    "n8n_api_call",
    "webhook_call",
    "credential_read_or_write",
    "external_system_call",
}

POLICY_FALSE_FLAGS = {
    "promotion_authorized",
    "production_write_allowed",
    "real_message_send_allowed",
    "real_media_conversion_allowed",
    "formal_tax_judgement_allowed",
}

REQUIRED_FORBIDDEN = {
    "import_n8n_workflow",
    "enable_n8n_workflow",
    "trigger_n8n_workflow",
    "call_n8n_webhook",
    "send_enterprise_wechat_real_message",
    "write_production_database",
    "write_production_knowledge_base",
    "write_vector_database",
    "convert_real_media",
    "render_or_publish_real_video",
    "make_formal_tax_judgement",
    "submit_tax_filing",
    "call_external_tax_api",
    "touch_main_work_system",
    "delete_or_move_user_files",
    "read_or_write_real_credentials",
}

LINE_REQUIRED_FORBIDDEN = {
    "enterprise_wechat": {
        "send_enterprise_wechat_real_message",
        "call_response_url",
        "call_group_robot_webhook",
        "write_formal_message_queue",
    },
    "knowledge_base": {
        "write_production_knowledge_base",
        "write_vector_database",
        "call_external_search_api",
    },
    "content_processing": {
        "write_production_content_database",
        "publish_content",
        "schedule_publish",
        "convert_real_document",
    },
    "video_production": {
        "convert_real_media",
        "transcode_video",
        "render_final_video",
        "publish_video",
    },
    "tax_readonly": {
        "make_formal_tax_judgement",
        "generate_tax_filing_advice",
        "submit_tax_filing",
        "write_production_tax_database",
        "call_external_tax_api",
    },
}


def check(condition, message, failures):
    if not condition:
        failures.append(message)


def all_false(mapping):
    return all(value is False for value in mapping.values())


def main():
    failures = []

    with PACKAGE_PATH.open("r", encoding="utf-8") as file:
        package = json.load(file)

    non_execution = package.get("non_execution_guarantee", {})
    for flag in GLOBAL_FALSE_FLAGS:
        check(non_execution.get(flag) is False, f"non_execution_guarantee.{flag} must be false", failures)
    check(non_execution.get("real_actions_triggered") == 0, "real_actions_triggered must be 0", failures)

    policy = package.get("global_gate_policy", {})
    check(policy.get("dry_run_default") is True, "dry_run_default must be true", failures)
    check(policy.get("manual_approval_required") is True, "manual approval must be required", failures)
    check(policy.get("two_person_review_required") is True, "two-person review must be required", failures)
    check(policy.get("audit_receipt_required") is True, "audit receipt must be required", failures)
    check(policy.get("rollback_plan_required") is True, "rollback plan must be required", failures)
    check(policy.get("kill_switch_required") is True, "kill switch must be required", failures)
    for flag in POLICY_FALSE_FLAGS:
        check(policy.get(flag) is False, f"global_gate_policy.{flag} must be false", failures)

    forbidden = set(policy.get("always_forbidden_action_types", []))
    missing_forbidden = sorted(REQUIRED_FORBIDDEN - forbidden)
    check(not missing_forbidden, f"missing global forbidden actions: {missing_forbidden}", failures)

    audit_fields = set(package.get("required_audit_fields", []))
    missing_audit_fields = sorted(REQUIRED_AUDIT_FIELDS - audit_fields)
    check(not missing_audit_fields, f"missing required audit fields: {missing_audit_fields}", failures)

    gates = package.get("business_line_gates", [])
    line_names = {gate.get("business_line") for gate in gates}
    check(line_names == EXPECTED_LINES, "business_line_gates must cover exactly five expected lines", failures)

    for gate in gates:
        line = gate.get("business_line", "<unknown>")
        check(len(gate.get("front_gate_checklist", [])) >= 5, f"{line} checklist must have at least five items", failures)
        check(gate.get("allowlist", {}).get("mode"), f"{line} allowlist mode is required", failures)
        check(gate.get("rollback", {}).get("rollback_ref"), f"{line} rollback_ref is required", failures)
        check(gate.get("rollback", {}).get("steps"), f"{line} rollback steps are required", failures)

        line_forbidden = set(gate.get("forbidden_actions", []))
        missing_line_forbidden = sorted(LINE_REQUIRED_FORBIDDEN.get(line, set()) - line_forbidden)
        check(not missing_line_forbidden, f"{line} missing forbidden actions: {missing_line_forbidden}", failures)

        sensitive = gate.get("sensitive_actions_status", {})
        check(sensitive and all_false(sensitive), f"{line} sensitive action flags must all be false", failures)

    n8n_guard = package.get("n8n_descriptor_guard", {})
    check(n8n_guard.get("descriptor_only") is True, "n8n descriptor_only must be true", failures)
    check(n8n_guard.get("workflow_json_export_path") is None, "workflow_json_export_path must be null", failures)
    check(n8n_guard.get("workflow_import_command") is None, "workflow_import_command must be null", failures)
    check(n8n_guard.get("workflow_activation_command") is None, "workflow_activation_command must be null", failures)
    check(n8n_guard.get("webhook_url") is None, "webhook_url must be null", failures)

    receipt_schema = package.get("sample_receipt_schema", {})
    check(receipt_schema.get("status") == "front_gate_defined_no_execution", "receipt schema status invalid", failures)
    check(receipt_schema.get("real_actions_triggered") == 0, "receipt real_actions_triggered must be 0", failures)

    validation = package.get("validation", {})
    check(validation.get("readonly") is True, "validation.readonly must be true", failures)
    check(validation.get("network_required") is False, "validation.network_required must be false", failures)
    check(validation.get("writes_files") is False, "validation.writes_files must be false", failures)

    result = {
        "package_path": str(PACKAGE_PATH),
        "checked_business_lines": sorted(line_names),
        "checked_gate_count": len(gates),
        "checked_required_audit_fields": len(audit_fields),
        "checked_global_forbidden_actions": len(forbidden),
        "real_actions_triggered": 0,
        "passed": not failures,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
