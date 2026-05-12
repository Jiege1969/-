# -*- coding: utf-8 -*-
"""
名称：生成L7可交易过滤池.py
作用：优先读取L8X综合候选池，缺失时回退L8指数基底池，基于公开历史K线生成L7可交易过滤池。
触发方式：python 生成L7可交易过滤池.py
依赖：03数据/130X综合候选池/L8X综合候选池_最新.json；03数据/130指数基底池/L8指数基底池_最新.json；01配置/L7可交易过滤池规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读L8数据和公开行情；只写03数据/132可交易过滤池与04日志/数据源；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易；不重启服务。
标识：stock-layered-pool-l7-tradable-filter
"""

from __future__ import annotations

import argparse
import json
import math
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def module_root() -> Path:
    # 本脚本约定放在股票研究系统/02脚本 下，因此 parents[1] 为股票研究系统根目录。
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"必需文件不存在: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_input_pool(root: Path, rule: dict[str, Any]) -> tuple[dict[str, Any], Path, str, bool, str]:
    inputs = rule.get("输入", {})
    candidate = inputs.get("候选池") or "03数据/130X综合候选池/L8X综合候选池_最新.json"
    fallback = inputs.get("备用候选池") or inputs.get("L8指数基底池") or "03数据/130指数基底池/L8指数基底池_最新.json"
    candidate_path = root / candidate
    fallback_path = root / fallback

    if candidate_path.exists():
        return load_json(candidate_path, required=True), candidate_path, "L8X综合候选池", False, ""

    reason = f"候选池不存在，已回退备用候选池: {candidate_path}"
    return load_json(fallback_path, required=True), fallback_path, "L8指数基底池", True, reason


def safe_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-", "None"):
            return None
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return None
        return number
    except (TypeError, ValueError):
        return None


def safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_code(code: str) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        suffix = suffix.upper()
        if suffix == "SH":
            return f"sh{num}"
        if suffix == "SZ":
            return f"sz{num}"
        if suffix == "BJ":
            return f"bj{num}"
    if len(text) == 6 and text.isdigit():
        if text.startswith(("6", "9")):
            return f"sh{text}"
        if text.startswith(("4", "8")):
            return f"bj{text}"
        return f"sz{text}"
    return text


def display_code(code: str) -> str:
    norm = normalize_code(code)
    if norm.startswith("sh"):
        return f"{norm[2:]}.SH"
    if norm.startswith("sz"):
        return f"{norm[2:]}.SZ"
    if norm.startswith("bj"):
        return f"{norm[2:]}.BJ"
    return str(code or "").upper()


def source_flags(stock: dict[str, Any]) -> dict[str, Any]:
    return {
        "sources": stock.get("sources", []),
        "是否指数基底": stock.get("是否指数基底"),
        "是否战略样本": stock.get("是否战略样本"),
        "是否用户增强": stock.get("是否用户增强"),
        "来源优先级": stock.get("来源优先级"),
        "用户增强权重加成": stock.get("用户增强权重加成"),
        "战略入池理由": stock.get("战略入池理由"),
        "战略证据来源": stock.get("战略证据来源"),
        "复核状态": stock.get("复核状态"),
        "行业": stock.get("行业"),
        "细分领域": stock.get("细分领域"),
        "名单分类": stock.get("名单分类"),
        "标签": stock.get("标签", []),
    }


def to_eastmoney_secid(code: str) -> str:
    norm = normalize_code(code)
    if norm.startswith("sh"):
        return "1." + norm[2:]
    if norm.startswith("sz"):
        return "0." + norm[2:]
    if norm.startswith("bj"):
        return "0." + norm[2:]
    if norm.startswith(("6", "9")):
        return "1." + norm
    return "0." + norm


def market_board(code: str) -> str:
    norm = normalize_code(code)
    num = norm[2:] if norm[:2] in ("sh", "sz", "bj") else norm
    if norm.startswith("bj") or num.startswith(("4", "8")):
        return "北交所"
    if num.startswith(("300", "301")):
        return "创业板"
    if num.startswith("688"):
        return "科创板"
    return "主板"


def limit_threshold(code: str, rule: dict[str, Any]) -> float:
    board = market_board(code)
    filters = rule.get("过滤规则", {})
    if board == "北交所":
        return float(filters.get("北交所涨跌停阈值", 29.9))
    if board in ("创业板", "科创板"):
        return float(filters.get("创业板科创板涨跌停阈值", 19.9))
    return float(filters.get("主板涨跌停阈值", 9.9))


def fetch_eastmoney_kline(code: str, begin: str, timeout: int) -> list[dict[str, Any]]:
    params = {
        "secid": to_eastmoney_secid(code),
        "klt": "101",
        "fqt": "1",
        "beg": begin,
        "end": "20500101",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
    }
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))

    rows: list[dict[str, Any]] = []
    for line in (payload.get("data") or {}).get("klines", []) or []:
        parts = line.split(",")
        if len(parts) < 11:
            continue
        amount = safe_float(parts[6])
        close = safe_float(parts[2])
        pct = safe_float(parts[8])
        rows.append({
            "日期": parts[0],
            "开盘": safe_float(parts[1]),
            "收盘": close,
            "最高": safe_float(parts[3]),
            "最低": safe_float(parts[4]),
            "成交量": safe_float(parts[5]),
            "成交额": amount,
            "振幅": safe_float(parts[7]),
            "涨跌幅": pct,
            "涨跌额": safe_float(parts[9]),
            "换手率": safe_float(parts[10]),
        })
    return rows


def fetch_tencent_kline(code: str, limit: int, timeout: int) -> list[dict[str, Any]]:
    norm = normalize_code(code)
    params = {"param": f"{norm},day,,,{max(limit, 80)},qfq"}
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": f"https://gu.qq.com/{norm}/gp",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))

    stock_data = (payload.get("data") or {}).get(norm, {}) or {}
    klines = stock_data.get("qfqday") or stock_data.get("day") or []
    rows: list[dict[str, Any]] = []
    previous_close: float | None = None
    for line in klines[-limit:]:
        if len(line) < 6:
            continue
        close = safe_float(line[2])
        high = safe_float(line[3])
        low = safe_float(line[4])
        volume = safe_float(line[5])
        pct = None
        diff = None
        amplitude = None
        if previous_close and close is not None:
            diff = round(close - previous_close, 4)
            pct = round(diff / previous_close * 100, 4)
        if previous_close and high is not None and low is not None:
            amplitude = round((high - low) / previous_close * 100, 4)
        estimated_amount = None
        if volume is not None and close is not None:
            # 腾讯日线返回成交量通常为“手”，这里按100股/手估算成交额，供L7流动性过滤兜底。
            estimated_amount = volume * 100 * close
        if close is not None:
            previous_close = close
        rows.append({
            "日期": line[0],
            "开盘": safe_float(line[1]),
            "收盘": close,
            "最高": high,
            "最低": low,
            "成交量": volume,
            "成交额": estimated_amount,
            "成交额是否估算": True,
            "振幅": amplitude,
            "涨跌幅": pct,
            "涨跌额": diff,
            "换手率": None,
        })
    return rows


def calc_metrics(rows: list[dict[str, Any]], period: int) -> dict[str, Any]:
    valid = [row for row in rows if safe_float(row.get("收盘")) is not None and safe_float(row.get("成交额")) is not None]
    latest = valid[-1] if valid else {}
    recent = valid[-period:] if period > 0 else valid
    recent5 = valid[-5:]
    amounts = [safe_float(row.get("成交额")) or 0.0 for row in recent]
    amounts5 = [safe_float(row.get("成交额")) or 0.0 for row in recent5]
    turnovers = [safe_float(row.get("换手率")) for row in recent if safe_float(row.get("换手率")) is not None]
    avg_amount = sum(amounts) / len(amounts) if amounts else None
    avg_amount5 = sum(amounts5) / len(amounts5) if amounts5 else None
    avg_turnover = sum(turnovers) / len(turnovers) if turnovers else None
    pct5 = None
    pct20 = None
    latest_close = safe_float(latest.get("收盘"))
    if latest_close is not None and len(valid) >= 6:
        base5 = safe_float(valid[-6].get("收盘"))
        if base5:
            pct5 = round((latest_close / base5 - 1) * 100, 4)
    if latest_close is not None and len(valid) > period:
        base20 = safe_float(valid[-period - 1].get("收盘"))
        if base20:
            pct20 = round((latest_close / base20 - 1) * 100, 4)
    return {
        "有效交易日": len(valid),
        "交易日期列表": [row.get("日期") for row in valid if row.get("日期")],
        "最新交易日": latest.get("日期"),
        "收盘价": safe_float(latest.get("收盘")),
        "涨跌幅": safe_float(latest.get("涨跌幅")),
        "成交额": safe_float(latest.get("成交额")),
        "换手率": safe_float(latest.get("换手率")),
        "近5日日均成交额": avg_amount5,
        "近20日日均成交额": avg_amount,
        "近20日平均换手率": avg_turnover,
        "近5日涨跌幅": pct5,
        "近20日涨跌幅": pct20,
        "首个交易日": valid[0].get("日期") if valid else None,
    }


def analyze_one(stock: dict[str, Any], begin: str, timeout: int, period: int, retry_count: int, primary_source: str) -> dict[str, Any]:
    code = normalize_code(stock.get("代码") or stock.get("展示代码") or "")
    errors: list[str] = []
    attempts = max(1, retry_count)
    source_order = ["tencent", "eastmoney"] if primary_source == "tencent" else ["eastmoney", "tencent"]
    source_name = {
        "tencent": "腾讯公开复权日线接口",
        "eastmoney": "东方财富公开历史K线接口",
    }

    request_count = 0
    for source in source_order:
        for attempt in range(1, attempts + 1):
            request_count += 1
            try:
                if source == "tencent":
                    rows = fetch_tencent_kline(code, max(period + 5, 30), timeout)
                else:
                    rows = fetch_eastmoney_kline(code, begin, timeout)
                metrics = calc_metrics(rows, period)
                if metrics.get("有效交易日", 0) > 0:
                    return {
                        "代码": code,
                        "展示代码": display_code(code),
                        "名称": stock.get("名称", ""),
                        "指数类型": stock.get("指数类型", ""),
                        "指数代码": stock.get("指数代码", ""),
                        "指数归属": stock.get("指数归属", []),
                        **source_flags(stock),
                        "状态": "成功",
                        "错误": "",
                        "指标": metrics,
                        "K线记录数": len(rows),
                        "请求次数": request_count,
                        "数据源": source_name[source],
                    }
                errors.append(f"{source_name[source]}返回空数据")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{source_name[source]}失败:{exc}")
            if attempt < attempts:
                time.sleep(0.25 * attempt)

    return {
        "代码": code,
        "展示代码": display_code(code),
        "名称": stock.get("名称", ""),
        "指数类型": stock.get("指数类型", ""),
        "指数代码": stock.get("指数代码", ""),
        "指数归属": stock.get("指数归属", []),
        **source_flags(stock),
        "状态": "失败",
        "错误": "；".join(errors),
        "指标": {},
        "K线记录数": 0,
        "请求次数": request_count,
        "数据源": "腾讯公开复权日线接口；东方财富公开历史K线接口",
    }


def count_suspend_days(latest_trade_date: str | None, market_dates: list[str], benchmark: str | None) -> int:
    if not latest_trade_date or not benchmark or latest_trade_date == benchmark:
        return 0
    try:
        return len([item for item in market_dates if latest_trade_date < item <= benchmark])
    except TypeError:
        return 0


def should_exclude(
    item: dict[str, Any],
    rule: dict[str, Any],
    market_dates: list[str],
    benchmark_date: str | None,
) -> tuple[bool, list[str], list[str]]:
    filters = rule.get("过滤规则", {})
    reasons: list[str] = []
    risk_flags: list[str] = []
    code = item.get("代码", "")
    name = str(item.get("名称") or "")
    metrics = item.get("指标", {})

    if filters.get("剔除ST", True) and "ST" in name.upper():
        reasons.append("ST或*ST")

    if item.get("状态") != "成功":
        reasons.append("公开行情数据失败或为空")

    latest_date = metrics.get("最新交易日")
    suspend_days = count_suspend_days(latest_date, market_dates, benchmark_date)
    item["停牌交易日数"] = suspend_days
    if filters.get("剔除当日停牌", True) and benchmark_date and latest_date and latest_date < benchmark_date:
        reasons.append("当日停牌")
    max_suspend_days = safe_int(filters.get("剔除连续停牌大于天数"), 5)
    if suspend_days > max_suspend_days:
        reasons.append(f"连续停牌>{max_suspend_days}个交易日")

    valid_days = safe_int(metrics.get("有效交易日"), 0)
    min_valid_days = safe_int(filters.get("最低有效交易日"), 15)
    if valid_days < min_valid_days:
        reasons.append(f"近20个交易日有效交易日不足{min_valid_days}天")

    close = safe_float(metrics.get("收盘价"))
    min_close = float(filters.get("最低收盘价", 1.0))
    if close is None or close <= 0:
        reasons.append("收盘价为空或为0")
    elif close < min_close:
        reasons.append(f"收盘价低于{min_close:g}元")

    avg_amount = safe_float(metrics.get("近20日日均成交额"))
    min_amount = float(filters.get("最低日均成交额_万元", 3000)) * 10000
    if avg_amount is None:
        reasons.append("近20日日均成交额为空")
    elif avg_amount < min_amount:
        reasons.append(f"近20日日均成交额低于{int(min_amount / 10000)}万元")

    pct = safe_float(metrics.get("涨跌幅"))
    threshold = limit_threshold(code, rule)
    item["涨跌停阈值"] = threshold
    if pct is not None:
        if pct >= threshold:
            risk_flags.append("涨停_强")
        elif pct <= -threshold:
            risk_flags.append("跌停_风险")
    if filters.get("剔除涨跌停", False) and risk_flags:
        reasons.append("涨跌停剔除规则命中")

    return bool(reasons), reasons, risk_flags


def build_report(
    l8_data: dict[str, Any],
    raw_items: list[dict[str, Any]],
    rule: dict[str, Any],
    started_at: datetime,
    args: argparse.Namespace,
) -> dict[str, Any]:
    filters = rule.get("过滤规则", {})
    market_dates = sorted({
        date
        for item in raw_items
        for date in item.get("指标", {}).get("交易日期列表", [])
        if date
    })
    latest_dates = sorted({item.get("指标", {}).get("最新交易日") for item in raw_items if item.get("指标", {}).get("最新交易日")})
    benchmark_date = market_dates[-1] if market_dates else (latest_dates[-1] if latest_dates else None)
    l7_stocks: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    data_errors: list[dict[str, Any]] = []

    for item in raw_items:
        exclude, reasons, risk_flags = should_exclude(item, rule, market_dates, benchmark_date)
        metrics = item.get("指标", {})
        record = {
            "代码": item.get("代码"),
            "展示代码": item.get("展示代码"),
            "名称": item.get("名称"),
            "指数类型": item.get("指数类型"),
            "指数代码": item.get("指数代码"),
            "指数归属": item.get("指数归属", []),
            "sources": item.get("sources", []),
            "是否指数基底": item.get("是否指数基底"),
            "是否战略样本": item.get("是否战略样本"),
            "是否用户增强": item.get("是否用户增强"),
            "来源优先级": item.get("来源优先级"),
            "用户增强权重加成": item.get("用户增强权重加成"),
            "战略入池理由": item.get("战略入池理由"),
            "战略证据来源": item.get("战略证据来源"),
            "复核状态": item.get("复核状态"),
            "行业": item.get("行业"),
            "细分领域": item.get("细分领域"),
            "名单分类": item.get("名单分类"),
            "标签": item.get("标签", []),
            "板块": market_board(item.get("代码", "")),
            "最新交易日": metrics.get("最新交易日"),
            "基准交易日": benchmark_date,
            "停牌交易日数": item.get("停牌交易日数", 0),
            "收盘价": metrics.get("收盘价"),
            "涨跌幅": metrics.get("涨跌幅"),
            "成交额": metrics.get("成交额"),
            "换手率": metrics.get("换手率"),
            "近5日日均成交额": metrics.get("近5日日均成交额"),
            "近20日日均成交额": metrics.get("近20日日均成交额"),
            "近20日平均换手率": metrics.get("近20日平均换手率"),
            "近5日涨跌幅": metrics.get("近5日涨跌幅"),
            "近20日涨跌幅": metrics.get("近20日涨跌幅"),
            "有效交易日": metrics.get("有效交易日", 0),
            "风险标记": risk_flags,
            "数据源": item.get("数据源"),
            "成交额是否估算": item.get("数据源") == "腾讯公开复权日线接口",
            "过滤状态": "剔除" if exclude else "保留",
            "剔除原因": reasons,
        }
        if exclude:
            excluded.append(record)
        else:
            l7_stocks.append(record)
        if item.get("状态") != "成功":
            data_errors.append({
                "代码": item.get("代码"),
                "展示代码": item.get("展示代码"),
                "名称": item.get("名称"),
                "状态": item.get("状态"),
                "错误": item.get("错误"),
            })

    success_count = sum(1 for item in raw_items if item.get("状态") == "成功")
    total = len(raw_items)
    success_rate = round(success_count / total, 4) if total else 0.0
    now = datetime.now()
    return {
        "名称": "L7可交易过滤池",
        "版本": "2026-05-01",
        "定位": "上游候选池经过可交易性过滤后的每日候选基础池。",
        "数据日期": benchmark_date or now.strftime("%Y-%m-%d"),
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "运行参数": {
            "limit": args.limit,
            "offline": False,
        },
        "规则文件": str(module_root() / "01配置" / "L7可交易过滤池规则.json"),
        "上游文件": l8_data.get("输出文件") or l8_data.get("输出文件", {}).get("最新文件") or "",
        "上游类型": l8_data.get("名称", "未知上游候选池"),
        "过滤规则": filters,
        "数据源": {
            "实际使用数据源": rule.get("数据源", {}).get("历史K线"),
            "基准交易日": benchmark_date,
            "请求股票数": total,
            "成功股票数": success_count,
            "失败股票数": len(data_errors),
            "成功率": success_rate,
        },
        "数据健康度": {
            "上游股票数": total,
            "L8股票数": total,
            "L7保留股票数": len(l7_stocks),
            "剔除股票数": len(excluded),
            "行情成功率": success_rate,
            "是否完整": total > 0 and success_rate >= 0.95,
            "完整性说明": "行情成功率>=95%视为完整；失败股票进入剔除记录，不静默通过。",
        },
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写旧系统": False,
            "是否写正式库": False,
        },
        "实际动作": {
            "读取上游候选池": True,
            "读取L8指数基底池": l8_data.get("名称") == "L8指数基底池",
            "读取L8X综合候选池": l8_data.get("名称") == "L8X综合候选池",
            "读取公开历史K线": True,
            "写入03数据": True,
            "写入04日志": True,
            "修改L8源文件": False,
            "触发n8n": False,
            "企业微信真实发送": False,
            "调用券商接口": False,
            "自动交易": False,
            "重启服务": False,
        },
        "耗时秒": round((now - started_at).total_seconds(), 3),
        "股票池": l7_stocks,
        "剔除记录": excluded,
        "数据错误记录": data_errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成L7可交易过滤池")
    parser.add_argument("--limit", type=int, default=0, help="仅处理前N只股票，用于调试；0表示全量。")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started_at = datetime.now()
    root = module_root()
    rule_path = root / "01配置" / "L7可交易过滤池规则.json"
    rule = load_json(rule_path, required=True)
    l8_data, input_path, input_type, is_fallback, fallback_reason = resolve_input_pool(root, rule)
    l8_data["输出文件"] = str(input_path)
    l8_data["L7输入类型"] = input_type
    l8_data["L7是否回退"] = is_fallback
    l8_data["L7回退原因"] = fallback_reason
    stocks = list(l8_data.get("股票池", []))
    if args.limit and args.limit > 0:
        stocks = stocks[: args.limit]

    source_rule = rule.get("数据源", {})
    lookback_days = safe_int(source_rule.get("获取自然日回看天数"), 60)
    workers = max(1, safe_int(source_rule.get("并发线程数"), 10))
    timeout = max(5, safe_int(source_rule.get("请求超时秒"), 20))
    retry_count = max(1, safe_int(source_rule.get("失败重试次数"), 3))
    primary_source = str(source_rule.get("主数据源", "tencent")).lower()
    period = max(1, safe_int(rule.get("过滤规则", {}).get("成交额计算周期"), 20))
    begin = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y%m%d")

    raw_items: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(analyze_one, stock, begin, timeout, period, retry_count, primary_source): stock
            for stock in stocks
        }
        for future in as_completed(future_map):
            raw_items.append(future.result())

    raw_items.sort(key=lambda item: item.get("代码", ""))
    report = build_report(l8_data, raw_items, rule, started_at, args)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = root / "03数据" / "132可交易过滤池"
    output_path = output_dir / f"L7可交易过滤池_{stamp}.json"
    latest_path = output_dir / "L7可交易过滤池_最新.json"
    log_dir = root / "04日志" / "数据源"
    log_path = log_dir / f"L7可交易过滤池数据源日志_{stamp}.json"
    log_latest_path = log_dir / "L7可交易过滤池数据源日志_最新.json"

    write_json(output_path, report)
    write_json(latest_path, report)
    write_json(log_path, {
        "名称": "L7可交易过滤池数据源日志",
        "生成时间": report["生成时间"],
        "数据源": report["数据源"],
        "数据健康度": report["数据健康度"],
        "数据错误记录": report["数据错误记录"][:100],
        "输出文件": str(output_path),
        "最新文件": str(latest_path),
        "安全边界": report["安全边界"],
        "实际动作": report["实际动作"],
    })
    write_json(log_latest_path, load_json(log_path, required=True))

    print(json.dumps({
        "状态": "完成",
        "L8股票数": report["数据健康度"]["L8股票数"],
        "L7保留股票数": report["数据健康度"]["L7保留股票数"],
        "剔除股票数": report["数据健康度"]["剔除股票数"],
        "行情成功率": report["数据健康度"]["行情成功率"],
        "是否完整": report["数据健康度"]["是否完整"],
        "上游类型": input_type,
        "是否回退": is_fallback,
        "输出": str(output_path),
        "最新": str(latest_path),
        "日志": str(log_path),
    }, ensure_ascii=False))
    return 0 if report["数据健康度"]["是否完整"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
