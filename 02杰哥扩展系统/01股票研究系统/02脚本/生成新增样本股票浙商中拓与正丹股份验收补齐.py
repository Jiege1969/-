# -*- coding: utf-8 -*-
"""生成新增样本股票浙商中拓与正丹股份验收补齐样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "新增样本股票浙商中拓与正丹股份验收补齐_最新.json"
MD_OUT = DATA_DIR / "新增样本股票浙商中拓与正丹股份验收补齐_最新.md"


SAMPLES = [
    {
        "stock_name": "浙商中拓",
        "stock_code": "000906",
        "sample_status": "shadow_sample_added",
        "object_identification": {
            "passed": True,
            "canonical_name": "浙商中拓",
            "aliases": ["浙商中拓集团", "中拓"],
            "first_line_required": "浙商中拓（000906）：",
        },
        "industry_tags": ["供应链服务", "大宗商品", "浙江国资"],
        "evidence_gaps": [
            {"priority": "P0", "field": "financial_report", "description": "最新财报核心指标与盈利质量待结构化"},
            {"priority": "P0", "field": "operating_cash_flow", "description": "经营现金流与贸易业务周转质量待复核"},
            {"priority": "P1", "field": "commodity_cycle", "description": "大宗商品景气对收入和毛利的影响待补"},
            {"priority": "P1", "field": "capital_flow", "description": "主力资金和机构持仓变化待补"},
        ],
        "frontend_expression_check": {
            "conclusion_cap": "可纳入观察",
            "confidence_cap": "low",
            "must_include_missing": True,
            "must_not_include_trade_action": True,
        },
    },
    {
        "stock_name": "正丹股份",
        "stock_code": "300641",
        "sample_status": "shadow_sample_added",
        "object_identification": {
            "passed": True,
            "canonical_name": "正丹股份",
            "aliases": ["正丹", "江苏正丹"],
            "first_line_required": "正丹股份（300641）：",
        },
        "industry_tags": ["化工", "TMA", "精细化工"],
        "evidence_gaps": [
            {"priority": "P0", "field": "product_price_series", "description": "核心产品价格连续观测待补"},
            {"priority": "P0", "field": "financial_report", "description": "盈利弹性和持续性待结构化复核"},
            {"priority": "P1", "field": "capacity_supply_demand", "description": "供需格局、产能变化和价格传导待补"},
            {"priority": "P1", "field": "capital_flow", "description": "资金承接和机构变化待补"},
        ],
        "frontend_expression_check": {
            "conclusion_cap": "可纳入观察",
            "confidence_cap": "medium",
            "must_include_missing": True,
            "must_not_include_trade_action": True,
        },
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "新增样本股票浙商中拓与正丹股份验收补齐",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W1新增样本验收矩阵",
        "status": "shadow_sample_acceptance",
        "purpose": "把浙商中拓、正丹股份作为新增股票样本纳入对象识别、行业标签、证据缺口和前台表达验收。",
        "not_real_market_report": True,
        "not_external_send": True,
        "not_formal_entry": True,
        "not_trade_advice": True,
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
            "all_object_identification_passed": all(item["object_identification"]["passed"] for item in SAMPLES),
            "all_have_industry_tags": all(bool(item["industry_tags"]) for item in SAMPLES),
            "all_have_p0_missing": all(any(gap["priority"] == "P0" for gap in item["evidence_gaps"]) for item in SAMPLES),
            "all_frontend_expression_constrained": all(item["frontend_expression_check"]["must_include_missing"] for item in SAMPLES),
        },
    }
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 新增样本股票浙商中拓与正丹股份验收补齐",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：W1新增样本验收矩阵",
        "- 真实外发：否",
        "- 交易建议：否",
        "",
    ]
    for sample in SAMPLES:
        lines.extend(
            [
                f"## {sample['stock_name']}（{sample['stock_code']}）",
                "",
                f"- 对象识别：{'通过' if sample['object_identification']['passed'] else '未通过'}",
                f"- 标准首行：{sample['object_identification']['first_line_required']}",
                f"- 行业标签：{'；'.join(sample['industry_tags'])}",
                f"- 前台结论上限：{sample['frontend_expression_check']['conclusion_cap']}",
                f"- 置信度上限：{sample['frontend_expression_check']['confidence_cap']}",
                "",
                "### 证据缺口",
                "",
            ]
        )
        for gap in sample["evidence_gaps"]:
            lines.append(f"- {gap['priority']} | {gap['field']} | {gap['description']}")
        lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
