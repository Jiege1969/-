# -*- coding: utf-8 -*-
"""只读验证Redis Streams低风险正式队列前评估包。

本脚本只读取本地JSON/Markdown并打印校验结果；不连接Redis，不启动服务，
不触发n8n/企业微信/券商/自动交易，不写任何文件。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
CONTRACT_DIR = MANAGER / "03数据" / "任务契约"
RECYCLE_DIR = MANAGER / "03数据" / "并行回收"

PACKAGE_JSON = CONTRACT_DIR / "RedisStreams低风险正式队列前评估包_最新.json"
PACKAGE_MD = CONTRACT_DIR / "RedisStreams低风险正式队列前评估包_最新.md"
REPORT_JSON = RECYCLE_DIR / "00总管_Redis低风险正式队列前评估回收报告_最新.json"
REPORT_MD = RECYCLE_DIR / "00总管_Redis低风险正式队列前评估回收报告_最新.md"

FORBIDDEN_TRUE_KEYS = [
    "connect_real_redis",
    "start_service",
    "trigger_n8n",
    "send_wecom",
    "write_formal_database",
    "call_broker_api",
    "auto_trade",
    "external_network",
]

REQUIRED_TOPICS = [
    "stream_fields",
    "consumer_group_plan",
    "ack_policy",
    "pending_policy",
    "retry_policy",
    "dead_letter_stream",
    "idempotency_and_sqlite_ledger",
    "failure_recovery",
    "gpu_queueing",
    "resource_assessment",
    "formal_upgrade_gates",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace") if path.exists() else ""


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def nested_contains_key(value: Any, target: str) -> bool:
    if isinstance(value, dict):
        return target in value or any(nested_contains_key(item, target) for item in value.values())
    if isinstance(value, list):
        return any(nested_contains_key(item, target) for item in value)
    return False


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"check": name, "pass": bool(condition), "detail": detail}


def main() -> int:
    package = load_json(PACKAGE_JSON)
    report = load_json(REPORT_JSON)
    package_md = read_text(PACKAGE_MD)
    report_md = read_text(REPORT_MD)
    safety = package.get("hard_safety_boundary", {})
    field_rules = package.get("stream_fields", {}).get("field_rules", {})
    safety_flags = field_rules.get("safety_flags_json", {})
    gates = package.get("formal_upgrade_gates", [])
    artifacts = report.get("artifacts", [])
    checks = [
        check(PACKAGE_JSON.exists(), "评估包JSON存在", str(PACKAGE_JSON)),
        check(PACKAGE_MD.exists(), "评估包Markdown存在", str(PACKAGE_MD)),
        check(REPORT_JSON.exists(), "回收报告JSON存在", str(REPORT_JSON)),
        check(REPORT_MD.exists(), "回收报告Markdown存在", str(REPORT_MD)),
        check(package.get("current_state") == "shadow_mapping_only", "当前状态仍为shadow_mapping_only", package.get("current_state")),
        check(package.get("target_state") == "low_risk_formal_candidate", "目标候选状态正确", package.get("target_state")),
        check(package.get("evaluation_mode") == "offline_static_assessment_only", "评估模式为离线静态", package.get("evaluation_mode")),
        check(all(safety.get(key) is False for key in FORBIDDEN_TRUE_KEYS), "硬安全边界全部关闭真实副作用", safety),
        check(package.get("queue_candidate", {}).get("producer_policy", {}).get("xadd_enabled") is False, "XADD未启用", package.get("queue_candidate", {}).get("producer_policy", {})),
        check("task_id" in package.get("stream_fields", {}).get("required", []), "stream必填字段覆盖task_id", ""),
        check("idempotency_key" in package.get("stream_fields", {}).get("required", []), "stream必填字段覆盖idempotency_key", ""),
        check(safety_flags.get("n8n_trigger_allowed") is False, "n8n触发保持关闭", safety_flags),
        check(safety_flags.get("broker_api_allowed") is False and safety_flags.get("auto_trade_allowed") is False, "券商和自动交易保持关闭", safety_flags),
        check(nested_contains_key(package, "ack_policy"), "ACK策略已覆盖", ""),
        check(nested_contains_key(package, "pending_policy"), "PENDING策略已覆盖", ""),
        check(nested_contains_key(package, "retry_policy"), "重试策略已覆盖", ""),
        check(nested_contains_key(package, "dead_letter_stream"), "死信流已覆盖", ""),
        check(package.get("idempotency_and_sqlite_ledger", {}).get("sqlite_table_candidate") == "task_queue_ledger", "SQLite落账候选表已定义", package.get("idempotency_and_sqlite_ledger", {})),
        check(package.get("gpu_queueing", {}).get("limits", {}).get("max_gpu_tasks_pending") == 2, "GPU排队阈值已定义", package.get("gpu_queueing", {}).get("limits", {})),
        check(package.get("resource_assessment", {}).get("initial_consumer_count") == 1, "初始consumer数量为1", package.get("resource_assessment", {})),
        check(len(gates) >= 7 and all(item.get("required") is True for item in gates), "正式升级门槛完整且均为必需", gates),
        check(package.get("current_assessment", {}).get("can_enable_formal_queue_now") is False, "当前不能启用正式队列", package.get("current_assessment", {})),
        check(all(topic in json.dumps(package, ensure_ascii=False) for topic in REQUIRED_TOPICS), "JSON覆盖所有评估主题", REQUIRED_TOPICS),
        check(all(word in package_md for word in ["ACK", "PENDING", "SQLite", "GPU", "正式升级门槛"]), "Markdown覆盖关键章节", ""),
        check(report.get("validation", {}).get("mode") == "read_only_local_parse", "回收报告声明只读验证", report.get("validation", {})),
        check(report.get("validation", {}).get("external_services_touched") is False, "回收报告声明未触碰外部服务", report.get("validation", {})),
        check(str(PACKAGE_JSON) in artifacts and str(PACKAGE_MD) in artifacts, "回收报告列出评估包产物", artifacts),
        check("不连接真实Redis" in report_md and "不触发n8n" in report_md and "不自动交易" in report_md, "回收报告Markdown覆盖禁用动作", ""),
    ]
    failed = [item for item in checks if not item["pass"]]
    result = {
        "result": "PASS" if not failed else "FAIL",
        "total_checks": len(checks),
        "failed_checks": len(failed),
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
