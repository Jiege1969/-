# -*- coding: utf-8 -*-
"""
名称：计算重点关注池技术指标.py
作用：读取重点关注池历史K线快照，计算MA、RSI、MACD、成交量MA等技术指标。
触发方式：python 计算重点关注池技术指标.py
依赖：Python标准库；技术指标计算规则.json；重点关注池历史K线快照_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读新系统历史K线快照；只写新系统股票模块03数据/12技术指标；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建重点关注池技术指标计算脚本。
标识：stock-focus-technical-indicator-calc
"""

from __future__ import annotations

import json
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
    recent_gains = gains[-period:]
    recent_losses = losses[-period:]
    avg_gain = sum(recent_gains) / period
    avg_loss = sum(recent_losses) / period
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
        "MACD": round((dif[-1] - dea[-1]) * 2, 4)
    }


def calc_item(item: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    rows = item.get("K线", [])
    closes = [float(row["收盘"]) for row in rows if row.get("收盘") is not None]
    volumes = [float(row["成交量"]) for row in rows if row.get("成交量") is not None]
    ma_periods = rules.get("指标参数", {}).get("MA", [5, 10, 20, 60])
    macd_rule = rules.get("指标参数", {}).get("MACD", {"快线": 12, "慢线": 26, "信号线": 9})
    latest_row = rows[-1] if rows else {}
    ma_values = {f"MA{period}": sma(closes, int(period)) for period in ma_periods}
    volume_ma_period = int(rules.get("指标参数", {}).get("成交量MA", 20))
    volume_ma = sma(volumes, volume_ma_period)
    last_volume = volumes[-1] if volumes else None
    volume_ratio = None
    if last_volume is not None and len(volumes) >= 5:
        base = sum(volumes[-5:]) / 5
        volume_ratio = round(last_volume / base, 4) if base else None
    macd = calc_macd(closes, int(macd_rule.get("快线", 12)), int(macd_rule.get("慢线", 26)), int(macd_rule.get("信号线", 9)))
    return {
        "代码": item.get("代码"),
        "名称": item.get("名称"),
        "状态": "成功" if closes else "无可计算数据",
        "K线数量": len(rows),
        "最新日期": latest_row.get("日期"),
        "最新收盘": latest_row.get("收盘"),
        "均线": ma_values,
        "RSI14": calc_rsi(closes, int(rules.get("指标参数", {}).get("RSI", 14))),
        "MACD": macd,
        "成交量MA20": volume_ma,
        "量比5日": volume_ratio,
        "技术观察": build_observation(latest_row, ma_values, macd, volume_ratio)
    }


def build_observation(latest: dict[str, Any], ma_values: dict[str, float | None], macd: dict[str, float | None], volume_ratio: float | None) -> list[str]:
    notes = []
    close = latest.get("收盘")
    ma60 = ma_values.get("MA60")
    if close is not None and ma60 is not None:
        notes.append("收盘价站上MA60" if close > ma60 else "收盘价低于MA60")
    if macd.get("DIF") is not None and macd.get("DEA") is not None:
        notes.append("MACD偏强" if macd["DIF"] > macd["DEA"] else "MACD偏弱")
    if volume_ratio is not None:
        notes.append("量能活跃" if volume_ratio >= 1.1 else "量能一般")
    return notes or ["指标不足，待补充历史数据。"]


def main() -> int:
    root = module_root()
    rules = load_json(root / "01配置" / "技术指标计算规则.json")
    history_path = root / rules.get("输出路径", {}).get("历史K线", "03数据/11历史行情") / "重点关注池历史K线快照_最新.json"
    history = load_json(history_path)
    results = [calc_item(item, rules) for item in history.get("历史K线", [])]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "历史K线快照": str(history_path),
        "股票数量": len(results),
        "成功数量": sum(1 for item in results if item["状态"] == "成功"),
        "技术指标": results,
        "安全边界": {
            "是否联网": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False
        }
    }
    output_dir = root / rules.get("输出路径", {}).get("技术指标", "03数据/12技术指标")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"重点关注池技术指标_{timestamp}.json"
    latest = output_dir / "重点关注池技术指标_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"股票数量": len(results), "成功数量": report["成功数量"], "输出": str(output)}, ensure_ascii=False))
    return 0 if report["成功数量"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
