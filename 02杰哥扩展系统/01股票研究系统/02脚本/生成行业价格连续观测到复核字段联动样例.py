# -*- coding: utf-8 -*-
"""生成行业价格连续观测到复核字段联动样例。

仅生成股票线W1影子样例，不接行情源、不写正式库、不触发外发。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "行业价格连续观测到复核字段联动样例_最新.json"
MD_OUT = DATA_DIR / "行业价格连续观测到复核字段联动样例_最新.md"


RECORDS = [
    {
        "stock": {"name": "云南锗业", "code": "002428"},
        "price_series": {"commodity": "锗", "frequency": "daily_or_weekly", "source_status": "manual_or_api_pending"},
        "backend_missing_update": ["锗价连续序列", "最近观察日", "价格变化幅度"],
        "front_review_focus": "下一次复核重点看锗价是否连续走强，以及资源板块热度是否同步。",
        "confidence_effect": "未补齐前最高不超过medium。",
    },
    {
        "stock": {"name": "天齐锂业", "code": "002466"},
        "price_series": {"commodity": "碳酸锂/氢氧化锂", "frequency": "daily_or_weekly", "source_status": "manual_or_api_pending"},
        "backend_missing_update": ["锂价连续序列", "库存/供需备注", "最近观察日"],
        "front_review_focus": "下一次复核重点看锂价企稳持续性和行业景气修复。",
        "confidence_effect": "价格未企稳前不提高结论强度。",
    },
    {
        "stock": {"name": "华虹公司", "code": "688347"},
        "price_series": {"commodity": "晶圆代工景气/半导体材料价格", "frequency": "monthly_or_quarterly", "source_status": "proxy_pending"},
        "backend_missing_update": ["行业景气代理指标", "产能利用率线索", "价格或订单趋势"],
        "front_review_focus": "下一次复核重点看半导体景气指标和产能利用率是否改善。",
        "confidence_effect": "行业景气证据缺失时保持观察结论。",
    },
    {
        "stock": {"name": "浙商中拓", "code": "000906"},
        "price_series": {"commodity": "大宗商品综合价格", "frequency": "daily_or_weekly", "source_status": "proxy_pending"},
        "backend_missing_update": ["相关商品价格篮子", "经营现金流联动说明", "最近观察日"],
        "front_review_focus": "下一次复核重点看商品周期和经营现金流是否同步改善。",
        "confidence_effect": "商品周期证据不足时不输出强结论。",
    },
    {
        "stock": {"name": "正丹股份", "code": "300641"},
        "price_series": {"commodity": "TMA等核心化工品", "frequency": "daily_or_weekly", "source_status": "manual_or_api_pending"},
        "backend_missing_update": ["核心产品价格连续序列", "价差变化", "最近观察日"],
        "front_review_focus": "下一次复核重点看核心产品价格和价差是否继续改善。",
        "confidence_effect": "产品价格缺失时只能保留观察结论。",
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "行业价格连续观测到复核字段联动样例",
        "version": "v1.0",
        "generated_at": generated_at,
        "asset_identity": "W1行业价格连续观测到复核字段联动样例",
        "status": "shadow_mapping_sample",
        "not_formal_config": True,
        "not_price_api": True,
        "not_formal_database_write": True,
        "records": RECORDS,
        "mapping_rules": [
            "行业价格只作为结构化证据或缺口进入后台，不直接生成强结论。",
            "前台只展示复核重点、证据缺口和置信度影响。",
            "缺少连续价格序列时，资源、化工、周期类股票不得给high置信度。",
        ],
        "summary": {
            "sample_count": len(RECORDS),
            "all_have_price_series": True,
            "all_have_review_focus": True,
            "all_have_confidence_effect": True,
            "real_price_api_allowed": False,
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
        "# 行业价格连续观测到复核字段联动样例",
        "",
        f"- 生成时间：{generated_at}",
        "- 资产身份：W1行业价格连续观测到复核字段联动样例",
        "- 状态：shadow_mapping_sample",
        "- 边界：不接真实价格API，不写正式库，不外发。",
        "",
        "## 样本",
        "",
    ]
    for item in RECORDS:
        lines.append(
            f"- {item['stock']['name']}（{item['stock']['code']}）：{item['price_series']['commodity']} -> {item['front_review_focus']}"
        )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
