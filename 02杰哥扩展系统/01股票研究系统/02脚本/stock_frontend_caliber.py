# -*- coding: utf-8 -*-
"""
股票前台口径统一工具。

安全边界：只提供本地文本映射；不联网、不发送企业微信、不调用券商接口、不自动交易。
"""

from __future__ import annotations

from typing import Any


RESEARCH_LEVELS = ("重点研究", "常规研究", "观察")
CURRENT_STATUSES = ("等待承接", "等待转强", "风险复核", "回避")
NON_ADVICE_STATEMENT = "仅供研究参考，不构成投资建议，不作为买卖指令。"
RECOMMENDATION_DISPLAY_WORDS = ("重点关注", "常规推荐", "重点推荐", "推荐", "买入研究信号", "买入信号")
RISK_DISPLAY_WORDS = ("风险复核", "继续回避", "回避", "暂不建议关注", "离场观望", "卖出研究信号", "卖出/退出研究信号")


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_frontend_caliber(
    raw_level: Any = "",
    score: Any = None,
    confidence: Any = "",
    risk_text: Any = "",
    holding_mode: bool = False,
) -> dict[str, str]:
    """把旧结论/评分统一成前台双字段：研究等级 + 当前状态。"""
    text = str(raw_level or "").strip()
    risk = str(risk_text or "")
    number = _to_float(score)
    confidence_text = str(confidence or "").strip().lower()

    risk_tokens = ("风险", "破位", "利空", "回撤", "失败", "离场", "退出", "回避")
    has_risk = any(token in text or token in risk for token in risk_tokens)

    if text in RESEARCH_LEVELS:
        research_level = text
    elif text in {"重点关注", "重点推荐", "高优先级研究对象", "重点"}:
        research_level = "重点研究"
    elif text in {"常规推荐", "可纳入观察", "观察等待", "观察股票", "可观察", "继续持仓观察", "降低关注"}:
        research_level = "常规研究"
    elif text in {"暂不建议关注", "暂不关注", "风险复核", "离场观望", "回避"}:
        research_level = "观察"
    elif number is not None:
        if number >= 80:
            research_level = "重点研究"
        elif number >= 60:
            research_level = "常规研究"
        else:
            research_level = "观察"
    else:
        research_level = "观察"

    if text in CURRENT_STATUSES:
        current_status = text
    elif text in {"风险复核"} or (has_risk and text not in {"暂不建议关注", "暂不关注", "回避"}):
        current_status = "风险复核"
    elif text in {"暂不建议关注", "暂不关注", "离场观望", "回避"}:
        current_status = "回避"
    elif holding_mode and text in {"降低关注"}:
        current_status = "等待转强"
    elif research_level == "重点研究":
        current_status = "等待承接"
    elif research_level == "常规研究":
        current_status = "等待转强" if confidence_text in {"low", "低"} else "等待承接"
    elif number is not None and number < 45:
        current_status = "回避"
    else:
        current_status = "等待转强"

    if has_risk and text not in {"回避", "离场观望"}:
        current_status = "风险复核"
        if research_level == "重点研究":
            research_level = "常规研究"
    elif has_risk and current_status not in {"风险复核", "回避"}:
        current_status = "风险复核"
        if research_level == "重点研究":
            research_level = "常规研究"

    return {
        "研究等级": research_level,
        "当前状态": current_status,
        "口径": f"研究等级={research_level}；当前状态={current_status}",
    }


def caliber_from_report(report: dict[str, Any], fallback_level: Any = "", risk_text: Any = "") -> dict[str, str]:
    confidence = report.get("confidence", {}) if isinstance(report, dict) else {}
    confidence_level = confidence.get("level") if isinstance(confidence, dict) else confidence
    return normalize_frontend_caliber(
        raw_level=(report.get("conclusion_text") if isinstance(report, dict) else "") or fallback_level,
        score=report.get("total_score") if isinstance(report, dict) else None,
        confidence=confidence_level,
        risk_text=risk_text,
    )


def current_status_action(status: str) -> str:
    if status == "等待承接":
        return "等待承接条件确认，不把研究判断写成买卖动作。"
    if status == "等待转强":
        return "等待转强条件确认，暂不提高到更高研究优先级。"
    if status == "风险复核":
        return "先做风险复核，等风险线修复和证据补齐后再重新评估。"
    if status == "回避":
        return "当前回避，不提高研究优先级。"
    return "保持研究观察，等待下一轮证据刷新。"


def operation_advice_from_caliber(caliber: dict[str, str] | None = None, fallback_level: Any = "") -> str:
    caliber = caliber or {}
    status = str(caliber.get("当前状态") or "")
    level = str(caliber.get("研究等级") or fallback_level or "")
    raw = str(fallback_level or "")
    if status in {"风险复核", "回避"} or any(token in raw for token in ("风险复核", "回避", "暂不建议")):
        return current_status_action(status or "风险复核")
    if status == "等待转强" or "观察" in raw:
        return "等待转强条件确认，暂不提高研究优先级。"
    if level in {"重点研究", "常规研究"}:
        return "仅作研究跟踪，等待承接、转强和成交条件确认。"
    return "保持观察，等待证据补齐。"


def display_signal_for_caliber(caliber: dict[str, str] | None, signal: dict[str, Any] | None = None) -> dict[str, Any]:
    signal = dict(signal or {})
    caliber = caliber or {}
    status = str(caliber.get("当前状态") or "")
    research_level = str(caliber.get("研究等级") or "")
    raw_strength = signal.get("显示星数", signal.get("星级", 0))
    try:
        strength = float(raw_strength or 0)
    except (TypeError, ValueError):
        strength = 0.0
    if status in {"风险复核", "回避"}:
        level = "风险复核" if status == "风险复核" else "回避观察"
        return {
            **signal,
            "方向": "风险复核信号",
            "级别": level,
            "颜色": "绿色",
            "色值": "#2E7D32",
            "星级": max(1.0, strength),
            "显示星数": max(1, int(round(max(1.0, strength)))),
            "强度": signal.get("强度") or f"{max(1.0, strength):g}/5",
            "说明": "当前展示以风险复核/回避口径为准，不展示机会类信号。",
        }
    level = "研究价值评分"
    if research_level == "重点研究":
        level = "高研究价值"
    elif research_level == "常规研究":
        level = "常规研究价值"
    elif research_level == "观察":
        level = "观察研究价值"
    return {
        **signal,
        "方向": "研究价值信号",
        "级别": level,
        "颜色": "金色",
        "色值": "#FFD700",
        "星级": strength,
        "显示星数": int(round(strength)) if strength else 0,
        "强度": signal.get("强度") or (f"{strength:g}/5" if strength else "0/5"),
        "说明": "仅表示研究价值评分，不构成交易动作建议。",
    }


def sanitize_display_words(text: Any) -> str:
    safe = str(text or "")
    replacements = {
        "买入研究信号": "研究价值信号",
        "买入信号": "研究价值信号",
        "卖出/退出研究信号": "风险复核信号",
        "卖出研究信号": "风险复核信号",
        "卖出信号": "风险复核信号",
        "重点推荐": "高研究价值",
        "重点关注": "高研究价值",
        "常规推荐": "常规研究价值",
        "达标推荐": "达标研究对象",
        "推荐股票": "研究对象",
        "股票推荐": "股票研究",
    }
    for old, new in replacements.items():
        safe = safe.replace(old, new)
    return safe


def detect_display_conflict(text: Any) -> dict[str, Any]:
    value = str(text or "")
    recommendation_hits = [word for word in RECOMMENDATION_DISPLAY_WORDS if word in value]
    risk_hits = [word for word in RISK_DISPLAY_WORDS if word in value]
    return {
        "has_conflict": bool(recommendation_hits and risk_hits),
        "recommendation_hits": recommendation_hits,
        "risk_hits": risk_hits,
    }


def sanitize_trade_words(text: Any) -> str:
    safe = sanitize_display_words(text)
    replacements = {
        "买入研究信号": "研究价值信号",
        "买入指令": "交易指令",
        "卖出/退出研究信号": "风险复核信号",
        "卖出研究信号": "风险复核信号",
        "卖出指令": "交易指令",
        "重点推荐": "高研究价值",
        "常规推荐": "常规研究价值",
    }
    for old, new in replacements.items():
        safe = safe.replace(old, new)
    return safe
