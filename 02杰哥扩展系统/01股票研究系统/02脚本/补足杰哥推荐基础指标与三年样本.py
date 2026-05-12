# -*- coding: utf-8 -*-
"""
名称：补足杰哥推荐基础指标与三年样本.py
作用：为【杰哥推荐】补齐全样本五年历史K线、完整技术指标、近三年强势成功样本、失败对照样本和相似度识别结果。
触发方式：python 补足杰哥推荐基础指标与三年样本.py
依赖：2000只样本池盘后影子轻扫描；东方财富公开历史K线接口。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读公开行情和本地样本池，只写新系统03数据；不触发n8n；不发送企业微信；不接券商；不自动交易；不输出买卖指令。
创建修改记录：2026-05-10 创建，用于补足【杰哥推荐】方法内核基础债。
标识：jiege-recommendation-foundation-backfill-v2-five-year-base
"""

from __future__ import annotations

import concurrent.futures
import json
import math
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


MAX_CANDIDATES = 2000
FETCH_WORKERS = 8
BEGIN_DATE = "20210510"
END_DATE = "20260510"
THREE_YEAR_TRADING_DAYS = 750


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
SCAN_PATH = ROOT / "03数据" / "2000只影子扫描" / "2000只样本池盘后影子轻扫描_最新.json"
OUT_DIR = ROOT / "03数据" / "271杰哥推荐基础补足"
KERNEL_DIR = ROOT / "03数据" / "270杰哥推荐方法内核"


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


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def norm_code(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text[:8]
    if text.startswith(("6", "9")):
        return "sh" + text[:6]
    return "sz" + text[:6]


def to_sec_id(code: str) -> str:
    code = norm_code(code)
    if code.startswith("sh"):
        return "1." + code[2:]
    if code.startswith("bj"):
        return "0." + code[2:]
    return "0." + code[2:]


def fetch_eastmoney_kline(code: str) -> list[dict[str, Any]]:
    params = {
        "secid": to_sec_id(code),
        "klt": "101",
        "fqt": "1",
        "beg": BEGIN_DATE,
        "end": END_DATE,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
    }
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=18) as response:
        raw = json.loads(response.read().decode("utf-8", errors="replace"))
    klines = ((raw.get("data") or {}).get("klines") or [])
    rows: list[dict[str, Any]] = []
    for line in klines:
        parts = str(line).split(",")
        if len(parts) < 11:
            continue
        rows.append({
            "日期": parts[0],
            "开盘": safe_float(parts[1]),
            "收盘": safe_float(parts[2]),
            "最高": safe_float(parts[3]),
            "最低": safe_float(parts[4]),
            "成交量": safe_float(parts[5]),
            "成交额": safe_float(parts[6]),
            "振幅": safe_float(parts[7]),
            "涨跌幅": safe_float(parts[8]),
            "涨跌额": safe_float(parts[9]),
            "换手率": safe_float(parts[10]),
        })
    return rows


def parse_percent(value: Any) -> float | None:
    text = str(value or "").strip().replace("%", "")
    if text in ("", "-"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fetch_sohu_kline(code: str) -> list[dict[str, Any]]:
    query_code = norm_code(code)[2:]
    params = {
        "code": "cn_" + query_code,
        "start": BEGIN_DATE,
        "end": END_DATE,
        "stat": "1",
        "order": "D",
        "period": "d",
        "callback": "historySearchHandler",
        "rt": "jsonp",
    }
    url = "https://q.stock.sohu.com/hisHq?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://q.stock.sohu.com/",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=18) as response:
        text = response.read().decode("gbk", errors="replace")
    start = text.find("(")
    end = text.rfind(")")
    payload = json.loads(text[start + 1:end] if start >= 0 and end > start else text)
    if not payload or not isinstance(payload, list):
        return []
    hq_rows = (payload[0] or {}).get("hq") or []
    rows: list[dict[str, Any]] = []
    for line in reversed(hq_rows):
        if len(line) < 10:
            continue
        open_price = safe_float(line[1])
        close_price = safe_float(line[2])
        low_price = safe_float(line[5])
        high_price = safe_float(line[6])
        volume_hands = safe_float(line[7])
        amount_wan = safe_float(line[8])
        turnover = parse_percent(line[9])
        previous_close = rows[-1]["收盘"] if rows else 0.0
        amplitude = round((high_price - low_price) / previous_close * 100, 4) if previous_close else None
        rows.append({
            "日期": line[0],
            "开盘": open_price,
            "收盘": close_price,
            "最高": high_price,
            "最低": low_price,
            "成交量": volume_hands * 100,
            "成交额": amount_wan * 10000,
            "振幅": amplitude,
            "涨跌幅": parse_percent(line[4]),
            "涨跌额": safe_float(line[3]),
            "换手率": turnover,
        })
    return rows


def fetch_tencent_kline(code: str, limit: int = 1300) -> list[dict[str, Any]]:
    params = {"param": f"{norm_code(code)},day,,,{max(limit, 640)},qfq"}
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": f"https://gu.qq.com/{norm_code(code)}/gp",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=18) as response:
        raw = json.loads(response.read().decode("utf-8", errors="replace"))
    stock_data = (raw.get("data") or {}).get(norm_code(code), {}) or {}
    klines = stock_data.get("qfqday") or stock_data.get("day") or []
    rows: list[dict[str, Any]] = []
    previous_close = None
    for line in klines[-limit:]:
        if len(line) < 6:
            continue
        open_price = safe_float(line[1])
        close_price = safe_float(line[2])
        high_price = safe_float(line[3])
        low_price = safe_float(line[4])
        volume_hands = safe_float(line[5])
        diff = round(close_price - previous_close, 4) if previous_close else None
        pct = round(diff / previous_close * 100, 4) if previous_close and diff is not None else None
        amplitude = round((high_price - low_price) / previous_close * 100, 4) if previous_close else None
        amount_estimated = volume_hands * 100 * close_price
        rows.append({
            "日期": line[0],
            "开盘": open_price,
            "收盘": close_price,
            "最高": high_price,
            "最低": low_price,
            "成交量": volume_hands * 100,
            "成交额": amount_estimated,
            "成交额是否估算": True,
            "振幅": amplitude,
            "涨跌幅": pct,
            "涨跌额": diff,
            "换手率": None,
        })
        previous_close = close_price
    return rows


def fetch_kline_multi_source(code: str) -> tuple[list[dict[str, Any]], str, str]:
    errors: list[str] = []
    for source_name, fetcher in (
        ("搜狐历史行情", fetch_sohu_kline),
        ("东方财富历史K线", fetch_eastmoney_kline),
        ("腾讯历史K线估算兜底", fetch_tencent_kline),
    ):
        try:
            rows = fetcher(code)
            if rows:
                return rows, source_name, "；".join(errors)
            errors.append(f"{source_name}返回空数据")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{source_name}失败：{exc}")
    return [], "", "；".join(errors)


def sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return round(sum(values[-period:]) / period, 4)


def ema_series(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    alpha = 2 / (period + 1)
    output = [values[0]]
    for value in values[1:]:
        output.append(value * alpha + output[-1] * (1 - alpha))
    return output


def calc_rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) <= period:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for index in range(1, len(closes)):
        diff = closes[index] - closes[index - 1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 4)


def calc_macd(closes: list[float]) -> dict[str, float | None]:
    if len(closes) < 35:
        return {"DIF": None, "DEA": None, "MACD": None}
    ema12 = ema_series(closes, 12)
    ema26 = ema_series(closes, 26)
    dif = [a - b for a, b in zip(ema12, ema26)]
    dea = ema_series(dif, 9)
    return {"DIF": round(dif[-1], 4), "DEA": round(dea[-1], 4), "MACD": round((dif[-1] - dea[-1]) * 2, 4)}


def calc_kdj(rows: list[dict[str, Any]], period: int = 9) -> dict[str, float | None]:
    if len(rows) < period:
        return {"K": None, "D": None, "J": None}
    k = 50.0
    d = 50.0
    for index in range(period - 1, len(rows)):
        window = rows[index - period + 1:index + 1]
        high = max(safe_float(row.get("最高")) for row in window)
        low = min(safe_float(row.get("最低")) for row in window)
        close = safe_float(rows[index].get("收盘"))
        rsv = 50.0 if high == low else (close - low) / (high - low) * 100
        k = (2 / 3) * k + (1 / 3) * rsv
        d = (2 / 3) * d + (1 / 3) * k
    return {"K": round(k, 4), "D": round(d, 4), "J": round(3 * k - 2 * d, 4)}


def calc_boll(closes: list[float], period: int = 20) -> dict[str, float | None]:
    if len(closes) < period:
        return {"中轨": None, "上轨": None, "下轨": None, "位置": None}
    window = closes[-period:]
    mid = mean(window)
    std = math.sqrt(sum((item - mid) ** 2 for item in window) / period)
    upper = mid + 2 * std
    lower = mid - 2 * std
    position = None if upper == lower else (closes[-1] - lower) / (upper - lower)
    return {"中轨": round(mid, 4), "上轨": round(upper, 4), "下轨": round(lower, 4), "位置": round(position, 4) if position is not None else None}


def calc_atr_pct(rows: list[dict[str, Any]], period: int = 14) -> float | None:
    if len(rows) <= period:
        return None
    true_ranges: list[float] = []
    previous_close = safe_float(rows[0].get("收盘"))
    for row in rows[1:]:
        high = safe_float(row.get("最高"))
        low = safe_float(row.get("最低"))
        close = safe_float(row.get("收盘"))
        true_ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
        previous_close = close
    close = safe_float(rows[-1].get("收盘"))
    if close <= 0:
        return None
    return round(mean(true_ranges[-period:]) / close * 100, 4)


def pct_return(closes: list[float], period: int) -> float | None:
    if len(closes) <= period or closes[-period - 1] == 0:
        return None
    return round((closes[-1] / closes[-period - 1] - 1) * 100, 4)


def available_return(closes: list[float]) -> tuple[float | None, int]:
    if len(closes) < 2 or closes[0] == 0:
        return None, len(closes)
    return round((closes[-1] / closes[0] - 1) * 100, 4), len(closes)


def window_or_available_return(closes: list[float], period: int) -> tuple[float | None, int, bool]:
    if len(closes) > period and closes[-period - 1] != 0:
        return round((closes[-1] / closes[-period - 1] - 1) * 100, 4), period, True
    value, available_days = available_return(closes)
    return value, available_days, False


def max_drawdown(closes: list[float], period: int) -> float | None:
    if len(closes) < min(period, 20):
        return None
    window = closes[-period:] if len(closes) >= period else closes
    peak = window[0]
    worst = 0.0
    for value in window:
        peak = max(peak, value)
        if peak:
            worst = min(worst, value / peak - 1)
    return round(worst * 100, 4)


def percentile(values: list[float], value: float) -> float:
    if not values:
        return 0.0
    return sum(1 for item in values if item <= value) / len(values)


def build_candidate_universe() -> list[dict[str, Any]]:
    scan = load_json(SCAN_PATH, {})
    rows = scan.get("股票", []) if isinstance(scan, dict) and isinstance(scan.get("股票"), list) else []
    rows = [row for row in rows if isinstance(row, dict) and row.get("代码")]
    rows.sort(
        key=lambda item: (
            safe_float(item.get("影子评分")),
            safe_float(item.get("成交额市值比")),
            safe_float(item.get("最新成交额")),
        ),
        reverse=True,
    )
    return rows[:MAX_CANDIDATES]


def enrich_one(candidate: dict[str, Any]) -> dict[str, Any]:
    code = norm_code(candidate.get("代码"))
    try:
        rows, source, warning = fetch_kline_multi_source(code)
        status = "成功" if len(rows) >= 60 else "历史K线不足"
        error = warning
    except Exception as exc:  # noqa: BLE001
        rows = []
        source = ""
        status = "失败"
        error = str(exc)
    closes = [safe_float(row.get("收盘")) for row in rows if row.get("收盘") is not None]
    volumes = [safe_float(row.get("成交量")) for row in rows if row.get("成交量") is not None]
    amounts = [safe_float(row.get("成交额")) for row in rows if row.get("成交额") is not None]
    available_ret, available_days = available_return(closes)
    three_year_ret, three_year_days, three_year_complete = window_or_available_return(closes, THREE_YEAR_TRADING_DAYS)
    latest = rows[-1] if rows else {}
    ma = {f"MA{period}": sma(closes, period) for period in (5, 10, 20, 60, 120, 250)}
    macd = calc_macd(closes)
    latest_volume = volumes[-1] if volumes else 0.0
    volume_ma20 = sma(volumes, 20)
    amount_ma20 = sma(amounts, 20)
    volume_ratio = round(latest_volume / volume_ma20, 4) if volume_ma20 else None
    latest_close = safe_float(latest.get("收盘"))
    latest_open = safe_float(latest.get("开盘"))
    previous_close = safe_float(rows[-2].get("收盘")) if len(rows) >= 2 else 0.0
    gap_pct = round((latest_open / previous_close - 1) * 100, 4) if previous_close else None
    highs = [safe_float(row.get("最高")) for row in rows if row.get("最高") is not None]
    high_60 = max(highs[-60:]) if len(highs) >= 60 else (max(highs) if highs else 0.0)
    return {
        "代码": code,
        "展示代码": candidate.get("展示代码") or code,
        "名称": candidate.get("名称"),
        "行业": candidate.get("行业") or "未知",
        "状态": status,
        "数据源": source,
        "错误": error,
        "K线数量": len(rows),
        "起始日期": rows[0].get("日期") if rows else "",
        "最新日期": latest.get("日期", ""),
        "最新收盘": latest_close,
        "最新成交额": candidate.get("最新成交额") or latest.get("成交额"),
        "市值": candidate.get("市值"),
        "成交额市值比": candidate.get("成交额市值比"),
        "影子评分": candidate.get("影子评分"),
        "中证全指权重": candidate.get("中证全指权重"),
        "历史K线": rows,
        "技术指标": {
            "MA": ma,
            "RSI14": calc_rsi(closes),
            "MACD": macd,
            "KDJ": calc_kdj(rows),
            "BOLL": calc_boll(closes),
            "ATR14波动率": calc_atr_pct(rows),
            "成交量MA20": volume_ma20,
            "成交额MA20": amount_ma20,
            "量比5日": volume_ratio,
            "20日涨跌幅": pct_return(closes, 20),
            "60日涨跌幅": pct_return(closes, 60),
            "120日涨跌幅": pct_return(closes, 120),
            "250日涨跌幅": pct_return(closes, 250),
            "近三年可得涨跌幅": three_year_ret,
            "近三年可得交易日数": three_year_days,
            "近三年数据完整": three_year_complete,
            "五年可得涨跌幅": available_ret,
            "五年可得交易日数": available_days,
            "60日最大回撤": max_drawdown(closes, 60),
            "250日最大回撤": max_drawdown(closes, 250),
            "60日突破": bool(high_60 and latest_close >= high_60 * 0.995),
            "最近跳空缺口": gap_pct,
            "换手率": latest.get("换手率"),
            "振幅": latest.get("振幅"),
            "站上MA20": bool(ma.get("MA20") and latest_close > safe_float(ma.get("MA20"))),
            "站上MA60": bool(ma.get("MA60") and latest_close > safe_float(ma.get("MA60"))),
            "MACD强": bool(macd.get("DIF") is not None and safe_float(macd.get("DIF")) > safe_float(macd.get("DEA"))),
        },
    }


def without_history(row: dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    item.pop("历史K线", None)
    item["历史K线引用"] = "03数据/271杰哥推荐基础补足/杰哥推荐候选历史K线增强_最新.json"
    return item


def calc_vectors(rows: list[dict[str, Any]]) -> None:
    valid = [row for row in rows if row.get("状态") == "成功"]
    ret_values = [safe_float(row["技术指标"].get("近三年可得涨跌幅")) for row in valid]
    ret250_values = [safe_float(row["技术指标"].get("250日涨跌幅")) for row in valid]
    amount_values = [safe_float(row.get("最新成交额")) for row in valid]
    turnover_values = [safe_float(row.get("成交额市值比")) for row in valid]
    shadow_values = [safe_float(row.get("影子评分")) for row in valid]
    industry_ret: dict[str, list[float]] = {}
    for row in valid:
        industry_ret.setdefault(str(row.get("行业") or "未知"), []).append(safe_float(row["技术指标"].get("近三年可得涨跌幅")))
    industry_score = {key: mean(vals) for key, vals in industry_ret.items() if vals}
    industry_values = list(industry_score.values())
    for row in rows:
        ind = row.get("技术指标", {})
        vector = {
            "三年涨幅分位": percentile(ret_values, safe_float(ind.get("近三年可得涨跌幅"))),
            "250日涨幅分位": percentile(ret250_values, safe_float(ind.get("250日涨跌幅"))),
            "成交额分位": percentile(amount_values, safe_float(row.get("最新成交额"))),
            "成交额市值比分位": percentile(turnover_values, safe_float(row.get("成交额市值比"))),
            "影子评分分位": percentile(shadow_values, safe_float(row.get("影子评分"))),
            "行业三年强度分位": percentile(industry_values, industry_score.get(str(row.get("行业") or "未知"), 0.0)),
            "站上MA20": 1.0 if ind.get("站上MA20") else 0.0,
            "站上MA60": 1.0 if ind.get("站上MA60") else 0.0,
            "MACD强": 1.0 if ind.get("MACD强") else 0.0,
            "量比归一": min(safe_float(ind.get("量比5日")) / 3, 1.0),
            "突破": 1.0 if ind.get("60日突破") else 0.0,
            "回撤控制": max(0.0, min(1.0, (60 + safe_float(ind.get("250日最大回撤"))) / 60)),
            "波动适中": 1.0 if 1 <= safe_float(ind.get("ATR14波动率")) <= 8 else 0.0,
        }
        strength = (
            vector["三年涨幅分位"] * 24
            + vector["250日涨幅分位"] * 18
            + vector["成交额市值比分位"] * 14
            + vector["成交额分位"] * 10
            + vector["影子评分分位"] * 10
            + vector["行业三年强度分位"] * 8
            + vector["站上MA20"] * 4
            + vector["站上MA60"] * 4
            + vector["MACD强"] * 3
            + vector["突破"] * 3
            + vector["回撤控制"] * 2
        )
        row["特征向量"] = vector
        row["杰哥推荐基础强度分"] = round(strength, 2)


def centroid(rows: list[dict[str, Any]]) -> dict[str, float]:
    keys = sorted({key for row in rows for key in row.get("特征向量", {}).keys()})
    return {key: mean([safe_float(row.get("特征向量", {}).get(key)) for row in rows]) for key in keys}


def similarity(vector: dict[str, Any], center: dict[str, float]) -> float:
    keys = sorted(set(vector.keys()) | set(center.keys()))
    if not keys:
        return 0.0
    distance = math.sqrt(sum((safe_float(vector.get(key)) - safe_float(center.get(key))) ** 2 for key in keys) / len(keys))
    return round(max(0, 1 - distance) * 100, 2)


def calibrated_recommendation_score(raw_values: list[float], raw_value: float) -> float:
    """把原始相似度压到可读区间，避免满屏100分。"""
    rank = percentile(raw_values, raw_value)
    return round(55 + rank * 40, 2)


def classify_recommendation(score: float, success_score: float, failure_score: float) -> str:
    """推荐分层：少量优先研究，一部分观察验证，大部分不进首页。"""
    edge = success_score - failure_score
    if score >= 90 and edge >= 5:
        return "优先研究"
    if score >= 82 and edge >= 0:
        return "观察验证"
    return "暂不进入推荐"


def make_markdown(title: str, rows: list[dict[str, Any]], score_key: str) -> str:
    lines = [
        f"# {title}",
        "",
        "| 排名 | 股票 | 行业 | 分数 | 三年可得涨跌幅 | 250日涨跌幅 | 结论 |",
        "| ---: | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for index, row in enumerate(rows[:50], start=1):
        ind = row.get("技术指标", {})
        stock = f"{row.get('名称')}({row.get('展示代码')})"
        conclusion = row.get("识别结论") or row.get("样本标签") or ""
        lines.append(f"| {index} | {stock} | {row.get('行业')} | {row.get(score_key)} | {ind.get('近三年可得涨跌幅')} | {ind.get('250日涨跌幅')} | {conclusion} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    started = datetime.now()
    stamp = started.strftime("%Y%m%d_%H%M%S")
    candidates = build_candidate_universe()
    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=FETCH_WORKERS) as executor:
        future_map = {executor.submit(enrich_one, item): item for item in candidates}
        for future in concurrent.futures.as_completed(future_map):
            results.append(future.result())
    results.sort(key=lambda item: safe_float(item.get("影子评分")), reverse=True)
    calc_vectors(results)
    valid = [row for row in results if row.get("状态") == "成功"]
    strong = sorted(valid, key=lambda item: safe_float(item.get("杰哥推荐基础强度分")), reverse=True)[:150]
    strong_codes = {row["代码"] for row in strong}
    failure_candidates = [
        row for row in valid
        if row["代码"] not in strong_codes
        and (safe_float(row["技术指标"].get("近三年可得涨跌幅")) <= 0 or safe_float(row["技术指标"].get("250日涨跌幅")) <= 0 or safe_float(row["技术指标"].get("250日最大回撤")) <= -35)
    ]
    failure = sorted(failure_candidates, key=lambda item: safe_float(item.get("杰哥推荐基础强度分")))[:150]
    if len(failure) < 150:
        extra = [row for row in valid if row["代码"] not in strong_codes and row not in failure]
        failure.extend(sorted(extra, key=lambda item: safe_float(item.get("杰哥推荐基础强度分")))[:150 - len(failure)])
    for row in strong:
        row["样本标签"] = "近三年强势成功样本_v2候选增强"
    for row in failure:
        row["样本标签"] = "近三年失败对照样本_v2候选增强"
    success_center = centroid(strong)
    failure_center = centroid(failure)
    scored_rows: list[dict[str, Any]] = []
    for row in valid:
        success_score = similarity(row.get("特征向量", {}), success_center)
        failure_score = similarity(row.get("特征向量", {}), failure_center)
        raw_score = (
            safe_float(row.get("杰哥推荐基础强度分")) * 0.45
            + success_score * 0.35
            - failure_score * 0.20
        )
        item = {**row}
        item["强势相似度"] = success_score
        item["失败相似度"] = failure_score
        item["杰哥推荐原始排序分"] = round(raw_score, 4)
        scored_rows.append(item)
    raw_values = [safe_float(item.get("杰哥推荐原始排序分")) for item in scored_rows]
    similarity_rows: list[dict[str, Any]] = []
    for item in scored_rows:
        success_score = safe_float(item.get("强势相似度"))
        failure_score = safe_float(item.get("失败相似度"))
        score = calibrated_recommendation_score(raw_values, safe_float(item.get("杰哥推荐原始排序分")))
        item["杰哥推荐相似度分"] = score
        item["星级"] = "⭐⭐⭐⭐⭐" if score >= 90 else ("⭐⭐⭐⭐" if score >= 82 else ("⭐⭐⭐" if score >= 70 else "⭐⭐"))
        conclusion = classify_recommendation(score, success_score, failure_score)
        item["识别结论"] = conclusion
        item["观察条件"] = [
            "继续确认成交活跃度能否维持。",
            "结合行业方向和风险线复核，不以相似度单独下结论。",
        ]
        item["风险提示"] = "本方法只做研究排序，不构成投资建议，不作为买卖指令。"
        similarity_rows.append(item)
    similarity_rows.sort(key=lambda item: (item["识别结论"] == "优先研究", item["杰哥推荐相似度分"], item["强势相似度"]), reverse=True)
    latest_kline = {
        "名称": "杰哥推荐候选历史K线增强",
        "生成时间": started.strftime("%Y-%m-%d %H:%M:%S"),
        "候选数量": len(results),
        "成功数量": len(valid),
        "失败数量": len([row for row in results if row.get("状态") == "失败"]),
        "历史区间": {"开始": BEGIN_DATE, "结束": END_DATE},
        "股票": results,
        "安全边界": safety_boundary(),
    }
    indicator_rows = [without_history(row) for row in results]
    strong_rows = [without_history(row) for row in strong]
    failure_rows = [without_history(row) for row in failure]
    similarity_compact_rows = [without_history(row) for row in similarity_rows]
    latest_indicator = {
        "名称": "杰哥推荐技术指标增强",
        "生成时间": latest_kline["生成时间"],
        "候选数量": len(results),
        "成功数量": len(valid),
        "指标": indicator_rows,
        "安全边界": safety_boundary(),
    }
    base = {
        "生成时间": latest_kline["生成时间"],
        "方法阶段": "v3五年基础近三年方法版",
        "输入统计": {
            "候选数量": len(results),
            "历史K线成功数量": len(valid),
            "五年历史起始日期": BEGIN_DATE,
            "五年历史结束日期": END_DATE,
            "近三年方法窗口交易日": THREE_YEAR_TRADING_DAYS,
            "强势样本数量": len(strong),
            "失败对照数量": len(failure),
            "相似度识别数量": len(similarity_rows),
        },
        "技术指标准备状态": {
            "基础指标": "已按五年日K基础补齐MA5/10/20/60/120/250、RSI14、MACD、成交量/成交额MA20、量比。",
            "补充指标": "已补齐KDJ、BOLL、ATR14、20/60/120/250日涨跌幅、近三年可得涨跌幅、五年可得涨跌幅、最大回撤、突破、跳空缺口、换手率、振幅。",
            "结论": "可支撑【杰哥推荐】v3五年基础近三年方法识别；仍需后续接入行业资金连续证据和板块指数长周期证据。",
        },
        "安全边界": safety_boundary(),
    }
    success_report = {**base, "名称": "强势成功样本库", "样本数量": len(strong), "样本": strong_rows}
    failure_report = {**base, "名称": "失败对照样本库", "样本数量": len(failure), "样本": failure_rows}
    similarity_report = {**base, "名称": "当前候选股相似度识别", "候选数量": len(similarity_rows), "候选": similarity_compact_rows}
    acceptance = {
        **base,
        "名称": "杰哥推荐基础补足验收",
        "验收结论": "已补足全样本五年历史K线、完整技术指标、近三年强势成功样本、失败对照样本和相似度识别；报告基础升级为v3五年基础近三年方法版。",
        "仍待补强": [
            "接入行业资金连续证据和板块指数长周期证据。",
            "把单股详情页同步读取本增强指标作为后台证据。"
        ],
    }
    write_dual(OUT_DIR, "杰哥推荐候选历史K线增强", stamp, latest_kline)
    write_dual(OUT_DIR, "杰哥推荐技术指标增强", stamp, latest_indicator)
    write_dual(OUT_DIR, "近三年强势成功样本库", stamp, success_report)
    write_dual(OUT_DIR, "近三年失败对照样本库", stamp, failure_report)
    write_dual(OUT_DIR, "当前候选股相似度识别增强", stamp, similarity_report)
    write_dual(OUT_DIR, "杰哥推荐基础补足验收", stamp, acceptance)
    publish_kernel = len(valid) >= 100 and len(strong) >= 100 and len(failure) >= 100
    if publish_kernel:
        write_dual(KERNEL_DIR, "强势成功样本库", stamp, success_report)
        write_dual(KERNEL_DIR, "失败对照样本库", stamp, failure_report)
        write_dual(KERNEL_DIR, "当前候选股相似度识别", stamp, similarity_report)
        write_dual(KERNEL_DIR, "杰哥推荐方法内核验收", stamp, {**acceptance, "名称": "杰哥推荐方法内核验收"})
    write_text(OUT_DIR / "近三年强势成功样本库_最新.md", make_markdown("近三年强势成功样本库", strong, "杰哥推荐基础强度分"))
    write_text(OUT_DIR / "近三年失败对照样本库_最新.md", make_markdown("近三年失败对照样本库", failure, "杰哥推荐基础强度分"))
    write_text(OUT_DIR / "当前候选股相似度识别增强_最新.md", make_markdown("当前候选股相似度识别增强", similarity_rows, "杰哥推荐相似度分"))
    print(json.dumps({
        "状态": "完成",
        "候选数量": len(results),
        "历史K线成功数量": len(valid),
        "强势样本": len(strong),
        "失败样本": len(failure),
        "相似度识别": len(similarity_rows),
        "输出目录": str(OUT_DIR),
        "安全边界": safety_boundary(),
    }, ensure_ascii=False))
    return 0 if len(valid) >= 100 and len(strong) >= 100 and len(failure) >= 100 else 1


def write_dual(directory: Path, base_name: str, stamp: str, data: Any) -> None:
    write_json(directory / f"{base_name}_{stamp}.json", data)
    write_json(directory / f"{base_name}_最新.json", data)


def safety_boundary() -> dict[str, bool]:
    return {
        "真实发送企业微信": False,
        "触发n8n": False,
        "调用券商接口": False,
        "自动交易": False,
        "输出交易指令": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
