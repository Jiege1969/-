# -*- coding: utf-8 -*-
"""生成财报资金缺口到前台结论约束样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "财报资金缺口到前台结论约束样例_最新.json"
MD_OUT = DATA_DIR / "财报资金缺口到前台结论约束样例_最新.md"


SAMPLES = [
    {
        "stock_name": "云南锗业",
        "stock_code": "002428",
        "raw_positive_signals": ["政策事件候选", "资源品主题", "市场风格可能适配"],
        "missing_evidence": ["financial_report", "valuation_position", "institutional_holding", "capital_flow"],
        "frontend_conclusion_before_constraint": "重点关注",
        "frontend_conclusion_after_constraint": "可纳入观察",
        "confidence_after_constraint": "medium",
        "must_say": "政策和资源属性有支撑，但财报、估值、机构和资金证据未补齐，结论只能保持观察。",
        "forbidden_behavior": "不得因政策主题强就直接输出重点关注。",
    },
    {
        "stock_name": "三花智控",
        "stock_code": "002050",
        "raw_positive_signals": ["产业链位置较清晰", "基本面验证价值较高"],
        "missing_evidence": ["capital_flow", "institutional_holding"],
        "frontend_conclusion_before_constraint": "重点关注",
        "frontend_conclusion_after_constraint": "可纳入观察",
        "confidence_after_constraint": "medium",
        "must_say": "产业位置较清晰，但资金和机构证据缺口仍在，暂不把结论上调到重点关注。",
        "forbidden_behavior": "不得用行业印象替代资金和机构证据。",
    },
    {
        "stock_name": "上纬新材",
        "stock_code": "688585",
        "raw_positive_signals": ["技术面局部企稳"],
        "missing_evidence": ["financial_report", "valuation_position", "industry_price", "capital_flow"],
        "frontend_conclusion_before_constraint": "可纳入观察",
        "frontend_conclusion_after_constraint": "暂不建议关注",
        "confidence_after_constraint": "low",
        "must_say": "当前证据主要停留在局部技术面，财报、估值、行业价格和资金均缺，前台结论应降为暂不建议关注。",
        "forbidden_behavior": "不得把单一技术信号包装成完整分析结论。",
    },
    {
        "stock_name": "浙商中拓",
        "stock_code": "000906",
        "raw_positive_signals": ["新增样本", "供应链/大宗商品属性待验证"],
        "missing_evidence": ["financial_report", "operating_cash_flow", "capital_flow"],
        "frontend_conclusion_before_constraint": "可纳入观察",
        "frontend_conclusion_after_constraint": "可纳入观察",
        "confidence_after_constraint": "low",
        "must_say": "作为新增样本可以观察，但财报、经营现金流和资金证据未补齐，观察结论置信度偏低。",
        "forbidden_behavior": "不得把新增样本纳入等同于证据充分。",
    },
    {
        "stock_name": "正丹股份",
        "stock_code": "300641",
        "raw_positive_signals": ["化工品价格弹性线索", "新增样本"],
        "missing_evidence": ["product_price_series", "financial_report", "capital_flow"],
        "frontend_conclusion_before_constraint": "重点关注",
        "frontend_conclusion_after_constraint": "可纳入观察",
        "confidence_after_constraint": "medium",
        "must_say": "若产品价格和盈利弹性能连续验证才可上修，当前缺产品价格、财报和资金证据，只保留观察。",
        "forbidden_behavior": "不得用价格弹性故事替代连续数据和财报验证。",
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "财报资金缺口到前台结论约束样例",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W1前台结论约束样例",
        "status": "shadow_sample",
        "purpose": "把财报、估值、机构、资金等关键证据缺口转成前台结论强度约束，防止缺证据仍输出强结论。",
        "not_real_market_report": True,
        "not_external_send": True,
        "not_formal_entry": True,
        "not_trade_advice": True,
        "constraint_rules": [
            {
                "rule_id": "FR-CAP-001",
                "condition": "financial_report缺失且valuation_position缺失",
                "effect": "confidence最高medium，结论最高可纳入观察",
            },
            {
                "rule_id": "FR-CAP-002",
                "condition": "capital_flow和institutional_holding同时缺失",
                "effect": "不得输出重点关注，必须说明资金/机构缺口",
            },
            {
                "rule_id": "FR-CAP-003",
                "condition": "只有技术面或主题线索，缺财报/行业/资金证据",
                "effect": "结论应降为暂不建议关注或低置信观察",
            },
            {
                "rule_id": "FR-CAP-004",
                "condition": "新增样本尚未完成财报资金结构化",
                "effect": "允许纳入观察样本池，但必须标注低置信或关键缺口",
            },
        ],
        "samples": SAMPLES,
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
            "not_order": True,
            "not_position_adjustment": True,
        },
        "summary": {
            "sample_count": len(SAMPLES),
            "rules_count": 4,
            "all_have_missing_evidence": True,
            "all_have_constrained_conclusion": True,
            "strong_conclusion_allowed_when_p0_missing": False,
        },
    }
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 财报资金缺口到前台结论约束样例",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：W1前台结论约束样例",
        "- 真实外发：否",
        "- 交易建议：否",
        "",
        "## 约束规则",
        "",
    ]
    for rule in asset["constraint_rules"]:
        lines.append(f"- {rule['rule_id']}：当{rule['condition']}时，{rule['effect']}。")
    lines.extend(["", "## 样本约束", ""])
    for sample in SAMPLES:
        lines.extend(
            [
                f"### {sample['stock_name']}（{sample['stock_code']}）",
                "",
                f"- 原始积极信号：{'；'.join(sample['raw_positive_signals'])}",
                f"- 缺失证据：{'；'.join(sample['missing_evidence'])}",
                f"- 约束前结论：{sample['frontend_conclusion_before_constraint']}",
                f"- 约束后结论：{sample['frontend_conclusion_after_constraint']}",
                f"- 约束后置信度：{sample['confidence_after_constraint']}",
                f"- 前台必须说明：{sample['must_say']}",
                f"- 禁止行为：{sample['forbidden_behavior']}",
                "",
            ]
        )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
