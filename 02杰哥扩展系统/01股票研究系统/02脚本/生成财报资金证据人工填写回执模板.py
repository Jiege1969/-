# -*- coding: utf-8 -*-
"""
生成财报资金证据人工填写回执模板。

仅生成 W1 人工回执模板，不抓取真实数据、不写正式库、不进入评分。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
SOURCE_PATH = DATA_DIR / "五样本财报资金证据采集模板草案_最新.json"
JSON_OUT = DATA_DIR / "财报资金证据人工填写回执模板_最新.json"
MD_OUT = DATA_DIR / "财报资金证据人工填写回执模板_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def group_receipt_template(stock: dict[str, Any], group: dict[str, Any]) -> dict[str, Any]:
    return {
        "stock": stock,
        "field_group": group.get("field_group"),
        "display_name": group.get("display_name"),
        "priority": group.get("priority"),
        "receipt_status": "blank",
        "filled_by": None,
        "filled_at": None,
        "source_package": {
            "source_name": None,
            "source_url": None,
            "as_of_date": None,
            "source_type": "manual_public_source_or_future_readonly_collection",
        },
        "field_receipts": {
            field_name: {
                "value": None,
                "unit": None,
                "evidence_status": "missing",
                "review_status": "pending_review",
                "review_note": None,
                "can_enter_score": False,
            }
            for field_name in group.get("fields", {})
        },
        "ready_review": {
            "ready": False,
            "ready_condition": group.get("minimum_ready_condition"),
            "reviewer": None,
            "reviewed_at": None,
            "blocking_reason": "尚未填写和复核，不能进入 L3 评分。",
        },
        "front_gap_wording": group.get("front_gap_wording"),
    }


def build_asset() -> dict[str, Any]:
    source = load_json(SOURCE_PATH)
    receipts = []
    for stock_template in source.get("templates", []):
        stock = stock_template.get("stock", {})
        for group in stock_template.get("evidence_groups", []):
            receipts.append(group_receipt_template(stock, group))

    return {
        "name": "财报资金证据人工填写回执模板",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1人工填写回执模板",
        "status": "blank_template",
        "source_assets": {
            "collection_template": str(SOURCE_PATH),
            "collection_template_exists": bool(source),
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
            "人工填写必须保留来源名称、来源链接、口径日期。",
            "字段从 missing 到 candidate 后，必须经过复核才能变为 evidence_ready。",
            "未 evidence_ready 的字段 can_enter_score 必须为 false。",
            "回执模板本身不代表证据已补齐。",
            "不得用回执空白字段生成强结论。",
        ],
        "summary": {
            "receipt_count": len(receipts),
            "stock_count": len({item.get("stock", {}).get("code") for item in receipts}),
            "ready_count": 0,
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
        "# 财报资金证据人工填写回执模板",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：W1 人工回执模板，不抓取真实数据，不写正式库，不进入评分。",
        "",
        "## 汇总",
        "",
        f"- 回执数量：{asset['summary']['receipt_count']}",
        f"- 股票数量：{asset['summary']['stock_count']}",
        f"- ready 数：{asset['summary']['ready_count']}",
        f"- 允许入评分数：{asset['summary']['score_allowed_count']}",
        "",
        "## 填写规则",
        "",
    ]
    lines.extend([f"- {item}" for item in asset["receipt_rules"]])
    lines.extend(["", "## 回执清单", ""])
    for item in asset["receipts"]:
        stock = item["stock"]
        lines.append(f"- {stock.get('name')}（{stock.get('code')}） / {item['display_name']}：{len(item['field_receipts'])} 个字段，ready={item['ready_review']['ready']}")
    lines.extend(["", "## 下一步自动推进", ""])
    lines.append("- 可继续生成行业价格观测人工填报回执模板，关闭行业价格连续观测的同类旧债。")
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
