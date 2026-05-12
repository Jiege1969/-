# -*- coding: utf-8 -*-
"""生成市场风格适配到结论强度限制样例。

仅生成股票线W1影子样例，不写正式市场风格日表、不改正式评分配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "市场风格适配到结论强度限制样例_最新.json"
MD_OUT = DATA_DIR / "市场风格适配到结论强度限制样例_最新.md"


STYLE_GATES = [
    {
        "style_state": "risk_appetite_low",
        "conclusion_cap": "可纳入观察",
        "front_phrase": "市场风险偏好偏低，单股即使有题材也要降低结论强度。",
        "confidence_effect": "high_blocked_unless_core_evidence_strong",
    },
    {
        "style_state": "sector_hot_but_market_weak",
        "conclusion_cap": "可纳入观察",
        "front_phrase": "板块有热度但市场整体弱，结论以观察和复核为主。",
        "confidence_effect": "medium_default",
    },
    {
        "style_state": "sector_hot_and_market_active",
        "conclusion_cap": "按L3总分阈值",
        "front_phrase": "板块热度和市场活跃度配合，可以允许结论强度跟随结构化总分上调。",
        "confidence_effect": "contract_based",
    },
    {
        "style_state": "style_missing",
        "conclusion_cap": "可纳入观察",
        "front_phrase": "市场风格数据缺失，不能把个股信号解释成市场共振。",
        "confidence_effect": "high_blocked",
    },
]


SAMPLES = [
    {
        "stock": {"name": "云南锗业", "code": "002428"},
        "stock_type": "资源股",
        "style_state": "sector_hot_and_market_active",
        "front_strength_rule": "若资源板块热度和成交活跃度同步较强，可允许结论随总分上调；否则维持观察。",
        "backend_required": ["risk_appetite.score", "sector_heat.top_sectors", "liquidity.total_amount_rank_percentile"],
    },
    {
        "stock": {"name": "天齐锂业", "code": "002466"},
        "stock_type": "资源/新能源",
        "style_state": "sector_hot_but_market_weak",
        "front_strength_rule": "锂电板块有热度但市场偏弱时，只能强调观察和价格复核。",
        "backend_required": ["sector_heat.hot_theme", "risk_appetite.score", "industry_price_series"],
    },
    {
        "stock": {"name": "华虹公司", "code": "688347"},
        "stock_type": "科技/半导体",
        "style_state": "style_missing",
        "front_strength_rule": "未取得半导体板块热度和市场风格前，不能表述为科技风格共振。",
        "backend_required": ["sector_heat.top_sectors", "size_style.dominant", "liquidity"],
    },
    {
        "stock": {"name": "浙商中拓", "code": "000906"},
        "stock_type": "供应链/周期",
        "style_state": "risk_appetite_low",
        "front_strength_rule": "风险偏好低时，供应链周期股不应给强结论，优先复核现金流和商品周期。",
        "backend_required": ["risk_appetite.score", "commodity_cycle_proxy", "capital_flow"],
    },
    {
        "stock": {"name": "正丹股份", "code": "300641"},
        "stock_type": "化工/小盘弹性",
        "style_state": "sector_hot_and_market_active",
        "front_strength_rule": "化工品价格和小盘风格同时配合时，才允许提高结论强度。",
        "backend_required": ["sector_heat.hot_theme", "size_style.dominant", "liquidity.total_amount_rank_percentile"],
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "市场风格适配到结论强度限制样例",
        "version": "v1.0",
        "generated_at": generated_at,
        "asset_identity": "W1市场风格适配到结论强度限制样例",
        "status": "shadow_style_gate_sample",
        "not_formal_config": True,
        "not_formal_market_style_table": True,
        "not_score_write": True,
        "style_gates": STYLE_GATES,
        "samples": SAMPLES,
        "global_rules": [
            "市场风格只能调节结论强度，不能替代个股证据。",
            "市场风格缺失时，confidence不得为high。",
            "市场风险偏好偏低时，前台结论必须保留观察或复核口径。",
        ],
        "summary": {
            "style_gate_count": len(STYLE_GATES),
            "sample_count": len(SAMPLES),
            "formal_market_style_write_allowed": False,
            "formal_score_update_allowed": False,
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
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 市场风格适配到结论强度限制样例",
        "",
        f"- 生成时间：{generated_at}",
        "- 资产身份：W1市场风格适配到结论强度限制样例",
        "- 状态：shadow_style_gate_sample",
        "- 边界：不写正式市场风格日表，不改正式评分配置。",
        "",
        "## 样本",
        "",
    ]
    for item in SAMPLES:
        lines.append(f"- {item['stock']['name']}（{item['stock']['code']}）：{item['front_strength_rule']}")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
