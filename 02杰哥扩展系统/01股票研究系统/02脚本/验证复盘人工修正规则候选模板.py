# -*- coding: utf-8 -*-
"""
验证复盘人工修正规则候选模板。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "复盘人工修正规则候选模板_最新.json"
RESULT_JSON = DATA_DIR / "复盘人工修正规则候选模板验收_最新.json"
RESULT_MD = DATA_DIR / "复盘人工修正规则候选模板验收_最新.md"


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1复盘经验候选模板":
        errors.append("资产身份必须是 W1复盘经验候选模板")
    if asset.get("status") != "blank_candidate_template":
        errors.append("状态必须是 blank_candidate_template")

    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write", "not_weight_change", "not_formal_rule_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    candidates = asset.get("candidates", [])
    if len(candidates) < 4:
        errors.append("候选模板至少应覆盖4类已暴露问题")
    required_issue_types = {
        "front_output_too_technical",
        "missing_evidence_not_surfaced",
        "unstructured_evidence_scoring",
        "construction_pause_after_closure",
    }
    issue_types = {item.get("issue_type") for item in candidates}
    if not required_issue_types.issubset(issue_types):
        errors.append(f"候选问题类型不完整：{sorted(issue_types)}")

    for item in candidates:
        gate = item.get("promotion_gate", {})
        if item.get("review_status") != "pending_review":
            errors.append(f"{item.get('candidate_id')} review_status必须pending_review")
        if gate.get("can_update_formal_rule") is not False:
            errors.append(f"{item.get('candidate_id')} 不得允许直接修改正式规则")
        if gate.get("can_promote_to_experience") is not False:
            errors.append(f"{item.get('candidate_id')} 初始不得直接推广为经验")
        if gate.get("minimum_cases", 0) < 3:
            errors.append(f"{item.get('candidate_id')} minimum_cases必须>=3")
        if gate.get("requires_human_review") is not True:
            errors.append(f"{item.get('candidate_id')} 必须要求人工复核")
        if gate.get("requires_total_manager_if_formal_config") is not True:
            errors.append(f"{item.get('candidate_id')} 涉及正式配置必须总管判断")
        forbidden = "\n".join(item.get("forbidden_actions", []))
        for phrase in ["自动改正式评分权重", "自动改正式配置", "自动触发企业微信外发", "生成买卖"]:
            if phrase not in forbidden:
                errors.append(f"{item.get('candidate_id')} 禁止动作缺少：{phrase}")

    rules_text = "\n".join(asset.get("intake_rules", []))
    for phrase in ["不直接改正式规则", "至少跨3个案例", "必须交回总管判断", "可复核字段", "不得生成买卖"]:
        if phrase not in rules_text:
            errors.append(f"进入规则缺少：{phrase}")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_adapter_write", "not_score_write", "not_formal_config", "not_entrypoint", "not_broker_interface", "not_auto_trade", "not_auto_weight_change"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "复盘人工修正规则候选模板验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": asset.get("summary", {}),
        "auto_continue_policy": "通过后继续进入下一低风险小闭环；不等待用户确认。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 复盘人工修正规则候选模板验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 候选数量：{result['metrics'].get('candidate_count', 0)}",
        f"- 正式规则可更新数量：{result['metrics'].get('formal_rule_update_allowed_count', 0)}",
        f"- 自动调权允许数量：{result['metrics'].get('weight_change_allowed_count', 0)}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in result["errors"]] or ["- 无"])
    lines.extend(["", "## 警告", ""])
    lines.extend([f"- {item}" for item in result["warnings"]] or ["- 无"])
    lines.extend(["", "## 自动续建口径", "", f"- {result['auto_continue_policy']}", ""])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
