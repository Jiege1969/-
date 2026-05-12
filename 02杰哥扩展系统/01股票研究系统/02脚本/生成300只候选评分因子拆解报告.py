# -*- coding: utf-8 -*-
"""
名称：生成300只候选评分因子拆解报告.py
作用：拆解推送前候选评分来源，输出解释报告；只解释评分，不修改评分规则、不改候选、不发送。
触发方式：python 生成300只候选评分因子拆解报告.py
依赖：Python标准库；300只候选评分因子拆解规则.json；96推送前候选包；101事件核验结果回填；109股票分析质量诊断。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读股票研究系统本地产物并写110评分因子拆解报告；不修改评分规则；不修改候选清单；不触发发送链路；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选评分因子拆解报告脚本。
标识：stock-trial-pool-300-score-factor-decomposition
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", "-", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def index_event_summary(event_backfill: dict[str, Any]) -> dict[str, dict[str, Any]]:
    direct = event_backfill.get("候选核验结果", event_backfill.get("事件核验结果", []))
    if direct:
        return {str(item.get("代码", "")).lower(): item for item in direct if item.get("代码")}
    ledger_items = event_backfill.get("派生复盘账本", []) or event_backfill.get("复盘账本", [])
    return {
        str(item.get("代码", "")).lower(): item.get("事件正文核验回填", {})
        for item in ledger_items
        if item.get("代码")
    }


def index_diagnosis(diagnosis: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("代码", "")).lower(): item
        for item in diagnosis.get("候选诊断", [])
        if item.get("代码")
    }


def technical_score(item: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    tech = item.get("技术指标摘要", {})
    ma = tech.get("均线", {})
    close = as_float(tech.get("最新收盘"))
    ma20 = as_float(ma.get("MA20"))
    ma60 = as_float(ma.get("MA60"))
    rsi = as_float(tech.get("RSI14"), -1)
    macd = tech.get("MACD", {})
    dif = as_float(macd.get("DIF"))
    dea = as_float(macd.get("DEA"))
    volume_ratio = as_float(tech.get("量比5日"))
    score = 0.0
    reasons: list[str] = []
    tags: list[str] = []
    if tech.get("状态") == "成功":
        score += 5
        reasons.append("技术指标状态成功 +5")
    if close and ma20 and close > ma20:
        score += 8
        reasons.append("站上MA20 +8")
    if close and ma60 and close > ma60:
        score += 8
        reasons.append("站上MA60 +8")
    else:
        tags.append("未站上MA60")
    if dif > dea:
        score += 5
        reasons.append("MACD偏强 +5")
    if 45 <= rsi <= 70:
        score += 10
        reasons.append("RSI处于较稳区间 +10")
    elif 35 <= rsi < 45 or 70 < rsi <= 75:
        score += 6
        reasons.append("RSI可观察但接近边界 +6")
    elif rsi >= 0:
        score += 2
        reasons.append("RSI偏热或偏弱 +2")
        if rsi > 75:
            tags.append("RSI偏热")
    else:
        tags.append("RSI缺失")
    if volume_ratio >= 1.2:
        score += 6
        reasons.append("量比5日活跃 +6")
    elif volume_ratio >= 1.0:
        score += 3
        reasons.append("量比5日一般 +3")
        tags.append("量能一般")
    else:
        tags.append("量能偏弱或缺失")
    return round(score, 4), reasons, tags


def activity_score(percent: float) -> tuple[float, str]:
    value = abs(percent)
    if value >= 5:
        return 8.0, "涨跌幅绝对值>=5%，活跃度 +8"
    if value >= 2:
        return 6.0, "涨跌幅绝对值>=2%，活跃度 +6"
    if value >= 1:
        return 3.0, "涨跌幅绝对值>=1%，活跃度 +3"
    return 0.0, "涨跌幅活跃度不足1%，活跃度 +0"


def event_score(event: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    tags: list[str] = []
    reasons: list[str] = []
    if event.get("是否可进入精选推送草案") is True:
        reasons.append("事件核验允许进入精选草案 +15")
        return 15.0, reasons, tags
    tags.append("事件待核验")
    reasons.append("事件核验未放行 +0")
    return 0.0, reasons, tags


def risk_penalty(tags: list[str]) -> tuple[float, list[str]]:
    penalty = 0.0
    reasons: list[str] = []
    unique_tags = list(dict.fromkeys(tags))
    if "事件待核验" in unique_tags:
        penalty -= 8
        reasons.append("事件待核验 -8")
    if "RSI偏热" in unique_tags:
        penalty -= 5
        reasons.append("RSI偏热 -5")
    if "量能一般" in unique_tags:
        penalty -= 3
        reasons.append("量能一般 -3")
    if "未站上MA60" in unique_tags:
        penalty -= 5
        reasons.append("未站上MA60 -5")
    if "量能偏弱或缺失" in unique_tags:
        penalty -= 6
        reasons.append("量能偏弱或缺失 -6")
    return penalty, reasons


def decompose_candidate(item: dict[str, Any], event: dict[str, Any], diagnosis: dict[str, Any]) -> dict[str, Any]:
    market = item.get("行情摘要", {})
    current_score = as_float(item.get("推送前评分"))
    light_score = round(as_float(item.get("轻扫描评分")) / 10, 4)
    tech_score, tech_reasons, tech_tags = technical_score(item)
    turnover = as_float(market.get("成交额"))
    liquidity = round(min(turnover / 1_000_000_000, 10), 4)
    percent = as_float(market.get("涨跌幅"))
    active_score, active_reason = activity_score(percent)
    evidence = round(min(len(item.get("候选依据", [])) * 1.2, 12), 4)
    evt_score, evt_reasons, evt_tags = event_score(event)
    diagnosis_blockers = diagnosis.get("主要阻断", [])
    risk_tags = tech_tags + evt_tags
    for blocker in diagnosis_blockers:
        if "RSI偏热" in blocker and "RSI偏热" not in risk_tags:
            risk_tags.append("RSI偏热")
        if "量能一般" in blocker and "量能一般" not in risk_tags:
            risk_tags.append("量能一般")
    penalty, penalty_reasons = risk_penalty(risk_tags)
    estimated = round(light_score + tech_score + liquidity + active_score + evidence + evt_score + penalty, 4)
    return {
        "代码": item.get("代码"),
        "名称": item.get("名称"),
        "行业": item.get("行业"),
        "现有推送前评分": current_score,
        "重算估算分": estimated,
        "与现有评分差异": round(current_score - estimated, 4),
        "因子拆解": {
            "轻扫描基础分": light_score,
            "技术趋势分": tech_score,
            "流动性成交额分": liquidity,
            "活跃度分": active_score,
            "证据数量分": evidence,
            "事件核验分": evt_score,
            "风险扣分": penalty
        },
        "解释明细": {
            "技术趋势": tech_reasons,
            "流动性": [f"成交额{round(turnover / 100000000, 2)}亿元，最高按10分封顶"],
            "活跃度": [active_reason],
            "事件核验": evt_reasons,
            "风险扣分": penalty_reasons or ["未触发额外风险扣分"]
        },
        "风险标签": list(dict.fromkeys(risk_tags)) or ["未发现拆解层新增风险标签"],
        "分析备注": "重算估算分用于解释和排序校验，不替换现有推送前评分。"
    }


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    hot = [row["名称"] for row in rows if "RSI偏热" in row.get("风险标签", [])]
    weak_volume = [row["名称"] for row in rows if "量能一般" in row.get("风险标签", [])]
    event_pending = [row["名称"] for row in rows if "事件待核验" in row.get("风险标签", [])]
    avg_diff = round(sum(abs(as_float(row.get("与现有评分差异"))) for row in rows) / max(len(rows), 1), 4)
    return {
        "候选数量": len(rows),
        "RSI偏热候选": hot,
        "量能一般候选": weak_volume,
        "事件待核验候选": event_pending,
        "平均绝对差异": avg_diff,
        "结论": "评分拆解层已能解释候选分数主要来源；下一步应先补事件核验，再根据复盘结果决定是否调整过热和量能权重。"
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选评分因子拆解报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 总结",
        "",
        f"- 候选数量：{report['摘要']['候选数量']}",
        f"- RSI偏热候选：{('、'.join(report['摘要']['RSI偏热候选']) or '无')}",
        f"- 量能一般候选：{('、'.join(report['摘要']['量能一般候选']) or '无')}",
        f"- 事件待核验候选：{('、'.join(report['摘要']['事件待核验候选']) or '无')}",
        f"- 平均绝对差异：{report['摘要']['平均绝对差异']}",
        f"- 当前结论：{report['摘要']['结论']}",
        "",
        "## 候选拆解",
        ""
    ]
    for row in report.get("候选评分拆解", []):
        factors = row["因子拆解"]
        lines.append(
            f"- {row['名称']}（{row['代码']}）：现有评分{row['现有推送前评分']}，估算分{row['重算估算分']}，差异{row['与现有评分差异']}；"
            f"轻扫描{factors['轻扫描基础分']}，趋势{factors['技术趋势分']}，流动性{factors['流动性成交额分']}，活跃度{factors['活跃度分']}，证据{factors['证据数量分']}，事件{factors['事件核验分']}，风险{factors['风险扣分']}；"
            f"标签：{'、'.join(row['风险标签'])}"
        )
    lines.extend([
        "",
        "## 使用边界",
        "",
        "- 本报告只解释现有候选评分，不替换原评分。",
        "- 未补齐事件正文人工核验前，不放行精选推送。",
        "- 后续评分权重调整必须等T+1/T+3/T+5复盘结果回填后再做。",
        "",
        "## 安全边界",
        ""
    ])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选评分因子拆解规则.json"
    rule = load_json(rule_path)
    package_path = root / "03数据" / "96推送前候选包" / "300只候选推送前候选包_最新.json"
    event_path = root / "03数据" / "101事件核验结果回填" / "300只候选事件核验结果回填包_最新.json"
    diagnosis_path = root / "03数据" / "109股票分析质量诊断" / "300只候选股票分析质量诊断报告_最新.json"
    package = load_json(package_path)
    event_map = index_event_summary(load_json(event_path))
    diagnosis_map = index_diagnosis(load_json(diagnosis_path))
    rows = [
        decompose_candidate(
            item,
            event_map.get(str(item.get("代码", "")).lower(), {}),
            diagnosis_map.get(str(item.get("代码", "")).lower(), {})
        )
        for item in package.get("推送前候选", [])
    ]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "96推送前候选包": str(package_path),
            "101事件核验结果回填": str(event_path),
            "109股票分析质量诊断": str(diagnosis_path)
        },
        "摘要": build_summary(rows),
        "候选评分拆解": rows,
        "下一步建议": [
            "先补齐103人工核验结果，再运行108联动刷新，确认是否能进入精选草案。",
            "保留当前评分规则不变，先用110报告观察评分解释性。",
            "等T+1/T+3/T+5复盘回填后，再决定是否加入RSI偏热惩罚和量能持续性因子。",
            "扩展到800-1000只核心样本池前，补齐行业分类和样本多样性统计。"
        ],
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    latest_json = output_dir / rule["输出"]["最新文件"]
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(latest_md, markdown)
    print(json.dumps({"候选数量": len(rows), "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
