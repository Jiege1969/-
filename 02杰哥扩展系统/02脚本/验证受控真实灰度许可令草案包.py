import json
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\03数据\12受控真实灰度许可令草案包")
PACKAGE_PATH = BASE_DIR / "受控真实灰度许可令草案包_20260505_I.json"
WHITELIST_PATH = BASE_DIR / "受控真实灰度许可令白名单草案_20260505_I.json"
CONTROL_PATH = BASE_DIR / "受控真实灰度回滚监控复核字段_20260505_I.json"

EXPECTED_LINES = {
    "enterprise_wechat",
    "knowledge_base",
    "content_processing",
    "video_production",
    "tax_readonly",
}

EXPECTED_LOW_RISK = {
    "read_only_pull",
    "draft_generation",
    "internal_report_circulation",
}

EXPECTED_FORBIDDEN = {
    "enterprise_wechat_scale_up",
    "formal_database_write",
    "real_media_conversion",
    "formal_tax_judgement",
    "broker_interface",
    "automatic_trading",
}


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    failures = []
    package = load_json(PACKAGE_PATH)
    whitelist = load_json(WHITELIST_PATH)
    controls = load_json(CONTROL_PATH)

    package_lines = {item.get("line_id") for item in package.get("business_lines", [])}
    whitelist_lines = {item.get("line_id") for item in whitelist.get("entries", [])}
    control_lines = {item.get("line_id") for item in controls.get("line_controls", [])}

    if package.get("status") != "draft_only":
        failures.append("package status is not draft_only")
    if package.get("real_action_count") != 0:
        failures.append("package real_action_count is not zero")
    if whitelist.get("real_action_count") != 0:
        failures.append("whitelist real_action_count is not zero")
    if controls.get("real_action_count") != 0:
        failures.append("controls real_action_count is not zero")

    if package_lines != EXPECTED_LINES:
        failures.append(f"package line mismatch: {sorted(package_lines)}")
    if whitelist_lines != EXPECTED_LINES:
        failures.append(f"whitelist line mismatch: {sorted(whitelist_lines)}")
    if control_lines != EXPECTED_LINES:
        failures.append(f"control line mismatch: {sorted(control_lines)}")

    low_risk = set(package.get("future_low_risk_formal_candidates", []))
    if low_risk != EXPECTED_LOW_RISK:
        failures.append(f"low risk candidates mismatch: {sorted(low_risk)}")

    forbidden = set(package.get("still_forbidden_actions", []))
    missing_forbidden = sorted(EXPECTED_FORBIDDEN - forbidden)
    if missing_forbidden:
        failures.append(f"missing forbidden actions: {missing_forbidden}")

    boundary = package.get("execution_boundary", {})
    expected_false_flags = [
        "external_system_called",
        "enterprise_wechat_sent",
        "production_database_written",
        "knowledge_base_written",
        "media_converted",
        "tax_formal_judgement_made",
        "broker_interface_called",
        "auto_trade_triggered",
    ]
    for flag in expected_false_flags:
        if boundary.get(flag) is not False:
            failures.append(f"boundary flag must be false: {flag}")
    if boundary.get("work_system_paused_and_untouched") is not True:
        failures.append("work system pause boundary missing")

    required_line_sections = [
        "permission_order_draft",
        "whitelist_draft",
        "rollback_draft",
        "monitoring_draft",
        "manual_review_fields",
    ]
    for line in package.get("business_lines", []):
        for section in required_line_sections:
            if not line.get(section):
                failures.append(f"{line.get('line_id')} missing section: {section}")

    result = {
        "checked_package": str(PACKAGE_PATH),
        "checked_whitelist": str(WHITELIST_PATH),
        "checked_controls": str(CONTROL_PATH),
        "checked_business_lines": sorted(package_lines),
        "checked_line_count": len(package_lines),
        "checked_low_risk_candidates": sorted(low_risk),
        "checked_forbidden_actions_minimum": sorted(EXPECTED_FORBIDDEN),
        "checked_global_review_fields": len(controls.get("global_review_fields", [])),
        "real_actions_triggered": 0,
        "passed": not failures,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not failures else 1)


if __name__ == "__main__":
    main()
