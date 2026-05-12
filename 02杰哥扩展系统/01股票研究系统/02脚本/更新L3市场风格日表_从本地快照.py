# -*- coding: utf-8 -*-
"""
名称：更新L3市场风格日表_从本地快照.py
作用：从本地行情快照和专家市场总览生成L3市场风格日表，作为market_style_daily_latest.json的保守版输入。
触发方式：python 更新L3市场风格日表_从本地快照.py
安全边界：只读03数据本地快照；只写03数据/245L3评分基础资产；不联网；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def to_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def sector_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(row.get("行业") or "未知"),
        "change_pct": round(float(row.get("当日平均涨跌幅") or 0), 4),
        "source": "03数据/185专家市场总览/股票专家市场总览_最新.json",
    }


def main() -> int:
    root = module_root()
    data = root / "03数据"
    out_dir = data / "245L3评分基础资产"
    quote_snapshot = load_json(data / "04数据快照" / "重点关注池公开行情快照_最新.json", {"行情": []})
    overview = load_json(data / "185专家市场总览" / "股票专家市场总览_最新.json", {})

    rows = quote_snapshot.get("行情", [])
    changes = [to_float(row.get("涨跌幅")) for row in rows]
    changes = [value for value in changes if value is not None]
    up_count = sum(1 for value in changes if value > 0)
    down_count = sum(1 for value in changes if value < 0)
    limit_up_count = sum(1 for value in changes if value >= 9.8)
    limit_down_count = sum(1 for value in changes if value <= -9.8)
    up_down_ratio = round(up_count / down_count, 4) if down_count else None
    total_amount = sum(to_float(row.get("成交额")) or 0 for row in rows) / 100000000

    ratio_component = ((up_down_ratio or 1) - 1) / 2
    limit_component = (limit_up_count - limit_down_count) / 50
    risk_score = round(clamp(ratio_component + limit_component, -1, 1), 2)

    strong_dirs = overview.get("强势方向", [])
    top = sorted(strong_dirs, key=lambda row: float(row.get("当日平均涨跌幅") or 0), reverse=True)[:5]
    bottom = sorted(strong_dirs, key=lambda row: float(row.get("当日平均涨跌幅") or 0))[:5]
    top_sectors = [sector_item(row) for row in top]
    bottom_sectors = [sector_item(row) for row in bottom if float(row.get("当日平均涨跌幅") or 0) < 0]

    hot_theme = top_sectors[0]["name"] if top_sectors else None
    resource_tags = {"有色金属", "小金属", "稀有金属", "半导体", "半导体材料"}
    resource_bonus = 2 if any(item["name"] in resource_tags for item in top_sectors[:3]) else 0
    score = 10 + round(risk_score * 3) + resource_bonus
    if total_amount >= 3000:
        score += 1
    final_score = int(clamp(score, 0, 20))

    trade_date = overview.get("数据日期") or datetime.now().date().isoformat()
    result = {
        "date": trade_date,
        "market": "cn",
        "status": "partial",
        "data_sources": [
            {
                "name": "重点关注池公开行情快照_最新.json",
                "type": "quote",
                "status": "success" if rows else "failed",
            },
            {
                "name": "股票专家市场总览_最新.json",
                "type": "sector",
                "status": "success" if strong_dirs else "partial",
            },
        ],
        "risk_appetite": {
            "score": risk_score,
            "up_down_ratio": up_down_ratio,
            "up_count": up_count,
            "down_count": down_count,
            "limit_up_count": limit_up_count,
            "limit_down_count": limit_down_count,
            "total_amount": round(total_amount, 2),
            "evidence": [
                f"本地重点关注池样本共{len(rows)}只，上涨{up_count}只、下跌{down_count}只。",
                f"样本成交额合计约{round(total_amount, 2)}亿元。"
            ],
            "missing": [
                "当前仅为重点关注池样本，不是全市场涨跌家数。",
                "未接入正式两市涨停/跌停全量统计。"
            ],
        },
        "sector_heat": {
            "top_sectors": top_sectors,
            "bottom_sectors": bottom_sectors,
            "hot_theme": hot_theme,
            "evidence": [
                "强势方向来自专家市场总览中的行业强度估算。",
                "该估算基于样本股等权统计，尚未接入正式申万行业指数。"
            ],
            "missing": [
                "缺正式申万行业指数或行业价格数据。",
                "缺全市场板块涨跌幅前5/后5。"
            ],
        },
        "size_style": {
            "big_small_ratio": None,
            "large_index_change_pct": None,
            "small_index_change_pct": None,
            "dominant": "unknown",
            "evidence": [],
            "missing": [
                "缺沪深300与国证2000等大小盘指数相对强弱。"
            ],
        },
        "liquidity": {
            "total_amount_rank_percentile": None,
            "activity_description": "仅有重点关注池样本成交额合计，不能替代两市总成交额近60日分位。",
            "evidence": [
                f"重点关注池样本成交额合计约{round(total_amount, 2)}亿元。"
            ],
            "missing": [
                "缺两市总成交额。",
                "缺近60个交易日成交额分位。"
            ],
        },
        "final_adaptation_score": final_score,
        "moderate_coefficient": round(clamp(1 + (final_score - 10) / 100, 0.85, 1.15), 2),
        "notes_for_stock_type": "当前风格表来自局部样本，只能作为资源股市场环境的低置信度参考；正式L3需接入全市场宽度、正式板块指数和大小盘指数。",
        "overall_summary": f"本地样本风险偏好约{risk_score}，强势方向以{hot_theme or '未知'}为代表；因缺全市场宽度和大小盘指数，市场风格适配维持partial状态。",
        "missing_summary": "缺全市场涨跌家数、正式板块涨跌幅、两市成交额近60日分位、沪深300/国证2000相对强弱。",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "last_reviewed_at": datetime.now().date().isoformat(),
    }
    write_json(out_dir / "market_style_daily_latest.json", result)
    write_json(out_dir / "market_style_daily_local_snapshot.json", result)
    print(json.dumps({"状态": "完成", "日期": trade_date, "市场风格分": final_score, "输出": str(out_dir)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
