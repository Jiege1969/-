# -*- coding: utf-8 -*-
"""验收置信度上限与缺口联动矩阵。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "置信度上限与缺口联动矩阵_最新.json"
RESULT_JSON = DATA_DIR / "置信度上限与缺口联动矩阵验收结果_最新.json"
RESULT_MD = DATA_DIR / "置信度上限与缺口联动矩阵验收结果_最新.md"
REQUIRED_CONDITIONS = {
    "stock_object_unresolved",
    "latest_financial_report_missing",
    "policy_event_unverified",
    "market_style_missing",
    "industry_price_series_missing",
    "capital_and_institution_missing",
    "two_or_more_critical_missing",
    "all_core_evidence_ready",
}


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1置信度上限与缺口联动影子规则矩阵":
        errors.append("资产身份不正确")
    if asset.get("status") != "shadow_gate_matrix":
        errors.append("状态不是shadow_gate_matrix")
    for flag in ["not_formal_config", "not_formal_scoring_rule", "not_entrypoint"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    rules = asset.get("rules", [])
    conditions = {rule.get("condition") for rule in rules}
    if conditions != REQUIRED_CONDITIONS:
        errors.append(f"条件覆盖不完整：{sorted(conditions)}")
    by_condition = {rule.get("condition"): rule for rule in rules}
    if by_condition.get("stock_object_unresolved", {}).get("conclusion_cap") != "不输出单股判断":
        errors.append("对象不明确时必须阻断单股判断")
    if by_condition.get("two_or_more_critical_missing", {}).get("confidence_cap") != "low":
        errors.append("两个以上关键缺口时置信度上限必须为low")
    for condition in [
        "latest_financial_report_missing",
        "policy_event_unverified",
        "market_style_missing",
        "industry_price_series_missing",
        "capital_and_institution_missing",
    ]:
        if by_condition.get(condition, {}).get("confidence_cap") != "medium":
            errors.append(f"{condition}置信度上限必须为medium")
    constraints = asset.get("global_constraints", {})
    for key in [
        "missing_must_be_explicit",
        "critical_missing_blocks_high_confidence",
        "llm_may_explain_not_fill_score",
        "front_answer_must_be_conclusion_first",
        "backend_must_keep_evidence_chain",
    ]:
        if constraints.get(key) is not True:
            errors.append(f"全局约束{key}必须为true")
    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_formal_config", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界{flag}必须为true")
    result = {
        "name": "置信度上限与缺口联动矩阵验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {
            "rule_count": len(rules),
            "condition_count": len(conditions),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 置信度上限与缺口联动矩阵验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 规则数：{result['metrics']['rule_count']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
