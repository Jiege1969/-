# -*- coding: utf-8 -*-
"""
生成行业价格观测人工填报回执模板。

仅生成 W1 人工填报模板，不抓取真实价格，不写正式库，不进入评分。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
SOURCE_PATH = DATA_DIR / "五样本行业价格连续观测补数队列_最新.json"
JSON_OUT = DATA_DIR / "行业价格观测人工填报回执模板_最新.json"
MD_OUT = DATA_DIR / "行业价格观测人工填报回执模板_最新.md"

FALLBACK_TASKS = [
    {
        "stock": {"name": "云南锗业", "code": "sz002428"},
        "product_code": "germanium_ingot",
        "product_name": "锗锭",
        "indicator_type": "metal_price",
        "current_observation_count": 0,
        "target_min_observation_count": 5,
        "preferred_sources": ["上海有色网SMM锗价格页", "百川盈孚锗价格页", "上市公司公告中的锗产品价格说明"],
        "front_usage": "不足5个连续观测点前，只能写锗价尚未形成可用趋势证据。",
    },
    {
        "stock": {"name": "天齐锂业", "code": "sz002466"},
        "product_code": "battery_grade_lithium_carbonate",
        "product_name": "电池级碳酸锂",
        "indicator_type": "chemical_material_price",
        "current_observation_count": 1,
        "target_min_observation_count": 5,
        "preferred_sources": ["上海有色网SMM新能源材料页", "公开锂盐价格页面", "上市公司公告中的锂盐价格说明"],
        "front_usage": "1-4个观测点只能写单点或弱参考，不得写趋势反转。",
    },
    {
        "stock": {"name": "华虹公司", "code": "sh688347"},
        "product_code": "wafer_foundry_cycle_indicator",
        "product_name": "晶圆代工景气指标",
        "indicator_type": "industry_cycle_indicator",
        "current_observation_count": 0,
        "target_min_observation_count": 5,
        "preferred_sources": ["公司公告中的产能利用率或ASP说明", "半导体行业协会或公开研究摘要", "公开晶圆代工价格或稼动率报道"],
        "front_usage": "未形成连续观测前，只能写行业景气证据不足。",
    },
    {
        "stock": {"name": "浙商中拓", "code": "sz000906"},
        "product_code": "supply_chain_cycle_indicator",
        "product_name": "供应链景气指标",
        "indicator_type": "business_cycle_indicator",
        "current_observation_count": 0,
        "target_min_observation_count": 5,
        "preferred_sources": ["公司公告中的大宗供应链经营数据", "公开大宗商品成交或流通指标", "行业公开景气摘要"],
        "front_usage": "供应链景气未形成连续观测前，不得写景气确认。",
    },
    {
        "stock": {"name": "正丹股份", "code": "sz300641"},
        "product_code": "tma_price",
        "product_name": "TMA价格",
        "indicator_type": "chemical_material_price",
        "current_observation_count": 0,
        "target_min_observation_count": 5,
        "preferred_sources": ["公开化工品价格页面", "公司公告中的TMA价格或价差说明", "行业公开研究摘要"],
        "front_usage": "TMA价格未形成连续观测前，不得写价格趋势确认。",
    },
]


def load_tasks() -> list[dict[str, Any]]:
    if not SOURCE_PATH.exists():
        return FALLBACK_TASKS
    try:
        source = json.loads(SOURCE_PATH.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return FALLBACK_TASKS
    tasks = source.get("tasks")
    return tasks if isinstance(tasks, list) and tasks else FALLBACK_TASKS


def blank_rows(target_count: int) -> list[dict[str, Any]]:
    return [
        {
            "row_no": index,
            "observation_date": None,
            "value_or_direction": None,
            "unit_or_caliber": None,
            "source_name": None,
            "source_url": None,
            "checked_at": None,
            "evidence_status": "missing",
            "review_status": "pending_review",
            "can_enter_trend": False,
            "can_enter_score": False,
            "review_note": None,
        }
        for index in range(1, target_count + 1)
    ]


def build_receipt(task: dict[str, Any]) -> dict[str, Any]:
    target_count = int(task.get("target_min_observation_count") or 5)
    current_count = int(task.get("current_observation_count") or 0)
    missing_count = max(target_count - current_count, 0)
    raw_front_gap = task.get("front_usage") or "行业价格/景气观测点不足，不能写趋势确认。"
    front_gap_wording = raw_front_gap if "不足" in raw_front_gap else f"行业价格/景气观测点不足：{raw_front_gap}"
    return {
        "stock": task.get("stock", {}),
        "product_code": task.get("product_code"),
        "product_name": task.get("product_name"),
        "indicator_type": task.get("indicator_type"),
        "receipt_status": "blank",
        "current_observation_count": current_count,
        "target_min_observation_count": target_count,
        "missing_observation_count": missing_count,
        "preferred_sources": task.get("preferred_sources", []),
        "minimum_fields": [
            "observation_date",
            "value_or_direction",
            "unit_or_caliber",
            "source_name",
            "source_url",
            "checked_at",
        ],
        "observation_rows": blank_rows(target_count),
        "ready_review": {
            "trend_ready": False,
            "score_ready": False,
            "ready_condition": "至少5个连续、同口径、可复核观测点，并经人工复核后，才可进入趋势证据。",
            "blocking_reason": "行业价格/景气观测点不足，不能写趋势确认，也不能进入L3市场或基本面加分。",
            "reviewer": None,
            "reviewed_at": None,
        },
        "front_gap_wording": front_gap_wording,
    }


def build_asset() -> dict[str, Any]:
    receipts = [build_receipt(task) for task in load_tasks()]
    return {
        "name": "行业价格观测人工填报回执模板",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1行业价格人工填报回执模板",
        "status": "blank_template",
        "source_assets": {
            "observation_queue": str(SOURCE_PATH),
            "observation_queue_exists": SOURCE_PATH.exists(),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "not_real_data_fetch": True,
        "not_formal_database_write": True,
        "receipts": receipts,
        "receipt_rules": [
            "人工填报必须保留观测日期、数值或方向、单位或口径、来源名称、来源URL和核验时间。",
            "不足5个连续、同口径、可复核观测点前，trend_ready必须为false。",
            "trend_ready为false时，前台只能写证据缺口，不能写价格趋势确认。",
            "空白回执不能进入L3评分，can_enter_score必须为false。",
            "本模板不抓取真实价格，不写正式价格账本，不触发外发或交易。",
        ],
        "summary": {
            "receipt_count": len(receipts),
            "stock_count": len({item.get("stock", {}).get("code") for item in receipts}),
            "required_observation_points": sum(item.get("target_min_observation_count", 0) for item in receipts),
            "existing_observation_points": sum(item.get("current_observation_count", 0) for item in receipts),
            "trend_ready_count": 0,
            "score_allowed_count": 0,
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
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
            "not_real_data_fetch": True,
        },
    }


def write_markdown(asset: dict[str, Any]) -> None:
    lines = [
        "# 行业价格观测人工填报回执模板",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：W1人工填报模板，不抓取真实价格，不写正式库，不进入评分。",
        "",
        "## 汇总",
        "",
        f"- 回执数量：{asset['summary']['receipt_count']}",
        f"- 股票数量：{asset['summary']['stock_count']}",
        f"- 需补观测点：{asset['summary']['required_observation_points']}",
        f"- 已有观测点：{asset['summary']['existing_observation_points']}",
        f"- 趋势可用数量：{asset['summary']['trend_ready_count']}",
        "",
        "## 填报规则",
        "",
    ]
    lines.extend([f"- {item}" for item in asset["receipt_rules"]])
    lines.extend(["", "## 回执清单", ""])
    for item in asset["receipts"]:
        stock = item.get("stock", {})
        lines.append(
            f"- {stock.get('name')}（{stock.get('code')}）/ {item.get('product_name')}："
            f"{item.get('current_observation_count')}/{item.get('target_min_observation_count')}，"
            f"trend_ready={item['ready_review']['trend_ready']}，缺口={item['front_gap_wording']}"
        )
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
