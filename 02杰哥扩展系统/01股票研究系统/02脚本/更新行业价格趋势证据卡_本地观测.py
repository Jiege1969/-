# -*- coding: utf-8 -*-
"""
名称：更新行业价格趋势证据卡_本地观测.py
作用：读取本地行业价格观测账本，按股票核心产品生成行业价格证据卡。
触发方式：python 更新行业价格趋势证据卡_本地观测.py
安全边界：只读本地观测账本和来源登记；只写245L3评分基础资产；不联网抓取；不发送企业微信；不触发n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


STOCK_PRODUCT_MAP = [
    {
        "stock": {"name": "云南锗业", "code": "002428", "display_code": "sz002428", "industry": "稀有金属/半导体材料", "stock_type": "资源股"},
        "product": {"product_name": "锗锭", "product_code": "germanium_ingot", "exposure_weight": 0.95},
        "direction_rule": "锗价持续上行通常对公司收入和利润预期偏正向；锗价回落或无趋势会削弱政策利好兑现。"
    },
    {
        "stock": {"name": "天齐锂业", "code": "002466", "display_code": "sz002466", "industry": "锂资源/锂化工", "stock_type": "锂资源/锂化工"},
        "product": {"product_name": "电池级碳酸锂", "product_code": "battery_grade_lithium_carbonate", "exposure_weight": 0.9},
        "direction_rule": "碳酸锂价格企稳或上行通常增强利润修复预期；价格持续下行会削弱财报修复持续性。"
    },
    {
        "stock": {"name": "正丹股份", "code": "300641", "display_code": "sz300641", "industry": "化工", "stock_type": "化工高波动"},
        "product": {"product_name": "偏苯三酸酐/TMA", "product_code": "trimellitic_anhydride_tma", "exposure_weight": 0.9},
        "direction_rule": "TMA价格和价差上行通常增强业绩弹性预期；价格下行或价差收窄会削弱关注等级。"
    }
]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_price(value: Any) -> float | None:
    try:
        if value in (None, "", "-"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def calc_trend(observations: list[dict[str, Any]], window: int) -> dict[str, Any]:
    rows = sorted(
        [row for row in observations if parse_price(row.get("price_mid")) is not None and row.get("price_date")],
        key=lambda row: str(row.get("price_date")),
    )
    if len(rows) < window:
        return {
            "status": "insufficient",
            "window": window,
            "available_points": len(rows),
            "direction": "unknown",
            "change_pct": None,
        }
    target = rows[-window:]
    first = parse_price(target[0].get("price_mid"))
    last = parse_price(target[-1].get("price_mid"))
    if first in (None, 0) or last is None:
        return {
            "status": "invalid",
            "window": window,
            "available_points": len(rows),
            "direction": "unknown",
            "change_pct": None,
        }
    change_pct = round((last - first) / first, 4)
    if change_pct > 0.02:
        direction = "up"
    elif change_pct < -0.02:
        direction = "down"
    else:
        direction = "flat"
    return {
        "status": "ready",
        "window": window,
        "available_points": len(rows),
        "start_date": target[0].get("price_date"),
        "end_date": target[-1].get("price_date"),
        "start_price": first,
        "end_price": last,
        "direction": direction,
        "change_pct": change_pct,
    }


def front_sentence(product_name: str, level: str, trend5: dict[str, Any]) -> str:
    if level == "trend_ready":
        direction = trend5.get("direction")
        if direction == "up":
            return f"{product_name}近5个观测点趋势向上，对相关股票形成行业价格弱支撑，但仍需结合财报和技术确认。"
        if direction == "down":
            return f"{product_name}近5个观测点趋势向下，行业价格暂不支持提高关注等级。"
        return f"{product_name}近5个观测点基本平稳，行业价格只能作为中性参考。"
    if level == "single_observation":
        return f"{product_name}已有单点价格观测，但还缺连续趋势，只能弱参考。"
    return f"{product_name}来源已登记但价格尚未入账，暂不能作为提高关注等级的依据。"


def build_card(root: Path, mapping: dict[str, Any], observations: list[dict[str, Any]]) -> dict[str, Any]:
    product = mapping["product"]
    stock = mapping["stock"]
    product_code = product["product_code"]
    product_obs = [row for row in observations if row.get("product_code") == product_code]
    product_obs = sorted(product_obs, key=lambda row: str(row.get("price_date") or ""))
    trend5 = calc_trend(product_obs, 5)
    trend20 = calc_trend(product_obs, 20)
    if trend5.get("status") == "ready":
        level = "trend_ready"
        score = 7 if trend5.get("direction") == "up" else 4 if trend5.get("direction") == "flat" else 2
        confidence = "medium"
    elif product_obs:
        level = "single_observation"
        score = 4
        confidence = "medium"
    else:
        level = "source_registered"
        score = 2
        confidence = "low"
    latest = product_obs[-1] if product_obs else {}
    sources = []
    seen_sources = set()
    for row in product_obs:
        key = (row.get("source_name"), row.get("source_url"))
        if key in seen_sources:
            continue
        seen_sources.add(key)
        sources.append({
            "source_name": row.get("source_name") or "本地行业价格观测账本",
            "source_url": row.get("source_url") or "03数据/245L3评分基础资产/industry_price_observations_ledger_v1.0.json",
            "source_type": "公开价格页" if "public" in str(row.get("authorization_status")) else "行业数据平台",
            "coverage": product["product_name"],
            "source_role": row.get("source_role") or "价格观测",
            "checked_at": row.get("checked_at") or datetime.now().date().isoformat(),
        })
    if not sources:
        sources.append({
            "source_name": "行业价格数据源候选清单",
            "source_url": "03数据/245L3评分基础资产/行业价格数据源候选清单_20260507.json",
            "source_type": "行业数据平台",
            "coverage": product["product_name"],
            "source_role": "待人工复核",
            "checked_at": datetime.now().date().isoformat(),
        })
    missing = []
    if not product_obs:
        missing.append(f"{product['product_name']}具体价格、日期、单位尚未入账。")
    if trend5.get("status") != "ready":
        missing.append(f"{product['product_name']}尚未形成5个连续观测点。")
    if trend20.get("status") != "ready":
        missing.append(f"{product['product_name']}尚未形成20个连续观测点。")
    missing.append("价格与公司毛利、现金流和产品暴露度的量化映射尚未完成。")
    card = {
        "名称": f"{stock['name']}行业价格证据卡",
        "版本": "2026-05-08-local-observation-v1",
        "生成日期": datetime.now().date().isoformat(),
        "所属系统": "02杰哥扩展系统/01股票研究系统",
        "资产身份": "正式候选证据卡",
        "状态": level,
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "stock": stock,
        "tracked_products": [
            {
                "product_name": product["product_name"],
                "product_code": product_code,
                "relevance_to_stock": f"{stock['name']}核心行业价格跟踪项。",
                "exposure_weight": product["exposure_weight"],
                "direction_rule": mapping["direction_rule"],
            }
        ],
        "source_status": {
            "source_registered": True,
            "price_value_available": bool(product_obs),
            "trend_available": trend5.get("status") == "ready",
            "spread_available": False,
            "formal_chain_status": "shadow_integrated" if product_obs else "not_integrated",
        },
        "sources": sources,
        "price_observations": [
            {
                "product_name": row.get("product_name"),
                "price_date": row.get("price_date"),
                "price_low": row.get("price_low"),
                "price_high": row.get("price_high"),
                "price_mid": row.get("price_mid"),
                "unit": row.get("unit"),
                "currency": row.get("currency"),
                "change_abs": row.get("change_abs"),
                "change_pct": row.get("change_pct"),
                "trend_5d": trend5.get("direction") if trend5.get("status") == "ready" else "unknown",
                "trend_20d": trend20.get("direction") if trend20.get("status") == "ready" else "unknown",
                "source_name": row.get("source_name"),
            }
            for row in product_obs[-20:]
        ],
        "trend_summary": {
            "level": level,
            "trend_5": trend5,
            "trend_20": trend20,
            "latest_price": latest.get("price_mid"),
            "latest_date": latest.get("price_date"),
        },
        "industry_price_shadow_score": {
            "score": score,
            "max_score": 10,
            "score_reason": front_sentence(product["product_name"], level, trend5),
            "positive_evidence": [front_sentence(product["product_name"], level, trend5)] if product_obs else [],
            "negative_evidence": missing[:3],
            "confidence": confidence,
        },
        "front_output_compression": {
            "one_sentence": front_sentence(product["product_name"], level, trend5),
            "user_facing_reason": "行业价格只作为研究证据之一，不能单独决定关注等级。",
            "do_not_say": [
                "价格已经确认反转",
                "行业价格足以单独提高关注等级",
                "可以因为行业价格直接转强"
            ]
        },
        "missing": missing,
        "safety_boundary": {
            "only_for_research": True,
            "not_investment_advice": True,
            "not_buy_sell_signal": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }
    return card


def markdown_summary(cards: list[dict[str, Any]]) -> str:
    rows = []
    for card in cards:
        stock = card["stock"]
        trend = card.get("trend_summary", {})
        rows.append(
            f"| {stock['name']} | {card['tracked_products'][0]['product_name']} | {card['状态']} | {trend.get('latest_price') or '-'} | {trend.get('trend_5', {}).get('direction')} | {card['front_output_compression']['one_sentence']} |"
        )
    return "\n".join([
        "# 行业价格趋势证据卡本地观测生成结果",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "| 股票 | 产品 | 状态 | 最新价 | 5点趋势 | 前台一句话 |",
        "|---|---|---|---:|---|---|",
        *rows,
        "",
        "说明：本脚本只读本地观测账本，不联网抓取，不外发，不触发交易。",
    ])


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "245L3评分基础资产"
    ledger = load_json(out_dir / "industry_price_observations_ledger_v1.0.json", {}) or {}
    observations = ledger.get("observations", []) if isinstance(ledger.get("observations"), list) else []
    cards = []
    for mapping in STOCK_PRODUCT_MAP:
        card = build_card(root, mapping, observations)
        cards.append(card)
        stock_name = mapping["stock"]["name"]
        path = out_dir / f"{stock_name}_行业价格证据卡_本地观测_latest.json"
        write_json(path, card)
    summary = {
        "名称": "行业价格趋势证据卡本地观测生成结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "completed",
        "cards": [
            {
                "stock": card["stock"]["name"],
                "product": card["tracked_products"][0]["product_name"],
                "level": card["状态"],
                "score": card["industry_price_shadow_score"]["score"],
                "front_sentence": card["front_output_compression"]["one_sentence"],
            }
            for card in cards
        ],
        "safety_boundary": {
            "not_external_send": True,
            "not_n8n": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }
    write_json(out_dir / "行业价格趋势证据卡本地观测生成结果_20260508.json", summary)
    write_text(out_dir / "行业价格趋势证据卡本地观测生成结果_20260508.md", markdown_summary(cards))
    print(json.dumps({"状态": "完成", "卡片数": len(cards), "输出": str(out_dir)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
