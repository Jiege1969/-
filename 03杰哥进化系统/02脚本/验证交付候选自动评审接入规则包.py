# -*- coding: utf-8 -*-
"""
名称：验证交付候选自动评审接入规则包.py
作用：只读解析03进化系统本地规则卡、审计清单、反退化样例和证据JSON，
      确认交付候选自动评审接入规则没有突破安全边界。
安全边界：不触发n8n，不发送企业微信，不写正式库，不调用Redis服务，
          不调用券商接口，不自动交易，不发起外部网络调用。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "03数据" / "29交付候选自动评审接入规则包"


FILES = {
    "规则卡JSON": DATA_DIR / "交付候选自动评审接入规则卡_最新.json",
    "规则卡MD": DATA_DIR / "交付候选自动评审接入规则卡_最新.md",
    "审计清单JSON": DATA_DIR / "交付候选自动评审审计清单_最新.json",
    "审计清单MD": DATA_DIR / "交付候选自动评审审计清单_最新.md",
    "反退化样例JSON": DATA_DIR / "反退化检查样例_最新.json",
    "反退化样例MD": DATA_DIR / "反退化检查样例_最新.md",
    "接入证据JSON": DATA_DIR / "交付候选自动评审接入证据_最新.json",
}


EXPECTED_RULE_IDS = {f"ARC-{index:03d}" for index in range(1, 10)}
EXPECTED_AUDIT_IDS = {f"DCA-{index:03d}" for index in range(1, 13)}
EXPECTED_BLOCK_SAMPLE_IDS = {f"AR-BLOCK-{index:03d}" for index in range(1, 11)}
REQUIRED_PRINCIPLES = {
    "总管唯一中枢",
    "不新增第二中枢",
    "不新增OpenClaw原件",
    "不新增Hermes原件",
    "只沉淀抽象接入规则",
    "任务契约dry_run优先",
    "Redis升级门槛",
    "n8n升级门槛",
    "真实动作闸门",
    "股票analysis_only",
    "并行小任务回收格式统一",
    "进度不得虚高",
}
REQUIRED_TASK_FIELDS = {
    "task_id",
    "source_system",
    "target_system",
    "candidate_type",
    "scope",
    "inputs",
    "expected_outputs",
    "dry_run",
    "real_action_requested",
    "external_service_requested",
    "safety_boundary",
    "rollback_plan",
    "acceptance",
    "recycle_report_path",
    "progress_claim_basis",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"检查项": name, "通过": bool(passed), "详情": detail})


def all_false(mapping: dict[str, Any]) -> bool:
    return all(value is False for value in mapping.values())


def main() -> int:
    checks: list[dict[str, Any]] = []

    for name, path in FILES.items():
        add_check(checks, f"{name}存在", path.exists(), str(path))

    if not all(item["通过"] for item in checks):
        failed_items = [item for item in checks if not item["通过"]]
        print(json.dumps({"通过": len(checks) - len(failed_items), "失败": len(failed_items), "检查项": checks}, ensure_ascii=False, indent=2))
        return 1

    rule_card = load_json(FILES["规则卡JSON"])
    audit = load_json(FILES["审计清单JSON"])
    samples = load_json(FILES["反退化样例JSON"])
    evidence = load_json(FILES["接入证据JSON"])

    rules = rule_card.get("核心规则", [])
    rule_ids = {item.get("规则ID") for item in rules}
    principles = rule_card.get("总体原则", {})
    task_fields = set(rule_card.get("任务契约必填字段", []))
    audit_items = audit.get("检查项", [])
    audit_ids = {item.get("检查项ID") for item in audit_items}
    sample_items = samples.get("反退化样例", [])
    sample_ids = {item.get("样例ID") for item in sample_items}
    shadow = evidence.get("影子接入声明", {})
    task_contract = shadow.get("task_contract", {})
    redis = shadow.get("redis", {})
    n8n = shadow.get("n8n", {})
    real_gate = shadow.get("real_action_gate", {})
    recycle = shadow.get("recycle_report", {})
    progress = shadow.get("progress", {})
    parallel = evidence.get("并行协作边界", {})

    add_check(checks, "规则ID ARC-001 至 ARC-009 完整", EXPECTED_RULE_IDS.issubset(rule_ids), sorted(rule_ids))
    add_check(checks, "总体原则12项均为true", REQUIRED_PRINCIPLES.issubset(principles.keys()) and all(principles.get(key) is True for key in REQUIRED_PRINCIPLES), principles)
    add_check(checks, "任务契约必填字段完整", REQUIRED_TASK_FIELDS.issubset(task_fields), sorted(task_fields))
    add_check(checks, "规则卡安全边界全关闭", all_false(rule_card.get("安全边界", {})), rule_card.get("安全边界", {}))

    add_check(checks, "审计检查项 DCA-001 至 DCA-012 完整", EXPECTED_AUDIT_IDS.issubset(audit_ids), sorted(audit_ids))
    add_check(checks, "审计检查项ID唯一", len(audit_ids) == len(audit_items), sorted(audit_ids))
    add_check(checks, "审计检查项均为阻断项", all(item.get("阻断项") is True for item in audit_items), audit_items)
    add_check(checks, "审计清单安全边界全关闭", all_false(audit.get("安全边界", {})), audit.get("安全边界", {}))

    add_check(checks, "反退化合规样例存在且期望pass", any(item.get("样例ID") == "AR-SAFE-001" and item.get("期望结论") == "pass" for item in sample_items), sorted(sample_ids))
    add_check(checks, "反退化阻断样例10项完整", EXPECTED_BLOCK_SAMPLE_IDS.issubset(sample_ids), sorted(sample_ids))
    add_check(checks, "反退化阻断样例均期望block", all(item.get("期望结论") == "block" for item in sample_items if str(item.get("样例ID", "")).startswith("AR-BLOCK-")), sample_items)
    add_check(checks, "反退化样例均映射规则", all(item.get("命中规则") for item in sample_items), sample_items)
    add_check(checks, "反退化样例安全边界全关闭", all_false(samples.get("安全边界", {})), samples.get("安全边界", {}))

    add_check(checks, "证据声明总管唯一中枢", shadow.get("center_role") == "rule_deposit_only" and shadow.get("second_center_created") is False, shadow)
    add_check(checks, "证据声明未新增OpenClaw/Hermes原件", shadow.get("source_originals_added") is False and shadow.get("openclaw_original_added") is False and shadow.get("hermes_original_added") is False and shadow.get("imported_runtime_dependency") is False, shadow)
    add_check(checks, "证据声明任务契约dry_run优先", task_contract.get("dry_run") is True and task_contract.get("real_action_requested") is False and task_contract.get("external_service_requested") is False and task_contract.get("required_fields_count") == len(REQUIRED_TASK_FIELDS), task_contract)
    add_check(checks, "证据声明Redis未升级为真实队列", redis.get("role") == "shadow_mapping_or_cache" and redis.get("real_action_queue") is False and redis.get("permission_release") is False and redis.get("upgrade_ready") is False and redis.get("official_progress_source") is False, redis)
    add_check(checks, "证据声明n8n仅dry_run且未触发", n8n.get("mode") == "dry_run_only" and n8n.get("workflow_import") is False and n8n.get("workflow_enabled") is False and n8n.get("workflow_triggered") is False and n8n.get("webhook_called") is False, n8n)
    add_check(checks, "证据声明真实动作闸门关闭", real_gate.get("enabled") is False and real_gate.get("mode") == "single_line_manual_gate" and real_gate.get("multi_gate_release") is False and real_gate.get("real_actions_triggered") == 0, real_gate)
    add_check(checks, "证据声明股票analysis-only", shadow.get("stock_scope") == "analysis_only" and shadow.get("broker_api_called") is False and shadow.get("order_created") is False and shadow.get("auto_trade") is False, shadow)
    add_check(checks, "证据声明回收格式统一", recycle.get("format_version") == "parallel-recycle-v1" and recycle.get("md_exists") is True and recycle.get("json_exists") is True and recycle.get("real_actions_triggered") == 0 and recycle.get("safety_boundary_present") is True and recycle.get("parallel_boundary_present") is True, recycle)
    add_check(checks, "证据声明进度不虚高", progress.get("claim_basis") == "verified_local_artifacts" and progress.get("validator_passed") is True and progress.get("blockers") == 0 and progress.get("global_progress_modified") is False, progress)
    add_check(checks, "证据安全边界全关闭", all_false(evidence.get("安全边界", {})), evidence.get("安全边界", {}))
    add_check(checks, "并行协作边界未触碰01/02和00非回收文件", parallel.get("未修改01智能系统文件") is True and parallel.get("未修改02扩展系统文件") is True and parallel.get("未修改00总管非并行回收文件") is True and parallel.get("未回退已有修改") is True, parallel)

    output_paths = evidence.get("产物路径", {})
    add_check(checks, "回收报告MD路径固定", output_paths.get("回收报告MD", "").endswith("00杰哥系统总管\\03数据\\并行回收\\03进化系统_交付候选自动评审接入回收报告_最新.md"), output_paths.get("回收报告MD"))
    add_check(checks, "回收报告JSON路径固定", output_paths.get("回收报告JSON", "").endswith("00杰哥系统总管\\03数据\\并行回收\\03进化系统_交付候选自动评审接入回收报告_最新.json"), output_paths.get("回收报告JSON"))

    failed_items = [item for item in checks if not item["通过"]]
    result = {
        "验证对象": str(DATA_DIR),
        "验证方式": "只读本地文件解析",
        "通过": len(checks) - len(failed_items),
        "失败": len(failed_items),
        "阻断项": len(failed_items),
        "真实动作数量": 0,
        "检查项": checks,
        "安全声明": "未触发n8n、未发送企业微信、未写正式库、未调用Redis服务、未调用券商接口、未自动交易、未发起外部网络调用",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failed_items else 1


if __name__ == "__main__":
    raise SystemExit(main())
