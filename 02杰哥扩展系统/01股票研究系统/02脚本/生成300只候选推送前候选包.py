# -*- coding: utf-8 -*-
"""
名称：生成300只候选推送前候选包.py
作用：基于轻扫描、历史K线、技术指标、公告财务行业事件入口生成推送前候选包。
触发方式：python 生成300只候选推送前候选包.py
依赖：Python标准库；300只候选推送前候选包规则.json；深度预处理包；候选技术指标；公告财务行业事件只读入口。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写新系统推送前候选包；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选推送前候选包脚本。
标识：stock-trial-pool-300-pre-push-candidate-package
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


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", "-", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_code(value: str) -> str:
    return str(value or "").strip().lower()


def technical_score(indicator: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    score = 0.0
    strengths: list[str] = []
    risks: list[str] = []
    if indicator.get("状态") == "成功":
        score += 20
    else:
        risks.append("技术指标未达完整成功状态")
    close = as_float(indicator.get("最新收盘"))
    ma = indicator.get("均线", {})
    ma20 = as_float(ma.get("MA20"))
    ma60 = as_float(ma.get("MA60"))
    if close and ma20 and close > ma20:
        score += 10
        strengths.append("收盘价站上MA20")
    elif ma20:
        risks.append("收盘价低于MA20")
    if close and ma60 and close > ma60:
        score += 10
        strengths.append("收盘价站上MA60")
    elif ma60:
        risks.append("收盘价低于MA60")
    rsi = as_float(indicator.get("RSI14"), default=-1)
    if 35 <= rsi <= 75:
        score += 8
        strengths.append("RSI处于可观察区间")
    elif rsi > 75:
        risks.append("RSI偏高，需警惕短线过热")
    elif rsi >= 0:
        risks.append("RSI偏弱")
    macd = indicator.get("MACD", {})
    if macd.get("DIF") is not None and macd.get("DEA") is not None:
        if as_float(macd.get("DIF")) > as_float(macd.get("DEA")):
            score += 8
            strengths.append("MACD偏强")
        else:
            risks.append("MACD偏弱")
    volume_ratio = as_float(indicator.get("量比5日"), default=0)
    if volume_ratio >= 1.1:
        score += 6
        strengths.append("量能活跃")
    elif volume_ratio:
        risks.append("量能一般")
    return score, strengths, risks


def build_candidate(candidate: dict[str, Any], indicator: dict[str, Any], event_entry: dict[str, Any]) -> dict[str, Any]:
    tech_score, tech_strengths, tech_risks = technical_score(indicator)
    scan_score = as_float(candidate.get("轻扫描评分"))
    pct = as_float(candidate.get("涨跌幅"))
    liquidity_bonus = min(as_float(candidate.get("成交额")) / 1_000_000_000, 10)
    activity_bonus = 6 if abs(pct) >= 2 else 3 if abs(pct) >= 1 else 0
    total_score = round(scan_score / 10 + tech_score + liquidity_bonus + activity_bonus, 4)
    return {
        "代码": candidate.get("代码"),
        "名称": candidate.get("名称"),
        "市场": candidate.get("市场"),
        "行业": candidate.get("行业"),
        "推送前评分": total_score,
        "轻扫描评分": candidate.get("轻扫描评分"),
        "行情摘要": {
            "现价": candidate.get("现价"),
            "涨跌幅": candidate.get("涨跌幅"),
            "成交额": candidate.get("成交额"),
            "流通市值": candidate.get("流通市值"),
            "行情时间": candidate.get("行情时间"),
        },
        "技术指标摘要": {
            "状态": indicator.get("状态"),
            "K线数量": indicator.get("K线数量"),
            "最新日期": indicator.get("最新日期"),
            "最新收盘": indicator.get("最新收盘"),
            "均线": indicator.get("均线", {}),
            "RSI14": indicator.get("RSI14"),
            "MACD": indicator.get("MACD", {}),
            "量比5日": indicator.get("量比5日"),
            "技术观察": indicator.get("技术观察", []),
        },
        "候选依据": list(candidate.get("候选理由", [])) + tech_strengths,
        "风险和复核点": list(candidate.get("风险和降级说明", [])) + tech_risks + [
            "公告、财务和行业事件尚未抓取正文，推送前必须人工复核。",
            "本候选包不构成投资建议，不形成买卖指令。"
        ],
        "公告财务行业入口状态": {
            "公告入口数量": len(event_entry.get("公告入口", [])),
            "财务入口数量": len(event_entry.get("财务入口", [])),
            "行业事件入口数量": len(event_entry.get("行业事件入口", [])),
            "入口状态": event_entry.get("入口状态", "未建立"),
            "深度分析前闸口": event_entry.get("深度分析前闸口", []),
        },
        "推送状态": "候选，真实发送关闭，待人工闸口确认",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选推送前候选包报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结果概览",
        "",
        f"- 输入候选数量：{report['输入候选数量']}",
        f"- 推送前候选数量：{report['推送前候选数量']}",
        "- 真实发送：关闭",
        "- 说明：本报告只用于研究筛选，不构成投资建议，不形成买卖指令。",
        "",
        "## 推送前候选",
        "",
    ]
    for index, item in enumerate(report.get("推送前候选", []), start=1):
        risks = "；".join(item.get("风险和复核点", [])[:3])
        lines.append(f"{index}. {item['名称']}（{item['代码']}）：评分{item['推送前评分']}，状态：{item['推送状态']}。复核点：{risks}")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    rules = load_json(root / "01配置" / "300只候选推送前候选包规则.json")
    preprocess = load_json(root / rules["输入"]["深度预处理包"])
    indicators = load_json(root / rules["输入"]["技术指标"])
    events = load_json(root / rules["输入"]["事件入口"])
    indicator_map = {normalize_code(item.get("代码")): item for item in indicators.get("技术指标", [])}
    event_map = {normalize_code(item.get("代码")): item for item in events.get("候选入口", [])}
    candidates = preprocess.get("预处理候选", [])
    rows = [
        build_candidate(candidate, indicator_map.get(normalize_code(candidate.get("代码")), {}), event_map.get(normalize_code(candidate.get("代码")), {}))
        for candidate in candidates
    ]
    rows.sort(key=lambda item: item["推送前评分"], reverse=True)
    limit = int(rules.get("候选限制", {}).get("最多推送前候选数量", 5))
    selected = rows[:limit]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(root / "01配置" / "300只候选推送前候选包规则.json"),
        "输入文件": {
            "深度预处理包": str(root / rules["输入"]["深度预处理包"]),
            "技术指标": str(root / rules["输入"]["技术指标"]),
            "事件入口": str(root / rules["输入"]["事件入口"]),
        },
        "输入候选数量": len(candidates),
        "推送前候选数量": len(selected),
        "推送前候选": selected,
        "未入选候选": rows[limit:],
        "人工闸口": rules.get("候选限制", {}).get("人工闸口", ""),
        "结论": "已生成推送前候选包；真实发送关闭；需人工复核公告、财务和行业事件后才可放行。",
        "安全边界": {
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否写正式库": False,
            "是否写旧系统": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否重启服务": False,
        },
    }
    output_dir = root / rules["输出"]["数据目录"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"300只候选推送前候选包_{timestamp}.json"
    latest = output_dir / rules["输出"]["最新文件"]
    markdown = output_dir / f"300只候选推送前候选包报告_{timestamp}.md"
    markdown_latest = output_dir / rules["输出"]["报告文件"]
    write_json(output, report)
    write_json(latest, report)
    markdown_text = build_markdown(report)
    markdown.write_text(markdown_text, encoding="utf-8")
    markdown_latest.write_text(markdown_text, encoding="utf-8")
    print(json.dumps({"输入候选数量": len(candidates), "推送前候选数量": len(selected), "输出": str(output)}, ensure_ascii=False))
    return 0 if selected else 1


if __name__ == "__main__":
    raise SystemExit(main())
