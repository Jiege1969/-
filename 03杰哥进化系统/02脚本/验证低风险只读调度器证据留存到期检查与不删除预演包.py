# -*- coding: utf-8 -*-
"""验证低风险只读调度器证据留存到期检查与不删除预演包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = EVOLUTION_ROOT / "03数据"
DATA_DIR = DATA_ROOT / "118低风险只读调度器证据留存到期检查与不删除预演包"
HISTORY_114_DIR = DATA_ROOT / "114并行自主施工分片护栏与抢占处理包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器证据留存到期检查与不删除预演包验收"

POLICY_JSON = DATA_DIR / "证据留存到期检查策略_最新.json"
POLICY_MD = DATA_DIR / "证据留存到期检查策略_最新.md"
INVENTORY_JSON = DATA_DIR / "证据留存样本清单_最新.json"
INVENTORY_MD = DATA_DIR / "证据留存样本清单_最新.md"
QUEUE_JSON = DATA_DIR / "到期不删除处理队列_最新.json"
QUEUE_MD = DATA_DIR / "到期不删除处理队列_最新.md"
REPORT_JSON = DATA_DIR / "不删除预演报告_最新.json"
REPORT_MD = DATA_DIR / "不删除预演报告_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器证据留存到期检查与不删除预演包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器证据留存到期检查与不删除预演包_最新.md"
VERIFY_JSON = LOG_DIR / "low-risk-readonly-scheduler-evidence-retention-expiry-verify-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def require_false(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not False:
        errors.append(f"{scope}.{key} 必须为 false")


def require_true(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not True:
        errors.append(f"{scope}.{key} 必须为 true")


def require_safety(errors: list[str], data: dict[str, Any], scope: str) -> None:
    for key in ["delete_file", "remove_directory", "move_history_package", "overwrite_history_package", "external_call", "send_notification", "connect_n8n", "reload_service", "promote_to_formal_rule", "modify_supervisor_panel", "modify_one_click_continuation_package"]:
        require_false(errors, data, key, scope)
    require_true(errors, data, "read_only", scope)
    require_true(errors, data, "write_scope_is_118_only", scope)


def main() -> int:
    errors: list[str] = []
    required_files = [
        POLICY_JSON,
        POLICY_MD,
        INVENTORY_JSON,
        INVENTORY_MD,
        QUEUE_JSON,
        QUEUE_MD,
        REPORT_JSON,
        REPORT_MD,
        PACKAGE_JSON,
        PACKAGE_MD,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件: {path}")

    policy = read_json(POLICY_JSON) if POLICY_JSON.exists() else {"rules": [], "safety_confirmation": {}}
    inventory = read_json(INVENTORY_JSON) if INVENTORY_JSON.exists() else {"samples": [], "safety_confirmation": {}}
    queue = read_json(QUEUE_JSON) if QUEUE_JSON.exists() else {"items": [], "safety_confirmation": {}}
    report = read_json(REPORT_JSON) if REPORT_JSON.exists() else {"results": [], "safety_confirmation": {}}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {"safety_confirmation": {}}

    if DATA_DIR.name.startswith("118") is not True:
        errors.append("数据目录必须使用 118 编号")
    if "114" in str(DATA_DIR):
        errors.append("118 包数据目录不得指向 114")
    if not HISTORY_114_DIR.exists():
        errors.append("114 历史包目录未找到，无法证明保护边界")

    for scope, data in [("policy", policy), ("inventory", inventory), ("queue", queue), ("report", report), ("package", package)]:
        require_false(errors, data, "delete_allowed", scope)
        require_safety(errors, data.get("safety_confirmation", {}), f"{scope}.safety_confirmation")
    require_true(errors, policy, "readonly_dry_run_only", "policy")
    require_true(errors, inventory, "readonly_dry_run_only", "inventory")
    require_true(errors, queue, "readonly_dry_run_only", "queue")
    require_true(errors, report, "readonly_dry_run_only", "report")
    require_true(errors, package, "readonly_dry_run_only", "package")
    require_true(errors, report, "history_content_untouched", "report")
    require_true(errors, package, "history_content_untouched", "package")
    require_true(errors, report, "write_scope_is_118_only", "report")
    require_true(errors, package, "write_scope_is_118_only", "package")

    if len(policy.get("rules", [])) < 5:
        errors.append("策略规则数必须不少于 5")
    if len(inventory.get("samples", [])) < 4:
        errors.append("证据样本数必须不少于 4")
    if len(queue.get("items", [])) < 4:
        errors.append("到期不删除处理队列必须不少于 4")
    if len(report.get("results", [])) != len(queue.get("items", [])):
        errors.append("不删除预演报告结果数必须等于队列数")

    for rule in policy.get("rules", []):
        scope = f"policy.{rule.get('id', '<missing>')}"
        require_false(errors, rule, "delete_allowed", scope)
        require_true(errors, rule, "requires_supervisor_confirmation", scope)
        require_true(errors, rule, "dry_run_only", scope)
    for sample in inventory.get("samples", []):
        scope = f"inventory.{sample.get('id', '<missing>')}"
        require_false(errors, sample, "delete_allowed", scope)
    for item in queue.get("items", []):
        scope = f"queue.{item.get('id', '<missing>')}"
        if item.get("decision") != "不删除":
            errors.append(f"{scope}.decision 必须为 不删除")
        require_false(errors, item, "delete_allowed", scope)
        require_true(errors, item, "dry_run_only", scope)
        require_true(errors, item, "evidence_retained", scope)
        require_true(errors, item, "history_content_untouched", scope)
    for result in report.get("results", []):
        scope = f"report.{result.get('queue_id', '<missing>')}"
        if result.get("decision") != "不删除":
            errors.append(f"{scope}.decision 必须为 不删除")
        require_false(errors, result, "delete_allowed", scope)
        require_true(errors, result, "dry_run_only", scope)
        require_true(errors, result, "evidence_retained", scope)
        require_true(errors, result, "history_content_untouched", scope)
        require_false(errors, result, "actual_delete_performed", scope)
        require_false(errors, result, "actual_move_performed", scope)
        require_false(errors, result, "external_call", scope)

    verification = {
        "name": "低风险只读调度器证据留存到期检查与不删除预演包验收",
        "generated_at": now(),
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "target_data_dir": str(DATA_DIR),
        "log_dir": str(LOG_DIR),
        "history_114_dir": str(HISTORY_114_DIR),
        "history_114_protected": HISTORY_114_DIR.exists(),
        "delete_allowed": False,
        "readonly_dry_run_only": True,
        "history_content_untouched": True,
        "write_scope_is_118_only": True,
        "metrics": {
            "required_file_count": len(required_files),
            "existing_file_count": sum(1 for path in required_files if path.exists()),
            "policy_rule_count": len(policy.get("rules", [])),
            "inventory_sample_count": len(inventory.get("samples", [])),
            "queue_count": len(queue.get("items", [])),
            "report_result_count": len(report.get("results", [])),
        },
        "hard_red_line_confirmation": {
            "delete_file": False,
            "remove_directory": False,
            "move_history_package": False,
            "overwrite_history_package": False,
            "external_call": False,
            "send_notification": False,
            "connect_n8n": False,
            "reload_service": False,
        },
    }
    write_json(VERIFY_JSON, verification)
    print(json.dumps({"pass": verification["pass"], "error_count": verification["error_count"], "target_data_dir": str(DATA_DIR), "log": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if verification["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
