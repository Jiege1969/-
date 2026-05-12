# -*- coding: utf-8 -*-
"""
名称：提取杰哥推荐量价特征.py
作用：基于【杰哥推荐】v3五年基础K线和方法内核，提取强势样本、失败样本与当前候选股的量价结构特征。
触发方式：python 提取杰哥推荐量价特征.py
依赖：03数据/271杰哥推荐基础补足/杰哥推荐候选历史K线增强_最新.json；03数据/270杰哥推荐方法内核/*.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地K线和方法内核，只写03数据/272杰哥推荐量价特征；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不输出买卖指令。
创建修改记录：2026-05-10 创建，用于把【杰哥推荐】从样本/相似度推进到量价规律提取。
标识：jiege-recommendation-price-volume-feature-extraction-v1
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
KLINE_PATH = ROOT / "03数据" / "271杰哥推荐基础补足" / "杰哥推荐候选历史K线增强_最新.json"
KERNEL_DIR = ROOT / "03数据" / "270杰哥推荐方法内核"
SUCCESS_PATH = KERNEL_DIR / "强势成功样本库_最新.json"
FAILURE_PATH = KERNEL_DIR / "失败对照样本库_最新.json"
SIMILARITY_PATH = KERNEL_DIR / "当前候选股相似度识别_最新.json"
OUT_DIR = ROOT / "03数据" / "272杰哥推荐量价特征"


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
        if isinstance(value, float) and math.isnan(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def norm_code(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    if text.startswith(("sh", "sz", "bj")):
        return text[:8]
    if text.startswith(("6", "9")):
        return "sh" + text[:6]
    return "sz" + text[:6]


def code_set(report: dict[str, Any], key: str = "样本") -> set[str]:
    rows = report.get(key, []) if isinstance(report.get(key), list) else []
    return {norm_code(item.get("代码") or item.get("展示代码")) for item in rows if isinstance(item, dict)}


def avg(values: list[float]) -> float | None:
    clean = [safe_float(item) for item in values if item not in (None, "")]
    return round(mean(clean), 4) if clean else None


def pct_return(closes: list[float], days: int) -> float | None:
    if len(closes) <= days:
        return None
    base = closes[-days - 1]
    if not base:
        return None
    return round((closes[-1] / base - 1) * 100, 4)


def simple_ma(values: list[float], days: int) -> float | None:
    if len(values) < days:
        return None
    return round(sum(values[-days:]) / days, 4)


def max_drawdown(closes: list[float], days: int) -> float | None:
    if len(closes) < min(days, 20):
        return None
    window = closes[-days:] if len(closes) >= days else closes
    peak = window[0]
    worst = 0.0
    for value in window:
        peak = max(peak, value)
        if peak:
            worst = min(worst, value / peak - 1)
    return round(worst * 100, 4)


def distance_to_high_low(closes: list[float], days: int) -> dict[str, float | None]:
    if not closes:
        return {"距高点": None, "距低点": None}
    window = closes[-days:] if len(closes) >= days else closes
    high = max(window)
    low = min(window)
    close = closes[-1]
    return {
        "距高点": round((close / high - 1) * 100, 4) if high else None,
        "距低点": round((close / low - 1) * 100, 4) if low else None,
    }


def rolling_volume_burst_days(volumes: list[float], days: int, factor: float) -> int:
    start = max(20, len(volumes) - days)
    count = 0
    for index in range(start, len(volumes)):
        baseline = mean(volumes[index - 20:index]) if index >= 20 else 0
        if baseline and volumes[index] >= baseline * factor:
            count += 1
    return count


def latest_gap(rows: list[dict[str, Any]]) -> float | None:
    if len(rows) < 2:
        return None
    prev_close = safe_float(rows[-2].get("收盘"))
    open_price = safe_float(rows[-1].get("开盘"))
    if not prev_close:
        return None
    return round((open_price / prev_close - 1) * 100, 4)


def gap_count(rows: list[dict[str, Any]], days: int, threshold: float) -> int:
    tail = rows[-days:] if len(rows) >= days else rows
    count = 0
    for index in range(1, len(tail)):
        prev_close = safe_float(tail[index - 1].get("收盘"))
        open_price = safe_float(tail[index].get("开盘"))
        if prev_close and abs((open_price / prev_close - 1) * 100) >= threshold:
            count += 1
    return count


def pattern_tags(feature: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    if feature.get("均线多头排列"):
        tags.append("均线多头")
    if safe_float(feature.get("60日涨跌幅")) >= 50:
        tags.append("60日主升")
    if safe_float(feature.get("120日涨跌幅")) >= 80:
        tags.append("120日趋势延续")
    if safe_float(feature.get("量比5日")) >= 1.1:
        tags.append("温和放量")
    if safe_float(feature.get("量比5日")) >= 2.5:
        tags.append("短期过热放量")
    if safe_float(feature.get("250日最大回撤")) >= -30:
        tags.append("回撤受控")
    if safe_float(feature.get("250日距高点")) >= -8:
        tags.append("接近中期高位")
    if safe_float(feature.get("近60日放量天数")) >= 8:
        tags.append("持续活跃")
    if safe_float(feature.get("20日涨跌幅")) >= 35:
        tags.append("短线过热")
    if feature.get("60日突破"):
        tags.append("突破信号")
    return tags


def extract_feature(row: dict[str, Any], group: str, similarity_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    code = norm_code(row.get("代码") or row.get("展示代码"))
    klines = row.get("历史K线", []) if isinstance(row.get("历史K线"), list) else []
    closes = [safe_float(item.get("收盘")) for item in klines if item.get("收盘") not in (None, "")]
    volumes = [safe_float(item.get("成交量")) for item in klines if item.get("成交量") not in (None, "")]
    amounts = [safe_float(item.get("成交额")) for item in klines if item.get("成交额") not in (None, "")]
    amplitudes = [safe_float(item.get("振幅")) for item in klines if item.get("振幅") not in (None, "")]
    latest_close = closes[-1] if closes else 0.0
    ma20 = simple_ma(closes, 20)
    ma60 = simple_ma(closes, 60)
    ma120 = simple_ma(closes, 120)
    ma250 = simple_ma(closes, 250)
    vol_ma20 = simple_ma(volumes, 20)
    vol_ma60 = simple_ma(volumes, 60)
    amount_ma20 = simple_ma(amounts, 20)
    amount_ma60 = simple_ma(amounts, 60)
    dist250 = distance_to_high_low(closes, 250)
    sim = similarity_map.get(code, {})
    feature = {
        "代码": code,
        "展示代码": row.get("展示代码") or sim.get("展示代码") or code,
        "名称": row.get("名称") or sim.get("名称"),
        "行业": row.get("行业") or sim.get("行业") or "未知",
        "分组": group,
        "数据源": row.get("数据源"),
        "K线数量": len(klines),
        "起始日期": row.get("起始日期"),
        "最新日期": row.get("最新日期"),
        "最新收盘": latest_close,
        "20日涨跌幅": pct_return(closes, 20),
        "60日涨跌幅": pct_return(closes, 60),
        "120日涨跌幅": pct_return(closes, 120),
        "250日涨跌幅": pct_return(closes, 250),
        "全区间涨跌幅": round((closes[-1] / closes[0] - 1) * 100, 4) if len(closes) >= 2 and closes[0] else None,
        "MA20": ma20,
        "MA60": ma60,
        "MA120": ma120,
        "MA250": ma250,
        "均线多头排列": bool(latest_close and ma20 and ma60 and ma120 and ma250 and latest_close > ma20 > ma60 > ma120 > ma250),
        "量比5日": round(volumes[-1] / mean(volumes[-6:-1]), 4) if len(volumes) >= 6 and mean(volumes[-6:-1]) else None,
        "成交量MA20": vol_ma20,
        "成交量MA60": vol_ma60,
        "成交量20_60比": round(vol_ma20 / vol_ma60, 4) if vol_ma20 and vol_ma60 else None,
        "成交额MA20": amount_ma20,
        "成交额MA60": amount_ma60,
        "成交额20_60比": round(amount_ma20 / amount_ma60, 4) if amount_ma20 and amount_ma60 else None,
        "近60日放量天数": rolling_volume_burst_days(volumes, 60, 1.5),
        "近120日放量天数": rolling_volume_burst_days(volumes, 120, 1.5),
        "60日最大回撤": max_drawdown(closes, 60),
        "250日最大回撤": max_drawdown(closes, 250),
        "250日距高点": dist250["距高点"],
        "250日距低点": dist250["距低点"],
        "20日平均振幅": avg(amplitudes[-20:]),
        "60日平均振幅": avg(amplitudes[-60:]),
        "最近跳空缺口": latest_gap(klines),
        "近60日显著缺口次数": gap_count(klines, 60, 3.0),
        "60日突破": bool(closes and len(closes) >= 60 and latest_close >= max(closes[-60:]) * 0.995),
        "杰哥推荐相似度分": sim.get("杰哥推荐相似度分"),
        "识别结论": sim.get("识别结论"),
    }
    feature["量价模式标签"] = pattern_tags(feature)
    return feature


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    numeric_keys = [
        "20日涨跌幅", "60日涨跌幅", "120日涨跌幅", "250日涨跌幅", "全区间涨跌幅",
        "量比5日", "成交量20_60比", "成交额20_60比", "近60日放量天数",
        "60日最大回撤", "250日最大回撤", "250日距高点", "250日距低点",
        "20日平均振幅", "60日平均振幅", "近60日显著缺口次数",
    ]
    summary: dict[str, Any] = {"数量": len(rows)}
    for key in numeric_keys:
        values = [safe_float(row.get(key)) for row in rows if row.get(key) not in (None, "")]
        summary[key] = {
            "均值": round(mean(values), 4) if values else None,
            "中位数": round(median(values), 4) if values else None,
        }
    tag_counter = Counter(tag for row in rows for tag in row.get("量价模式标签", []))
    industry_counter = Counter(str(row.get("行业") or "未知") for row in rows)
    summary["模式标签Top10"] = tag_counter.most_common(10)
    summary["行业Top10"] = industry_counter.most_common(10)
    summary["均线多头比例"] = round(sum(1 for row in rows if row.get("均线多头排列")) / len(rows), 4) if rows else 0
    summary["60日突破比例"] = round(sum(1 for row in rows if row.get("60日突破")) / len(rows), 4) if rows else 0
    return summary


def build_markdown(report: dict[str, Any]) -> str:
    strong = report["分组摘要"]["强势成功样本"]
    failure = report["分组摘要"]["失败对照样本"]
    diff = report["强弱差异"]
    lines = [
        "# 杰哥推荐量价特征提取报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 候选数量：{report['统计']['候选数量']}",
        f"- 强势样本：{report['统计']['强势样本数量']}",
        f"- 失败对照：{report['统计']['失败对照数量']}",
        "",
        "## 一、强势样本画像",
        "",
        f"- 模式标签Top10：{strong['模式标签Top10']}",
        f"- 行业Top10：{strong['行业Top10']}",
        f"- 均线多头比例：{strong['均线多头比例']}",
        f"- 60日突破比例：{strong['60日突破比例']}",
        "",
        "## 二、失败样本画像",
        "",
        f"- 模式标签Top10：{failure['模式标签Top10']}",
        f"- 行业Top10：{failure['行业Top10']}",
        f"- 均线多头比例：{failure['均线多头比例']}",
        f"- 60日突破比例：{failure['60日突破比例']}",
        "",
        "## 三、强弱差异",
        "",
    ]
    for key, value in diff.items():
        lines.append(f"- {key}：强势均值 {value['强势均值']}；失败均值 {value['失败均值']}；差值 {value['差值']}")
    lines.extend([
        "",
        "## 四、安全边界",
        "",
    ])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    success_report = load_json(SUCCESS_PATH, {})
    failure_report = load_json(FAILURE_PATH, {})
    similarity_report = load_json(SIMILARITY_PATH, {})
    kline_report = load_json(KLINE_PATH, {})
    success_codes = code_set(success_report)
    failure_codes = code_set(failure_report)
    similarity_rows = similarity_report.get("候选", []) if isinstance(similarity_report.get("候选"), list) else []
    similarity_map = {norm_code(row.get("代码") or row.get("展示代码")): row for row in similarity_rows if isinstance(row, dict)}
    stocks = kline_report.get("股票", []) if isinstance(kline_report.get("股票"), list) else []
    all_features: list[dict[str, Any]] = []
    strong_features: list[dict[str, Any]] = []
    failure_features: list[dict[str, Any]] = []
    for row in stocks:
        if not isinstance(row, dict):
            continue
        code = norm_code(row.get("代码") or row.get("展示代码"))
        group = "当前候选"
        if code in success_codes:
            group = "强势成功样本"
        elif code in failure_codes:
            group = "失败对照样本"
        feature = extract_feature(row, group, similarity_map)
        all_features.append(feature)
        if group == "强势成功样本":
            strong_features.append(feature)
        elif group == "失败对照样本":
            failure_features.append(feature)
    strong_summary = summarize(strong_features)
    failure_summary = summarize(failure_features)
    diff_keys = ["60日涨跌幅", "120日涨跌幅", "250日涨跌幅", "量比5日", "成交额20_60比", "近60日放量天数", "250日最大回撤", "250日距高点", "60日平均振幅"]
    diff: dict[str, dict[str, float | None]] = {}
    for key in diff_keys:
        strong_avg = strong_summary.get(key, {}).get("均值")
        failure_avg = failure_summary.get(key, {}).get("均值")
        diff[key] = {
            "强势均值": strong_avg,
            "失败均值": failure_avg,
            "差值": round(safe_float(strong_avg) - safe_float(failure_avg), 4) if strong_avg is not None and failure_avg is not None else None,
        }
    report = {
        "名称": "杰哥推荐量价特征提取报告",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "输入": {
            "历史K线": str(KLINE_PATH),
            "强势成功样本": str(SUCCESS_PATH),
            "失败对照样本": str(FAILURE_PATH),
            "当前候选相似度": str(SIMILARITY_PATH),
        },
        "统计": {
            "候选数量": len(all_features),
            "强势样本数量": len(strong_features),
            "失败对照数量": len(failure_features),
        },
        "分组摘要": {
            "强势成功样本": strong_summary,
            "失败对照样本": failure_summary,
            "全候选": summarize(all_features),
        },
        "强弱差异": diff,
        "安全边界": safety_boundary(),
    }
    write_json(OUT_DIR / f"全候选量价特征_{stamp}.json", all_features)
    write_json(OUT_DIR / "全候选量价特征_最新.json", all_features)
    write_json(OUT_DIR / f"强势成功样本量价特征_{stamp}.json", strong_features)
    write_json(OUT_DIR / "强势成功样本量价特征_最新.json", strong_features)
    write_json(OUT_DIR / f"失败对照样本量价特征_{stamp}.json", failure_features)
    write_json(OUT_DIR / "失败对照样本量价特征_最新.json", failure_features)
    write_json(OUT_DIR / f"杰哥推荐量价特征提取报告_{stamp}.json", report)
    write_json(OUT_DIR / "杰哥推荐量价特征提取报告_最新.json", report)
    write_text(OUT_DIR / f"杰哥推荐量价特征提取报告_{stamp}.md", build_markdown(report))
    write_text(OUT_DIR / "杰哥推荐量价特征提取报告_最新.md", build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "候选数量": len(all_features),
        "强势样本数量": len(strong_features),
        "失败对照数量": len(failure_features),
        "输出目录": str(OUT_DIR),
        "安全边界": safety_boundary(),
    }, ensure_ascii=False))
    return 0 if len(strong_features) >= 100 and len(failure_features) >= 100 else 1


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
