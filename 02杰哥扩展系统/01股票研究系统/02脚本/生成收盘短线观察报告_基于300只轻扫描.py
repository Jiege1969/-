# -*- coding: utf-8 -*-
"""
名称：生成收盘短线观察报告_基于300只轻扫描.py
作用：用现有300只盘后轻扫描候选和技术指标，生成【收盘短线观察】报告样例。
安全边界：只读读取本地股票池和指标产物并写260包；不发送企业微信；不触发n8n；不接券商；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from 重点观察池晋级候选公共库 import register_promotion_candidate


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def money(value: Any) -> str:
    try:
        return f"{float(value):.2f}元"
    except (TypeError, ValueError):
        return "暂无"


def pct(value: Any) -> str:
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "暂无"


def code_key(code: str) -> str:
    return str(code or "").lower().replace(".", "")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def ratio_text(value: float) -> str:
    return f"{value:.2f}" if value > 0 else "暂无"


def build_indicator_index(*indicator_files: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for path in indicator_files:
        data = load_json(path, {})
        for item in data.get("技术指标", []):
            if isinstance(item, dict):
                index[code_key(item.get("代码", ""))] = item
    return index


def build_observation_index(path: Path) -> dict[str, dict[str, Any]]:
    data = load_json(path, {})
    index: dict[str, dict[str, Any]] = {}
    for item in data.get("逐股结果", []):
        if isinstance(item, dict):
            index[code_key(item.get("代码", ""))] = item
    return index


def build_history_index(history_path: Path) -> dict[str, dict[str, Any]]:
    data = load_json(history_path, {})
    index: dict[str, dict[str, Any]] = {}
    for item in data.get("历史K线", []):
        if isinstance(item, dict):
            index[code_key(item.get("代码", ""))] = item
    return index


def risk_refresh_is_valid(status: dict[str, Any]) -> bool:
    generated_date = str(status.get("生成时间") or "")[:10]
    return bool(status.get("刷新成功") is True and generated_date == datetime.now().strftime("%Y-%m-%d"))


def preflight_is_valid(status: dict[str, Any]) -> bool:
    generated_date = str(status.get("生成时间") or "")[:10]
    return bool(status.get("结论") == "pass" and generated_date == datetime.now().strftime("%Y-%m-%d"))


def latest_amount_context(history: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    rows = history.get("K线", []) if isinstance(history.get("K线"), list) else []
    valid_rows = [row for row in rows if isinstance(row, dict) and safe_float(row.get("成交额")) > 0]
    if valid_rows:
        latest = valid_rows[-1]
        last5 = valid_rows[-5:]
        last20 = valid_rows[-20:]
        avg5 = sum(safe_float(row.get("成交额")) for row in last5) / len(last5)
        avg20 = sum(safe_float(row.get("成交额")) for row in last20) / len(last20)
        return {
            "当日成交额": safe_float(latest.get("成交额")),
            "5日成交额均值": avg5,
            "20日成交额均值": avg20,
            "当日涨跌幅": safe_float(latest.get("涨跌幅")),
            "成交额来源": "候选历史K线",
            "最新日期": latest.get("日期", ""),
        }
    return {
        "当日成交额": safe_float(candidate.get("成交额")),
        "5日成交额均值": safe_float(candidate.get("近5日日均成交额")),
        "20日成交额均值": safe_float(candidate.get("近20日日均成交额")),
        "当日涨跌幅": safe_float(candidate.get("涨跌幅")),
        "成交额来源": "候选清单降级字段",
        "最新日期": "",
    }


def nearest_short_rebound_metric(ma20_deviation_pct: float | None, rsi14: float | None, amount_ratio5: float) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    if ma20_deviation_pct is not None:
        candidates.append({"指标": "MA20偏离度", "当前值": round(ma20_deviation_pct, 4), "触发阈值": "<=1%", "距离": max(0.0, ma20_deviation_pct - 1.0)})
    if rsi14 is not None:
        candidates.append({"指标": "RSI14", "当前值": round(rsi14, 4), "触发阈值": "<30", "距离": max(0.0, rsi14 - 30.0)})
    if amount_ratio5 > 0:
        candidates.append({"指标": "成交额/5日均额比", "当前值": round(amount_ratio5, 4), "触发阈值": ">1", "距离": max(0.0, 1.0 - amount_ratio5)})
    return min(candidates, key=lambda item: item["距离"]) if candidates else {"指标": "数据不足", "当前值": None, "触发阈值": "", "距离": None}


def detect_short_rebound_resonance(candidate: dict[str, Any], indicator: dict[str, Any], history: dict[str, Any]) -> dict[str, Any]:
    ma = indicator.get("均线", {}) if isinstance(indicator.get("均线"), dict) else {}
    close = safe_float(indicator.get("最新收盘") or candidate.get("现价"))
    ma20 = safe_float(ma.get("MA20"))
    rsi14 = safe_float(indicator.get("RSI14"), default=999.0)
    amount_ctx = latest_amount_context(history, candidate)
    today_amount = safe_float(amount_ctx.get("当日成交额"))
    avg5_amount = safe_float(amount_ctx.get("5日成交额均值"))
    ma20_deviation_pct = abs(close - ma20) / ma20 * 100 if ma20 > 0 and close > 0 else None
    amount_ratio5 = today_amount / avg5_amount if today_amount > 0 and avg5_amount > 0 else 0.0
    near_ma20 = ma20 > 0 and close > 0 and abs(close - ma20) / ma20 <= 0.01
    rsi_oversold = rsi14 < 30
    amount_expanded = today_amount > 0 and avg5_amount > 0 and today_amount > avg5_amount
    triggered = bool(near_ma20 and rsi_oversold and amount_expanded)
    return {
        "规则名称": "短线反弹共振信号",
        "触发": triggered,
        "固定话术": "触发短线超卖反弹共振信号，可关注修复性反弹机会。",
        "条件": {
            "最新收盘": round(close, 4),
            "MA20": round(ma20, 4),
            "是否MA20上下1%以内": near_ma20,
            "RSI14": round(rsi14, 4) if rsi14 != 999.0 else None,
            "是否RSI14低于30": rsi_oversold,
            "当日成交额": round(today_amount, 2),
            "5日成交额均值": round(avg5_amount, 2),
            "MA20偏离度百分比": round(ma20_deviation_pct, 4) if ma20_deviation_pct is not None else None,
            "成交额/5日均额比": round(amount_ratio5, 4) if amount_ratio5 > 0 else None,
            "是否当日成交额大于5日均额": amount_expanded,
            "成交额来源": amount_ctx.get("成交额来源", ""),
        },
        "最接近触发指标": nearest_short_rebound_metric(ma20_deviation_pct, None if rsi14 == 999.0 else rsi14, amount_ratio5),
        "调试摘要": f"MA20偏离度{ma20_deviation_pct:.2f}%，RSI {rsi14:.2f}，成交额/5日均额比{ratio_text(amount_ratio5)}" if ma20_deviation_pct is not None and rsi14 != 999.0 else f"MA20偏离度暂无，RSI {None if rsi14 == 999.0 else round(rsi14, 2)}，成交额/5日均额比{ratio_text(amount_ratio5)}",
    }


def nearest_strong_breakthrough_metric(close_vs_confirm_pct: float | None, amount_ratio20: float, change_pct: float | None) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    if close_vs_confirm_pct is not None:
        candidates.append({"指标": "收盘价/强度确认线偏离", "当前值": round(close_vs_confirm_pct, 4), "触发阈值": ">0%", "距离": max(0.0, 0.0 - close_vs_confirm_pct)})
    if amount_ratio20 > 0:
        candidates.append({"指标": "成交额/20日均额比", "当前值": round(amount_ratio20, 4), "触发阈值": ">1.5", "距离": max(0.0, 1.5 - amount_ratio20)})
    if change_pct is not None:
        candidates.append({"指标": "当日涨幅", "当前值": round(change_pct, 4), "触发阈值": ">3%", "距离": max(0.0, 3.0 - change_pct)})
    return min(candidates, key=lambda item: item["距离"]) if candidates else {"指标": "数据不足", "当前值": None, "触发阈值": "", "距离": None}


def detect_strong_breakthrough_signal(candidate: dict[str, Any], indicator: dict[str, Any], history: dict[str, Any], observation: dict[str, Any], risk_refresh_valid: bool) -> dict[str, Any]:
    close = safe_float(indicator.get("最新收盘") or candidate.get("现价"))
    amount_ctx = latest_amount_context(history, candidate)
    today_amount = safe_float(amount_ctx.get("当日成交额"))
    avg20_amount = safe_float(amount_ctx.get("20日成交额均值"))
    change_pct = safe_float(amount_ctx.get("当日涨跌幅"), default=safe_float(candidate.get("涨跌幅")))
    lines = observation.get("观察线", {}) if isinstance(observation.get("观察线"), dict) else {}
    confirm_line = safe_float(lines.get("强度确认线"))
    close_vs_confirm_pct = (close / confirm_line - 1) * 100 if close > 0 and confirm_line > 0 else None
    amount_ratio20 = today_amount / avg20_amount if today_amount > 0 and avg20_amount > 0 else 0.0
    close_breaks_confirm = bool(risk_refresh_valid and close > 0 and confirm_line > 0 and close > confirm_line)
    amount_expanded = bool(today_amount > 0 and avg20_amount > 0 and today_amount > avg20_amount * 1.5)
    change_strong = bool(change_pct > 3)
    triggered = bool(close_breaks_confirm and amount_expanded and change_strong)
    return {
        "规则名称": "强势突破确认信号",
        "触发": triggered,
        "固定话术": "触发强势突破确认信号，可提升该标的观察优先级。",
        "条件": {
            "最新收盘": round(close, 4),
            "强度确认线": round(confirm_line, 4) if confirm_line > 0 else None,
            "收盘价是否站上强度确认线": close_breaks_confirm,
            "收盘价/强度确认线偏离百分比": round(close_vs_confirm_pct, 4) if close_vs_confirm_pct is not None else None,
            "当日成交额": round(today_amount, 2),
            "20日成交额均值": round(avg20_amount, 2),
            "成交额/20日均额比": round(amount_ratio20, 4) if amount_ratio20 > 0 else None,
            "是否成交额大于20日均额1.5倍": amount_expanded,
            "当日涨跌幅": round(change_pct, 4),
            "是否涨幅超过3%": change_strong,
            "观察线时效有效": risk_refresh_valid,
            "成交额来源": amount_ctx.get("成交额来源", ""),
        },
        "最接近触发指标": nearest_strong_breakthrough_metric(close_vs_confirm_pct, amount_ratio20, change_pct),
        "调试摘要": f"强度线偏离{close_vs_confirm_pct:.2f}%，成交额/20日均额比{ratio_text(amount_ratio20)}，当日涨幅{change_pct:.2f}%" if close_vs_confirm_pct is not None else f"强度线偏离暂无，成交额/20日均额比{ratio_text(amount_ratio20)}，当日涨幅{change_pct:.2f}%",
    }


def derive_price_levels(candidate: dict[str, Any], indicator: dict[str, Any]) -> dict[str, Any]:
    close = float(indicator.get("最新收盘") or candidate.get("现价") or 0)
    ma = indicator.get("均线", {}) if isinstance(indicator.get("均线"), dict) else {}
    ma_values = [float(v) for v in ma.values() if isinstance(v, (int, float)) and v > 0]
    below = sorted([v for v in ma_values if v <= close], reverse=True)
    above = sorted([v for v in ma_values if v > close])
    support = below[0] if below else (min(ma_values) if ma_values else close * 0.97)
    pressure = above[0] if above else close * 1.035
    stop = min(support * 0.97, close * 0.97)
    confirm = max(pressure, close * 1.02)
    return {
        "现价": round(close, 2),
        "承接位": round(support, 2),
        "压力位": round(pressure, 2),
        "转强确认位": round(confirm, 2),
        "短线放弃线": round(stop, 2),
    }


def build_evidence_summary(candidate: dict[str, Any], indicator: dict[str, Any], history: dict[str, Any]) -> str:
    amount_ctx = latest_amount_context(history, candidate)
    today_amount = safe_float(amount_ctx.get("当日成交额"))
    avg5_amount = safe_float(amount_ctx.get("5日成交额均值"))
    amount_ratio5 = today_amount / avg5_amount if today_amount > 0 and avg5_amount > 0 else safe_float(indicator.get("量比5日"))
    industry = candidate.get("行业") or candidate.get("申万一级行业") or indicator.get("行业") or "行业未分类"
    strength = (
        candidate.get("行业强度")
        or candidate.get("行业强度评分")
        or candidate.get("行业评分")
        or indicator.get("行业强度")
        or indicator.get("行业强度评分")
    )
    if strength not in (None, ""):
        industry_part = f"行业强度{strength}（{industry}）"
    else:
        industry_part = f"行业字段{industry}"
    if amount_ratio5 > 0:
        if amount_ratio5 >= 1:
            amount_part = f"近5日放量{(amount_ratio5 - 1) * 100:.2f}%"
        else:
            amount_part = f"近5日缩量{(1 - amount_ratio5) * 100:.2f}%"
    else:
        amount_part = "近5日成交额对比数据不足"
    return f"{industry_part}，{amount_part}。待核验公告及财务数据。"


def build_stock_line(candidate: dict[str, Any], indicator: dict[str, Any], history: dict[str, Any], observation: dict[str, Any], risk_refresh_valid: bool) -> dict[str, Any]:
    levels = derive_price_levels(candidate, indicator)
    name = candidate.get("名称") or indicator.get("名称") or "未知股票"
    code = candidate.get("代码") or indicator.get("代码") or ""
    volume_ratio = indicator.get("量比5日")
    macd = indicator.get("MACD", {}) if isinstance(indicator.get("MACD"), dict) else {}
    macd_value = macd.get("MACD")
    rsi = indicator.get("RSI14")
    observations = indicator.get("技术观察", [])
    obs_text = "、".join(observations) if observations else "现有指标不足，按价格和成交额字段降级判断"
    volume_phrase = f"量比5日约{float(volume_ratio):.2f}倍" if isinstance(volume_ratio, (int, float)) else "量能字段不足"
    macd_phrase = "MACD偏强" if isinstance(macd_value, (int, float)) and macd_value > 0 else "MACD未形成强动能"
    rsi_phrase = f"RSI14为{float(rsi):.2f}" if isinstance(rsi, (int, float)) else "RSI字段不足"
    resonance = detect_short_rebound_resonance(candidate, indicator, history)
    breakthrough = detect_strong_breakthrough_signal(candidate, indicator, history, observation, risk_refresh_valid)
    evidence_summary = build_evidence_summary(candidate, indicator, history)
    triggered_texts = [signal["固定话术"] for signal in (resonance, breakthrough) if signal["触发"]]
    if triggered_texts:
        core_logic = " ".join(triggered_texts)
    else:
        core_logic = f"{name}进入短线观察池，主要依据是量价活跃度、关键均线位置和盘后轻扫描排序。"
    action = f"{name}收盘在{money(levels['现价'])}，{obs_text}，{volume_phrase}，{macd_phrase}。"
    if risk_refresh_valid:
        condition = f"明天若放量站稳{money(levels['转强确认位'])}上方，再列入短线高优先级；若开盘后始终压在{money(levels['承接位'])}下方，则不进入当日主盯列表。"
        stop = f"跌破{money(levels['短线放弃线'])}则日内不再看。"
    else:
        condition = "观察线刷新未通过，不设具体触发价；只保留量价候选身份，等待观察线刷新后再给价位型条件。"
        stop = "观察线刷新未通过，不生成具体止损价；该票先进入数据维护复核。"
    return {
        "代码": code,
        "名称": name,
        "核心逻辑": core_logic,
        "技术动作": action,
        "明天短线观察条件": condition,
        "短线止损参考价": stop,
        "证据摘要": evidence_summary,
        "指标共振信号": [resonance, breakthrough],
        "价位": levels,
        "辅助指标": {
            "量比5日": volume_ratio,
            "MACD": macd_value,
            "RSI14": rsi,
            "RSI描述": rsi_phrase,
            "候选评分": candidate.get("轻扫描评分"),
            "涨跌幅": candidate.get("涨跌幅"),
            "成交额": candidate.get("成交额"),
        },
        "指标匹配状态": "已匹配技术指标" if indicator else "未匹配技术指标",
        "观察线刷新状态": "有效" if risk_refresh_valid else "未通过",
    }


def build_report(root: Path) -> dict[str, Any]:
    scan_path = root / "03数据" / "92盘后轻扫描" / "300只试运行池盘后轻扫描_最新.json"
    focus_indicator_path = root / "03数据" / "12技术指标" / "重点关注池技术指标_最新.json"
    candidate_indicator_path = root / "03数据" / "94候选历史K线技术指标" / "300只候选技术指标_最新.json"
    candidate_history_path = root / "03数据" / "94候选历史K线技术指标" / "300只候选历史K线_最新.json"
    observation_panel_path = root / "03数据" / "184风险失效条件观察面板" / "股票风险失效条件观察面板_最新.json"
    risk_refresh_status_path = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "盘后观察线刷新状态_最新.json"
    preflight_status_path = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "收盘短线观察前置数据刷新状态_最新.json"
    scan = load_json(scan_path, {})
    indicators = build_indicator_index(focus_indicator_path, candidate_indicator_path)
    histories = build_history_index(candidate_history_path)
    observations = build_observation_index(observation_panel_path)
    risk_refresh_status = load_json(risk_refresh_status_path, {})
    risk_refresh_valid = risk_refresh_is_valid(risk_refresh_status)
    preflight_status = load_json(preflight_status_path, {})
    preflight_valid = preflight_is_valid(preflight_status)
    if not preflight_valid:
        return {
            "名称": "收盘短线观察报告",
            "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "总体状态": "blocked",
            "阻断原因": "收盘短线观察前置数据刷新状态不是当日pass，禁止生成正式收盘短线观察。",
            "前置刷新状态": {
                "状态文件": str(preflight_status_path),
                "结论": preflight_status.get("结论"),
                "生成时间": preflight_status.get("生成时间", ""),
                "当日未刷新或缺失产物": preflight_status.get("当日未刷新或缺失产物", []),
            },
            "候选数量": 0,
            "指标匹配数量": 0,
            "股票": [],
            "输出正文": "收盘短线观察前置数据未完成当日刷新，本次禁止生成正式报告。请先运行：python 刷新收盘短线观察前置数据.py",
            "安全边界": {
                "是否真实发送企业微信": False,
                "是否触发n8n": False,
                "是否接券商": False,
                "是否交易": False,
                "是否群发": False,
            },
        }
    candidates = scan.get("候选清单", [])[:10]
    rows = []
    for candidate in candidates:
        indicator = indicators.get(code_key(candidate.get("代码", "")), {})
        history = histories.get(code_key(candidate.get("代码", "")), {})
        observation = observations.get(code_key(candidate.get("代码", "")), {})
        rows.append(build_stock_line(candidate, indicator, history, observation, risk_refresh_valid))
    data_date = "2026-04-30"
    for row in rows:
        if row.get("指标匹配状态") == "已匹配技术指标":
            matched = indicators.get(code_key(row.get("代码", "")), {})
            if matched.get("最新日期"):
                data_date = str(matched.get("最新日期"))
                break
    lines = [
        f"【收盘短线观察｜{data_date}】",
        "",
        "杰哥，您好。今天收盘后，通过纯量价扫描，以下个股在技术面上出现了短线可观察的信号。",
        "",
    ]
    if not risk_refresh_valid:
        lines.extend([
            "观察线刷新未通过：本报告只展示量价候选，不生成具体触发价、承接位和止损价。",
            "",
        ])
    for index, row in enumerate(rows, start=1):
        lines.extend([
            f"{index}. {row['名称']}（{row['代码']}）",
            f"- 核心逻辑：{row['核心逻辑']}",
            f"- 技术动作：{row['技术动作']}",
            f"- 明天条件：{row['明天短线观察条件']}",
            f"- 短线止损参考价：{row['短线止损参考价']}",
            f"- 证据摘要：{row['证据摘要']}",
            "",
        ])
    promotion_results = []
    for row in rows:
        for signal in row.get("指标共振信号", []):
            if not isinstance(signal, dict) or signal.get("触发") is not True:
                continue
            rule_name = str(signal.get("规则名称", ""))
            if rule_name not in {"短线反弹共振信号", "强势突破确认信号"}:
                continue
            promotion_results.append(register_promotion_candidate(
                code=row.get("代码"),
                name=row.get("名称"),
                source_type=rule_name,
                reason=str(signal.get("固定话术") or f"{rule_name}触发"),
                score=30 if rule_name == "强势突破确认信号" else 20,
                evidence={
                    "规则名称": rule_name,
                    "条件": signal.get("条件", {}),
                    "最接近触发指标": signal.get("最接近触发指标", {}),
                },
                source_path="收盘短线观察_基于300只轻扫描_最新.json",
                root=root,
            ))
    lines.append("以上仅基于今日收盘价量结构筛选，不构成买卖建议，盈亏自负。")
    return {
        "名称": "收盘短线观察报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "数据日期": data_date,
        "输入": {
            "300只盘后轻扫描": str(scan_path),
            "重点关注池技术指标": str(focus_indicator_path),
            "300只候选技术指标": str(candidate_indicator_path),
            "300只候选历史K线": str(candidate_history_path),
            "风险失效条件观察面板": str(observation_panel_path),
            "收盘短线观察前置数据刷新状态": str(preflight_status_path),
            "盘后观察线刷新状态": str(risk_refresh_status_path),
        },
        "前置刷新状态": {
            "有效": preflight_valid,
            "状态文件": str(preflight_status_path),
            "结论": preflight_status.get("结论"),
            "生成时间": preflight_status.get("生成时间", ""),
        },
        "观察线刷新状态": {
            "有效": risk_refresh_valid,
            "状态文件": str(risk_refresh_status_path),
            "刷新成功": risk_refresh_status.get("刷新成功"),
            "生成时间": risk_refresh_status.get("生成时间", ""),
            "前置脚本": risk_refresh_status.get("前置脚本", ""),
        },
        "候选数量": len(rows),
        "指标匹配数量": sum(1 for row in rows if row["指标匹配状态"] == "已匹配技术指标"),
        "股票": rows,
        "共振规则调试日志": [
            {
                "代码": row["代码"],
                "名称": row["名称"],
                "数据日期": data_date,
                "规则调试": [
                    {
                        "规则名称": signal.get("规则名称"),
                        "触发": signal.get("触发"),
                        "最接近触发指标": signal.get("最接近触发指标"),
                        "调试摘要": signal.get("调试摘要"),
                        "条件": signal.get("条件"),
                    }
                    for signal in row.get("指标共振信号", [])
                    if isinstance(signal, dict)
                ],
            }
            for row in rows
        ],
        "晋级候选写入结果": promotion_results,
        "输出正文": "\n".join(lines),
        "安全边界": {
            "是否真实发送企业微信": False,
            "是否触发n8n": False,
            "是否接券商": False,
            "是否交易": False,
            "是否群发": False,
        },
    }


def build_debug_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 共振信号规则调试日志 - {report.get('生成时间', '')}",
        "",
        f"- 数据日期：{report.get('数据日期', '')}",
        f"- 候选数量：{report.get('候选数量', 0)}",
        "",
        "| 股票 | 规则 | 是否触发 | 最接近触发指标 | 调试摘要 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report.get("共振规则调试日志", []):
        label = f"{item.get('名称', '')}({item.get('代码', '')})"
        for signal in item.get("规则调试", []):
            nearest = signal.get("最接近触发指标", {}) if isinstance(signal.get("最接近触发指标"), dict) else {}
            nearest_text = f"{nearest.get('指标', '')}={nearest.get('当前值', '')}，阈值{nearest.get('触发阈值', '')}"
            lines.append(f"| {label} | {signal.get('规则名称', '')} | {signal.get('触发')} | {nearest_text} | {signal.get('调试摘要', '')} |")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = build_report(root)
    json_path = out_dir / f"收盘短线观察_基于300只轻扫描_{stamp}.json"
    latest_json = out_dir / "收盘短线观察_基于300只轻扫描_最新.json"
    md_path = out_dir / f"收盘短线观察_基于300只轻扫描_{stamp}.md"
    latest_md = out_dir / "收盘短线观察_基于300只轻扫描_最新.md"
    debug_json = out_dir / f"共振信号规则调试日志_{stamp}.json"
    debug_md = out_dir / f"共振信号规则调试日志_{stamp}.md"
    latest_debug_json = out_dir / "共振信号规则调试日志_最新.json"
    latest_debug_md = out_dir / "共振信号规则调试日志_最新.md"
    write_json(json_path, report)
    write_json(latest_json, report)
    write_text(md_path, report["输出正文"])
    write_text(latest_md, report["输出正文"])
    debug_report = {
        "名称": "共振信号规则调试日志",
        "生成时间": report.get("生成时间"),
        "数据日期": report.get("数据日期"),
        "候选数量": report.get("候选数量"),
        "调试日志": report.get("共振规则调试日志", []),
        "安全边界": report.get("安全边界", {}),
    }
    write_json(debug_json, debug_report)
    write_json(latest_debug_json, debug_report)
    debug_markdown = build_debug_markdown(report)
    write_text(debug_md, debug_markdown)
    write_text(latest_debug_md, debug_markdown)
    status = report.get("总体状态") or "pass"
    print(json.dumps({"总体状态": status, "候选数量": report["候选数量"], "指标匹配数量": report["指标匹配数量"], "Markdown": str(latest_md)}, ensure_ascii=False))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
