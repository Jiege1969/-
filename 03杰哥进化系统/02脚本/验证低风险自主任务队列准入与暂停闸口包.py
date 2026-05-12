# -*- coding: utf-8 -*-
"""验证低风险自主任务队列准入与暂停闸口包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "93低风险自主任务队列准入与暂停闸口包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险自主任务队列准入与暂停闸口包验收"

RULES_JSON = DATA_DIR / "低风险任务准入规则_最新.json"
RULES_MD = DATA_DIR / "低风险任务准入规则_最新.md"
QUEUE_JSON = DATA_DIR / "自主任务队列候选_最新.json"
QUEUE_MD = DATA_DIR / "自主任务队列候选_最新.md"
PAUSE_JSON = DATA_DIR / "暂停闸口_最新.json"
PAUSE_MD = DATA_DIR / "暂停闸口_最新.md"
REPORT_JSON = DATA_DIR / "只读准入检查报告_最新.json"
REPORT_MD = DATA_DIR / "只读准入检查报告_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险自主任务队列准入与暂停闸口包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险自主任务队列准入与暂停闸口包_最新.md"

VERIFY_JSON = LOG_DIR / "low-risk-autonomous-task-queue-gate-verify-最新.json"


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


def main() -> int:
    generated_at = now()
    errors: list[str] = []
    required_files = [
        RULES_JSON,
        RULES_MD,
        QUEUE_JSON,
        QUEUE_MD,
        PAUSE_JSON,
        PAUSE_MD,
        REPORT_JSON,
        REPORT_MD,
        PACKAGE_JSON,
        PACKAGE_MD,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件：{path}")

    rules = read_json(RULES_JSON) if RULES_JSON.exists() else {}
    queue = read_json(QUEUE_JSON) if QUEUE_JSON.exists() else {"candidates": []}
    pause_gate = read_json(PAUSE_JSON) if PAUSE_JSON.exists() else {}
    report = read_json(REPORT_JSON) if REPORT_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}

    allowed_names = {item.get("name") for item in rules.get("allowed_categories", [])}
    required_allowed = {"只读巡检", "产物完整性检查", "回归验收", "证据归档", "状态包刷新"}
    missing_allowed = sorted(required_allowed - allowed_names)
    if missing_allowed:
        errors.append(f"准入规则缺少允许类别：{missing_allowed}")

    excluded = set(rules.get("excluded_actions", []))
    required_excluded = {"真实发企微", "n8n触发", "券商交易", "税局登录", "财税软件", "正式规则生效", "视频真实发布"}
    missing_excluded = sorted(required_excluded - excluded)
    if missing_excluded:
        errors.append(f"准入规则缺少明确排除项：{missing_excluded}")

    for key in ["auto_execute"]:
        require_false(errors, rules, key, "rules")
    for key, value in rules.get("hard_red_lines", {}).items():
        if value is not False:
            errors.append(f"hard_red_lines.{key} 必须为 false")

    candidates = queue.get("candidates", [])
    if len(candidates) < 8:
        errors.append("自主任务队列候选不足 8 条")
    for item in candidates:
        item_id = item.get("id", "<missing>")
        if item.get("enabled") is not False:
            errors.append(f"{item_id}.enabled 必须为 false")
        if item.get("dry_run_only") is not True:
            errors.append(f"{item_id}.dry_run_only 必须为 true")
        if item.get("requires_supervisor_confirmation") is not False:
            errors.append(f"{item_id}.requires_supervisor_confirmation 必须为 false")
        for key in ["auto_execute", "external_call", "write_formal_rule", "reload_service", "real_send"]:
            require_false(errors, item, key, item_id)
        if item.get("category") not in required_allowed:
            errors.append(f"{item_id}.category 不在允许的只读类别内")
        if "readonly" not in str(item.get("scope", "")):
            errors.append(f"{item_id}.scope 必须限定 readonly")

    trigger_names = {item.get("name"): item.get("pause_required") for item in pause_gate.get("triggers", [])}
    for name in ["出现失败", "红线词", "需重载", "正式规则影响", "外部接口需求"]:
        if trigger_names.get(name) is not True:
            errors.append(f"暂停闸口 {name} 必须 pause_required=true")
    for key in ["on_failure", "on_red_line_word", "on_requires_reload", "on_formal_rule_impact", "on_external_interface_required"]:
        if pause_gate.get("pause_decision", {}).get(key) is not True:
            errors.append(f"pause_decision.{key} 必须为 true")

    if report.get("pass") is not True:
        errors.append("只读准入检查报告必须 pass=true")
    if report.get("error_count") != 0:
        errors.append("只读准入检查报告 error_count 必须为 0")
    safety = report.get("safety_confirmation", {})
    for key in ["auto_execute", "external_call", "write_formal_rule", "reload_service", "real_send"]:
        require_false(errors, safety, key, "safety_confirmation")

    for key in ["auto_execute", "external_call", "write_formal_rule", "reload_service", "real_send"]:
        require_false(errors, package, key, "package")

    verification = {
        "name": "低风险自主任务队列准入与暂停闸口包验收",
        "generated_at": generated_at,
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "metrics": {
            "candidate_count": len(candidates),
            "allowed_category_count": len(allowed_names),
            "excluded_action_count": len(excluded),
            "pause_trigger_count": len(pause_gate.get("triggers", [])),
            "required_file_count": len(required_files),
            "existing_file_count": sum(1 for path in required_files if path.exists()),
        },
        "fixed_log_path": str(VERIFY_JSON),
        "hard_red_line_confirmation": {
            "real_wecom_send": False,
            "trigger_n8n": False,
            "broker_connection": False,
            "trade_order": False,
            "tax_bureau_login": False,
            "finance_tax_software_connection": False,
            "write_formal_rule": False,
            "reload_service": False,
            "real_video_publish": False,
        },
    }
    write_json(VERIFY_JSON, verification)
    print(json.dumps({"pass": verification["pass"], "error_count": verification["error_count"], "log": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if verification["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
