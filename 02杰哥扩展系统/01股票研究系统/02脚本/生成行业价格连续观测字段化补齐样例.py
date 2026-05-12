# -*- coding: utf-8 -*-
"""生成行业价格连续观测字段化补齐样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "行业价格连续观测字段化补齐样例_最新.json"
MD_OUT = DATA_DIR / "行业价格连续观测字段化补齐样例_最新.md"


FIELD_SCHEMA = [
    {"field": "tracked_product", "label": "跟踪品种", "required": True},
    {"field": "price_source_status", "label": "价格来源状态", "required": True},
    {"field": "observation_window_days", "label": "连续观察窗口", "required": True},
    {"field": "latest_price", "label": "最新价格", "required": False},
    {"field": "price_change_30d", "label": "30日变化", "required": False},
    {"field": "price_trend", "label": "价格趋势", "required": True},
    {"field": "stock_exposure", "label": "股票暴露度", "required": True},
    {"field": "frontend_effect", "label": "前台影响", "required": True},
    {"field": "missing_reason", "label": "缺口原因", "required": True},
]


SAMPLES = [
    {
        "stock_name": "云南锗业",
        "stock_code": "002428",
        "industry_price_fields": {
            "tracked_product": "锗",
            "price_source_status": "missing",
            "observation_window_days": 60,
            "latest_price": None,
            "price_change_30d": None,
            "price_trend": "unknown",
            "stock_exposure": 0.95,
            "frontend_effect": "锗价连续数据缺失时，政策和资源属性只能支撑观察，不能支撑强结论。",
            "missing_reason": "尚未接入可复核的锗价连续观测来源。",
        },
    },
    {
        "stock_name": "正丹股份",
        "stock_code": "300641",
        "industry_price_fields": {
            "tracked_product": "TMA/偏苯三酸酐",
            "price_source_status": "missing",
            "observation_window_days": 60,
            "latest_price": None,
            "price_change_30d": None,
            "price_trend": "unknown",
            "stock_exposure": 0.9,
            "frontend_effect": "核心产品价格未连续验证前，盈利弹性只能作为线索，不进入强结论。",
            "missing_reason": "尚未接入TMA连续价格和供需复核字段。",
        },
    },
    {
        "stock_name": "浙商中拓",
        "stock_code": "000906",
        "industry_price_fields": {
            "tracked_product": "大宗商品综合景气",
            "price_source_status": "partial",
            "observation_window_days": 60,
            "latest_price": None,
            "price_change_30d": None,
            "price_trend": "mixed",
            "stock_exposure": 0.65,
            "frontend_effect": "大宗商品景气未拆到具体品类前，只能作为经营环境备注，不直接提高结论。",
            "missing_reason": "需进一步拆分贸易品类、毛利敏感度和周转指标。",
        },
    },
    {
        "stock_name": "上纬新材",
        "stock_code": "688585",
        "industry_price_fields": {
            "tracked_product": "树脂/复合材料相关原料",
            "price_source_status": "missing",
            "observation_window_days": 60,
            "latest_price": None,
            "price_change_30d": None,
            "price_trend": "unknown",
            "stock_exposure": 0.55,
            "frontend_effect": "行业价格和需求证据缺失时，前台应保持谨慎或暂不建议关注。",
            "missing_reason": "未形成关键原料、产品价格与需求的连续观测字段。",
        },
    },
    {
        "stock_name": "三花智控",
        "stock_code": "002050",
        "industry_price_fields": {
            "tracked_product": "制冷/汽零产业链景气",
            "price_source_status": "partial",
            "observation_window_days": 60,
            "latest_price": None,
            "price_change_30d": None,
            "price_trend": "mixed",
            "stock_exposure": 0.7,
            "frontend_effect": "产业链景气为辅助证据，仍需财报、订单和资金字段共同确认。",
            "missing_reason": "产业景气尚未拆为可连续观测的价格/订单字段。",
        },
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "行业价格连续观测字段化补齐样例",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W1行业价格连续观测字段化样例",
        "status": "shadow_field_sample",
        "purpose": "把锗价、TMA/化工品价格、大宗商品景气等行业价格线索拆成连续观测字段和前台影响约束。",
        "not_real_market_report": True,
        "not_external_send": True,
        "not_formal_entry": True,
        "not_trade_advice": True,
        "field_schema": FIELD_SCHEMA,
        "samples": SAMPLES,
        "summary": {
            "field_count": len(FIELD_SCHEMA),
            "sample_count": len(SAMPLES),
            "all_have_tracked_product": all(bool(item["industry_price_fields"]["tracked_product"]) for item in SAMPLES),
            "all_have_frontend_effect": all(bool(item["industry_price_fields"]["frontend_effect"]) for item in SAMPLES),
            "ready_source_count": len([item for item in SAMPLES if item["industry_price_fields"]["price_source_status"] == "ready"]),
            "missing_or_partial_source_count": len([item for item in SAMPLES if item["industry_price_fields"]["price_source_status"] in {"missing", "partial"}]),
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
        "# 行业价格连续观测字段化补齐样例",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：W1行业价格连续观测字段化样例",
        "- 真实外发：否",
        "- 交易建议：否",
        "",
        "## 字段定义",
        "",
        "| 字段 | 名称 | 必填 |",
        "| --- | --- | --- |",
    ]
    for item in FIELD_SCHEMA:
        lines.append(f"| {item['field']} | {item['label']} | {'是' if item['required'] else '否'} |")
    lines.extend(["", "## 样本", ""])
    for sample in SAMPLES:
        fields = sample["industry_price_fields"]
        lines.extend(
            [
                f"### {sample['stock_name']}（{sample['stock_code']}）",
                "",
                f"- 跟踪品种：{fields['tracked_product']}",
                f"- 来源状态：{fields['price_source_status']}",
                f"- 观察窗口：{fields['observation_window_days']}日",
                f"- 价格趋势：{fields['price_trend']}",
                f"- 股票暴露度：{fields['stock_exposure']}",
                f"- 前台影响：{fields['frontend_effect']}",
                f"- 缺口原因：{fields['missing_reason']}",
                "",
            ]
        )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
