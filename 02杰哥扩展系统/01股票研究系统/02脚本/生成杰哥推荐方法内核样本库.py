# -*- coding: utf-8 -*-
"""
名称：生成杰哥推荐方法内核样本库.py
作用：生成【杰哥推荐】方法内核的强势成功样本库、失败对照样本库和当前候选股相似度识别结果。
触发方式：python 生成杰哥推荐方法内核样本库.py
依赖：杰哥推荐方法内核规则.json；2000只样本股票池；2000只样本池盘后影子轻扫描；L8X综合候选池；现有技术指标/K线快照。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地股票数据，只写03数据/270杰哥推荐方法内核；不触发n8n；不发送企业微信；不接券商；不自动交易；不输出买卖指令。
创建修改记录：2026-05-10 创建v1本地样本影子版方法内核。
标识：jiege-recommendation-method-kernel-v1
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
RULE_PATH = ROOT / "01配置" / "杰哥推荐方法内核规则.json"


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


def rel(path_text: str) -> Path:
    return ROOT / path_text.replace("/", "\\")


def norm_code(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    if text.startswith(("sh", "sz", "bj")):
        return text
    if text.startswith(("6", "9")):
        return "sh" + text[:6]
    return "sz" + text[:6]


def code_key(item: dict[str, Any]) -> str:
    return norm_code(item.get("代码") or item.get("展示代码"))


def percentile_rank(values: list[float], value: float) -> float:
    if not values:
        return 0.0
    below = sum(1 for item in values if item <= value)
    return round(below / len(values), 6)


def log_scale(value: float) -> float:
    return math.log10(max(value, 0.0) + 1.0)


def load_rows(data: Any, keys: list[str]) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        return []
    for key in keys:
        rows = data.get(key)
        if isinstance(rows, list):
            return [item for item in rows if isinstance(item, dict)]
    return []


def build_indicator_maps(indicator_rows: list[dict[str, Any]], candidate_indicator_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for row in [*indicator_rows, *candidate_indicator_rows]:
        key = code_key(row)
        if key:
            output[key] = row
    return output


def build_kline_map(history_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = {}
    for row in history_rows:
        key = code_key(row)
        klines = row.get("K线")
        if key and isinstance(klines, list):
            output[key] = [item for item in klines if isinstance(item, dict)]
    return output


def sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return round(sum(values[-period:]) / period, 4)


def calc_kdj(klines: list[dict[str, Any]], period: int = 9) -> dict[str, float | None]:
    if len(klines) < period:
        return {"K": None, "D": None, "J": None}
    k = 50.0
    d = 50.0
    for index in range(period - 1, len(klines)):
        window = klines[index - period + 1:index + 1]
        high = max(safe_float(row.get("最高")) for row in window)
        low = min(safe_float(row.get("最低")) for row in window)
        close = safe_float(klines[index].get("收盘"))
        rsv = 50.0 if high == low else (close - low) / (high - low) * 100
        k = (2 / 3) * k + (1 / 3) * rsv
        d = (2 / 3) * d + (1 / 3) * k
    j = 3 * k - 2 * d
    return {"K": round(k, 4), "D": round(d, 4), "J": round(j, 4)}


def calc_boll(closes: list[float], period: int = 20) -> dict[str, float | None]:
    if len(closes) < period:
        return {"中轨": None, "上轨": None, "下轨": None, "位置": None}
    window = closes[-period:]
    mid = mean(window)
    variance = sum((item - mid) ** 2 for item in window) / period
    std = math.sqrt(variance)
    upper = mid + 2 * std
    lower = mid - 2 * std
    close = closes[-1]
    position = None if upper == lower else (close - lower) / (upper - lower)
    return {"中轨": round(mid, 4), "上轨": round(upper, 4), "下轨": round(lower, 4), "位置": round(position, 4) if position is not None else None}


def calc_atr_pct(klines: list[dict[str, Any]], period: int = 14) -> float | None:
    if len(klines) <= period:
        return None
    true_ranges: list[float] = []
    previous_close = safe_float(klines[0].get("收盘"))
    for row in klines[1:]:
        high = safe_float(row.get("最高"))
        low = safe_float(row.get("最低"))
        close = safe_float(row.get("收盘"))
        true_ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
        previous_close = close
    close = safe_float(klines[-1].get("收盘"))
    if close <= 0:
        return None
    return round(mean(true_ranges[-period:]) / close * 100, 4)


def pct_return(closes: list[float], period: int) -> float | None:
    if len(closes) <= period or closes[-period - 1] == 0:
        return None
    return round((closes[-1] / closes[-period - 1] - 1) * 100, 4)


def max_drawdown(closes: list[float], period: int) -> float | None:
    if len(closes) < period:
        return None
    window = closes[-period:]
    peak = max(window)
    if peak <= 0:
        return None
    return round((min(window) / peak - 1) * 100, 4)


def latest_gap_pct(klines: list[dict[str, Any]]) -> float | None:
    if len(klines) < 2:
        return None
    previous_close = safe_float(klines[-2].get("收盘"))
    latest_open = safe_float(klines[-1].get("开盘"))
    if previous_close <= 0:
        return None
    return round((latest_open / previous_close - 1) * 100, 4)


def enhanced_technical_features(klines: list[dict[str, Any]]) -> dict[str, Any]:
    closes = [safe_float(row.get("收盘")) for row in klines if row.get("收盘") is not None]
    if len(closes) < 20:
        return {"状态": "历史K线不足"}
    highs = [safe_float(row.get("最高")) for row in klines if row.get("最高") is not None]
    latest_close = closes[-1]
    high_60 = max(highs[-60:]) if len(highs) >= 60 else max(highs)
    return {
        "状态": "已计算",
        "KDJ": calc_kdj(klines),
        "BOLL": calc_boll(closes),
        "ATR14波动率": calc_atr_pct(klines),
        "20日涨跌幅": pct_return(closes, 20),
        "60日涨跌幅": pct_return(closes, 60),
        "120日涨跌幅": pct_return(closes, 120),
        "60日最大回撤": max_drawdown(closes, 60),
        "60日突破": bool(len(highs) >= 60 and latest_close >= high_60 * 0.995),
        "最近跳空缺口": latest_gap_pct(klines),
        "换手率可用": any(row.get("换手率") is not None for row in klines[-20:]),
        "振幅可用": any(row.get("振幅") is not None for row in klines[-20:]),
    }


def merge_feature_row(
    item: dict[str, Any],
    pool_map: dict[str, dict[str, Any]],
    indicator_map: dict[str, dict[str, Any]],
    kline_map: dict[str, list[dict[str, Any]]],
    score_values: list[float],
    turnover_values: list[float],
    amount_values: list[float],
    industry_score: dict[str, float],
) -> dict[str, Any]:
    key = code_key(item)
    pool_item = pool_map.get(key, {})
    indicator = indicator_map.get(key, {})
    klines = kline_map.get(key, [])
    industry = str(item.get("行业") or pool_item.get("行业") or indicator.get("行业") or "").strip()
    amount = safe_float(item.get("最新成交额") or pool_item.get("最新成交额"))
    market_value = safe_float(item.get("市值") or pool_item.get("市值"))
    turnover_proxy = safe_float(item.get("成交额市值比"))
    if turnover_proxy <= 0 and amount > 0 and market_value > 0:
        turnover_proxy = amount / market_value
    score = safe_float(item.get("影子评分"))
    index_weight = safe_float(item.get("中证全指权重") or pool_item.get("中证全指权重"))
    ma = indicator.get("均线") if isinstance(indicator.get("均线"), dict) else {}
    macd = indicator.get("MACD") if isinstance(indicator.get("MACD"), dict) else {}
    latest_close = safe_float(indicator.get("最新收盘"))
    ma20 = safe_float(ma.get("MA20"))
    ma60 = safe_float(ma.get("MA60"))
    volume_ratio = safe_float(indicator.get("量比5日"))
    enhanced = enhanced_technical_features(klines)
    vector = {
        "影子评分分位": percentile_rank(score_values, score),
        "成交额市值比分位": percentile_rank(turnover_values, turnover_proxy),
        "成交额分位": percentile_rank(amount_values, amount),
        "市值log": log_scale(market_value),
        "指数权重": index_weight,
        "行业热度": industry_score.get(industry, 0.0),
        "站上MA20": 1.0 if latest_close and ma20 and latest_close > ma20 else 0.0,
        "站上MA60": 1.0 if latest_close and ma60 and latest_close > ma60 else 0.0,
        "RSI14归一": min(max(safe_float(indicator.get("RSI14")) / 100, 0), 1),
        "MACD强度": 1.0 if safe_float(macd.get("DIF")) > safe_float(macd.get("DEA")) else 0.0,
        "量比归一": min(volume_ratio / 3, 1.0) if volume_ratio else 0.0,
    }
    if enhanced.get("状态") == "已计算":
        vector["60日涨跌幅归一"] = min(max((safe_float(enhanced.get("60日涨跌幅")) + 30) / 80, 0), 1)
        vector["60日突破"] = 1.0 if enhanced.get("60日突破") else 0.0
        vector["BOLL位置"] = min(max(safe_float((enhanced.get("BOLL") or {}).get("位置")), 0), 1)
        vector["ATR适中"] = 1.0 if 1.0 <= safe_float(enhanced.get("ATR14波动率")) <= 8.0 else 0.0
    else:
        vector["60日涨跌幅归一"] = 0.0
        vector["60日突破"] = 0.0
        vector["BOLL位置"] = 0.0
        vector["ATR适中"] = 0.0
    return {
        "代码": key,
        "展示代码": item.get("展示代码") or pool_item.get("展示代码") or key,
        "名称": item.get("名称") or pool_item.get("名称") or indicator.get("名称"),
        "行业": industry or "未知",
        "影子评分": score,
        "最新成交额": amount,
        "市值": market_value,
        "成交额市值比": round(turnover_proxy, 6),
        "中证全指权重": index_weight,
        "基础技术指标": {
            "MA": ma,
            "RSI14": indicator.get("RSI14"),
            "MACD": macd,
            "成交量MA20": indicator.get("成交量MA20"),
            "量比5日": indicator.get("量比5日"),
            "技术观察": indicator.get("技术观察", []),
        },
        "补充派生指标": enhanced,
        "特征向量": vector,
    }


def centroid(rows: list[dict[str, Any]]) -> dict[str, float]:
    vectors = [row.get("特征向量", {}) for row in rows]
    keys = sorted({key for vector in vectors for key in vector.keys()})
    result: dict[str, float] = {}
    for key in keys:
        values = [safe_float(vector.get(key)) for vector in vectors]
        result[key] = mean(values) if values else 0.0
    return result


def similarity(vector: dict[str, Any], center: dict[str, float]) -> float:
    keys = sorted(set(vector.keys()) | set(center.keys()))
    if not keys:
        return 0.0
    distance = math.sqrt(sum((safe_float(vector.get(key)) - safe_float(center.get(key))) ** 2 for key in keys) / len(keys))
    return round(max(0.0, 1.0 - distance) * 100, 2)


def build_observation_conditions(row: dict[str, Any], success_score: float, failure_score: float) -> list[str]:
    conditions: list[str] = []
    vector = row.get("特征向量", {})
    if safe_float(vector.get("成交额市值比分位")) < 0.65:
        conditions.append("成交额市值比需继续提升，优先看后续量能是否放大。")
    if safe_float(vector.get("站上MA20")) < 1:
        conditions.append("价格需重新站上MA20后再提高观察优先级。")
    if safe_float(vector.get("MACD强度")) < 1:
        conditions.append("MACD需由弱转强，避免只靠单日波动判断。")
    if success_score <= failure_score:
        conditions.append("当前更接近失败对照组，暂不进入【杰哥推荐】重点关注。")
    if not conditions:
        conditions.append("维持成交活跃度，确认行业热度和价格结构没有快速转弱。")
    return conditions


def markdown_table(title: str, rows: list[dict[str, Any]], score_key: str = "方法内核强度分") -> str:
    lines = [
        f"# {title}",
        "",
        "| 排名 | 股票 | 行业 | 分数/相似度 | 核心判断 |",
        "| ---: | --- | --- | ---: | --- |",
    ]
    for index, row in enumerate(rows[:30], start=1):
        stock = f"{row.get('名称')}({row.get('展示代码') or row.get('代码')})"
        score = row.get(score_key, row.get("强势相似度", row.get("失败相似度", "")))
        judgement = row.get("样本标签") or row.get("识别结论") or row.get("入库理由", "")
        lines.append(f"| {index} | {stock} | {row.get('行业')} | {score} | {judgement} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    rules = load_json(RULE_PATH, {})
    input_rules = rules.get("输入", {})
    output_rules = rules.get("输出", {})
    out_dir = rel(output_rules.get("目录", "03数据/270杰哥推荐方法内核"))
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    pool_data = load_json(rel(input_rules["2000只样本池"]), {})
    scan_data = load_json(rel(input_rules["2000只影子扫描"]), {})
    l8x_data = load_json(rel(input_rules["L8X综合候选池"]), {})
    focus_indicator_data = load_json(rel(input_rules["重点关注池技术指标"]), {})
    candidate_history_data = load_json(rel(input_rules["300只候选历史K线"]), {})
    candidate_indicator_data = load_json(rel(input_rules["300只候选技术指标"]), {})

    pool_rows = load_rows(pool_data, ["股票列表", "股票池"])
    scan_rows = load_rows(scan_data, ["股票"])
    l8x_rows = load_rows(l8x_data, ["股票池"])
    focus_indicators = load_rows(focus_indicator_data, ["技术指标"])
    candidate_indicators = load_rows(candidate_indicator_data, ["技术指标"])
    history_rows = load_rows(candidate_history_data, ["历史K线"])

    pool_map = {code_key(row): row for row in pool_rows if code_key(row)}
    scan_map = {code_key(row): row for row in scan_rows if code_key(row)}
    indicator_map = build_indicator_maps(focus_indicators, candidate_indicators)
    kline_map = build_kline_map(history_rows)

    score_values = [safe_float(row.get("影子评分")) for row in scan_rows]
    turnover_values = [safe_float(row.get("成交额市值比")) for row in scan_rows]
    amount_values = [safe_float(row.get("最新成交额")) for row in scan_rows]
    industry_groups: dict[str, list[float]] = {}
    for row in scan_rows:
        industry = str(row.get("行业") or "未知")
        industry_groups.setdefault(industry, []).append(safe_float(row.get("影子评分")))
    industry_score = {key: percentile_rank([mean(vals) for vals in industry_groups.values()], mean(vals)) for key, vals in industry_groups.items()}

    feature_rows = [
        merge_feature_row(row, pool_map, indicator_map, kline_map, score_values, turnover_values, amount_values, industry_score)
        for row in scan_rows
        if code_key(row)
    ]
    for row in feature_rows:
        vector = row["特征向量"]
        strength = (
            safe_float(vector.get("影子评分分位")) * 28
            + safe_float(vector.get("成交额市值比分位")) * 22
            + safe_float(vector.get("成交额分位")) * 15
            + safe_float(vector.get("行业热度")) * 12
            + safe_float(vector.get("站上MA20")) * 6
            + safe_float(vector.get("站上MA60")) * 6
            + safe_float(vector.get("MACD强度")) * 5
            + safe_float(vector.get("60日突破")) * 4
            + safe_float(vector.get("ATR适中")) * 2
        )
        row["方法内核强度分"] = round(strength, 2)

    success_count = int(rules.get("样本库规则", {}).get("强势成功样本数量", 150))
    failure_count = int(rules.get("样本库规则", {}).get("失败对照样本数量", 150))
    candidate_count = int(rules.get("样本库规则", {}).get("候选识别数量", 120))

    success_samples = sorted(feature_rows, key=lambda item: item["方法内核强度分"], reverse=True)[:success_count]
    success_codes = {row["代码"] for row in success_samples}
    failure_pool = [row for row in feature_rows if row["代码"] not in success_codes]
    failure_samples = sorted(
        failure_pool,
        key=lambda item: (
            safe_float(item["特征向量"].get("影子评分分位")),
            safe_float(item["特征向量"].get("成交额市值比分位")),
            safe_float(item["特征向量"].get("行业热度")),
        ),
    )[:failure_count]

    for row in success_samples:
        row["样本标签"] = "强势成功样本_v1影子"
        row["入库理由"] = "影子评分、成交活跃度、行业热度或技术结构综合靠前。"
    for row in failure_samples:
        row["样本标签"] = "失败对照样本_v1影子"
        row["入库理由"] = "同属基础样本但成交活跃、行业热度或技术结构综合偏弱。"

    success_center = centroid(success_samples)
    failure_center = centroid(failure_samples)

    candidate_base: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in (l8x_rows, [scan_map[row["代码"]] for row in success_samples if row["代码"] in scan_map], scan_rows):
        for row in source:
            key = code_key(row)
            if not key or key in seen:
                continue
            seen.add(key)
            base = scan_map.get(key) or row
            candidate_base.append(base)
            if len(candidate_base) >= candidate_count:
                break
        if len(candidate_base) >= candidate_count:
            break

    candidate_features = [
        merge_feature_row(row, pool_map, indicator_map, kline_map, score_values, turnover_values, amount_values, industry_score)
        for row in candidate_base
        if code_key(row)
    ]
    similarity_rows: list[dict[str, Any]] = []
    for row in candidate_features:
        vector = row.get("特征向量", {})
        success_score = similarity(vector, success_center)
        failure_score = similarity(vector, failure_center)
        net_score = round(success_score - failure_score + 50, 2)
        if success_score >= 78 and success_score > failure_score + 5:
            conclusion = "优先研究"
        elif success_score >= 68 and success_score >= failure_score:
            conclusion = "观察验证"
        else:
            conclusion = "暂不进入推荐"
        similarity_rows.append({
            **row,
            "强势相似度": success_score,
            "失败相似度": failure_score,
            "杰哥推荐相似度分": max(0, min(100, net_score)),
            "识别结论": conclusion,
            "观察条件": build_observation_conditions(row, success_score, failure_score),
            "风险提示": "本识别只用于研究排序，不构成投资建议，不作为买卖指令。",
        })
    similarity_rows.sort(key=lambda item: (item["识别结论"] == "优先研究", item["杰哥推荐相似度分"], item["强势相似度"]), reverse=True)

    base_report = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(RULE_PATH),
        "方法阶段": rules.get("当前阶段"),
        "输入统计": {
            "2000样本池": len(pool_rows),
            "2000影子扫描": len(scan_rows),
            "L8X综合候选池": len(l8x_rows),
            "基础技术指标": len(focus_indicators) + len(candidate_indicators),
            "可计算补充派生指标_K线股票数": len(kline_map),
        },
        "技术指标准备状态": {
            "基础指标": "已具备MA/RSI/MACD/成交量MA20/量比/成交额市值比/影子评分",
            "补充派生指标": "已在本内核对有K线样本计算KDJ/BOLL/ATR/涨跌幅/回撤/突破/缺口",
            "缺口": rules.get("技术指标要求", {}).get("仍待升级", []),
            "结论": "可支撑v1影子识别；尚不能声称已完成近三年全量强势股真实回测。",
        },
        "安全边界": rules.get("安全边界", {}),
    }

    success_report = {**base_report, "名称": "强势成功样本库", "样本数量": len(success_samples), "样本": success_samples}
    failure_report = {**base_report, "名称": "失败对照样本库", "样本数量": len(failure_samples), "样本": failure_samples}
    similarity_report = {**base_report, "名称": "当前候选股相似度识别", "候选数量": len(similarity_rows), "候选": similarity_rows}
    acceptance = {
        **base_report,
        "名称": "杰哥推荐方法内核验收",
        "验收结论": "v1方法内核已建立，可运行；近三年真实涨幅强势样本库仍需进入v2补齐。",
        "产物": {
            "强势成功样本库": str(out_dir / output_rules.get("强势成功样本库", "强势成功样本库_最新.json")),
            "失败对照样本库": str(out_dir / output_rules.get("失败对照样本库", "失败对照样本库_最新.json")),
            "当前候选股相似度识别": str(out_dir / output_rules.get("当前候选股相似度识别", "当前候选股相似度识别_最新.json")),
        },
        "数量": {
            "强势成功样本": len(success_samples),
            "失败对照样本": len(failure_samples),
            "当前候选识别": len(similarity_rows),
        },
        "下一步": [
            "补近三年真实涨幅数据，给成功样本打真实标签。",
            "补失败样本真实回测标签，避免只看当前快照。",
            "把杰哥推荐相似度分接入推荐排序，但仍由风险线和证据边界过滤。",
        ],
    }

    outputs = [
        (success_report, "强势成功样本库"),
        (failure_report, "失败对照样本库"),
        (similarity_report, "当前候选股相似度识别"),
        (acceptance, "验收报告"),
    ]
    for data, key in outputs:
        latest_name = output_rules.get(key, f"{key}_最新.json")
        latest_path = out_dir / latest_name
        stamped_path = out_dir / latest_name.replace("_最新.json", f"_{stamp}.json")
        write_json(stamped_path, data)
        write_json(latest_path, data)

    write_text(out_dir / f"强势成功样本库_{stamp}.md", markdown_table("强势成功样本库", success_samples))
    write_text(out_dir / "强势成功样本库_最新.md", markdown_table("强势成功样本库", success_samples))
    write_text(out_dir / f"失败对照样本库_{stamp}.md", markdown_table("失败对照样本库", failure_samples, score_key="方法内核强度分"))
    write_text(out_dir / "失败对照样本库_最新.md", markdown_table("失败对照样本库", failure_samples, score_key="方法内核强度分"))
    write_text(out_dir / f"当前候选股相似度识别_{stamp}.md", markdown_table("当前候选股相似度识别", similarity_rows, score_key="杰哥推荐相似度分"))
    write_text(out_dir / "当前候选股相似度识别_最新.md", markdown_table("当前候选股相似度识别", similarity_rows, score_key="杰哥推荐相似度分"))

    print(json.dumps({
        "状态": "完成",
        "强势成功样本": len(success_samples),
        "失败对照样本": len(failure_samples),
        "候选识别": len(similarity_rows),
        "可计算补充派生指标_K线股票数": len(kline_map),
        "输出目录": str(out_dir),
        "安全边界": rules.get("安全边界", {}),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
