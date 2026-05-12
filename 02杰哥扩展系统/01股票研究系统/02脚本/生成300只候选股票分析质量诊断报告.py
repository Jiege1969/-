# -*- coding: utf-8 -*-
"""
名称：生成300只候选股票分析质量诊断报告.py
作用：诊断300只试运行池到推送前候选的分析质量和优化方向；只生成报告，不改评分、不发送。
触发方式：python 生成300只候选股票分析质量诊断报告.py
依赖：Python标准库；300只候选股票分析质量诊断规则.json；92/93/94/96/101/102/108最新产物。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读股票研究系统本地产物并写109诊断报告；不修改评分规则；不修改候选清单；不触发发送链路；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选股票分析质量诊断报告脚本。
标识：stock-trial-pool-300-analysis-quality-diagnosis
"""

from __future__ import annotations

import json
from collections import Counter
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


def index_by_code(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("代码", "")).lower(): item for item in items if item.get("代码")}


def trend_state(item: dict[str, Any]) -> dict[str, Any]:
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
    return {
        "站上MA20": bool(close and ma20 and close > ma20),
        "站上MA60": bool(close and ma60 and close > ma60),
        "RSI14": rsi,
        "RSI状态": "偏热" if rsi > 75 else "可观察" if 35 <= rsi <= 75 else "偏弱" if rsi >= 0 else "缺失",
        "MACD状态": "偏强" if dif > dea else "偏弱或缺失",
        "量比5日": volume_ratio,
        "量能状态": "活跃" if volume_ratio >= 1.1 else "一般" if volume_ratio > 0 else "缺失"
    }


def diagnose_candidate(item: dict[str, Any], event_summary: dict[str, Any] | None) -> dict[str, Any]:
    trend = trend_state(item)
    risks = list(item.get("风险和复核点", []))
    strengths = list(item.get("候选依据", []))
    event_summary = event_summary or {}
    blockers: list[str] = []
    if event_summary.get("是否存在待人工核验") is True or "待人工核验" in event_summary.get("核验状态统计", {}):
        blockers.append("公告、财务、行业事件正文仍待人工核验")
    if trend["RSI状态"] == "偏热":
        blockers.append("RSI偏热，需在复盘中验证是否短线过热")
    if not trend["站上MA60"]:
        blockers.append("未站上MA60，中期趋势需谨慎")
    if trend["量能状态"] == "一般":
        blockers.append("量能一般，需观察持续性")
    return {
        "代码": item.get("代码"),
        "名称": item.get("名称"),
        "推送前评分": item.get("推送前评分"),
        "轻扫描评分": item.get("轻扫描评分"),
        "趋势诊断": trend,
        "依据数量": len(strengths),
        "风险复核点数量": len(risks),
        "事件核验结论": event_summary.get("系统回填结论", "未找到事件核验摘要"),
        "是否可进入精选推送草案": event_summary.get("是否可进入精选推送草案", False),
        "主要阻断": blockers or ["未发现诊断层新增阻断"],
        "优化提示": build_candidate_suggestions(trend, event_summary)
    }


def build_candidate_suggestions(trend: dict[str, Any], event_summary: dict[str, Any]) -> list[str]:
    suggestions: list[str] = []
    if event_summary.get("是否可进入精选推送草案") is not True:
        suggestions.append("优先补齐公告、财务、行业事件正文核验，否则评分无法转化为精选草案。")
    if trend["RSI状态"] == "偏热":
        suggestions.append("增加短线过热惩罚或观察标签，避免只因趋势强就过度靠前。")
    if trend["量能状态"] == "一般":
        suggestions.append("补充量能持续性指标，如3日/10日量能变化，而不是只看单个量比。")
    if trend["站上MA20"] and trend["站上MA60"]:
        suggestions.append("保留趋势强度标签，并在T+1/T+3/T+5验证是否兑现。")
    return suggestions


def build_bottlenecks(draft: dict[str, Any], refresh: dict[str, Any], diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bottlenecks: list[dict[str, Any]] = []
    if int(draft.get("入选草案数量", 0)) == 0:
        bottlenecks.append({
            "问题": "当前精选草案入选数量为0",
            "影响": "分析链路能筛出候选，但不能进入精选推送草案。",
            "优化动作": "先完成事件正文核验填写，再运行108联动刷新。"
        })
    if refresh.get("最新状态摘要", {}).get("105是否具备提交真实发送讨论资格") is False:
        bottlenecks.append({
            "问题": "真实发送前检查仍阻断",
            "影响": "不能进入真实发送讨论。",
            "优化动作": "保持真实发送关闭，优先提升候选证据质量和人工确认质量。"
        })
    hot_count = sum(1 for item in diagnostics if item.get("趋势诊断", {}).get("RSI状态") == "偏热")
    if hot_count:
        bottlenecks.append({
            "问题": f"{hot_count}只候选RSI偏热",
            "影响": "趋势强但短线过热，可能影响后续复盘稳定性。",
            "优化动作": "在下一层评分优化中加入短线过热惩罚或风险标签。"
        })
    volume_general = sum(1 for item in diagnostics if item.get("趋势诊断", {}).get("量能状态") == "一般")
    if volume_general:
        bottlenecks.append({
            "问题": f"{volume_general}只候选量能一般",
            "影响": "候选活跃度持续性不足，单日强度可能不稳定。",
            "优化动作": "增加3日/10日量能连续性观察。"
        })
    return bottlenecks


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选股票分析质量诊断报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 总结",
        "",
        f"- 数据健康状态：{report['数据覆盖诊断']['轻扫描健康状态']}",
        f"- 技术指标成功率：{report['数据覆盖诊断']['技术指标成功率']}",
        f"- 推送前候选数量：{report['数据覆盖诊断']['推送前候选数量']}",
        f"- 精选草案入选数量：{report['数据覆盖诊断']['精选草案入选数量']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 主要瓶颈",
        "",
    ]
    for item in report.get("主要瓶颈", []):
        lines.append(f"- {item['问题']}：{item['影响']} 建议：{item['优化动作']}")
    lines.extend(["", "## 候选诊断", ""])
    for item in report.get("候选诊断", []):
        lines.append(f"- {item['名称']}（{item['代码']}）：评分{item['推送前评分']}，事件结论：{item['事件核验结论']}，阻断：{'；'.join(item['主要阻断'])}")
    lines.extend(["", "## 下一步优化优先级", ""])
    for index, item in enumerate(report.get("下一步优化优先级", []), start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选股票分析质量诊断规则.json"
    rule = load_json(rule_path)
    scan = load_json(root / "03数据" / "92盘后轻扫描" / "300只试运行池盘后轻扫描_最新.json")
    preprocess = load_json(root / "03数据" / "93深度分析预处理" / "300只盘后深度分析预处理包_最新.json")
    indicators = load_json(root / "03数据" / "94候选历史K线技术指标" / "300只候选技术指标_最新.json")
    package = load_json(root / "03数据" / "96推送前候选包" / "300只候选推送前候选包_最新.json")
    event_backfill = load_json(root / "03数据" / "101事件核验结果回填" / "300只候选事件核验结果回填包_最新.json")
    draft = load_json(root / "03数据" / "102精选推送草案" / "300只候选精选推送草案_最新.json")
    refresh = load_json(root / "03数据" / "108人工核验后联动刷新" / "300只候选人工核验后联动刷新报告_最新.json")
    event_map = index_by_code(event_backfill.get("候选核验结果", event_backfill.get("事件核验结果", [])))
    if not event_map:
        ledger_items = event_backfill.get("派生复盘账本", []) or event_backfill.get("复盘账本", [])
        event_map = {
            str(item.get("代码", "")).lower(): item.get("事件正文核验回填", {})
            for item in ledger_items
            if item.get("代码")
        }
    diagnostics = [
        diagnose_candidate(item, event_map.get(str(item.get("代码", "")).lower()))
        for item in package.get("推送前候选", [])
    ]
    tech_success = int(indicators.get("成功数量", 0))
    tech_total = int(indicators.get("候选数量", len(indicators.get("技术指标", [])) or 1))
    source_counter = Counter(item.get("入池原因", "未知") for item in scan.get("候选清单", []))
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "92轻扫描": str(root / "03数据" / "92盘后轻扫描" / "300只试运行池盘后轻扫描_最新.json"),
            "93深度预处理": str(root / "03数据" / "93深度分析预处理" / "300只盘后深度分析预处理包_最新.json"),
            "94技术指标": str(root / "03数据" / "94候选历史K线技术指标" / "300只候选技术指标_最新.json"),
            "96推送前候选包": str(root / "03数据" / "96推送前候选包" / "300只候选推送前候选包_最新.json"),
            "101事件回填": str(root / "03数据" / "101事件核验结果回填" / "300只候选事件核验结果回填包_最新.json"),
            "102精选草案": str(root / "03数据" / "102精选推送草案" / "300只候选精选推送草案_最新.json"),
            "108联动刷新": str(root / "03数据" / "108人工核验后联动刷新" / "300只候选人工核验后联动刷新报告_最新.json")
        },
        "数据覆盖诊断": {
            "轻扫描健康状态": scan.get("数据健康度", {}).get("状态"),
            "试运行池股票数量": scan.get("数据健康度", {}).get("股票数量"),
            "真实行情字段完整比例": scan.get("数据健康度", {}).get("真实行情字段完整比例"),
            "深度预处理候选数量": len(preprocess.get("预处理候选", [])),
            "技术指标成功率": f"{tech_success}/{tech_total}",
            "推送前候选数量": package.get("推送前候选数量"),
            "精选草案入选数量": draft.get("入选草案数量"),
            "精选草案暂缓数量": draft.get("暂缓数量")
        },
        "候选来源结构": dict(source_counter),
        "候选诊断": diagnostics,
        "主要瓶颈": build_bottlenecks(draft, refresh, diagnostics),
        "下一步优化优先级": [
            "第一优先级：补齐103人工核验结果，再运行108联动刷新，解决候选无法进入精选草案的问题。",
            "第二优先级：建立110评分因子拆解层，把轻扫描、趋势、量能、过热、事件核验分别列分，提升评分可解释性。",
            "第三优先级：增加短线过热和量能持续性诊断，避免强趋势候选只因单日表现靠前。",
            "第四优先级：补齐行业分类和样本多样性统计，为800-1000只核心样本池扩容做准备。",
            "第五优先级：到T+1/T+3/T+5后回填107复盘结果，用真实复盘数据反校准评分权重。"
        ],
        "当前结论": "股票分析链路已能稳定筛出候选；当前主要短板不是脚本运行，而是事件正文核验、评分因子可解释性、过热/量能持续性和复盘反校准。",
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选股票分析质量诊断报告_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只候选股票分析质量诊断报告_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"推送前候选数量": package.get("推送前候选数量"), "主要瓶颈数量": len(report["主要瓶颈"]), "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
