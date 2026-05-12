# -*- coding: utf-8 -*-
"""
名称：生成股票风险失效条件观察面板.py
作用：为当前L5股票生成风险观察线、失效条件和后续观察触发条件，支撑前台结论式表达。
触发方式：python 生成股票风险失效条件观察面板.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地03数据；只写03数据/184风险失效条件观察面板；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不改变评分和推荐排序。
标识：stock-risk-invalidation-observation-panel
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")) and len(text) >= 8:
        return text[:2] + text[-6:]
    if "." in text:
        num, suffix = text.split(".", 1)
        suffix = suffix.upper()
        if suffix in {"SH", "SZ", "BJ"}:
            return suffix.lower() + num[-6:]
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 6:
        digits = digits[-6:]
        if digits.startswith(("6", "9")):
            return "sh" + digits
        if digits.startswith(("4", "8")):
            return "bj" + digits
        return "sz" + digits
    return text


def display_code(code: str) -> str:
    code = normalize_code(code)
    if len(code) == 8 and code[:2] in {"sh", "sz", "bj"}:
        return f"{code[2:]}.{code[:2].upper()}"
    return code


def stock_list(data: dict[str, Any], *keys: str) -> list[dict[str, Any]]:
    for key in keys:
        value = data.get(key, [])
        if isinstance(value, list):
            return value
    return []


def by_code(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        code = normalize_code(row.get("代码") or row.get("展示代码"))
        if code:
            result[code] = row
    return result


def to_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in {None, ""}:
            return default
        return float(value)
    except Exception:
        return default


def pct_text(value: float | None) -> str:
    if value is None:
        return "待补充"
    return f"{value:.2f}%"


def price_text(value: float | None) -> str:
    if value is None:
        return "待补充"
    return f"{value:.2f}元"


def score_level(score: float | None) -> str:
    if score is None:
        return "待观察"
    if score >= 4.5:
        return "重点关注"
    if score >= 4.0:
        return "常规关注"
    if score >= 3.6:
        return "观察等待"
    return "降低关注"


def front_level(stock: dict[str, Any], ai_row: dict[str, Any]) -> str:
    score = to_float(stock.get("调整分") or ai_row.get("调整分"))
    if score is not None and score >= 4.5:
        return "推荐股票"
    if score is not None and score >= 4.0:
        return "观察股票"
    return "暂不关注"


def industry_status(industry_row: dict[str, Any]) -> str:
    conclusion = str(industry_row.get("前台结论") or industry_row.get("景气结论") or "")
    level = str(industry_row.get("景气档位") or industry_row.get("状态") or "")
    combined = conclusion + level
    if any(word in combined for word in ["转弱", "偏弱", "下降", "谨慎"]):
        return "偏弱或需谨慎"
    if any(word in combined for word in ["强", "改善", "景气", "上行"]):
        return "方向偏强"
    if combined:
        return "已接入，需跟踪"
    return "待核验"


def calc_lines(stock: dict[str, Any], quote: dict[str, Any], tech: dict[str, Any]) -> dict[str, Any]:
    latest = to_float(quote.get("最新价") or tech.get("最新收盘") or stock.get("收盘价"))
    high = to_float(quote.get("最高"))
    ma = tech.get("均线") if isinstance(tech.get("均线"), dict) else {}
    ma5 = to_float(ma.get("MA5"))
    ma20 = to_float(ma.get("MA20"))
    ma60 = to_float(ma.get("MA60"))

    support_candidates = [value for value in [ma5, ma20, latest * 0.98 if latest else None] if value]
    risk_candidates = [value for value in [ma60, latest * 0.94 if latest else None] if value]
    confirm_candidates = [value for value in [high, latest * 1.08 if latest else None] if value]

    support_line = round(min(support_candidates), 2) if support_candidates else None
    risk_line = round(min(risk_candidates), 2) if risk_candidates else None
    confirm_line = round(max(confirm_candidates), 2) if confirm_candidates else None

    return {
        "现价": round(latest, 2) if latest is not None else None,
        "承接观察线": support_line,
        "风险观察线": risk_line,
        "强度确认线": confirm_line,
        "MA5": ma5,
        "MA20": ma20,
        "MA60": ma60,
    }


def build_conditions(stock: dict[str, Any], quote: dict[str, Any], tech: dict[str, Any], industry_row: dict[str, Any], lines: dict[str, Any]) -> dict[str, list[str]]:
    latest = to_float(lines.get("现价"))
    support_line = to_float(lines.get("承接观察线"))
    risk_line = to_float(lines.get("风险观察线"))
    confirm_line = to_float(lines.get("强度确认线"))
    score = to_float(stock.get("调整分"))
    volume_rate = to_float(stock.get("资金放量率"))
    turnover_ratio = to_float(quote.get("量比") or tech.get("量比5日"))
    rsi = to_float(tech.get("RSI14"))
    macd = tech.get("MACD") if isinstance(tech.get("MACD"), dict) else {}
    macd_value = to_float(macd.get("MACD"))
    industry = industry_status(industry_row)

    invalidation: list[str] = []
    caution: list[str] = []
    strengthen: list[str] = []

    if risk_line:
        invalidation.append(f"收盘跌破风险观察线 {price_text(risk_line)}，先转为谨慎观察。")
    if score is not None:
        invalidation.append(f"分层调整分跌破 {max(score - 0.35, 3.6):.2f}，说明原入选强度开始失效。")
    invalidation.append("公告、财报、减持解禁或监管事件出现实质利空且未被新证据消化。")
    if industry == "偏弱或需谨慎":
        invalidation.append("行业景气已提示偏弱，若个股强度同步回落，需要降低关注。")
    else:
        invalidation.append("行业景气从偏强/待核验转为明确走弱，需要重新评估。")

    if support_line:
        caution.append(f"回踩 {price_text(support_line)} 附近能否承接，是短线观察重点。")
    if turnover_ratio is not None and turnover_ratio < 0.8:
        caution.append(f"量比 {turnover_ratio:.2f}，资金持续性一般，先观察放量能否延续。")
    else:
        caution.append("继续观察量能是否保持在近期均值上方，避免只看单日冲高。")
    if rsi is not None and rsi >= 75:
        caution.append(f"RSI14={rsi:.2f}，短线偏热，追高风险增加。")
    if macd_value is not None and macd_value < 0:
        caution.append("MACD处于偏弱区，技术结构还需要修复。")

    if confirm_line:
        strengthen.append(f"放量站稳强度确认线 {price_text(confirm_line)}，可提高观察优先级。")
    if score is not None:
        strengthen.append(f"分层调整分维持或升至 {min(score + 0.20, 5.0):.2f} 以上，说明强度得到延续。")
    if volume_rate is not None and volume_rate > 0:
        strengthen.append(f"资金放量率继续为正（当前 {pct_text(volume_rate * 100)}），且不是单日脉冲。")
    strengthen.append("公司概况、行业景气、事件风险证据完成核验后，前台结论可信度可进一步提高。")

    return {
        "失效条件": invalidation,
        "观察条件": caution,
        "增强条件": strengthen,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票风险失效条件观察面板 - {report['生成时间']}",
        "",
        "## 一、定位",
        "",
        "- 本面板把“什么时候继续看、什么时候转谨慎、什么时候增强关注”写清楚。",
        "- 它服务企业微信前台的结论式表达，不改变后台评分、推荐排序或持仓诊断。",
        "",
        "## 二、总览",
        "",
        f"- 覆盖L5股票：{report['覆盖L5数量']}只",
        f"- 推荐股票：{report['分布'].get('推荐股票', 0)}只",
        f"- 观察股票：{report['分布'].get('观察股票', 0)}只",
        f"- 暂不关注：{report['分布'].get('暂不关注', 0)}只",
        "",
        "## 三、逐股观察线",
        "",
        "| 优先级 | 代码 | 名称 | 前台层级 | 现价 | 承接观察线 | 风险观察线 | 强度确认线 | 当前提示 |",
        "|---:|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in report["逐股结果"]:
        lines.append(
            f"| {row['优先级']} | {row['展示代码']} | {row['名称']} | {row['前台层级']} | "
            f"{price_text(row['观察线']['现价'])} | {price_text(row['观察线']['承接观察线'])} | "
            f"{price_text(row['观察线']['风险观察线'])} | {price_text(row['观察线']['强度确认线'])} | {row['当前提示']} |"
        )

    lines.extend(["", "## 四、逐股条件", ""])
    for row in report["逐股结果"]:
        lines.extend([
            f"### {row['名称']}（{row['展示代码']}）",
            "",
            f"- 当前判断：{row['当前判断']}",
            f"- 研究策略：{row['研究策略']}",
            "- 失效条件：",
        ])
        for item in row["条件"]["失效条件"]:
            lines.append(f"  - {item}")
        lines.append("- 观察条件：")
        for item in row["条件"]["观察条件"]:
            lines.append(f"  - {item}")
        lines.append("- 增强条件：")
        for item in row["条件"]["增强条件"]:
            lines.append(f"  - {item}")
        lines.append("")

    lines.extend([
        "## 五、安全边界",
        "",
        "- 只生成观察面板，不自动发送企业微信。",
        "- 不触发n8n，不调用券商接口，不自动交易。",
        "- 不修改股票评分、推荐等级、股票池和正式证据档案。",
        "- 所有价格线仅作研究观察参考，不是买卖指令。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    data_dir = root / "03数据"
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    l5 = load_json(data_dir / "134深度研究池" / "L5深度研究池_最新.json", {})
    quote = load_json(data_dir / "04数据快照" / "重点关注池公开行情快照_最新.json", {})
    tech = load_json(data_dir / "12技术指标" / "重点关注池技术指标_最新.json", {})
    ai = load_json(data_dir / "135分层日报" / "AI分析报告_最新.json", {})
    industry = load_json(data_dir / "167行业景气结论" / "行业景气结论_最新.json", {})

    l5_rows = stock_list(l5, "股票池")
    quote_map = by_code(stock_list(quote, "行情", "股票列表"))
    tech_map = by_code(stock_list(tech, "技术指标", "股票列表"))
    ai_map = by_code(stock_list(ai, "分析结果", "推荐股票", "观察股票"))
    industry_map = {
        str(item.get("行业") or ""): item
        for item in stock_list(industry, "行业景气结论", "行业列表")
    }

    rows: list[dict[str, Any]] = []
    distribution: dict[str, int] = {}
    for index, stock in enumerate(l5_rows, 1):
        code = normalize_code(stock.get("代码") or stock.get("展示代码"))
        quote_row = quote_map.get(code, {})
        tech_row = tech_map.get(code, {})
        ai_row = ai_map.get(code, {})
        industry_name = str(stock.get("行业") or ai_row.get("行业") or quote_row.get("行业") or "")
        industry_row = industry_map.get(industry_name, {})
        lines = calc_lines(stock, quote_row, tech_row)
        conditions = build_conditions(stock, quote_row, tech_row, industry_row, lines)
        level = front_level(stock, ai_row)
        distribution[level] = distribution.get(level, 0) + 1
        current_score = to_float(stock.get("调整分") or ai_row.get("调整分"))
        level_text = score_level(current_score)
        risk_line = lines.get("风险观察线")
        support_line = lines.get("承接观察线")
        confirm_line = lines.get("强度确认线")
        current_tip = f"守住{price_text(support_line)}看承接，跌破{price_text(risk_line)}转谨慎。"
        strategy = f"以研究跟踪为主；若放量站稳{price_text(confirm_line)}再看强度延续，若跌破风险观察线则降低关注。"
        rows.append({
            "优先级": stock.get("优先级") or index,
            "代码": code,
            "展示代码": display_code(code),
            "名称": stock.get("名称") or ai_row.get("名称") or quote_row.get("名称"),
            "行业": industry_name or "待补充",
            "前台层级": level,
            "研究等级": level_text,
            "调整分": current_score,
            "观察线": lines,
            "行业景气状态": industry_status(industry_row),
            "当前提示": current_tip,
            "当前判断": f"{level_text}，{level}口径；当前先看承接和资金持续性，不把单日上涨当成最终结论。",
            "研究策略": strategy,
            "条件": conditions,
        })

    report = {
        "名称": "股票风险失效条件观察面板",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票风险失效条件观察面板.py",
        "定位": "支撑前台当前判断、策略、参考位置和风险观察线；不改变推荐排序。",
        "覆盖L5数量": len(rows),
        "分布": distribution,
        "逐股结果": rows,
        "输入文件": {
            "L5深度研究池": str(data_dir / "134深度研究池" / "L5深度研究池_最新.json"),
            "公开行情快照": str(data_dir / "04数据快照" / "重点关注池公开行情快照_最新.json"),
            "技术指标": str(data_dir / "12技术指标" / "重点关注池技术指标_最新.json"),
            "AI分析报告": str(data_dir / "135分层日报" / "AI分析报告_最新.json"),
            "行业景气结论": str(data_dir / "167行业景气结论" / "行业景气结论_最新.json"),
        },
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否修改评分规则": False,
            "是否修改推荐排序": False,
        },
    }

    output_dir = data_dir / "184风险失效条件观察面板"
    latest_json = output_dir / "股票风险失效条件观察面板_最新.json"
    latest_md = output_dir / "股票风险失效条件观察面板_最新.md"
    json_path = output_dir / f"股票风险失效条件观察面板_{stamp}.json"
    md_path = output_dir / f"股票风险失效条件观察面板_{stamp}.md"
    markdown = build_markdown(report)
    write_json(json_path, report)
    write_json(latest_json, report)
    write_text(md_path, markdown)
    write_text(latest_md, markdown)

    print(json.dumps({
        "状态": "完成",
        "覆盖L5数量": len(rows),
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
