# -*- coding: utf-8 -*-
"""
名称：生成杰哥推荐分析方法v1.py
作用：把【杰哥推荐】从“指标清单”升级为可执行的方法评分层。
输入：当前候选相似度、P0增强量价特征、历史K线、行业归因。
输出：03数据/280杰哥推荐分析方法v1 下的方法评分、方法报告、学习说明。
安全边界：只读本地数据；只写本地03数据；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不输出买卖指令。
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any


def stock_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = stock_root()
DATA = ROOT / "03数据"
CONFIG = ROOT / "01配置"
CANDIDATE_PATH = DATA / "270杰哥推荐方法内核" / "当前候选股相似度识别_最新.json"
FEATURE_PATH = DATA / "272杰哥推荐量价特征" / "全候选量价特征_最新.json"
P0_FEATURE_PATH = DATA / "279杰哥推荐P0指标补足" / "全候选P0增强量价特征_最新.json"
KLINE_PATH = DATA / "271杰哥推荐基础补足" / "杰哥推荐候选历史K线增强_最新.json"
INDUSTRY_PATH = DATA / "273杰哥推荐行业归因" / "杰哥推荐行业归因报告_最新.json"
UNIVERSAL_MECHANISM_PATH = CONFIG / "股票通用分析判断机制_v1.0.json"
OUT_DIR = DATA / "280杰哥推荐分析方法v1"


METHOD_RULE = {
    "名称": "杰哥强势股分析方法v1",
    "定位": "先做趋势资格，再看强势结构，再做行业验证，最后用A股短期反转和失败样本做刹车。",
    "数据抓取先后顺序": [
        "270当前候选相似度：拿原始强弱排序、强势相似度、失败相似度。",
        "279P0增强量价特征：拿日线量价、周线趋势、行业动态强度。",
        "271历史K线：补算第二阶段趋势模板、波动收缩、均线方向和近一年高低点。",
        "273行业归因：确认行业顺风、失败集中和行业解释边界。",
        "280方法评分：输出方法分层、证据链、刹车项和复盘学习任务。",
    ],
    "分析先后顺序": [
        "第一步：趋势资格层。用米勒维尼第二阶段趋势模板做基础门槛，不满足则不得直接进入重点候选。",
        "第二步：强势结构层。检查放量突破、回踩不破、均线多头、板块共振，并加入VCP波动收缩观察。",
        "第三步：行业验证层。行业动态强度优先，静态行业归因只做解释；高拥挤行业降权。",
        "第四步：失败对照层。强势相似度必须明显高于失败相似度，否则进入观察验证。",
        "第五步：A股刹车层。短期涨幅过热、回撤过大、周线未确认、量能尖峰过大时，降低前台表达强度。",
        "第六步：输出层。只输出研究分层、观察条件和风险边界，不输出买卖点、仓位或交易指令。",
        "第七步：复盘学习层。后续用实际走势、人工反馈、失败案例反向更新阈值和权重。",
    ],
    "权重": {
        "趋势资格层": 0.25,
        "强势结构层": 0.25,
        "行业验证层": 0.20,
        "失败对照层": 0.20,
        "A股刹车层": 0.10,
    },
    "方法法阶": [
        {
            "层级": "宪法层",
            "名称": "核心硬门槛",
            "规则": "趋势资格、失败对照、行业逆风、交易安全边界优先于所有加分项；不过核心门槛不得进入方法重点候选。",
        },
        {
            "层级": "法律层",
            "名称": "主分析方法",
            "规则": "第二阶段趋势模板、强势结构、行业动态验证和A股刹车共同决定方法分层。",
        },
        {
            "层级": "规章层",
            "名称": "辅助解释指标",
            "规则": "VCP、行业静态归因、拥挤度、量能波动只负责解释和微调，不能越级推翻核心门槛。",
        },
        {
            "层级": "案例层",
            "名称": "复盘学习",
            "规则": "复盘只提出阈值修正建议，不自动改规则；失败案例优先进入失败对照。",
        },
    ],
    "市场环境平衡": {
        "原则": "推荐榜先满足核心门槛，再在当期市场横截面内排序；牛市提高入围门槛，熊市不强行凑名单。",
        "牛市或强势市": "满足条件股票变多时，只允许方法分和横截面分位同时靠前的样本进入重点。",
        "震荡市": "保持标准阈值，重点看趋势资格、行业动态和失败对照距离。",
        "熊市或弱势市": "允许观察池保留少量强者，但重点候选必须更稀缺；不为了数量降低质量。",
    },
    "指标适用性": [
        {
            "指标组": "趋势资格",
            "擅长": "判断股票是否处于可研究的中长期强趋势阶段。",
            "适用环境": ["震荡市/中性市", "强势市/牛市"],
            "失效或降权": "急跌反弹、低位超跌修复时容易滞后，只能做门槛，不能单独推荐。",
            "默认角色": "核心门槛",
        },
        {
            "指标组": "强势结构",
            "擅长": "识别放量突破、回踩不破、均线多头和波动收缩后的承接结构。",
            "适用环境": ["震荡市/中性市"],
            "失效或降权": "普涨牛市里容易出现大量假突破，弱势市里突破失败率上升。",
            "默认角色": "主证据",
        },
        {
            "指标组": "行业验证",
            "擅长": "判断个股是否处于板块共振或行业顺风。",
            "适用环境": ["强势市/牛市", "震荡市/中性市"],
            "失效或降权": "行业高拥挤或失败样本集中时只做解释，不可越级加分。",
            "默认角色": "环境证据",
        },
        {
            "指标组": "失败对照",
            "擅长": "识别高分样本是否接近历史失败形态。",
            "适用环境": ["强势市/牛市", "震荡市/中性市", "弱势市/熊市"],
            "失效或降权": "不降权，始终是刹车项。",
            "默认角色": "核心刹车",
        },
        {
            "指标组": "A股刹车",
            "擅长": "处理短期反转、过热、尖峰量、周线未确认、回撤放大。",
            "适用环境": ["强势市/牛市", "弱势市/熊市"],
            "失效或降权": "震荡市不过度惩罚正常波动，但P0问题仍强制生效。",
            "默认角色": "风险闸门",
        },
    ],
    "硬性刹车": [
        "高分但失败相似度>=55或强势-失败差值<18，降为观察验证。",
        "行业动态逆风且不具备强趋势资格，降为方法观察或方法暂缓。",
        "第二阶段趋势模板通过少于5项，不进入方法重点候选。",
        "周线未确认且短期涨幅过热，不得在前台表达为趋势共振。",
        "高拥挤行业只做观察，不因行业热度提高分层。",
    ],
    "长期学习规则": [
        "每次前台投影后保留方法分、证据链、刹车项和当时输入版本。",
        "复盘时按20/60/120日实际表现标记成功、一般、失败，不用单日涨跌定性。",
        "失败样本优先学习：凡高分后走弱，回填失败对照库并检查是哪一层误判。",
        "行业判断单独复盘：验证行业动态强度是否真的领先个股表现。",
        "权重只能由复盘报告提出建议，再由总管审批，不允许脚本自发改规则。",
    ],
}


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


def active_feature_path() -> Path:
    return P0_FEATURE_PATH if P0_FEATURE_PATH.exists() else FEATURE_PATH


def safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value in (None, "", "-"):
            return default
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except (TypeError, ValueError):
        return default


def safe_bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def normalize_code(value: Any) -> str:
    text = str(value or "").strip().lower().replace("_", "").replace("-", "")
    if "." in text:
        code, market = text.split(".", 1)
        return f"{market}{code}" if market in {"sh", "sz", "bj"} else text
    if text.endswith(("sh", "sz", "bj")) and len(text) >= 8:
        return text[-2:] + text[:6]
    return text


def list_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.replace("，", " ").split() if item.strip()]
    return []


def load_candidates() -> list[dict[str, Any]]:
    raw = load_json(CANDIDATE_PATH, {})
    if isinstance(raw, dict) and isinstance(raw.get("候选"), list):
        return [item for item in raw["候选"] if isinstance(item, dict)]
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    return []


def build_map(rows: Any) -> dict[str, dict[str, Any]]:
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


def load_kline_map() -> dict[str, list[dict[str, Any]]]:
    raw = load_json(KLINE_PATH, {})
    rows = raw.get("股票", []) if isinstance(raw, dict) else raw
    mapping: dict[str, list[dict[str, Any]]] = {}
    if not isinstance(rows, list):
        return mapping
    for item in rows:
        if not isinstance(item, dict):
            continue
        code = normalize_code(item.get("代码") or item.get("展示代码"))
        kline = item.get("历史K线") or item.get("kline") or item.get("K线数据") or []
        if code and isinstance(kline, list):
            mapping[code] = [row for row in kline if isinstance(row, dict)]
    return mapping


def build_industry_map() -> dict[str, dict[str, Any]]:
    raw = load_json(INDUSTRY_PATH, {})
    rows = raw.get("全部行业归因", []) if isinstance(raw, dict) else []
    return {str(item.get("行业")): item for item in rows if isinstance(item, dict) and item.get("行业")}


def moving_average(values: list[float], window: int) -> list[float | None]:
    result: list[float | None] = []
    total = 0.0
    queue: list[float] = []
    for value in values:
        queue.append(value)
        total += value
        if len(queue) > window:
            total -= queue.pop(0)
        result.append(total / window if len(queue) == window else None)
    return result


def series_from_kline(kline: list[dict[str, Any]], key: str) -> list[float]:
    values = []
    for row in kline:
        value = safe_float(row.get(key), None)
        if value is not None:
            values.append(value)
    return values


def pct_change(current: float | None, base: float | None) -> float | None:
    if current is None or base in (None, 0):
        return None
    return (current / base - 1) * 100


def calc_trend_template(feature: dict[str, Any], kline: list[dict[str, Any]]) -> tuple[float, list[dict[str, Any]], dict[str, Any]]:
    closes = series_from_kline(kline, "收盘")
    latest = safe_float(feature.get("最新收盘"), None) or (closes[-1] if closes else None)
    ma60 = safe_float(feature.get("MA60"), None)
    ma120 = safe_float(feature.get("MA120"), None)
    ma250 = safe_float(feature.get("MA250"), None)
    low_distance = safe_float(feature.get("250日距低点"), None)
    high_distance = safe_float(feature.get("250日距高点"), None)

    ma250_rising = False
    if len(closes) >= 270:
        ma250_series = moving_average(closes, 250)
        latest_ma250 = ma250_series[-1]
        prior_ma250 = ma250_series[-21] if len(ma250_series) >= 21 else None
        ma250_rising = latest_ma250 is not None and prior_ma250 is not None and latest_ma250 > prior_ma250

    year_low_gain = low_distance
    year_high_distance = high_distance
    if len(closes) >= 20 and latest is not None:
        recent = closes[-250:] if len(closes) >= 250 else closes
        if recent:
            year_low_gain = pct_change(latest, min(recent))
            year_high_distance = pct_change(latest, max(recent))

    checks = [
        ("股价站上MA120", latest is not None and ma120 is not None and latest > ma120, "近似替代150日均线"),
        ("股价站上MA250", latest is not None and ma250 is not None and latest > ma250, "第二阶段基础门槛"),
        ("MA120高于MA250", ma120 is not None and ma250 is not None and ma120 > ma250, "中长期趋势抬升"),
        ("MA250近20日上行", ma250_rising, "长期均线方向确认"),
        ("MA60高于MA120和MA250", ma60 is not None and ma120 is not None and ma250 is not None and ma60 > ma120 and ma60 > ma250, "中期均线多头"),
        ("股价站上MA60", latest is not None and ma60 is not None and latest > ma60, "当前价格不弱于中期趋势"),
        ("相对250日低点涨幅>=30%", year_low_gain is not None and year_low_gain >= 30, "确认已经脱离长期低位"),
        ("距离250日高点不超过25%", year_high_distance is not None and year_high_distance >= -25, "强势股应接近中长期高位"),
    ]
    passed = sum(1 for _, ok, _ in checks if ok)
    detail = [{"条件": name, "通过": bool(ok), "说明": note} for name, ok, note in checks]
    extra = {
        "第二阶段趋势模板通过数": passed,
        "第二阶段趋势模板总数": len(checks),
        "MA250近20日上行": ma250_rising,
        "250日低点涨幅": round(year_low_gain, 4) if year_low_gain is not None else None,
        "250日距高点重算": round(year_high_distance, 4) if year_high_distance is not None else None,
    }
    return round(passed / len(checks) * 100, 2), detail, extra


def calc_vcp(feature: dict[str, Any], kline: list[dict[str, Any]]) -> dict[str, Any]:
    highs = series_from_kline(kline, "最高")
    lows = series_from_kline(kline, "最低")
    closes = series_from_kline(kline, "收盘")
    amounts = series_from_kline(kline, "成交额")
    volumes = series_from_kline(kline, "成交量")

    def avg_range(days: int) -> float | None:
        if len(highs) < days or len(lows) < days or len(closes) < days:
            return None
        ranges = []
        for high, low, close in zip(highs[-days:], lows[-days:], closes[-days:]):
            if close:
                ranges.append((high - low) / close * 100)
        return sum(ranges) / len(ranges) if ranges else None

    range60 = avg_range(60)
    range30 = avg_range(30)
    range15 = avg_range(15)
    amount60 = sum(amounts[-60:]) / 60 if len(amounts) >= 60 else None
    amount20 = sum(amounts[-20:]) / 20 if len(amounts) >= 20 else None
    volume60 = sum(volumes[-60:]) / 60 if len(volumes) >= 60 else None
    volume20 = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else None
    prior_high20 = max(closes[-21:-1]) if len(closes) >= 21 else None
    latest = closes[-1] if closes else None

    range_shrinking = range60 is not None and range30 is not None and range15 is not None and range15 < range30 < range60
    amount_cooling = amount20 is not None and amount60 not in (None, 0) and amount20 <= amount60 * 1.05
    volume_cooling = volume20 is not None and volume60 not in (None, 0) and volume20 <= volume60 * 1.05
    near_pivot = latest is not None and prior_high20 is not None and latest >= prior_high20 * 0.97
    breakout = safe_bool(feature.get("60日突破")) or (latest is not None and prior_high20 is not None and latest > prior_high20)

    score = 0
    if range_shrinking:
        score += 35
    if amount_cooling or volume_cooling:
        score += 25
    if near_pivot:
        score += 20
    if breakout:
        score += 20

    if score >= 75:
        state = "VCP候选"
    elif score >= 45:
        state = "收缩观察"
    else:
        state = "未成型"

    return {
        "VCP分": round(score, 2),
        "VCP状态": state,
        "振幅60日均值": round(range60, 4) if range60 is not None else None,
        "振幅30日均值": round(range30, 4) if range30 is not None else None,
        "振幅15日均值": round(range15, 4) if range15 is not None else None,
        "振幅逐步收缩": range_shrinking,
        "量能整理": bool(amount_cooling or volume_cooling),
        "接近20日中枢": near_pivot,
        "突破观察": breakout,
    }


def compute_industry_crowding(features: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_industry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in features:
        industry = str(item.get("行业") or "未知")
        by_industry[industry].append(item)

    med_amount_ratio: dict[str, float] = {}
    med_volume_ratio: dict[str, float] = {}
    med_turnover_proxy: dict[str, float] = {}
    for industry, rows in by_industry.items():
        amount_values = [safe_float(row.get("成交额20_60比"), None) for row in rows]
        volume_values = [safe_float(row.get("成交量20_60比"), None) for row in rows]
        vol5_values = [safe_float(row.get("量比5日"), None) for row in rows]
        amount_values = [v for v in amount_values if v is not None]
        volume_values = [v for v in volume_values if v is not None]
        vol5_values = [v for v in vol5_values if v is not None]
        med_amount_ratio[industry] = median(amount_values) if amount_values else 0.0
        med_volume_ratio[industry] = median(volume_values) if volume_values else 0.0
        med_turnover_proxy[industry] = median(vol5_values) if vol5_values else 0.0

    amount_sorted = sorted(med_amount_ratio.values())
    volume_sorted = sorted(med_volume_ratio.values())

    def percentile(values: list[float], value: float) -> float:
        if not values:
            return 0.0
        below = sum(1 for item in values if item <= value)
        return below / len(values) * 100

    result: dict[str, dict[str, Any]] = {}
    for industry in by_industry:
        amount_pct = percentile(amount_sorted, med_amount_ratio[industry])
        volume_pct = percentile(volume_sorted, med_volume_ratio[industry])
        crowding_score = round(amount_pct * 0.6 + volume_pct * 0.4, 2)
        high = crowding_score >= 80 and (med_amount_ratio[industry] >= 1.35 or med_volume_ratio[industry] >= 1.35)
        warm = crowding_score >= 65 and (med_amount_ratio[industry] >= 1.15 or med_volume_ratio[industry] >= 1.15)
        state = "高拥挤" if high else "温和拥挤" if warm else "正常"
        result[industry] = {
            "行业拥挤度分": crowding_score,
            "行业拥挤状态": state,
            "行业成交额20_60比中位数": round(med_amount_ratio[industry], 4),
            "行业成交量20_60比中位数": round(med_volume_ratio[industry], 4),
            "行业量比5日中位数": round(med_turnover_proxy[industry], 4),
        }
    return result


def calc_market_context(features: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(features)
    if not total:
        return {
            "市场状态": "未知",
            "市场温度分": 50.0,
            "说明": "特征样本缺失，按中性阈值处理。",
            "重点候选最大分位": 8.0,
            "待验证最大分位": 22.0,
            "重点最低方法分": 86.0,
            "待验证最低方法分": 74.0,
        }

    ma_bull_count = sum(1 for item in features if safe_bool(item.get("均线多头排列")))
    above_ma60_count = 0
    change60_values: list[float] = []
    dynamic_values: list[float] = []
    amount_ratio_values: list[float] = []
    for item in features:
        latest = safe_float(item.get("最新收盘"), None)
        ma60 = safe_float(item.get("MA60"), None)
        if latest is not None and ma60 is not None and latest > ma60:
            above_ma60_count += 1
        change60 = safe_float(item.get("60日涨跌幅"), None)
        if change60 is not None:
            change60_values.append(change60)
        dynamic_score = safe_float(item.get("行业动态强度分"), None)
        if dynamic_score is not None:
            dynamic_values.append(dynamic_score)
        amount_ratio = safe_float(item.get("成交额20_60比"), None)
        if amount_ratio is not None:
            amount_ratio_values.append(amount_ratio)

    ma_bull_ratio = ma_bull_count / total
    above_ma60_ratio = above_ma60_count / total
    median_change60 = median(change60_values) if change60_values else 0.0
    median_dynamic = median(dynamic_values) if dynamic_values else 50.0
    median_amount_ratio = median(amount_ratio_values) if amount_ratio_values else 1.0
    temperature = clamp(
        above_ma60_ratio * 35
        + ma_bull_ratio * 25
        + clamp((median_change60 + 20) / 60 * 25, 0, 25)
        + clamp(median_dynamic / 100 * 15, 0, 15)
    )

    if temperature >= 68 and above_ma60_ratio >= 0.55:
        state = "强势市/牛市"
        thresholds = {
            "重点候选最大分位": 5.5,
            "待验证最大分位": 18.0,
            "重点最低方法分": 88.0,
            "待验证最低方法分": 76.0,
        }
        note = "市场整体较热，采用更严格横截面排名，防止普涨时名单膨胀。"
    elif temperature <= 42 or above_ma60_ratio < 0.35:
        state = "弱势市/熊市"
        thresholds = {
            "重点候选最大分位": 4.0,
            "待验证最大分位": 14.0,
            "重点最低方法分": 84.0,
            "待验证最低方法分": 70.0,
        }
        note = "市场整体偏弱，不强行凑重点名单，只保留少数相对强者。"
    else:
        state = "震荡市/中性市"
        thresholds = {
            "重点候选最大分位": 7.0,
            "待验证最大分位": 20.0,
            "重点最低方法分": 86.0,
            "待验证最低方法分": 74.0,
        }
        note = "市场处于中性区间，按标准阈值做相对排序。"

    return {
        "市场状态": state,
        "市场温度分": round(temperature, 2),
        "均线多头比例": round(ma_bull_ratio, 4),
        "站上MA60比例": round(above_ma60_ratio, 4),
        "60日涨跌幅中位数": round(median_change60, 4),
        "行业动态强度中位数": round(median_dynamic, 4),
        "成交额20_60比中位数": round(median_amount_ratio, 4),
        "说明": note,
        **thresholds,
    }


def calc_pattern_score(feature: dict[str, Any], vcp: dict[str, Any]) -> tuple[float, list[str]]:
    tags = list_tags(feature.get("量价模式标签"))
    reasons: list[str] = []
    score = 0.0
    if safe_bool(feature.get("60日突破")) or "突破信号" in tags:
        score += 22
        reasons.append("放量突破或突破信号")
    if safe_float(feature.get("60日最大回撤"), 0.0) is not None and (safe_float(feature.get("60日最大回撤"), 0.0) or 0.0) >= -20:
        score += 18
        reasons.append("60日回撤受控")
    if safe_bool(feature.get("均线多头排列")) or "均线多头" in tags:
        score += 22
        reasons.append("均线多头")
    if (safe_float(feature.get("成交额20_60比"), 0.0) or 0.0) >= 1.05 or (safe_float(feature.get("量比5日"), 0.0) or 0.0) >= 1.05:
        score += 18
        reasons.append("成交活跃度不弱")
    if vcp.get("VCP状态") == "VCP候选":
        score += 20
        reasons.append("波动收缩后接近中枢")
    elif vcp.get("VCP状态") == "收缩观察":
        score += 10
        reasons.append("波动收缩观察")
    return round(clamp(score), 2), reasons


def calc_industry_score(feature: dict[str, Any], industry: dict[str, Any], crowding: dict[str, Any]) -> tuple[float, list[str]]:
    dynamic_score = safe_float(feature.get("行业动态强度分"), 50.0) or 50.0
    label = str(industry.get("归因标签") or feature.get("行业归因标签") or "未知")
    strong_rep = safe_float(industry.get("强势过度代表指数") or feature.get("行业静态强势指数"), 0.0) or 0.0
    failure_rep = safe_float(industry.get("失败过度代表指数") or feature.get("行业静态失败指数"), 0.0) or 0.0
    crowding_state = str(crowding.get("行业拥挤状态") or "正常")

    score = dynamic_score * 0.55 + clamp(strong_rep * 20, 0, 25)
    if label == "强势共振行业":
        score += 15
    elif label == "结构活跃行业":
        score += 8
    elif label == "弱势/失败集中行业":
        score -= 20
    if failure_rep >= 2:
        score -= min(18, failure_rep * 4)
    if crowding_state == "高拥挤":
        score -= 18
    elif crowding_state == "温和拥挤":
        score -= 8

    reasons = [
        f"行业动态强度={round(dynamic_score, 2)}",
        f"行业归因={label}",
        f"行业拥挤={crowding_state}",
    ]
    return round(clamp(score), 2), reasons


def calc_failure_control(candidate: dict[str, Any]) -> tuple[float, list[str]]:
    strong = safe_float(candidate.get("强势相似度"), None)
    failure = safe_float(candidate.get("失败相似度"), None)
    if strong is None or failure is None:
        return 60.0, ["强势/失败相似度缺失，按中性处理"]
    spread = strong - failure
    score = 50 + spread
    if failure >= 55:
        score -= 25
    if spread >= 35:
        score += 10
    reasons = [f"强势相似度={round(strong, 2)}", f"失败相似度={round(failure, 2)}", f"差值={round(spread, 2)}"]
    return round(clamp(score), 2), reasons


def calc_ashare_brake(feature: dict[str, Any], candidate: dict[str, Any], crowding: dict[str, Any]) -> tuple[float, list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    score = 100.0
    change20 = safe_float(feature.get("20日涨跌幅"), 0.0) or 0.0
    change60 = safe_float(feature.get("60日涨跌幅"), 0.0) or 0.0
    drawdown60 = safe_float(feature.get("60日最大回撤"), 0.0) or 0.0
    amount_vol = safe_float(feature.get("成交额60日波动率"), 0.0) or 0.0
    volume_vol = safe_float(feature.get("成交量60日波动率"), 0.0) or 0.0
    weekly_state = str(feature.get("周线趋势状态") or "待补足")
    dynamic_state = str(feature.get("行业动态状态") or "待补足")
    crowding_state = str(crowding.get("行业拥挤状态") or "正常")
    strong = safe_float(candidate.get("强势相似度"), None)
    failure = safe_float(candidate.get("失败相似度"), None)

    def issue(code: str, level: str, text: str, penalty: float) -> None:
        nonlocal score
        score -= penalty
        issues.append({"问题代码": code, "级别": level, "说明": text, "扣分": penalty})

    if change60 < 0:
        issue("negative_60d", "P0", f"60日涨跌幅为{round(change60, 2)}%，短期反转风险未解除。", 30)
    if change20 >= 80 or change60 >= 180:
        issue("short_term_overheat", "P1", f"20日={round(change20, 2)}%，60日={round(change60, 2)}%，短期过热需等待验证。", 16)
    if drawdown60 < -25:
        issue("large_60d_drawdown", "P1", f"60日最大回撤={round(drawdown60, 2)}%，趋势承接不够平滑。", 14)
    if amount_vol >= 1.3 or volume_vol >= 1.3:
        issue("volume_spike_risk", "P1", f"成交额波动率={round(amount_vol, 4)}，成交量波动率={round(volume_vol, 4)}，可能是尖峰量。", 12)
    if "未确认" in weekly_state:
        issue("weekly_not_confirmed", "P1", f"周线趋势状态={weekly_state}。", 12)
    if dynamic_state == "动态逆风":
        issue("dynamic_industry_headwind", "P1", f"行业动态状态={dynamic_state}。", 12)
    if crowding_state == "高拥挤":
        issue("industry_crowded", "P1", "行业拥挤度高，短线一致性交易风险上升。", 10)
    if strong is not None and failure is not None and (failure >= 55 or strong - failure < 18):
        issue("failure_similarity_close", "P0", f"强势相似度={round(strong, 2)}，失败相似度={round(failure, 2)}，距离不足。", 25)

    return round(clamp(score), 2), issues


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if not total:
        return METHOD_RULE["权重"].copy()
    return {key: round(value / total, 4) for key, value in weights.items()}


def adaptive_weights(market: dict[str, Any], feature: dict[str, Any], crowding: dict[str, Any]) -> tuple[dict[str, float], list[str]]:
    state = str(market.get("市场状态") or "震荡市/中性市")
    weights = METHOD_RULE["权重"].copy()
    reasons: list[str] = []
    if "强势" in state or "牛市" in state:
        weights["失败对照层"] += 0.05
        weights["A股刹车层"] += 0.04
        weights["强势结构层"] -= 0.04
        weights["行业验证层"] -= 0.03
        reasons.append("强势市里满足技术条件的股票会变多，抬高失败对照和过热刹车权重。")
    elif "弱势" in state or "熊市" in state:
        weights["趋势资格层"] += 0.06
        weights["失败对照层"] += 0.04
        weights["A股刹车层"] += 0.03
        weights["行业验证层"] -= 0.05
        weights["强势结构层"] -= 0.08
        reasons.append("弱势市里突破更容易失败，优先看趋势资格、失败对照和风险闸门。")
    else:
        weights["强势结构层"] += 0.02
        weights["行业验证层"] += 0.01
        weights["A股刹车层"] -= 0.01
        weights["失败对照层"] -= 0.02
        reasons.append("震荡市里强者恒强更有区分度，略提高结构和行业验证权重。")

    if str(crowding.get("行业拥挤状态") or "正常") == "高拥挤":
        weights["A股刹车层"] += 0.04
        weights["行业验证层"] -= 0.04
        reasons.append("行业高拥挤时，行业热度从加分项变成风险解释。")

    if safe_bool(feature.get("周线MA多头")) and safe_bool(feature.get("周线收盘在MA20上")):
        weights["趋势资格层"] += 0.02
        weights["强势结构层"] += 0.01
        weights["行业验证层"] -= 0.01
        weights["A股刹车层"] -= 0.02
        reasons.append("周线趋势确认时，趋势和结构证据更有发言权。")

    return normalize_weights(weights), reasons


def build_analysis_route(
    market: dict[str, Any],
    feature: dict[str, Any],
    crowding: dict[str, Any],
    trend_extra: dict[str, Any],
    vcp: dict[str, Any],
    brake_issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    state = str(market.get("市场状态") or "未知")
    route = [
        {
            "顺序": 1,
            "分析层": "趋势资格",
            "当前角色": "核心门槛",
            "理由": "先判断是不是处在可研究的中长期强趋势；不过门槛则辅助指标不得越级。",
        },
        {
            "顺序": 2,
            "分析层": "失败对照",
            "当前角色": "核心刹车",
            "理由": "任何市场环境下，都要先排除接近历史失败样本的高分假象。",
        },
        {
            "顺序": 3,
            "分析层": "强势结构",
            "当前角色": "主证据",
            "理由": "趋势资格通过后，再看放量突破、回踩不破、均线多头和VCP是否支持。",
        },
        {
            "顺序": 4,
            "分析层": "行业验证",
            "当前角色": "环境证据",
            "理由": "行业只验证顺风和逆风，不单独决定推荐。",
        },
        {
            "顺序": 5,
            "分析层": "A股刹车",
            "当前角色": "风险闸门",
            "理由": "最后处理短期反转、过热、周线未确认和拥挤风险。",
        },
    ]

    if "强势" in state or "牛市" in state:
        route[1], route[4] = route[4], route[1]
        route[1]["顺序"] = 2
        route[4]["顺序"] = 5
        route[1]["理由"] = "强势市里普涨会放大假阳性，先看过热和拥挤刹车。"
    elif "弱势" in state or "熊市" in state:
        route[2], route[4] = route[4], route[2]
        route[2]["顺序"] = 3
        route[4]["顺序"] = 5
        route[2]["理由"] = "弱势市里先排除回撤和破位风险，再谈突破形态。"

    if str(crowding.get("行业拥挤状态") or "正常") == "高拥挤":
        for item in route:
            if item["分析层"] == "行业验证":
                item["当前角色"] = "风险解释"
                item["理由"] = "行业高拥挤时，行业热度只能解释风险，不能加分越级。"

    if vcp.get("VCP状态") == "VCP候选" and int(trend_extra.get("第二阶段趋势模板通过数") or 0) >= 6:
        for item in route:
            if item["分析层"] == "强势结构":
                item["理由"] = "趋势门槛通过且VCP候选，结构层用于确认整理质量。"

    if any(item.get("级别") == "P0" for item in brake_issues):
        for item in route:
            if item["分析层"] == "A股刹车":
                item["当前角色"] = "强制刹车"
                item["理由"] = "存在P0问题，风险闸门直接优先于所有加分项。"

    return sorted(route, key=lambda item: item["顺序"])


def build_indicator_roles(
    weights: dict[str, float],
    market: dict[str, Any],
    feature: dict[str, Any],
    crowding: dict[str, Any],
    trend_extra: dict[str, Any],
    vcp: dict[str, Any],
    brake_issues: list[dict[str, Any]],
) -> dict[str, Any]:
    state = str(market.get("市场状态") or "未知")
    template_passed = int(trend_extra.get("第二阶段趋势模板通过数") or 0)
    weekly_confirmed = safe_bool(feature.get("周线MA多头")) and safe_bool(feature.get("周线收盘在MA20上"))
    crowding_state = str(crowding.get("行业拥挤状态") or "正常")
    has_p0 = any(item.get("级别") == "P0" for item in brake_issues)

    base = [
        {
            "指标": "第二阶段趋势模板",
            "所属层": "趋势资格层",
            "默认角色": "主指标",
            "本次角色": "主指标" if template_passed >= 6 else "硬门槛不足",
            "理由": f"趋势模板通过{template_passed}/8，决定是否具备强趋势研究资格。",
        },
        {
            "指标": "MA250方向与250日高低点位置",
            "所属层": "趋势资格层",
            "默认角色": "主指标",
            "本次角色": "主指标" if template_passed >= 6 else "辅助观察",
            "理由": "用于确认不是单纯短线反弹，而是中长期趋势抬升。",
        },
        {
            "指标": "强势相似度-失败相似度差值",
            "所属层": "失败对照层",
            "默认角色": "主指标",
            "本次角色": "硬刹车" if has_p0 else "主指标",
            "理由": "失败对照始终优先，接近失败样本时直接压制推荐层级。",
        },
        {
            "指标": "60日突破/回踩不破/均线多头",
            "所属层": "强势结构层",
            "默认角色": "主指标",
            "本次角色": "主指标" if "震荡" in state else "辅助指标",
            "理由": "震荡市里结构信号区分度较高；强势市和弱势市需防假突破。",
        },
        {
            "指标": "VCP波动收缩",
            "所属层": "强势结构层",
            "默认角色": "辅助指标",
            "本次角色": "主验证指标" if vcp.get("VCP状态") == "VCP候选" and template_passed >= 6 else "辅助指标",
            "理由": f"当前VCP状态={vcp.get('VCP状态')}，只在趋势资格通过后升级为主验证。",
        },
        {
            "指标": "行业动态强度",
            "所属层": "行业验证层",
            "默认角色": "辅助指标",
            "本次角色": "主环境指标" if crowding_state != "高拥挤" and str(feature.get("行业动态状态")) in {"动态强势", "动态偏强"} else "辅助解释",
            "理由": f"行业动态状态={feature.get('行业动态状态')}，行业拥挤={crowding_state}。",
        },
        {
            "指标": "行业静态归因",
            "所属层": "行业验证层",
            "默认角色": "辅助指标",
            "本次角色": "辅助解释",
            "理由": "静态归因只能解释历史强弱集中，不单独决定推荐。",
        },
        {
            "指标": "行业拥挤度",
            "所属层": "A股刹车层",
            "默认角色": "辅助风险",
            "本次角色": "主风险指标" if crowding_state == "高拥挤" else "辅助风险",
            "理由": f"行业拥挤状态={crowding_state}，高拥挤时热度从加分变成风险。",
        },
        {
            "指标": "周线趋势确认",
            "所属层": "趋势资格层",
            "默认角色": "辅助指标",
            "本次角色": "主验证指标" if weekly_confirmed else "辅助指标",
            "理由": "周线确认时趋势和结构证据权重提高；未确认时作为待验证边界。",
        },
        {
            "指标": "短期过热/回撤/尖峰量",
            "所属层": "A股刹车层",
            "默认角色": "风险指标",
            "本次角色": "硬刹车" if has_p0 else "主风险指标" if brake_issues else "辅助风险",
            "理由": "短期反转、过热和尖峰量用于防止把一时强度误判成稳定强势。",
        },
    ]

    primary = [item for item in base if item["本次角色"] in {"主指标", "主验证指标", "主环境指标", "主风险指标", "硬刹车"}]
    auxiliary = [item for item in base if item["本次角色"] in {"辅助指标", "辅助解释", "辅助风险", "辅助观察"}]
    downgraded = [item for item in base if item["本次角色"] in {"硬门槛不足"}]
    return {
        "市场环境": state,
        "权重排序": sorted(
            [{"指标层": key, "权重": value} for key, value in weights.items()],
            key=lambda item: item["权重"],
            reverse=True,
        ),
        "本次主指标": primary,
        "本次辅助指标": auxiliary,
        "本次降权或否决指标": downgraded,
    }


def score_one(
    candidate: dict[str, Any],
    feature: dict[str, Any],
    kline: list[dict[str, Any]],
    industry: dict[str, Any],
    crowding: dict[str, Any],
    market_context: dict[str, Any],
) -> dict[str, Any]:
    trend_score, trend_detail, trend_extra = calc_trend_template(feature, kline)
    vcp = calc_vcp(feature, kline)
    pattern_score, pattern_reasons = calc_pattern_score(feature, vcp)
    industry_score, industry_reasons = calc_industry_score(feature, industry, crowding)
    failure_score, failure_reasons = calc_failure_control(candidate)
    brake_score, brake_issues = calc_ashare_brake(feature, candidate, crowding)

    weights, weight_reasons = adaptive_weights(market_context, feature, crowding)
    analysis_route = build_analysis_route(market_context, feature, crowding, trend_extra, vcp, brake_issues)
    indicator_roles = build_indicator_roles(weights, market_context, feature, crowding, trend_extra, vcp, brake_issues)
    final_score = (
        trend_score * weights["趋势资格层"]
        + pattern_score * weights["强势结构层"]
        + industry_score * weights["行业验证层"]
        + failure_score * weights["失败对照层"]
        + brake_score * weights["A股刹车层"]
    )
    p0_count = sum(1 for item in brake_issues if item.get("级别") == "P0")
    p1_count = sum(1 for item in brake_issues if item.get("级别") == "P1")
    template_passed = int(trend_extra["第二阶段趋势模板通过数"])
    dynamic_state = str(feature.get("行业动态状态") or "待补足")
    crowding_state = str(crowding.get("行业拥挤状态") or "正常")
    constitutional_checks = [
        {"层级": "宪法层", "条件": "第二阶段趋势模板至少6项通过", "通过": template_passed >= 6},
        {"层级": "宪法层", "条件": "无P0刹车", "通过": p0_count == 0},
        {"层级": "宪法层", "条件": "行业动态不是逆风", "通过": dynamic_state != "动态逆风"},
        {"层级": "宪法层", "条件": "行业不是高拥挤", "通过": crowding_state != "高拥挤"},
    ]
    core_gate_passed = all(item["通过"] for item in constitutional_checks)

    if p0_count or final_score < 60 or template_passed < 4:
        layer = "方法暂缓"
    elif final_score >= 85 and pattern_score >= 58 and core_gate_passed:
        layer = "方法重点候选"
    elif final_score >= 75 and template_passed >= 5:
        layer = "方法待验证"
    elif final_score >= 60:
        layer = "方法观察"
    else:
        layer = "方法暂缓"

    if p0_count:
        risk_level = "P0刹车"
    elif p1_count >= 2:
        risk_level = "P1多项待验证"
    elif p1_count:
        risk_level = "P1待验证"
    else:
        risk_level = "通过"

    code = normalize_code(candidate.get("代码") or feature.get("代码"))
    display_code = candidate.get("展示代码") or feature.get("展示代码") or code
    return {
        "代码": code,
        "展示代码": display_code,
        "名称": candidate.get("名称") or feature.get("名称"),
        "行业": candidate.get("行业") or feature.get("行业") or "未知",
        "原始推荐分": round(safe_float(candidate.get("杰哥推荐相似度分"), 0.0) or 0.0, 2),
        "综合方法分": round(final_score, 2),
        "方法分层": layer,
        "原始方法分层": layer,
        "方法风险等级": risk_level,
        "核心门槛通过": core_gate_passed,
        "方法法阶判定": constitutional_checks,
        "指标动态权重": weights,
        "权重调整说明": weight_reasons,
        "智能分析路线": analysis_route,
        "指标主辅角色": indicator_roles,
        "趋势资格分": trend_score,
        "强势结构分": pattern_score,
        "行业验证分": industry_score,
        "失败对照分": failure_score,
        "A股刹车分": brake_score,
        "第二阶段趋势模板通过数": trend_extra["第二阶段趋势模板通过数"],
        "第二阶段趋势模板总数": trend_extra["第二阶段趋势模板总数"],
        "250日低点涨幅": trend_extra["250日低点涨幅"],
        "250日距高点重算": trend_extra["250日距高点重算"],
        "MA250近20日上行": trend_extra["MA250近20日上行"],
        "VCP分": vcp["VCP分"],
        "VCP状态": vcp["VCP状态"],
        "行业动态强度分": safe_float(feature.get("行业动态强度分"), None),
        "行业动态状态": feature.get("行业动态状态"),
        "行业拥挤度分": crowding.get("行业拥挤度分"),
        "行业拥挤状态": crowding.get("行业拥挤状态"),
        "周线趋势状态": feature.get("周线趋势状态"),
        "量价模式标签": list_tags(feature.get("量价模式标签")),
        "趋势资格明细": trend_detail,
        "VCP明细": vcp,
        "结构证据": pattern_reasons,
        "行业证据": industry_reasons,
        "失败对照证据": failure_reasons,
        "刹车项": brake_issues,
        "学习标记": {
            "需要复盘": layer in {"方法重点候选", "方法待验证"},
            "复盘周期": ["20日", "60日", "120日"],
            "复盘重点": [
                "趋势模板是否继续保持",
                "VCP/突破是否被证伪",
                "行业动态强度是否持续",
                "失败对照距离不足是否导致误判",
            ],
        },
    }


def make_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 杰哥推荐分析方法v1报告",
        "",
        f"生成时间：{report['生成时间']}",
        f"候选数量：{report['统计']['候选数量']}",
        f"市场状态：{report['市场环境']['市场状态']}；市场温度分：{report['市场环境']['市场温度分']}",
        f"市场平衡说明：{report['市场环境']['说明']}",
        "",
        "## 方法顺序",
        "",
    ]
    for idx, item in enumerate(report["方法规则"]["分析先后顺序"], 1):
        lines.append(f"{idx}. {item}")
    lines.extend(["", "## 方法法阶", ""])
    if report.get("上位规则摘要"):
        summary = report["上位规则摘要"]
        lines.append(f"- 上位规则：{summary.get('名称')}（{summary.get('路径')}）")
        lines.append(f"- 继承关系：{summary.get('继承关系')}")
    for item in report["方法规则"]["方法法阶"]:
        lines.append(f"- {item['层级']}：{item['名称']}。{item['规则']}")
    lines.extend(["", "## 指标适用性", ""])
    for item in report["方法规则"]["指标适用性"]:
        lines.append(f"- {item['指标组']}：擅长{item['擅长']}；角色={item['默认角色']}。")
    lines.extend(["", "## 分层统计", ""])
    for key, value in report["统计"]["方法分层分布"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 方法重点候选 Top 20", ""])
    for idx, item in enumerate(report["方法重点候选Top"], 1):
        lines.append(
            f"{idx}. {item['名称']}({item['展示代码']})：方法分={item['综合方法分']}；"
            f"分位={item.get('市场平衡分位')}%；"
            f"趋势={item['趋势资格分']}；结构={item['强势结构分']}；行业={item['行业验证分']}；"
            f"风险={item['方法风险等级']}"
        )
    lines.extend(["", "## 方法待验证 Top 20", ""])
    for idx, item in enumerate(report["方法待验证Top"], 1):
        first_brake = item["刹车项"][0]["说明"] if item.get("刹车项") else "待验证"
        lines.append(f"{idx}. {item['名称']}({item['展示代码']})：方法分={item['综合方法分']}；首要验证={first_brake}")
    lines.extend(["", "## 学习要求", ""])
    for item in report["方法规则"]["长期学习规则"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 安全边界",
            "- 未真实发送企业微信。",
            "- 未触发n8n。",
            "- 未调用券商接口。",
            "- 未自动交易。",
            "- 未输出买卖指令。",
        ]
    )
    return "\n".join(lines) + "\n"


def make_learning_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 杰哥推荐方法学习说明",
        "",
        "这份文件教系统按固定顺序学习和复盘，不是交易指令。",
        "",
        "## 数据怎么抓",
        "",
    ]
    for item in METHOD_RULE["数据抓取先后顺序"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 怎么分析", ""])
    for item in METHOD_RULE["分析先后顺序"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 方法主次", ""])
    if report.get("上位规则摘要"):
        lines.append(f"- 先继承全系统上位规则：{report['上位规则摘要'].get('名称')}。")
        lines.append("- 杰哥推荐只是强势样本推荐场景的专用方法，不能替代通用分析判断机制。")
    for item in METHOD_RULE["方法法阶"]:
        lines.append(f"- {item['层级']}：{item['规则']}")
    lines.extend(["", "## 市场环境怎么平衡", ""])
    lines.append(f"- 本次市场状态：{report['市场环境']['市场状态']}，市场温度分：{report['市场环境']['市场温度分']}。")
    lines.append(f"- {report['市场环境']['说明']}")
    lines.extend(["", "## 怎么长期修正", ""])
    for item in METHOD_RULE["长期学习规则"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 本次学习任务队列", ""])
    for item in report["学习任务队列"][:30]:
        lines.append(
            f"- {item['名称']}({item['展示代码']})：{item['任务类型']}；"
            f"复盘重点={';'.join(item['复盘重点'])}"
        )
    return "\n".join(lines) + "\n"


def apply_market_balanced_layers(scored: list[dict[str, Any]], market: dict[str, Any]) -> None:
    total = len(scored)
    if not total:
        return
    focus_pct = safe_float(market.get("重点候选最大分位"), 7.0) or 7.0
    watch_pct = safe_float(market.get("待验证最大分位"), 20.0) or 20.0
    focus_score = safe_float(market.get("重点最低方法分"), 86.0) or 86.0
    watch_score = safe_float(market.get("待验证最低方法分"), 74.0) or 74.0

    for idx, item in enumerate(scored, 1):
        rank_pct = idx / total * 100
        original_layer = item.get("方法分层")
        method_score = safe_float(item.get("综合方法分"), 0.0) or 0.0
        template_passed = int(safe_float(item.get("第二阶段趋势模板通过数"), 0) or 0)
        pattern_score = safe_float(item.get("强势结构分"), 0.0) or 0.0
        risk_level = str(item.get("方法风险等级") or "")
        core_gate = safe_bool(item.get("核心门槛通过"))
        crowding_state = str(item.get("行业拥挤状态") or "正常")

        if (
            core_gate
            and method_score >= focus_score
            and rank_pct <= focus_pct
            and template_passed >= 6
            and pattern_score >= 58
            and risk_level in {"通过", "P1待验证"}
            and crowding_state != "高拥挤"
        ):
            balanced_layer = "方法重点候选"
            reason = "核心门槛通过，且方法分与市场横截面分位均进入重点区。"
        elif (
            core_gate
            and method_score >= watch_score
            and rank_pct <= watch_pct
            and template_passed >= 5
            and risk_level != "P0刹车"
        ):
            balanced_layer = "方法待验证"
            reason = "核心门槛基本通过，但市场分位或风险项未达到重点标准。"
        elif method_score >= 60 and risk_level != "P0刹车":
            balanced_layer = "方法观察"
            reason = "具备部分方法证据，但未达到当期市场环境下的前列要求。"
        else:
            balanced_layer = "方法暂缓"
            reason = "核心门槛、风险刹车或相对排名不足。"

        item["市场平衡排名"] = idx
        item["市场平衡分位"] = round(rank_pct, 4)
        item["市场环境"] = market.get("市场状态")
        item["市场温度分"] = market.get("市场温度分")
        item["市场平衡规则"] = {
            "重点候选最大分位": focus_pct,
            "待验证最大分位": watch_pct,
            "重点最低方法分": focus_score,
            "待验证最低方法分": watch_score,
        }
        item["市场平衡说明"] = reason
        item["方法分层"] = balanced_layer
        item["市场平衡调层"] = original_layer != balanced_layer
        item["学习标记"]["需要复盘"] = balanced_layer in {"方法重点候选", "方法待验证"}


def main() -> None:
    candidates = load_candidates()
    features = load_json(active_feature_path(), [])
    feature_rows = [item for item in features if isinstance(item, dict)] if isinstance(features, list) else []
    feature_map = build_map(feature_rows)
    kline_map = load_kline_map()
    industry_map = build_industry_map()
    crowding_map = compute_industry_crowding(feature_rows)
    market_context = calc_market_context(feature_rows)

    scored: list[dict[str, Any]] = []
    for candidate in candidates:
        code = normalize_code(candidate.get("代码") or candidate.get("展示代码"))
        feature = feature_map.get(code, {})
        industry_name = candidate.get("行业") or feature.get("行业") or "未知"
        scored.append(
            score_one(
                candidate=candidate,
                feature=feature,
                kline=kline_map.get(code, []),
                industry=industry_map.get(str(industry_name), {}),
                crowding=crowding_map.get(str(industry_name), {}),
                market_context=market_context,
            )
        )

    scored.sort(key=lambda item: (item["综合方法分"], item["原始推荐分"]), reverse=True)
    apply_market_balanced_layers(scored, market_context)
    layer_counter = Counter(item["方法分层"] for item in scored)
    risk_counter = Counter(item["方法风险等级"] for item in scored)
    industry_layer_counter: dict[str, Counter[str]] = defaultdict(Counter)
    for item in scored:
        industry_layer_counter[str(item.get("行业") or "未知")][item["方法分层"]] += 1

    learning_tasks = [
        {
            "代码": item["代码"],
            "展示代码": item["展示代码"],
            "名称": item["名称"],
            "行业": item["行业"],
            "任务类型": "重点候选复盘" if item["方法分层"] == "方法重点候选" else "待验证复盘",
            "生成依据": {
                "综合方法分": item["综合方法分"],
                "方法分层": item["方法分层"],
                "方法风险等级": item["方法风险等级"],
            },
            "复盘周期": item["学习标记"]["复盘周期"],
            "复盘重点": item["学习标记"]["复盘重点"],
        }
        for item in scored
        if item["学习标记"]["需要复盘"]
    ]

    universal_mechanism = load_json(UNIVERSAL_MECHANISM_PATH, {})
    universal_summary = {
        "名称": universal_mechanism.get("名称", "股票通用分析判断机制"),
        "路径": str(UNIVERSAL_MECHANISM_PATH),
        "继承关系": "杰哥推荐分析方法v1是通用分析判断机制在强势样本推荐场景下的专用落地；通用机制的市场环境、指标主辅、证据法阶和安全边界优先。",
        "总原则": universal_mechanism.get("总原则", [])[:5],
        "分析法阶": [item.get("层级") for item in universal_mechanism.get("分析法阶", [])],
    }

    report = {
        "名称": "杰哥推荐分析方法v1报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "输入": {
            "当前候选股相似度识别": str(CANDIDATE_PATH),
            "全候选量价特征": str(active_feature_path()),
            "原始全候选量价特征": str(FEATURE_PATH),
            "P0增强量价特征": str(P0_FEATURE_PATH),
            "历史K线": str(KLINE_PATH),
            "行业归因": str(INDUSTRY_PATH),
            "通用分析判断机制": str(UNIVERSAL_MECHANISM_PATH),
        },
        "上位规则摘要": universal_summary,
        "方法规则": METHOD_RULE,
        "统计": {
            "候选数量": len(scored),
            "方法分层分布": dict(layer_counter),
            "风险等级分布": dict(risk_counter),
            "学习任务数量": len(learning_tasks),
            "方法重点候选数量": layer_counter.get("方法重点候选", 0),
            "方法待验证数量": layer_counter.get("方法待验证", 0),
            "市场平衡调层数量": sum(1 for item in scored if item.get("市场平衡调层")),
        },
        "市场环境": market_context,
        "行业方法分布": {key: dict(value) for key, value in industry_layer_counter.items()},
        "方法重点候选Top": [item for item in scored if item["方法分层"] == "方法重点候选"][:20],
        "方法待验证Top": [item for item in scored if item["方法分层"] == "方法待验证"][:20],
        "方法刹车样本Top": [item for item in scored if item["刹车项"]][:50],
        "学习任务队列": learning_tasks,
        "全量方法评分": scored,
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "输出交易指令": False,
        },
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    score_path = OUT_DIR / f"全候选方法评分_{timestamp}.json"
    latest_score_path = OUT_DIR / "全候选方法评分_最新.json"
    report_json_path = OUT_DIR / f"杰哥推荐分析方法v1报告_{timestamp}.json"
    latest_report_json_path = OUT_DIR / "杰哥推荐分析方法v1报告_最新.json"
    report_md_path = OUT_DIR / f"杰哥推荐分析方法v1报告_{timestamp}.md"
    latest_report_md_path = OUT_DIR / "杰哥推荐分析方法v1报告_最新.md"
    learning_json_path = OUT_DIR / "杰哥推荐分析方法学习说明_最新.json"
    learning_md_path = OUT_DIR / "杰哥推荐分析方法学习说明_最新.md"

    write_json(score_path, scored)
    write_json(latest_score_path, scored)
    write_json(report_json_path, report)
    write_json(latest_report_json_path, report)
    markdown = make_report_markdown(report)
    write_text(report_md_path, markdown)
    write_text(latest_report_md_path, markdown)
    write_json(
        learning_json_path,
        {
            "上位规则摘要": universal_summary,
            "方法规则": METHOD_RULE,
            "学习任务队列": learning_tasks,
            "安全边界": report["安全边界"],
        },
    )
    write_text(learning_md_path, make_learning_markdown(report))

    print(
        json.dumps(
            {
                "方法评分": "完成",
                "候选数量": len(scored),
                "方法重点候选数量": layer_counter.get("方法重点候选", 0),
                "方法待验证数量": layer_counter.get("方法待验证", 0),
                "学习任务数量": len(learning_tasks),
                "报告": str(latest_report_md_path),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
