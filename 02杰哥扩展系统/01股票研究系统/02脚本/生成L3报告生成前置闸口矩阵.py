# -*- coding: utf-8 -*-
"""
生成L3报告生成前置闸口矩阵。

作用：把各类证据的ready状态映射到报告允许/禁止口径，防止缺证据仍输出
强结论、用空值冒充判断、或把影子资产说成正式L3。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "L3报告生成前置闸口矩阵_最新.json"
MD_OUT = DATA_DIR / "L3报告生成前置闸口矩阵_最新.md"

SOURCE_CHECKS = {
    "financial_capital": DATA_DIR / "财报资金证据人工填写回执模板验收_最新.json",
    "industry_price": DATA_DIR / "行业价格观测人工填报回执模板验收_最新.json",
    "policy_event_exposure": DATA_DIR / "政策事件单股暴露度人工复核回执模板验收_最新.json",
    "market_style_fit": DATA_DIR / "市场风格单股适配人工复核回执模板验收_最新.json",
    "front_short_answer": DATA_DIR / "前台结论型短答统一验收记录验收_最新.json",
    "review_candidate": DATA_DIR / "复盘人工修正规则候选模板验收_最新.json",
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def source_status(key: str, path: Path) -> dict[str, Any]:
    data = load_json(path)
    return {
        "key": key,
        "path": str(path),
        "exists": path.exists(),
        "passed": data.get("passed") is True,
        "metrics": data.get("metrics", {}),
    }


def build_asset() -> dict[str, Any]:
    sources = [source_status(key, path) for key, path in SOURCE_CHECKS.items()]
    gates = [
        {
            "gate_id": "GATE-L3-001",
            "name": "对象明确闸口",
            "required_ready_fields": ["stock_name", "stock_code"],
            "if_not_ready": "禁止生成报告；必须先明确股票名称和代码。",
            "front_allowed": False,
            "backend_allowed": False,
        },
        {
            "gate_id": "GATE-L3-002",
            "name": "前台短答闸口",
            "required_source": "front_short_answer",
            "if_ready": "允许生成影子前台结论型短答。",
            "if_not_ready": "只能生成后台草案，不能输出企业微信短答。",
            "front_allowed_when_ready": True,
            "real_wecom_allowed": False,
        },
        {
            "gate_id": "GATE-L3-003",
            "name": "财报资金证据闸口",
            "required_source": "financial_capital",
            "ready_condition": "财报资金回执字段经人工复核为evidence_ready。",
            "if_not_ready": "基本面/资金项只能写缺口，不得强行给高分或说资金确认。",
            "max_confidence_if_missing": "medium",
        },
        {
            "gate_id": "GATE-L3-004",
            "name": "行业价格趋势闸口",
            "required_source": "industry_price",
            "ready_condition": "至少5个连续、同口径、可复核观测点；20点以上才可增强趋势表述。",
            "if_not_ready": "行业价格/景气只能写观测点不足，不得写趋势确认。",
            "trend_confirmation_allowed": False,
        },
        {
            "gate_id": "GATE-L3-005",
            "name": "政策事件入分闸口",
            "required_source": "policy_event_exposure",
            "ready_condition": "官方来源、方向、强度、股票暴露度、时效衰减、反证风险、重复计分均已复核。",
            "if_not_ready": "政策只能写背景或缺口，不得写政策强驱动或政策加分。",
            "policy_score_allowed": False,
        },
        {
            "gate_id": "GATE-L3-006",
            "name": "市场风格单股适配闸口",
            "required_source": "market_style_fit",
            "ready_condition": "风险偏好、板块热度、大小盘风格、成交活跃度四项适配均已复核。",
            "if_not_ready": "市场风格只能写环境参考，不能写该股强适配。",
            "style_score_allowed": False,
        },
        {
            "gate_id": "GATE-L3-007",
            "name": "强结论闸口",
            "required_ready_fields": ["technical_ready", "financial_ready", "policy_ready", "market_style_ready"],
            "if_not_ready": "不得输出重点关注；最高只能保守观察，并必须解释为什么不是更高分。",
            "strong_conclusion_allowed": False,
        },
        {
            "gate_id": "GATE-L3-008",
            "name": "复盘候选闸口",
            "required_source": "review_candidate",
            "if_ready": "允许把人工修正进入经验候选。",
            "if_not_ready": "不得把人工反馈说成已改正式规则。",
            "formal_rule_update_allowed": False,
            "auto_weight_change_allowed": False,
        },
    ]
    return {
        "name": "L3报告生成前置闸口矩阵",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1报告生成前置闸口矩阵",
        "status": "shadow_gate_matrix",
        "source_checks": sources,
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_score_write": True,
        "not_formal_database_write": True,
        "gates": gates,
        "report_output_contract": {
            "front": "对象明确、结论先行、原因少量、缺口明确、置信度明确。",
            "backend": "保留evidence、missing、confidence、next_review、复盘候选字段。",
            "forbidden_when_missing": [
                "缺财报资金仍写基本面确认",
                "缺价格连续观测仍写趋势确认",
                "缺政策复核仍写政策强驱动",
                "缺单股风格复核仍写市场强适配",
                "缺关键证据仍输出重点关注",
            ],
        },
        "summary": {
            "source_count": len(sources),
            "source_passed_count": len([item for item in sources if item["passed"]]),
            "gate_count": len(gates),
            "formal_entry_allowed": False,
            "real_wecom_allowed": False,
            "auto_weight_change_allowed": False,
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_formal_config": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }


def write_markdown(asset: dict[str, Any]) -> None:
    lines = [
        "# L3报告生成前置闸口矩阵",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：影子闸口矩阵，不改正式入口、不外发、不写评分。",
        "",
        "## 闸口",
        "",
    ]
    for gate in asset["gates"]:
        lines.append(f"- {gate['gate_id']}｜{gate['name']}｜缺失处理：{gate.get('if_not_ready')}")
    lines.extend(["", "## 禁止口径", ""])
    lines.extend([f"- {item}" for item in asset["report_output_contract"]["forbidden_when_missing"]])
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
