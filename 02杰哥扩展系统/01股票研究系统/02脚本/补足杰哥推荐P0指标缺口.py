# -*- coding: utf-8 -*-
# ============================================================
# 脚本名称：补足杰哥推荐P0指标缺口.py
# 所属系统：02杰哥扩展系统/01股票研究系统/02脚本
# 功能描述：补全成交量/成交额波动率、周线趋势、行业动态强弱等P0增强指标。
# 创建日期：2026-05-10
# 输入：272全候选量价特征 + 271候选历史K线增强 + 273行业归因报告
# 输出：279杰哥推荐P0指标补足/全候选P0增强量价特征_最新.json
# 安全边界：只读03数据基础产物；只写279增强产物；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
# ============================================================

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any

import pandas as pd


STOCK_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_ROOT = STOCK_ROOT / "03数据"
OUT_DIR = DATA_ROOT / "279杰哥推荐P0指标补足"

FEATURE_PATH = DATA_ROOT / "272杰哥推荐量价特征" / "全候选量价特征_最新.json"
KLINE_PATH = DATA_ROOT / "271杰哥推荐基础补足" / "杰哥推荐候选历史K线增强_最新.json"
INDUSTRY_REPORT_PATH = DATA_ROOT / "273杰哥推荐行业归因" / "杰哥推荐行业归因报告_最新.json"

LATEST_FEATURE_PATH = OUT_DIR / "全候选P0增强量价特征_最新.json"
LATEST_REPORT_JSON = OUT_DIR / "杰哥推荐P0指标补足报告_最新.json"
LATEST_REPORT_MD = OUT_DIR / "杰哥推荐P0指标补足报告_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_code(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    text = text.replace("_", "").replace("-", "")
    if "." in text:
        code, market = text.split(".", 1)
        if market.lower() in {"sh", "sz", "bj"}:
            return market.lower() + code
    if len(text) == 8 and text[:2] in {"sh", "sz", "bj"}:
        return text
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) == 6:
        if digits.startswith(("6", "9")):
            return "sh" + digits
        if digits.startswith(("0", "2", "3")):
            return "sz" + digits
        if digits.startswith(("4", "8")):
            return "bj" + digits
    return text


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-"):
            return default
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except (TypeError, ValueError):
        return default


def percentile_rank(values: list[float], value: float | None) -> float:
    if value is None or not values:
        return 0.0
    ordered = sorted(values)
    below_or_equal = sum(1 for item in ordered if item <= value)
    return round(below_or_equal / len(ordered) * 100, 4)


def coefficient_of_variation(values: list[Any], window: int = 60) -> float | None:
    numbers = [safe_float(item) for item in values]
    clean = [item for item in numbers if item is not None and item > 0]
    if len(clean) < max(20, window // 2):
        return None
    recent = clean[-window:]
    avg = mean(recent)
    if avg <= 0:
        return None
    return round(pstdev(recent) / avg, 4)


def weekly_trend(kline: list[dict[str, Any]]) -> dict[str, Any]:
    default = {
        "周线数量": 0,
        "周线MA多头": False,
        "周线MACD向上": False,
        "周线收盘在MA20上": False,
        "周线趋势状态": "数据不足",
    }
    if len(kline) < 80:
        return default
    rows: list[dict[str, Any]] = []
    for item in kline:
        if not isinstance(item, dict):
            continue
        date = item.get("日期")
        close = safe_float(item.get("收盘"))
        if not date or close is None:
            continue
        rows.append(
            {
                "日期": date,
                "开盘": safe_float(item.get("开盘"), close),
                "最高": safe_float(item.get("最高"), close),
                "最低": safe_float(item.get("最低"), close),
                "收盘": close,
                "成交量": safe_float(item.get("成交量"), 0.0) or 0.0,
                "成交额": safe_float(item.get("成交额"), 0.0) or 0.0,
            }
        )
    if len(rows) < 80:
        return default

    df = pd.DataFrame(rows)
    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    df = df.dropna(subset=["日期"]).sort_values("日期").set_index("日期")
    weekly = (
        df.resample("W-FRI")
        .agg({"开盘": "first", "最高": "max", "最低": "min", "收盘": "last", "成交量": "sum", "成交额": "sum"})
        .dropna(subset=["收盘"])
    )
    if len(weekly) < 20:
        return {**default, "周线数量": int(len(weekly))}

    close = weekly["收盘"]
    ma20 = close.rolling(20).mean()
    ma60 = close.rolling(60).mean()
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd = 2 * (dif - dea)

    latest_close = float(close.iloc[-1])
    latest_ma20 = safe_float(ma20.iloc[-1])
    latest_ma60 = safe_float(ma60.iloc[-1]) if len(weekly) >= 60 else None
    ma_bull = bool(latest_ma20 is not None and latest_close > latest_ma20 and (latest_ma60 is None or latest_ma20 > latest_ma60))
    macd_up = bool(len(macd) >= 2 and safe_float(macd.iloc[-1], 0.0) > safe_float(macd.iloc[-2], 0.0))
    above_ma20 = bool(latest_ma20 is not None and latest_close > latest_ma20)
    if ma_bull and macd_up and above_ma20:
        state = "周线共振"
    elif above_ma20 and (ma_bull or macd_up):
        state = "周线偏强"
    elif above_ma20:
        state = "周线观察"
    else:
        state = "周线未确认"
    return {
        "周线数量": int(len(weekly)),
        "周线MA多头": ma_bull,
        "周线MACD向上": macd_up,
        "周线收盘在MA20上": above_ma20,
        "周线趋势状态": state,
    }


def build_kline_map(kline_data: Any) -> dict[str, dict[str, Any]]:
    rows = kline_data.get("股票", []) if isinstance(kline_data, dict) else kline_data
    mapping: dict[str, dict[str, Any]] = {}
    if not isinstance(rows, list):
        return mapping
    for item in rows:
        if not isinstance(item, dict):
            continue
        code = normalize_code(item.get("代码") or item.get("展示代码"))
        if code:
            mapping[code] = item
    return mapping


def build_static_industry_map(industry_report: Any) -> dict[str, dict[str, Any]]:
    rows = industry_report.get("全部行业归因", []) if isinstance(industry_report, dict) else []
    mapping: dict[str, dict[str, Any]] = {}
    if not isinstance(rows, list):
        return mapping
    for item in rows:
        if isinstance(item, dict) and item.get("行业"):
            mapping[str(item.get("行业"))] = item
    return mapping


def median_float(values: list[float]) -> float:
    return round(float(median(values)), 4) if values else 0.0


def mean_float(values: list[float]) -> float:
    return round(float(mean(values)), 4) if values else 0.0


def build_dynamic_industry_stats(features: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in features:
        industry = str(item.get("行业") or "未知")
        buckets[industry].append(item)

    raw_stats: dict[str, dict[str, Any]] = {}
    for industry, rows in buckets.items():
        change20 = [safe_float(row.get("20日涨跌幅")) for row in rows]
        change60 = [safe_float(row.get("60日涨跌幅")) for row in rows]
        amount_ratio = [safe_float(row.get("成交额20_60比")) for row in rows]
        volume_ratio = [safe_float(row.get("量比5日")) for row in rows]
        ma_bull_count = sum(1 for row in rows if row.get("均线多头排列") is True)
        breakthrough_count = sum(1 for row in rows if row.get("60日突破") is True)
        clean20 = [item for item in change20 if item is not None]
        clean60 = [item for item in change60 if item is not None]
        clean_amount = [item for item in amount_ratio if item is not None]
        clean_volume = [item for item in volume_ratio if item is not None]
        count = len(rows)
        raw_stats[industry] = {
            "行业": industry,
            "候选数": count,
            "行业20日中位涨跌幅": median_float(clean20),
            "行业60日中位涨跌幅": median_float(clean60),
            "行业成交额20_60比中位数": median_float(clean_amount),
            "行业量比5日中位数": median_float(clean_volume),
            "行业均线多头比例": round(ma_bull_count / count, 4) if count else 0.0,
            "行业突破比例": round(breakthrough_count / count, 4) if count else 0.0,
        }

    values_20 = [item["行业20日中位涨跌幅"] for item in raw_stats.values()]
    values_60 = [item["行业60日中位涨跌幅"] for item in raw_stats.values()]
    values_amount = [item["行业成交额20_60比中位数"] for item in raw_stats.values()]
    values_ma = [item["行业均线多头比例"] for item in raw_stats.values()]
    values_break = [item["行业突破比例"] for item in raw_stats.values()]

    for item in raw_stats.values():
        score = (
            percentile_rank(values_20, item["行业20日中位涨跌幅"]) * 0.2
            + percentile_rank(values_60, item["行业60日中位涨跌幅"]) * 0.3
            + percentile_rank(values_amount, item["行业成交额20_60比中位数"]) * 0.2
            + percentile_rank(values_ma, item["行业均线多头比例"]) * 0.2
            + percentile_rank(values_break, item["行业突破比例"]) * 0.1
        )
        item["行业动态强度分"] = round(score, 4)

    ranked = sorted(raw_stats.values(), key=lambda row: row["行业动态强度分"], reverse=True)
    for rank, item in enumerate(ranked, start=1):
        score = item["行业动态强度分"]
        if score >= 80:
            state = "动态强势"
        elif score >= 60:
            state = "动态偏强"
        elif score >= 40:
            state = "动态中性"
        else:
            state = "动态逆风"
        item["行业动态排名"] = rank
        item["行业动态状态"] = state

    return raw_stats


def main() -> int:
    feature_data = load_json(FEATURE_PATH, [])
    kline_data = load_json(KLINE_PATH, {})
    industry_report = load_json(INDUSTRY_REPORT_PATH, {})
    if not isinstance(feature_data, list):
        raise RuntimeError(f"量价特征文件结构异常，应为列表：{FEATURE_PATH}")

    kline_map = build_kline_map(kline_data)
    static_industry_map = build_static_industry_map(industry_report)
    dynamic_industry_map = build_dynamic_industry_stats(feature_data)
    volume_volatility_values: list[float] = []
    amount_volatility_values: list[float] = []
    enhanced: list[dict[str, Any]] = []
    missing_kline = 0

    for item in feature_data:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        code = normalize_code(row.get("代码") or row.get("展示代码"))
        stock = kline_map.get(code, {})
        kline = stock.get("历史K线") if isinstance(stock.get("历史K线"), list) else []
        if not kline:
            missing_kline += 1

        volumes = [bar.get("成交量") for bar in kline if isinstance(bar, dict)]
        amounts = [bar.get("成交额") for bar in kline if isinstance(bar, dict)]
        volume_volatility = coefficient_of_variation(volumes, 60)
        amount_volatility = coefficient_of_variation(amounts, 60)
        if volume_volatility is not None:
            volume_volatility_values.append(volume_volatility)
        if amount_volatility is not None:
            amount_volatility_values.append(amount_volatility)

        weekly = weekly_trend(kline)
        industry = str(row.get("行业") or "未知")
        static_industry = static_industry_map.get(industry, {})
        dynamic_industry = dynamic_industry_map.get(industry, {})

        row.update(
            {
                "成交量60日波动率": volume_volatility,
                "成交额60日波动率": amount_volatility,
                **weekly,
                "行业静态强势指数": safe_float(static_industry.get("强势过度代表指数"), 0.0),
                "行业静态失败指数": safe_float(static_industry.get("失败过度代表指数"), 0.0),
                "行业归因标签": static_industry.get("归因标签"),
                "行业动态强度分": dynamic_industry.get("行业动态强度分"),
                "行业动态排名": dynamic_industry.get("行业动态排名"),
                "行业动态状态": dynamic_industry.get("行业动态状态"),
                "行业20日中位涨跌幅": dynamic_industry.get("行业20日中位涨跌幅"),
                "行业60日中位涨跌幅": dynamic_industry.get("行业60日中位涨跌幅"),
                "行业成交额20_60比中位数": dynamic_industry.get("行业成交额20_60比中位数"),
                "行业均线多头比例": dynamic_industry.get("行业均线多头比例"),
                "P0增强来源": "补足杰哥推荐P0指标缺口.py",
                "P0增强时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        enhanced.append(row)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dated_feature_path = OUT_DIR / f"全候选P0增强量价特征_{timestamp}.json"
    write_json(LATEST_FEATURE_PATH, enhanced)
    write_json(dated_feature_path, enhanced)

    dynamic_rank = sorted(dynamic_industry_map.values(), key=lambda row: row.get("行业动态排名") or 999)
    report = {
        "名称": "杰哥推荐P0指标补足报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "输入": {
            "全候选量价特征": str(FEATURE_PATH),
            "候选历史K线增强": str(KLINE_PATH),
            "行业归因报告": str(INDUSTRY_REPORT_PATH),
        },
        "输出": {
            "最新增强特征": str(LATEST_FEATURE_PATH),
            "本次增强特征": str(dated_feature_path),
        },
        "统计": {
            "候选数量": len(enhanced),
            "K线命中数量": len(enhanced) - missing_kline,
            "K线缺失数量": missing_kline,
            "成交量60日波动率可用数量": len(volume_volatility_values),
            "成交额60日波动率可用数量": len(amount_volatility_values),
            "成交量60日波动率中位数": median_float(volume_volatility_values),
            "成交额60日波动率中位数": median_float(amount_volatility_values),
            "周线MA多头数量": sum(1 for row in enhanced if row.get("周线MA多头") is True),
            "周线MACD向上数量": sum(1 for row in enhanced if row.get("周线MACD向上") is True),
            "周线收盘在MA20上数量": sum(1 for row in enhanced if row.get("周线收盘在MA20上") is True),
            "行业数量": len(dynamic_industry_map),
        },
        "行业动态强弱Top": dynamic_rank[:10],
        "行业动态弱势Top": list(reversed(dynamic_rank[-10:])),
        "新增字段": [
            "成交量60日波动率",
            "成交额60日波动率",
            "周线数量",
            "周线MA多头",
            "周线MACD向上",
            "周线收盘在MA20上",
            "周线趋势状态",
            "行业动态强度分",
            "行业动态排名",
            "行业动态状态",
        ],
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "输出交易指令": False,
        },
    }
    write_json(LATEST_REPORT_JSON, report)
    write_json(OUT_DIR / f"杰哥推荐P0指标补足报告_{timestamp}.json", report)
    write_text(
        LATEST_REPORT_MD,
        "\n".join(
            [
                "# 杰哥推荐P0指标补足报告",
                "",
                f"- 生成时间：{report['生成时间']}",
                f"- 候选数量：{report['统计']['候选数量']}",
                f"- K线命中数量：{report['统计']['K线命中数量']}",
                f"- 成交量60日波动率可用数量：{report['统计']['成交量60日波动率可用数量']}",
                f"- 成交额60日波动率可用数量：{report['统计']['成交额60日波动率可用数量']}",
                f"- 周线MA多头数量：{report['统计']['周线MA多头数量']}",
                "",
                "## 行业动态强弱Top",
                *[
                    f"{idx}. {item['行业']}：强度{item['行业动态强度分']}，排名{item['行业动态排名']}，状态{item['行业动态状态']}"
                    for idx, item in enumerate(report["行业动态强弱Top"][:10], start=1)
                ],
                "",
                "## 安全边界",
                "",
                "只写P0增强产物，不覆盖原始272量价特征，不触发外部接口，不输出交易指令。",
            ]
        ),
    )
    print("P0指标缺口补全完成。")
    print(f"更新股票数量: {len(enhanced)}")
    print(f"增强特征: {LATEST_FEATURE_PATH}")
    print(f"报告: {LATEST_REPORT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
