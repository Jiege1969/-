# -*- coding: utf-8 -*-
"""生成市场风格日表字段化补齐样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "市场风格日表字段化补齐样例_最新.json"
MD_OUT = DATA_DIR / "市场风格日表字段化补齐样例_最新.md"


FIELD_SCHEMA = [
    {"field": "trade_date", "label": "交易日", "required": True},
    {"field": "risk_appetite", "label": "风险偏好", "required": True},
    {"field": "sector_heat", "label": "板块热度", "required": True},
    {"field": "size_style", "label": "大小盘风格", "required": True},
    {"field": "liquidity", "label": "流动性", "required": True},
    {"field": "resource_style_fit", "label": "资源股适配", "required": True},
    {"field": "chemical_style_fit", "label": "化工股适配", "required": True},
    {"field": "manufacturing_style_fit", "label": "制造股适配", "required": True},
    {"field": "frontend_effect", "label": "前台影响", "required": True},
    {"field": "missing_reason", "label": "缺口原因", "required": True},
]


DAILY_STYLE = {
    "trade_date": "shadow_sample",
    "data_status": "shadow_not_real_market_data",
    "risk_appetite": {"status": "missing", "score": None, "source_status": "missing"},
    "sector_heat": {
        "status": "partial",
        "top_sectors": ["有色金属候选", "化工候选", "先进制造候选"],
        "source_status": "shadow_tags_only",
    },
    "size_style": {"status": "missing", "dominant": "unknown", "source_status": "missing"},
    "liquidity": {"status": "missing", "rank_percentile": None, "source_status": "missing"},
    "style_fit_by_stock_type": {
        "resource": {"fit_score": None, "status": "missing", "frontend_cap": "只可作为观察备注"},
        "chemical": {"fit_score": None, "status": "missing", "frontend_cap": "只可作为观察备注"},
        "manufacturing": {"fit_score": None, "status": "missing", "frontend_cap": "只可作为观察备注"},
    },
    "frontend_effect": "市场风格日表未接入真实日度数据前，只能限制结论，不得作为强加分依据。",
    "missing_reason": "尚未接入真实涨跌家数、板块涨跌、大小盘相对强弱和成交额分位。",
}


SAMPLES = [
    {
        "stock_name": "云南锗业",
        "stock_code": "002428",
        "stock_type": "resource",
        "style_fit_status": "missing",
        "conclusion_effect": "资源股适配数据缺失时，政策与资源主线只能支持观察，不得提升到重点关注。",
    },
    {
        "stock_name": "正丹股份",
        "stock_code": "300641",
        "stock_type": "chemical",
        "style_fit_status": "missing",
        "conclusion_effect": "化工股风格适配缺失时，产品价格弹性仍需价格和资金证据确认。",
    },
    {
        "stock_name": "三花智控",
        "stock_code": "002050",
        "stock_type": "manufacturing",
        "style_fit_status": "missing",
        "conclusion_effect": "制造风格适配缺失时，不得用风格因素强化结论。",
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "市场风格日表字段化补齐样例",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W1市场风格日表字段化样例",
        "status": "shadow_field_sample",
        "purpose": "把风险偏好、板块热度、大小盘风格、流动性和股票类型适配拆成字段，并明确缺口如何限制前台结论。",
        "not_real_market_data": True,
        "not_external_send": True,
        "not_formal_entry": True,
        "not_score_write": True,
        "field_schema": FIELD_SCHEMA,
        "daily_style": DAILY_STYLE,
        "samples": SAMPLES,
        "summary": {
            "field_count": len(FIELD_SCHEMA),
            "sample_count": len(SAMPLES),
            "real_market_data_ready": False,
            "all_samples_have_conclusion_effect": all(bool(item["conclusion_effect"]) for item in SAMPLES),
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
            "not_order": True,
            "not_position_adjustment": True,
        },
    }
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 市场风格日表字段化补齐样例",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：W1市场风格日表字段化样例",
        "- 真实市场数据：否",
        "- 交易建议：否",
        "",
        "## 字段定义",
        "",
        "| 字段 | 名称 | 必填 |",
        "| --- | --- | --- |",
    ]
    for item in FIELD_SCHEMA:
        lines.append(f"| {item['field']} | {item['label']} | {'是' if item['required'] else '否'} |")
    lines.extend(
        [
            "",
            "## 日表样例",
            "",
            f"- 交易日：{DAILY_STYLE['trade_date']}",
            f"- 数据状态：{DAILY_STYLE['data_status']}",
            f"- 前台影响：{DAILY_STYLE['frontend_effect']}",
            f"- 缺口原因：{DAILY_STYLE['missing_reason']}",
            "",
            "## 股票适配样本",
            "",
        ]
    )
    for sample in SAMPLES:
        lines.extend(
            [
                f"### {sample['stock_name']}（{sample['stock_code']}）",
                "",
                f"- 股票类型：{sample['stock_type']}",
                f"- 风格适配状态：{sample['style_fit_status']}",
                f"- 结论影响：{sample['conclusion_effect']}",
                "",
            ]
        )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
