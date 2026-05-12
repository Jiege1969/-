# -*- coding: utf-8 -*-
"""
验证股票 L3 统一刷新验收执行记录模板。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "股票L3统一刷新验收执行记录模板_最新.json"
RESULT_JSON = DATA_DIR / "股票L3统一刷新验收执行记录模板验收_最新.json"
RESULT_MD = DATA_DIR / "股票L3统一刷新验收执行记录模板验收_最新.md"

REQUIRED_DECISION_FIELDS = {
    "all_required_assets_ready",
    "allow_front_answer_generation",
    "allow_l3_complete_claim",
    "blocked_reasons",
    "missing_summary",
    "next_action",
}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1执行记录模板":
        errors.append("资产身份必须是 W1执行记录模板")
    if asset.get("status") != "blank_template":
        errors.append("状态必须是 blank_template")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write", "not_real_refresh"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    header = asset.get("execution_header", {})
    for flag in ["real_refresh_performed", "external_send_performed", "formal_database_write_performed"]:
        if header.get(flag) is not False:
            errors.append(f"execution_header.{flag} 默认必须为 false")

    records = asset.get("asset_check_records", [])
    if len(records) < 7:
        errors.append("资产检查记录不得少于 7 条")
    for item in records:
        if item.get("check_result") != "pending":
            errors.append(f"{item.get('asset_key')} check_result 默认必须 pending")
        if item.get("actual_exists") is not None:
            errors.append(f"{item.get('asset_key')} actual_exists 默认必须为空")
        if not item.get("missing_action"):
            errors.append(f"{item.get('asset_key')} 缺少 missing_action")

    decision_keys = set(asset.get("decision_section", {}))
    if decision_keys != REQUIRED_DECISION_FIELDS:
        errors.append(f"决策字段不完整：{sorted(decision_keys)}")

    gate = asset.get("front_answer_gate", {})
    for flag in ["object_first_line_required", "conclusion_from_contract_required", "missing_must_be_explicit", "no_trade_wording", "no_formal_recommendation"]:
        if gate.get(flag) is not True:
            errors.append(f"front_answer_gate.{flag} 必须为 true")

    prohibited = "\n".join(asset.get("prohibited_actions", []))
    for phrase in ["真实发送企业微信", "触发 n8n", "写正式库", "买入", "自动交易"]:
        if phrase not in prohibited:
            errors.append(f"禁止动作缺少：{phrase}")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_adapter_write", "not_score_write", "not_entrypoint", "not_broker_interface", "not_auto_trade", "not_real_refresh"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "股票L3统一刷新验收执行记录模板验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "asset_record_count": len(records),
            "decision_field_count": len(decision_keys),
        },
        "next_step": "继续生成统一刷新验收执行记录样例；仍不得真实刷新、外发或写正式库。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 股票L3统一刷新验收执行记录模板验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 资产记录数：{result['metrics']['asset_record_count']}",
        f"- 决策字段数：{result['metrics']['decision_field_count']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in result["errors"]] or ["- 无"])
    lines.extend(["", "## 警告", ""])
    lines.extend([f"- {item}" for item in result["warnings"]] or ["- 无"])
    lines.extend(["", "## 下一步", "", f"- {result['next_step']}", ""])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
