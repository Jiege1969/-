# -*- coding: utf-8 -*-
"""
生成行业价格连续观测入账前检查清单。

作用：明确5点、20点、同口径、来源URL、核验时间等入账前条件；
防止少量价格点被写成趋势确认。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
RECEIPT_PATH = DATA_DIR / "行业价格观测人工填报回执模板_最新.json"
VALIDATION_PATH = DATA_DIR / "行业价格观测人工填报回执模板验收_最新.json"
JSON_OUT = DATA_DIR / "行业价格连续观测入账前检查清单_最新.json"
MD_OUT = DATA_DIR / "行业价格连续观测入账前检查清单_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def stock_checklist(receipt: dict[str, Any]) -> dict[str, Any]:
    current_count = int(receipt.get("current_observation_count") or 0)
    target_count = int(receipt.get("target_min_observation_count") or 5)
    return {
        "stock": receipt.get("stock", {}),
        "product_code": receipt.get("product_code"),
        "product_name": receipt.get("product_name"),
        "indicator_type": receipt.get("indicator_type"),
        "current_observation_count": current_count,
        "target_min_observation_count": target_count,
        "entry_gates": {
            "public_or_authorized_source": False,
            "observation_date_complete": False,
            "value_or_direction_complete": False,
            "unit_or_caliber_complete": False,
            "source_name_complete": False,
            "source_url_complete": False,
            "checked_at_complete": False,
            "same_caliber_continuity": False,
            "minimum_5_points_for_trend": current_count >= 5,
            "minimum_20_points_for_strong_trend": current_count >= 20,
            "human_review_passed": False,
        },
        "entry_decision": {
            "can_enter_observation_ledger": False,
            "can_enter_trend_evidence": False,
            "can_enter_score": False,
            "blocking_reason": "行业价格/景气观测点不足或字段未复核，不能写趋势确认，也不能进入L3加分。",
        },
        "front_wording": {
            "when_less_than_5": "行业价格/景气观测点不足，不能写趋势确认。",
            "when_5_to_19": "已有连续观测基础，可写弱趋势参考，但不能写强趋势。",
            "when_20_plus": "连续观测较充分，可结合财报和公司暴露度写趋势影响，但仍需后台保留来源链。",
        },
    }


def build_asset() -> dict[str, Any]:
    receipt = load_json(RECEIPT_PATH)
    validation = load_json(VALIDATION_PATH)
    checklists = [stock_checklist(item) for item in receipt.get("receipts", [])]
    return {
        "name": "行业价格连续观测入账前检查清单",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1行业价格入账前检查清单",
        "status": "shadow_checklist",
        "source_assets": {
            "receipt_template": str(RECEIPT_PATH),
            "receipt_template_exists": RECEIPT_PATH.exists(),
            "receipt_validation": str(VALIDATION_PATH),
            "receipt_validation_passed": validation.get("passed") is True,
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "not_real_data_fetch": True,
        "checklists": checklists,
        "global_entry_rules": [
            "每条观测必须包含日期、数值或方向、单位或口径、来源名称、来源URL、核验时间。",
            "不足5个连续、同口径、可复核观测点，不得写趋势确认。",
            "5到19个连续观测点，只能写弱趋势参考。",
            "20个及以上连续观测点，才允许考虑强趋势表述，但仍需结合财报和公司业务暴露度。",
            "媒体摘要只能作为线索，不能替代原始价格来源。",
            "未通过人工复核前，can_enter_score必须为false。",
        ],
        "summary": {
            "stock_count": len(checklists),
            "required_observation_points": validation.get("metrics", {}).get("required_observation_points", 0),
            "existing_observation_points": validation.get("metrics", {}).get("existing_observation_points", 0),
            "trend_ready_count": validation.get("metrics", {}).get("trend_ready_count", 0),
            "score_allowed_count": validation.get("metrics", {}).get("score_allowed_count", 0),
            "ledger_entry_allowed_count": 0,
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
        "# 行业价格连续观测入账前检查清单",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：影子检查清单，不抓取真实数据，不写正式价格账本。",
        "",
        "## 样本",
        "",
    ]
    for item in asset["checklists"]:
        stock = item["stock"]
        lines.append(
            f"- {stock.get('name')}（{stock.get('code')}）/{item.get('product_name')}："
            f"{item['current_observation_count']}/{item['target_min_observation_count']}，"
            f"trend={item['entry_decision']['can_enter_trend_evidence']}"
        )
    lines.extend(["", "## 入账规则", ""])
    lines.extend([f"- {rule}" for rule in asset["global_entry_rules"]])
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
