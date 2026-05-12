# -*- coding: utf-8 -*-
"""
名称：生成300只候选历史K线与技术指标.py
作用：为300只试运行池盘后轻扫描进入深度预处理的候选补齐历史K线和技术指标。
触发方式：python 生成300只候选历史K线与技术指标.py
依赖：Python标准库；300只候选历史K线技术指标规则.json；300只盘后深度分析预处理包_最新.json；东方财富公开历史K线接口；腾讯公开历史K线接口。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读公开行情；只写新系统股票模块03数据/94候选历史K线技术指标；不写旧系统；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选历史K线和技术指标脚本。
标识：stock-trial-pool-300-candidate-kline-indicator
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def to_float(value: Any) -> float | None:
    try:
        if value in ("", "-", None):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def to_sec_id(code: str) -> str:
    code = str(code or "").strip().lower()
    if code.startswith("sh"):
        return "1." + code[2:]
    if code.startswith("sz"):
        return "0." + code[2:]
    if code.startswith(("6", "9")):
        return "1." + code
    return "0." + code


def fetch_eastmoney_kline(code: str) -> dict[str, Any]:
    params = {
        "secid": to_sec_id(code),
        "klt": "101",
        "fqt": "1",
        "beg": "0",
        "end": "20500101",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
    }
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_tencent_kline(code: str, limit: int) -> dict[str, Any]:
    params = {"param": f"{code.lower()},day,,,{max(limit, 160)},qfq"}
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": f"https://gu.qq.com/{code.lower()}/gp",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_eastmoney_rows(raw: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    klines = raw.get("data", {}).get("klines", []) or []
    for line in klines[-limit:]:
        parts = line.split(",")
        if len(parts) < 11:
            continue
        rows.append({
            "日期": parts[0],
            "开盘": to_float(parts[1]),
            "收盘": to_float(parts[2]),
            "最高": to_float(parts[3]),
            "最低": to_float(parts[4]),
            "成交量": to_float(parts[5]),
            "成交额": to_float(parts[6]),
            "振幅": to_float(parts[7]),
            "涨跌幅": to_float(parts[8]),
            "涨跌额": to_float(parts[9]),
            "换手率": to_float(parts[10]),
        })
    return rows


def parse_tencent_rows(raw: dict[str, Any], code: str, limit: int) -> list[dict[str, Any]]:
    stock_data = (raw.get("data", {}) or {}).get(code.lower(), {}) or {}
    klines = stock_data.get("qfqday") or stock_data.get("day") or []
    rows: list[dict[str, Any]] = []
    previous_close = None
    for line in klines[-limit:]:
        if len(line) < 6:
            continue
        open_price = to_float(line[1])
        close_price = to_float(line[2])
        high_price = to_float(line[3])
        low_price = to_float(line[4])
        volume = to_float(line[5])
        pct = None
        diff = None
        amplitude = None
        if previous_close and close_price is not None:
            diff = round(close_price - previous_close, 4)
            pct = round(diff / previous_close * 100, 4)
        if previous_close and high_price is not None and low_price is not None:
            amplitude = round((high_price - low_price) / previous_close * 100, 4)
        if close_price is not None:
            previous_close = close_price
        rows.append({
            "日期": line[0],
            "开盘": open_price,
            "收盘": close_price,
            "最高": high_price,
            "最低": low_price,
            "成交量": volume,
            "成交额": None,
            "振幅": amplitude,
            "涨跌幅": pct,
            "涨跌额": diff,
            "换手率": None,
        })
    return rows


def fetch_kline_multi_source(code: str, limit: int) -> tuple[list[dict[str, Any]], str, str]:
    errors: list[str] = []
    try:
        raw = fetch_eastmoney_kline(code)
        rows = parse_eastmoney_rows(raw, limit)
        if rows:
            return rows, "东方财富历史K线", ""
        errors.append("东方财富返回空数据")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"东方财富失败：{exc}")
    try:
        raw = fetch_tencent_kline(code, limit)
        rows = parse_tencent_rows(raw, code, limit)
        if rows:
            return rows, "腾讯历史K线", "；".join(errors)
        errors.append("腾讯返回空数据")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"腾讯失败：{exc}")
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


def calc_rsi(closes: list[float], period: int) -> float | None:
    if len(closes) <= period:
        return None
    gains = []
    losses = []
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


def calc_macd(closes: list[float], fast: int, slow: int, signal: int) -> dict[str, float | None]:
    if len(closes) < slow + signal:
        return {"DIF": None, "DEA": None, "MACD": None}
    ema_fast = ema_series(closes, fast)
    ema_slow = ema_series(closes, slow)
    dif = [fast_value - slow_value for fast_value, slow_value in zip(ema_fast, ema_slow)]
    dea = ema_series(dif, signal)
    return {
        "DIF": round(dif[-1], 4),
        "DEA": round(dea[-1], 4),
        "MACD": round((dif[-1] - dea[-1]) * 2, 4),
    }


def build_observation(latest: dict[str, Any], ma_values: dict[str, float | None], macd: dict[str, float | None], volume_ratio: float | None) -> list[str]:
    notes = []
    close = latest.get("收盘")
    ma20 = ma_values.get("MA20")
    ma60 = ma_values.get("MA60")
    if close is not None and ma20 is not None:
        notes.append("收盘价站上MA20" if close > ma20 else "收盘价低于MA20")
    if close is not None and ma60 is not None:
        notes.append("收盘价站上MA60" if close > ma60 else "收盘价低于MA60")
    if macd.get("DIF") is not None and macd.get("DEA") is not None:
        notes.append("MACD偏强" if macd["DIF"] > macd["DEA"] else "MACD偏弱")
    if volume_ratio is not None:
        notes.append("量能活跃" if volume_ratio >= 1.1 else "量能一般")
    return notes or ["指标不足，待补充历史数据。"]


def calc_indicator(item: dict[str, Any], rules: dict[str, Any], minimum: int) -> dict[str, Any]:
    rows = item.get("K线", [])
    closes = [float(row["收盘"]) for row in rows if row.get("收盘") is not None]
    volumes = [float(row["成交量"]) for row in rows if row.get("成交量") is not None]
    ma_periods = rules.get("指标参数", {}).get("MA", [5, 10, 20, 60])
    macd_rule = rules.get("指标参数", {}).get("MACD", {"快线": 12, "慢线": 26, "信号线": 9})
    latest_row = rows[-1] if rows else {}
    ma_values = {f"MA{period}": sma(closes, int(period)) for period in ma_periods}
    volume_ma_period = int(rules.get("指标参数", {}).get("成交量MA", 20))
    volume_ratio_period = int(rules.get("指标参数", {}).get("量比周期", 5))
    volume_ma = sma(volumes, volume_ma_period)
    volume_ratio = None
    if volumes and len(volumes) >= volume_ratio_period:
        base = sum(volumes[-volume_ratio_period:]) / volume_ratio_period
        volume_ratio = round(volumes[-1] / base, 4) if base else None
    macd = calc_macd(closes, int(macd_rule.get("快线", 12)), int(macd_rule.get("慢线", 26)), int(macd_rule.get("信号线", 9)))
    status = "成功" if len(rows) >= minimum and closes else "K线不足"
    return {
        "代码": item.get("代码"),
        "名称": item.get("名称"),
        "状态": status,
        "K线数量": len(rows),
        "最新日期": latest_row.get("日期"),
        "最新收盘": latest_row.get("收盘"),
        "均线": ma_values,
        "RSI14": calc_rsi(closes, int(rules.get("指标参数", {}).get("RSI", 14))),
        "MACD": macd,
        "成交量MA20": volume_ma,
        "量比5日": volume_ratio,
        "技术观察": build_observation(latest_row, ma_values, macd, volume_ratio),
    }


def build_markdown(report: dict[str, Any], indicator_report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选历史K线与技术指标报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结果概览",
        "",
        f"- 候选数量：{report['候选数量']}",
        f"- 历史K线成功数量：{report['成功数量']}",
        f"- 技术指标成功数量：{indicator_report['成功数量']}",
        "- 安全边界：不触发n8n，不发送企业微信，不写正式库，不调用券商接口，不自动交易。",
        "",
        "## 候选摘要",
        "",
    ]
    indicators = {item["代码"]: item for item in indicator_report.get("技术指标", [])}
    for index, item in enumerate(report.get("历史K线", []), start=1):
        indicator = indicators.get(item.get("代码"), {})
        notes = "；".join(indicator.get("技术观察", []))
        lines.append(
            f"{index}. {item.get('名称')}（{item.get('代码')}）："
            f"K线{item.get('状态')}，记录{item.get('记录数')}条，"
            f"指标{indicator.get('状态', '未计算')}，观察：{notes}"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    rules = load_json(root / "01配置" / "300只候选历史K线技术指标规则.json")
    preprocess_path = root / rules["输入"]["深度预处理包"]
    preprocess = load_json(preprocess_path)
    candidates = preprocess.get(rules["输入"].get("候选字段", "预处理候选"), [])
    limit = int(rules.get("历史K线", {}).get("目标交易日数量", 160))
    minimum = int(rules.get("历史K线", {}).get("最低可计算数量", 80))

    history_rows = []
    for candidate in candidates:
        code = candidate.get("代码", "")
        try:
            rows, source, source_warning = fetch_kline_multi_source(code, limit)
            status = "成功" if len(rows) >= minimum else ("K线不足" if rows else "无数据")
            error = source_warning if rows else source_warning or "多源均无数据"
        except Exception as exc:  # noqa: BLE001
            rows = []
            source = ""
            status = "失败"
            error = str(exc)
        history_rows.append({
            "代码": code,
            "名称": candidate.get("名称", ""),
            "市场": candidate.get("市场", ""),
            "行业": candidate.get("行业", ""),
            "轻扫描评分": candidate.get("轻扫描评分"),
            "状态": status,
            "数据源": source,
            "错误": error,
            "记录数": len(rows),
            "K线": rows,
        })

    history_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(root / "01配置" / "300只候选历史K线技术指标规则.json"),
        "深度预处理包": str(preprocess_path),
        "数据源": "东方财富公开历史K线接口；腾讯公开历史K线接口",
        "候选数量": len(candidates),
        "成功数量": sum(1 for item in history_rows if item["状态"] == "成功"),
        "历史K线": history_rows,
        "安全边界": {
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写正式库": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否重启服务": False,
        },
    }
    indicator_rows = [calc_indicator(item, rules, minimum) for item in history_rows]
    indicator_report = {
        "生成时间": history_report["生成时间"],
        "历史K线快照": "",
        "候选数量": len(indicator_rows),
        "成功数量": sum(1 for item in indicator_rows if item["状态"] == "成功"),
        "技术指标": indicator_rows,
        "安全边界": {
            "是否联网": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写正式库": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否重启服务": False,
        },
    }

    output_dir = root / rules["输出"]["数据目录"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    history_output = output_dir / f"300只候选历史K线_{timestamp}.json"
    history_latest = output_dir / rules["输出"]["历史K线最新文件"]
    indicator_output = output_dir / f"300只候选技术指标_{timestamp}.json"
    indicator_latest = output_dir / rules["输出"]["技术指标最新文件"]
    report_output = output_dir / f"300只候选历史K线技术指标报告_{timestamp}.md"
    report_latest = output_dir / rules["输出"]["报告最新文件"]
    indicator_report["历史K线快照"] = str(history_output)

    write_json(history_output, history_report)
    write_json(history_latest, history_report)
    write_json(indicator_output, indicator_report)
    write_json(indicator_latest, indicator_report)
    markdown = build_markdown(history_report, indicator_report)
    report_output.write_text(markdown, encoding="utf-8")
    report_latest.write_text(markdown, encoding="utf-8")

    print(json.dumps({
        "候选数量": len(candidates),
        "历史K线成功数量": history_report["成功数量"],
        "技术指标成功数量": indicator_report["成功数量"],
        "输出": str(history_output),
    }, ensure_ascii=False))
    return 0 if indicator_report["成功数量"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
