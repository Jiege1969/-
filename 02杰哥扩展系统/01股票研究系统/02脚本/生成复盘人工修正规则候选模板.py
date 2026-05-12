# -*- coding: utf-8 -*-
"""
生成复盘人工修正规则候选模板。

作用：把用户或人工复核发现的问题沉淀为“经验候选”，但不自动修改正式规则、
不自动调权、不写正式配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
REVIEW_VERIFY_PATH = DATA_DIR / "复盘闭环验收_最新.json"
JSON_OUT = DATA_DIR / "复盘人工修正规则候选模板_最新.json"
MD_OUT = DATA_DIR / "复盘人工修正规则候选模板_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def candidate_template(candidate_id: str, title: str, issue_type: str, example: str) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "title": title,
        "issue_type": issue_type,
        "source_example": example,
        "related_stock": None,
        "related_report_id": None,
        "original_output_problem": None,
        "human_correction": None,
        "evidence_before": [],
        "evidence_after": [],
        "affected_contract_fields": [],
        "proposed_rule_candidate": None,
        "applicable_scope": "stock_research_shadow_or_review_candidate",
        "review_status": "pending_review",
        "case_count": 1,
        "promotion_gate": {
            "can_promote_to_experience": False,
            "can_update_formal_rule": False,
            "minimum_cases": 3,
            "requires_multi_stock_validation": True,
            "requires_human_review": True,
            "requires_total_manager_if_formal_config": True,
            "blocking_reason": "人工修正只能先进入复盘/经验候选；未完成多案例验证和人工复核前，不得修改正式规则或权重。",
        },
        "forbidden_actions": [
            "自动改正式评分权重",
            "自动改正式配置",
            "自动触发企业微信外发",
            "自动触发n8n",
            "生成买卖/下单/仓位调整/交易建议",
        ],
    }


def build_asset() -> dict[str, Any]:
    review = load_json(REVIEW_VERIFY_PATH)
    candidates = [
        candidate_template(
            "REVIEW-CAND-001",
            "前台回答过度技术化",
            "front_output_too_technical",
            "用户认为后台分析过程不应原样堆给前台，前台应结论先行、原因少量且明确。",
        ),
        candidate_template(
            "REVIEW-CAND-002",
            "证据缺口未被系统主动暴露",
            "missing_evidence_not_surfaced",
            "财报、资金、行业价格等缺口应由系统主动标注，而不是等用户发现。",
        ),
        candidate_template(
            "REVIEW-CAND-003",
            "政策或市场风格凭感觉入分",
            "unstructured_evidence_scoring",
            "政策事件和市场风格必须读取结构化证据及复核字段，不能由模型凭空补分。",
        ),
        candidate_template(
            "REVIEW-CAND-004",
            "完成小闭环后等待用户确认",
            "construction_pause_after_closure",
            "W1/W2低风险施工完成后应自动进入下一小闭环，红线事项只登记阻断。",
        ),
    ]
    return {
        "name": "复盘人工修正规则候选模板",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1复盘经验候选模板",
        "status": "blank_candidate_template",
        "source_assets": {
            "review_loop_acceptance": str(REVIEW_VERIFY_PATH),
            "review_loop_acceptance_exists": REVIEW_VERIFY_PATH.exists(),
            "auto_weight_adjustment_status": review.get("auto_weight_adjustment_status"),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "not_weight_change": True,
        "not_formal_rule_write": True,
        "candidates": candidates,
        "intake_rules": [
            "人工修正先进入复盘/经验候选，不直接改正式规则。",
            "同类问题至少跨3个案例验证后，才允许提出规则升级建议。",
            "涉及正式配置、正式脚本、企业微信入口或评分权重时，必须交回总管判断。",
            "用户指出的问题必须转成可复核字段：原输出问题、人工修正、证据前后、适用范围、推广闸口。",
            "复盘候选不得生成买卖、下单、仓位或交易建议。",
        ],
        "summary": {
            "candidate_count": len(candidates),
            "formal_rule_update_allowed_count": 0,
            "weight_change_allowed_count": 0,
            "pending_review_count": len(candidates),
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_adapter_write": True,
            "not_score_write": True,
            "not_formal_config": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
            "not_auto_weight_change": True,
        },
    }


def write_markdown(asset: dict[str, Any]) -> None:
    lines = [
        "# 复盘人工修正规则候选模板",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：只进入复盘/经验候选，不自动改正式规则，不自动调权。",
        "",
        "## 候选清单",
        "",
    ]
    for item in asset["candidates"]:
        lines.append(f"- {item['candidate_id']}｜{item['title']}｜{item['issue_type']}｜formal_update={item['promotion_gate']['can_update_formal_rule']}")
    lines.extend(["", "## 进入规则", ""])
    lines.extend([f"- {rule}" for rule in asset["intake_rules"]])
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    asset = build_asset()
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({"status": "ok", "json": str(JSON_OUT), "md": str(MD_OUT), "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
