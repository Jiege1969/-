import json
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\03数据\13低风险小样本许可令只读签发草案包")
PACKAGE_PATH = BASE_DIR / "低风险小样本许可令只读签发草案_20260505_Q.json"

EXPECTED_CANDIDATES = {
    "read_only_pull",
    "draft_generation",
    "internal_report_circulation",
}

REQUIRED_FORBIDDEN = {
    "enterprise_wechat_scale_up",
    "n8n_formal_trigger",
    "formal_database_write",
    "real_media_conversion",
    "formal_tax_judgement",
    "broker_interface",
    "automatic_trading",
}

REQUIRED_FALSE_FLAGS = [
    "external_system_called",
    "enterprise_wechat_sent",
    "enterprise_wechat_scale_up",
    "n8n_workflow_imported",
    "n8n_workflow_enabled",
    "n8n_formal_triggered",
    "production_database_written",
    "knowledge_base_written",
    "media_converted",
    "tax_formal_judgement_made",
    "broker_interface_called",
    "auto_trade_triggered",
]


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    failures = []
    package = load_json(PACKAGE_PATH)

    if package.get("status") != "readonly_issuance_draft_only":
        failures.append("status must be readonly_issuance_draft_only")
    if package.get("real_action_count") != 0:
        failures.append("real_action_count must be 0")
    if package.get("n8n_imported") is not False:
        failures.append("n8n_imported must be false")
    if package.get("n8n_enabled") is not False:
        failures.append("n8n_enabled must be false")
    if package.get("n8n_formal_triggered") is not False:
        failures.append("n8n_formal_triggered must be false")

    candidates = {
        item.get("candidate_id")
        for item in package.get("only_allowed_future_candidates", [])
    }
    if candidates != EXPECTED_CANDIDATES:
        failures.append(f"candidate set mismatch: {sorted(candidates)}")

    forbidden = {
        item.get("action_id")
        for item in package.get("still_forbidden_actions", [])
    }
    missing_forbidden = sorted(REQUIRED_FORBIDDEN - forbidden)
    if missing_forbidden:
        failures.append(f"missing forbidden actions: {missing_forbidden}")

    boundary = package.get("execution_boundary", {})
    for flag in REQUIRED_FALSE_FLAGS:
        if boundary.get(flag) is not False:
            failures.append(f"boundary flag must be false: {flag}")

    guardrails = package.get("small_sample_guardrails", {})
    if guardrails.get("data_write_flag_required_value") is not False:
        failures.append("data_write_flag_required_value must be false")
    if guardrails.get("external_call_flag_required_value") is not False:
        failures.append("external_call_flag_required_value must be false")
    if guardrails.get("formal_trigger_flag_required_value") is not False:
        failures.append("formal_trigger_flag_required_value must be false")
    if guardrails.get("human_review_required") is not True:
        failures.append("human_review_required must be true")

    for line in package.get("business_lines", []):
        line_candidates = set(line.get("allowed_future_candidates", []))
        if line_candidates != EXPECTED_CANDIDATES:
            failures.append(f"{line.get('line_id')} candidate set mismatch")
        if not line.get("required_evidence_before_future_use"):
            failures.append(f"{line.get('line_id')} missing required evidence")

    result = {
        "checked_package": str(PACKAGE_PATH),
        "checked_candidate_count": len(candidates),
        "checked_candidates": sorted(candidates),
        "checked_required_forbidden_actions": sorted(REQUIRED_FORBIDDEN),
        "checked_business_line_count": len(package.get("business_lines", [])),
        "n8n_imported": package.get("n8n_imported"),
        "n8n_enabled": package.get("n8n_enabled"),
        "n8n_formal_triggered": package.get("n8n_formal_triggered"),
        "real_actions_triggered": 0,
        "passed": not failures,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not failures else 1)


if __name__ == "__main__":
    main()
