import json
import sys
from pathlib import Path


PACKAGE_PATH = Path(
    r"D:\杰哥智能化系统\02杰哥扩展系统\03数据\10多业务线任务契约干跑适配包\多业务线任务契约干跑适配包_20260505_B.json"
)

EXPECTED_LINES = {
    "enterprise_wechat",
    "knowledge_base",
    "content_processing",
    "video_production",
    "tax_readonly",
}

REQUIRED_GLOBAL_BLOCKS = {
    "trigger_n8n",
    "send_enterprise_wechat_real_message",
    "write_production_database",
    "write_production_knowledge_base",
    "convert_real_media",
    "make_formal_tax_judgement",
    "call_broker_api",
    "auto_trade",
    "touch_main_work_system",
}


def check(condition, name, failures):
    if condition:
        return
    failures.append(name)


def main():
    failures = []
    with PACKAGE_PATH.open("r", encoding="utf-8") as file:
        package = json.load(file)

    principle = package.get("principle", {})
    check(principle.get("real_actions_enabled") is False, "real_actions_enabled must be false", failures)
    check(principle.get("dry_run_only") is True, "dry_run_only must be true", failures)
    check(principle.get("production_systems_blocked") is True, "production systems must be blocked", failures)

    adapters = package.get("business_line_adapters", [])
    adapter_lines = {item.get("business_line") for item in adapters}
    check(adapter_lines == EXPECTED_LINES, "all five business line adapters must exist exactly", failures)

    for adapter in adapters:
        line = adapter.get("business_line", "<unknown>")
        receive = adapter.get("receive_standard_task_order", {})
        receipt = adapter.get("receipt_output", {})
        check(receive.get("dry_run_required") is True, f"{line} dry_run_required must be true", failures)
        check(bool(adapter.get("blocked_real_actions")), f"{line} blocked_real_actions must be non-empty", failures)
        check(bool(adapter.get("dry_run_guards")), f"{line} dry_run_guards must be non-empty", failures)
        check(receipt.get("status", "").endswith("receipt_only"), f"{line} receipt status must be receipt_only", failures)

    infra = package.get("shadow_infrastructure", {})
    sqlite_shadow = infra.get("sqlite_shadow_ledger", {})
    redis_shadow = infra.get("redis_shadow_mapping", {})
    n8n_shadow = infra.get("n8n_dry_run", {})
    check(sqlite_shadow.get("connect") is False, "sqlite connect must be false", failures)
    check(sqlite_shadow.get("write") is False, "sqlite write must be false", failures)
    check(redis_shadow.get("connect") is False, "redis connect must be false", failures)
    check(redis_shadow.get("write") is False, "redis write must be false", failures)
    check(n8n_shadow.get("trigger_n8n") is False, "n8n trigger must be false", failures)
    check(n8n_shadow.get("webhook_url") is None, "n8n webhook_url must be null", failures)
    check(n8n_shadow.get("workflow_activation") is False, "n8n workflow_activation must be false", failures)

    task_orders = package.get("sample_task_orders", [])
    receipts = package.get("sample_receipts", [])
    check(len(task_orders) == len(EXPECTED_LINES), "sample task order count must match business lines", failures)
    check(len(receipts) == len(EXPECTED_LINES), "sample receipt count must match business lines", failures)

    for order in task_orders:
        task_id = order.get("task_id", "<unknown>")
        check(order.get("dry_run") is True, f"{task_id} dry_run must be true", failures)
        check(order.get("receipt_required") is True, f"{task_id} receipt_required must be true", failures)
        check(order.get("business_line") in EXPECTED_LINES, f"{task_id} business_line must be expected", failures)

    for receipt in receipts:
        receipt_id = receipt.get("receipt_id", "<unknown>")
        check(receipt.get("dry_run") is True, f"{receipt_id} dry_run must be true", failures)
        check(bool(receipt.get("blocked_actions")), f"{receipt_id} blocked_actions must be non-empty", failures)
        check(str(receipt.get("shadow_ledger_ref", "")).startswith("sqlite-shadow://"), f"{receipt_id} shadow ledger ref missing", failures)
        check(str(receipt.get("redis_shadow_key", "")).startswith("dryrun:ext:task_contract:"), f"{receipt_id} redis shadow key missing", failures)
        check(receipt.get("n8n_dry_run_ref") == "n8n-dryrun-descriptor-only:no-trigger", f"{receipt_id} n8n dry-run ref invalid", failures)

    global_blocks = set(package.get("global_blocked_actions", []))
    missing_blocks = sorted(REQUIRED_GLOBAL_BLOCKS - global_blocks)
    check(not missing_blocks, f"missing global blocked actions: {missing_blocks}", failures)

    result = {
        "package_path": str(PACKAGE_PATH),
        "checked_business_lines": sorted(adapter_lines),
        "checked_task_orders": len(task_orders),
        "checked_receipts": len(receipts),
        "real_actions_triggered": 0,
        "passed": not failures,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
