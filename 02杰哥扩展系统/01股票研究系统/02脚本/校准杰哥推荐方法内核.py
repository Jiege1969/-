# -*- coding: utf-8 -*-
"""
名称：校准杰哥推荐方法内核.py
作用：读取【杰哥推荐】候选评分、量价特征和行业归因，生成方法内核冲突清单与分层校准建议。
触发方式：python 校准杰哥推荐方法内核.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地03数据；只写03数据/278杰哥推荐方法内核校准；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不输出买卖指令。
标识：jiege-recommendation-method-kernel-calibrator-v1
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def stock_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = stock_root()
CANDIDATE_PATH = ROOT / "03数据" / "270杰哥推荐方法内核" / "当前候选股相似度识别_最新.json"
FEATURE_PATH = ROOT / "03数据" / "272杰哥推荐量价特征" / "全候选量价特征_最新.json"
P0_ENHANCED_FEATURE_PATH = ROOT / "03数据" / "279杰哥推荐P0指标补足" / "全候选P0增强量价特征_最新.json"
METHOD_SCORE_PATH = ROOT / "03数据" / "280杰哥推荐分析方法v1" / "全候选方法评分_最新.json"
INDUSTRY_PATH = ROOT / "03数据" / "273杰哥推荐行业归因" / "杰哥推荐行业归因报告_最新.json"
OUT_DIR = ROOT / "03数据" / "278杰哥推荐方法内核校准"


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


def safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value in (None, "", "-"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def normalize_code(value: Any) -> str:
    text = str(value or "").strip().lower()
    if "." in text:
        code, market = text.split(".", 1)
        if market.lower() == "sh":
            return "sh" + code
        if market.lower() == "sz":
            return "sz" + code
        if market.lower() == "bj":
            return "bj" + code
    return text


def list_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.replace("，", " ").split() if item.strip()]
    return []


def star_count(value: Any) -> int:
    text = str(value or "")
    return text.count("⭐")


def expected_stars(score: float) -> int:
    if score >= 90:
        return 5
    if score >= 80:
        return 4
    if score >= 70:
        return 3
    if score >= 60:
        return 2
    return 1


def expected_layer(score: float) -> str:
    if score >= 90:
        return "优先研究"
    if score >= 80:
        return "观察验证"
    return "暂不进入推荐"


def load_candidates() -> list[dict[str, Any]]:
    raw = load_json(CANDIDATE_PATH, {})
    if isinstance(raw, dict):
        candidates = raw.get("候选", [])
        return candidates if isinstance(candidates, list) else []
    if isinstance(raw, list):
        return raw
    return []


def build_feature_map() -> dict[str, dict[str, Any]]:
    rows = load_json(active_feature_path(), [])
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


def active_feature_path() -> Path:
    return P0_ENHANCED_FEATURE_PATH if P0_ENHANCED_FEATURE_PATH.exists() else FEATURE_PATH


def build_industry_map() -> dict[str, dict[str, Any]]:
    report = load_json(INDUSTRY_PATH, {})
    rows = report.get("全部行业归因", []) if isinstance(report, dict) else []
    mapping: dict[str, dict[str, Any]] = {}
    if not isinstance(rows, list):
        return mapping
    for item in rows:
        if isinstance(item, dict) and item.get("行业"):
            mapping[str(item.get("行业"))] = item
    return mapping


def build_method_score_map() -> dict[str, dict[str, Any]]:
    rows = load_json(METHOD_SCORE_PATH, [])
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


def add_issue(issues: list[dict[str, Any]], code: str, title: str, severity: str, detail: str, advice: str) -> None:
    issues.append(
        {
            "问题代码": code,
            "问题": title,
            "级别": severity,
            "说明": detail,
            "处理建议": advice,
        }
    )


def calibrate_row(candidate: dict[str, Any], feature: dict[str, Any], industry: dict[str, Any], method: dict[str, Any]) -> dict[str, Any]:
    code = normalize_code(candidate.get("代码") or feature.get("代码") or candidate.get("展示代码"))
    name = candidate.get("名称") or feature.get("名称") or ""
    display_code = candidate.get("展示代码") or feature.get("展示代码") or code
    industry_name = candidate.get("行业") or feature.get("行业") or "未知"

    score = safe_float(candidate.get("杰哥推荐相似度分") or feature.get("杰哥推荐相似度分"), 0.0) or 0.0
    strong_similarity = safe_float(candidate.get("强势相似度"), None)
    failure_similarity = safe_float(candidate.get("失败相似度"), None)
    conclusion = str(candidate.get("识别结论") or feature.get("识别结论") or "")
    tags = list_tags(feature.get("量价模式标签") if feature else candidate.get("量价模式标签"))

    change_60 = safe_float(feature.get("60日涨跌幅") if feature else candidate.get("技术指标", {}).get("60日涨跌幅"), 0.0) or 0.0
    change_250 = safe_float(feature.get("250日涨跌幅") if feature else candidate.get("技术指标", {}).get("250日涨跌幅"), 0.0) or 0.0
    amount_ratio = safe_float(feature.get("成交额20_60比"), None)
    volume_ratio = safe_float(feature.get("量比5日"), None)
    volume_volatility_60 = safe_float(feature.get("成交量60日波动率"), None)
    amount_volatility_60 = safe_float(feature.get("成交额60日波动率"), None)
    drawdown_60 = safe_float(feature.get("60日最大回撤"), 0.0) or 0.0
    ma_bull = safe_bool(feature.get("均线多头排列")) if feature else bool("均线多头" in tags)
    breakthrough = safe_bool(feature.get("60日突破")) if feature else bool("突破信号" in tags)
    weekly_ma_bull = safe_bool(feature.get("周线MA多头")) if feature else False
    weekly_macd_up = safe_bool(feature.get("周线MACD向上")) if feature else False
    weekly_above_ma20 = safe_bool(feature.get("周线收盘在MA20上")) if feature else False
    weekly_state = str(feature.get("周线趋势状态") or "待补足")
    industry_dynamic_score = safe_float(feature.get("行业动态强度分"), None)
    industry_dynamic_rank = feature.get("行业动态排名")
    industry_dynamic_state = str(feature.get("行业动态状态") or "待补足")
    kline_count = int(safe_float(candidate.get("K线数量") or feature.get("K线数量"), 0) or 0)
    method_score = safe_float(method.get("综合方法分"), None)
    method_layer = str(method.get("方法分层") or "待生成")
    method_risk_level = str(method.get("方法风险等级") or "待生成")
    trend_template_passed = safe_float(method.get("第二阶段趋势模板通过数"), None)
    trend_template_total = safe_float(method.get("第二阶段趋势模板总数"), None)
    vcp_state = str(method.get("VCP状态") or "待生成")
    industry_crowding_state = str(method.get("行业拥挤状态") or "待生成")
    market_context_state = str(method.get("市场环境") or "待生成")
    market_rank_pct = safe_float(method.get("市场平衡分位"), None)
    core_gate_passed = safe_bool(method.get("核心门槛通过"))

    industry_label = str(industry.get("归因标签") or "未知")
    strong_sample_count = int(safe_float(industry.get("强势样本数"), 0) or 0)
    failure_sample_count = int(safe_float(industry.get("失败样本数"), 0) or 0)
    strong_rep = safe_float(industry.get("强势过度代表指数"), 0.0) or 0.0
    failure_rep = safe_float(industry.get("失败过度代表指数"), 0.0) or 0.0

    issues: list[dict[str, Any]] = []

    if expected_layer(score) != conclusion:
        add_issue(
            issues,
            "layer_score_mismatch",
            "分数与识别结论不一致",
            "P1",
            f"分数={score}，当前结论={conclusion}，按阈值应为{expected_layer(score)}。",
            "复核分层阈值或前台映射，避免高分低配或低分高配。",
        )

    actual_stars = star_count(candidate.get("星级"))
    if actual_stars and actual_stars != expected_stars(score):
        add_issue(
            issues,
            "star_score_mismatch",
            "星级与100分制不一致",
            "P1",
            f"分数={score}，星级={actual_stars}，按当前规则应为{expected_stars(score)}星。",
            "统一星级只作为分数投影，不再独立表达另一套强度。",
        )

    if score >= 90 and not tags:
        add_issue(
            issues,
            "high_score_empty_tags",
            "高分但量价标签为空",
            "P0",
            f"分数={score}，量价标签为空。",
            "不得直接进入重点关注，先回到量价特征提取补证据。",
        )

    if score >= 90 and change_60 < 0:
        add_issue(
            issues,
            "high_score_negative_60d",
            "高分但60日走势为负",
            "P0",
            f"分数={score}，60日涨跌幅={change_60}%。",
            "降为观察验证，必须说明短期未确认。",
        )
    elif score >= 90 and change_60 < 10:
        add_issue(
            issues,
            "high_score_weak_60d",
            "高分但60日走势偏弱",
            "P1",
            f"分数={score}，60日涨跌幅={change_60}%。",
            "保留观察，但重点关注需等待短期量价再确认。",
        )

    if score >= 90 and not ma_bull:
        add_issue(
            issues,
            "high_score_no_ma_bull",
            "高分但均线多头未确认",
            "P1",
            f"分数={score}，均线多头排列={ma_bull}。",
            "不直接进入重点关注，等待结构重新转强。",
        )

    if score >= 90 and industry_label == "弱势/失败集中行业":
        add_issue(
            issues,
            "high_score_reverse_industry",
            "高分但处于逆风行业",
            "P0",
            f"行业={industry_name}，行业标签={industry_label}。",
            "行业归因只能作为刹车，需降为观察验证并提高验证条件。",
        )

    if score >= 90 and industry_dynamic_state == "动态逆风":
        add_issue(
            issues,
            "high_score_dynamic_industry_headwind",
            "高分但行业动态逆风",
            "P0",
            f"行业={industry_name}，行业动态强度分={industry_dynamic_score}，动态排名={industry_dynamic_rank}。",
            "动态行业强度是前台刹车项，降为观察验证并等待行业排名修复。",
        )
    elif score >= 90 and industry_dynamic_state == "动态中性":
        add_issue(
            issues,
            "high_score_dynamic_industry_neutral",
            "高分但行业动态未共振",
            "P1",
            f"行业={industry_name}，行业动态强度分={industry_dynamic_score}，动态状态={industry_dynamic_state}。",
            "保留观察，前台不得写成板块共振。",
        )

    if score >= 90 and amount_ratio is not None and amount_ratio < 1.0:
        add_issue(
            issues,
            "high_score_amount_not_expanding",
            "高分但成交额未放大",
            "P1",
            f"成交额20_60比={amount_ratio}。",
            "重点关注需等待成交额重新放大。",
        )

    if score >= 90 and volume_ratio is not None and volume_ratio < 0.8:
        add_issue(
            issues,
            "high_score_volume_cooling",
            "高分但短期量能降温",
            "P1",
            f"量比5日={volume_ratio}。",
            "保留观察，不宜在前台表达成强势确认。",
        )

    if score >= 90 and amount_volatility_60 is not None and amount_volatility_60 >= 1.3:
        add_issue(
            issues,
            "high_score_amount_volatility_extreme",
            "高分但成交额波动过大",
            "P1",
            f"成交额60日波动率={amount_volatility_60}。",
            "需要观察成交连续性，避免把一次性放量误判为稳定强势。",
        )

    if score >= 90 and volume_volatility_60 is not None and volume_volatility_60 >= 1.3:
        add_issue(
            issues,
            "high_score_volume_volatility_extreme",
            "高分但成交量波动过大",
            "P1",
            f"成交量60日波动率={volume_volatility_60}。",
            "需要确认量能是否连续，不宜只凭尖峰成交提高前台优先级。",
        )

    if score >= 90 and (not weekly_above_ma20 or (not weekly_ma_bull and not weekly_macd_up)):
        add_issue(
            issues,
            "high_score_weekly_trend_not_confirmed",
            "高分但周线趋势未确认",
            "P1",
            f"周线状态={weekly_state}，周线MA多头={weekly_ma_bull}，周线MACD向上={weekly_macd_up}，周线收盘在MA20上={weekly_above_ma20}。",
            "作为多周期验证刹车，前台只写待验证，不写成趋势共振。",
        )

    if score >= 90 and method_layer == "方法暂缓":
        add_issue(
            issues,
            "high_score_method_rejected",
            "高分但分析方法v1暂缓",
            "P0",
            f"方法分={method_score}，方法分层={method_layer}，风险等级={method_risk_level}，趋势模板={trend_template_passed}/{trend_template_total}。",
            "降为观察验证；前台必须以方法刹车为准，不得只按相似度投影重点关注。",
        )

    if score >= 90 and method_layer == "方法观察":
        add_issue(
            issues,
            "high_score_method_observation",
            "高分但分析方法v1仅观察",
            "P1",
            f"方法分={method_score}，方法分层={method_layer}，VCP={vcp_state}，行业拥挤={industry_crowding_state}。",
            "保留待验证，不进入重点关注候选。",
        )

    if score >= 90 and method_layer == "方法待验证":
        add_issue(
            issues,
            "high_score_method_wait_verify",
            "高分但分析方法v1仍待验证",
            "P1",
            f"方法分={method_score}，方法分层={method_layer}，市场环境={market_context_state}，市场分位={market_rank_pct}%。",
            "方法层优先于相似度分数，前台不得越级为重点关注候选。",
        )

    if score >= 90 and method_risk_level == "P1多项待验证":
        add_issue(
            issues,
            "high_score_method_multi_p1",
            "高分但方法刹车项较多",
            "P1",
            f"方法风险等级={method_risk_level}，方法分={method_score}。",
            "前台降低表达强度，单股材料包展示关键待验证条件。",
        )

    if score >= 90 and not core_gate_passed and method:
        add_issue(
            issues,
            "high_score_core_gate_failed",
            "高分但方法核心门槛未通过",
            "P0",
            f"方法分={method_score}，方法分层={method_layer}，核心门槛通过={core_gate_passed}。",
            "核心门槛优先于指标加分，必须降为观察验证。",
        )

    if score >= 90 and market_rank_pct is not None and market_rank_pct > 10 and method_layer == "方法重点候选":
        add_issue(
            issues,
            "high_score_market_rank_not_top",
            "高分但市场横截面排名不够靠前",
            "P1",
            f"市场环境={market_context_state}，市场分位={market_rank_pct}%。",
            "牛市或普涨时只保留相对更靠前样本，避免满足条件股票过多导致名单膨胀。",
        )

    if score >= 90 and drawdown_60 < -25:
        add_issue(
            issues,
            "high_score_large_drawdown",
            "高分但60日回撤偏大",
            "P1",
            f"60日最大回撤={drawdown_60}%。",
            "需要在单股页明确风险线和修复条件。",
        )

    if failure_similarity is not None and strong_similarity is not None:
        spread = strong_similarity - failure_similarity
        if score >= 85 and (failure_similarity >= 55 or spread < 18):
            add_issue(
                issues,
                "failure_control_too_close",
                "失败对照距离不足",
                "P0",
                f"强势相似度={strong_similarity}，失败相似度={failure_similarity}，差值={round(spread, 2)}。",
                "降为观察验证；前台必须提示失败样本校验未完全拉开。",
            )

    if industry_label in {"强势共振行业", "结构活跃行业"} and strong_sample_count < 5:
        add_issue(
            issues,
            "thin_industry_evidence",
            "行业样本偏薄",
            "P2",
            f"行业={industry_name}，强势样本数={strong_sample_count}。",
            "行业只作为弱解释，不提高推荐层级。",
        )

    if industry_label == "中性观察行业" and failure_rep >= 2.5 and strong_sample_count == 0:
        add_issue(
            issues,
            "neutral_but_failure_heavy",
            "中性行业存在失败集中风险",
            "P2",
            f"行业={industry_name}，失败过度代表指数={failure_rep}，失败样本数={failure_sample_count}。",
            "单股页应提示行业侧不加分，并依赖个股量价确认。",
        )

    if kline_count and kline_count < 750:
        add_issue(
            issues,
            "history_window_incomplete",
            "近三年样本窗口不完整",
            "P2",
            f"K线数量={kline_count}。",
            "作为证据边界提示，不直接否定，但不得包装成完整三年统计。",
        )

    p0_count = sum(1 for item in issues if item["级别"] == "P0")
    p1_count = sum(1 for item in issues if item["级别"] == "P1")

    if p0_count:
        calibrated_layer = "观察验证"
    elif score >= 92 and p1_count == 0:
        calibrated_layer = "重点关注候选"
    elif score >= 90:
        calibrated_layer = "重点关注待验证"
    elif score >= 80:
        calibrated_layer = "观察验证"
    else:
        calibrated_layer = "暂不进入推荐"

    if industry_label == "弱势/失败集中行业" and calibrated_layer == "重点关注候选":
        calibrated_layer = "重点关注待验证"

    if method_layer in {"方法暂缓", "方法观察", "方法待验证"} and calibrated_layer == "重点关注候选":
        calibrated_layer = "重点关注待验证"

    return {
        "代码": code,
        "展示代码": display_code,
        "名称": name,
        "行业": industry_name,
        "原始识别结论": conclusion,
        "原始分数": round(score, 2),
        "原始星级": actual_stars or None,
        "校准建议": calibrated_layer,
        "问题数量": len(issues),
        "P0问题数": p0_count,
        "P1问题数": p1_count,
        "行业归因标签": industry_label,
        "行业强势样本数": strong_sample_count,
        "行业失败样本数": failure_sample_count,
        "行业强势过度代表指数": strong_rep,
        "行业失败过度代表指数": failure_rep,
        "60日涨跌幅": round(change_60, 4),
        "250日涨跌幅": round(change_250, 4),
        "成交额20_60比": amount_ratio,
        "量比5日": volume_ratio,
        "成交量60日波动率": volume_volatility_60,
        "成交额60日波动率": amount_volatility_60,
        "60日最大回撤": drawdown_60,
        "均线多头排列": ma_bull,
        "60日突破": breakthrough,
        "周线MA多头": weekly_ma_bull,
        "周线MACD向上": weekly_macd_up,
        "周线收盘在MA20上": weekly_above_ma20,
        "周线趋势状态": weekly_state,
        "行业动态强度分": industry_dynamic_score,
        "行业动态排名": industry_dynamic_rank,
        "行业动态状态": industry_dynamic_state,
        "综合方法分": method_score,
        "方法分层": method_layer,
        "方法风险等级": method_risk_level,
        "第二阶段趋势模板通过数": trend_template_passed,
        "第二阶段趋势模板总数": trend_template_total,
        "核心门槛通过": core_gate_passed,
        "VCP状态": vcp_state,
        "行业拥挤状态": industry_crowding_state,
        "市场环境": market_context_state,
        "市场平衡分位": market_rank_pct,
        "量价模式标签": tags,
        "强势相似度": strong_similarity,
        "失败相似度": failure_similarity,
        "问题清单": issues,
    }


def make_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    summary = report["统计"]
    lines.extend(
        [
            "# 杰哥推荐方法内核校准报告",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 候选数量：{summary['候选数量']}",
            f"- P0冲突：{summary['P0问题总数']}",
            f"- P1待复核：{summary['P1问题总数']}",
            f"- 校准后重点关注候选：{summary['校准分层分布'].get('重点关注候选', 0)}",
            f"- 校准后重点关注待验证：{summary['校准分层分布'].get('重点关注待验证', 0)}",
            f"- 校准后观察验证：{summary['校准分层分布'].get('观察验证', 0)}",
            "",
            "## 一、判定原则",
            "",
            "1. 量价强弱是第一权重。",
            "2. 失败样本对照是刹车。",
            "3. 行业归因只解释顺逆风，不单独决定推荐。",
            "4. 证据缺口只做边界提示，不包装成确定结论。",
            "",
            "## 二、问题分布",
            "",
        ]
    )
    for code, count in report["问题类型分布"].most_common():
        lines.append(f"- {code}：{count}")

    lines.extend(["", "## 三、重点关注候选 Top 20", ""])
    for idx, item in enumerate(report["重点关注候选Top"], 1):
        lines.append(
            f"{idx}. {item['名称']}({item['展示代码']})：{item['原始分数']}；"
            f"行业={item['行业']}；60日={item['60日涨跌幅']}%；"
            f"行业标签={item['行业归因标签']}"
        )

    lines.extend(["", "## 四、重点关注待验证 Top 20", ""])
    for idx, item in enumerate(report["重点关注待验证Top"], 1):
        first_issue = item["问题清单"][0]["问题"] if item.get("问题清单") else "待验证"
        lines.append(
            f"{idx}. {item['名称']}({item['展示代码']})：{item['原始分数']}；"
            f"首要问题={first_issue}；行业={item['行业']}"
        )

    lines.extend(["", "## 五、P0冲突样本 Top 30", ""])
    for idx, item in enumerate(report["P0冲突样本Top"], 1):
        issue_text = "；".join(issue["问题"] for issue in item.get("问题清单", []) if issue["级别"] == "P0")
        lines.append(
            f"{idx}. {item['名称']}({item['展示代码']})：{item['原始分数']}；"
            f"原结论={item['原始识别结论']}；校准={item['校准建议']}；P0={issue_text}"
        )

    lines.extend(
        [
            "",
            "## 六、安全边界",
            "",
            "- 未真实发送企业微信。",
            "- 未触发n8n。",
            "- 未调用券商接口。",
            "- 未自动交易。",
            "- 未输出买卖指令。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    candidates = load_candidates()
    feature_map = build_feature_map()
    method_score_map = build_method_score_map()
    industry_map = build_industry_map()

    calibrated: list[dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        code = normalize_code(candidate.get("代码") or candidate.get("展示代码"))
        feature = feature_map.get(code, {})
        method = method_score_map.get(code, {})
        industry_name = candidate.get("行业") or feature.get("行业") or "未知"
        industry = industry_map.get(str(industry_name), {})
        calibrated.append(calibrate_row(candidate, feature, industry, method))

    layer_counter = Counter(item["校准建议"] for item in calibrated)
    original_counter = Counter(item["原始识别结论"] for item in calibrated)
    issue_counter: Counter[str] = Counter()
    severity_counter: Counter[str] = Counter()
    industry_issue_counter: dict[str, Counter[str]] = defaultdict(Counter)
    for item in calibrated:
        for issue in item["问题清单"]:
            issue_counter[issue["问题代码"]] += 1
            severity_counter[issue["级别"]] += 1
            industry_issue_counter[item["行业"]][issue["级别"]] += 1

    sorted_by_score = sorted(calibrated, key=lambda x: x["原始分数"], reverse=True)
    report = {
        "名称": "杰哥推荐方法内核校准报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "输入": {
            "当前候选股相似度识别": str(CANDIDATE_PATH),
            "全候选量价特征": str(active_feature_path()),
            "原始全候选量价特征": str(FEATURE_PATH),
            "P0增强量价特征": str(P0_ENHANCED_FEATURE_PATH),
            "使用P0增强量价特征": P0_ENHANCED_FEATURE_PATH.exists(),
            "分析方法v1评分": str(METHOD_SCORE_PATH),
            "使用分析方法v1评分": METHOD_SCORE_PATH.exists(),
            "行业归因报告": str(INDUSTRY_PATH),
        },
        "统计": {
            "候选数量": len(calibrated),
            "原始分层分布": dict(original_counter),
            "校准分层分布": dict(layer_counter),
            "P0问题总数": severity_counter.get("P0", 0),
            "P1问题总数": severity_counter.get("P1", 0),
            "P2问题总数": severity_counter.get("P2", 0),
            "有问题样本数": sum(1 for item in calibrated if item["问题数量"] > 0),
            "P0冲突样本数": sum(1 for item in calibrated if item["P0问题数"] > 0),
        },
        "问题类型分布": issue_counter,
        "行业问题分布": {key: dict(value) for key, value in industry_issue_counter.items()},
        "重点关注候选Top": [item for item in sorted_by_score if item["校准建议"] == "重点关注候选"][:20],
        "重点关注待验证Top": [item for item in sorted_by_score if item["校准建议"] == "重点关注待验证"][:20],
        "P0冲突样本Top": [item for item in sorted_by_score if item["P0问题数"] > 0][:30],
        "全量校准明细": sorted_by_score,
        "方法边界": [
            "本报告只做方法内核校准，不直接修改推荐名单。",
            "行业归因只能作为解释层和刹车项，不能单独作为推荐理由。",
            "重点关注候选仍需单股材料包补齐风险线、验证条件和证据边界。",
        ],
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "输出交易指令": False,
        },
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUT_DIR / f"杰哥推荐方法内核校准报告_{timestamp}.json"
    md_path = OUT_DIR / f"杰哥推荐方法内核校准报告_{timestamp}.md"
    latest_json = OUT_DIR / "杰哥推荐方法内核校准报告_最新.json"
    latest_md = OUT_DIR / "杰哥推荐方法内核校准报告_最新.md"

    write_json(json_path, report)
    write_json(latest_json, report)
    markdown = make_markdown(report)
    write_text(md_path, markdown)
    write_text(latest_md, markdown)

    print(json.dumps({"校准结论": "完成", "候选数量": len(calibrated), "P0冲突样本数": report["统计"]["P0冲突样本数"], "Markdown": str(latest_md)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
