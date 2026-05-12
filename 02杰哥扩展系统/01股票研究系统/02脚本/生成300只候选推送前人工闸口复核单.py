# -*- coding: utf-8 -*-
"""
名称：生成300只候选推送前人工闸口复核单.py
作用：根据300只试运行池推送前候选包和复盘日期账本，生成推送前人工闸口复核单。
触发方式：python 生成300只候选推送前人工闸口复核单.py
依赖：Python标准库；300只候选推送前人工闸口规则.json；300只候选推送前候选包_最新.json；300只候选复盘日期账本_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地候选包和复盘日期账本并写入03数据；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选推送前人工闸口复核单脚本。
标识：stock-trial-pool-300-pre-push-human-gate-generate
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


def find_review_dates(review_book: dict[str, Any], code: str) -> dict[str, str]:
    for item in review_book.get("复盘账本", []):
        if item.get("代码") == code:
            dates: dict[str, str] = {}
            for plan in item.get("验证计划", []):
                dates[str(plan.get("周期"))] = str(plan.get("目标交易日"))
            return dates
    return {}


def initial_gate_result(candidate: dict[str, Any]) -> dict[str, Any]:
    risk_text = json.dumps(candidate.get("风险和复核点", []), ensure_ascii=False)
    indicator = candidate.get("技术指标摘要", {})
    rsi = indicator.get("RSI14")
    event_status = candidate.get("公告财务行业入口状态", {})
    blocks: list[str] = []
    if "公告、财务和行业事件尚未抓取正文" in risk_text:
        blocks.append("公告、财务和行业事件尚未核验正文，不能自动放行真实发送。")
    if isinstance(rsi, (int, float)) and rsi >= 75:
        blocks.append("RSI偏高，需人工判断是否短线过热。")
    if "不构成投资建议" not in risk_text:
        blocks.append("缺少不构成投资建议边界。")
    if "不形成买卖指令" not in risk_text:
        blocks.append("缺少不形成买卖指令边界。")
    if event_status.get("入口状态") != "已建立只读入口":
        blocks.append("公告财务行业事件只读入口状态异常。")
    return {
        "系统初始状态": "待人工复核",
        "系统初始意见": "暂缓真实发送，先做人工闸口复核。",
        "阻断或关注项": blocks or ["未发现系统层面新增阻断项，但仍需人工确认。"],
        "可填写人工意见": [
            "继续观察，暂不推送",
            "允许进入精选推送草案",
            "暂缓，等待公告财务行业正文核验",
            "剔除本轮候选"
        ],
        "默认人工意见": "暂缓，等待公告财务行业正文核验" if blocks else "继续观察，暂不推送",
        "人工确认人": "",
        "人工确认时间": "",
        "人工备注": ""
    }


def build_review_items(candidates: list[dict[str, Any]], review_book: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for rank, candidate in enumerate(candidates, start=1):
        code = str(candidate.get("代码", ""))
        indicator = candidate.get("技术指标摘要", {})
        items.append({
            "排序": rank,
            "代码": code,
            "名称": candidate.get("名称", ""),
            "推送前评分": candidate.get("推送前评分"),
            "行情摘要": candidate.get("行情摘要", {}),
            "技术摘要": {
                "最新日期": indicator.get("最新日期"),
                "最新收盘": indicator.get("最新收盘"),
                "RSI14": indicator.get("RSI14"),
                "MACD": indicator.get("MACD"),
                "量比5日": indicator.get("量比5日"),
                "技术观察": indicator.get("技术观察", [])
            },
            "候选依据": candidate.get("候选依据", []),
            "风险和复核点": candidate.get("风险和复核点", []),
            "公告财务行业入口状态": candidate.get("公告财务行业入口状态", {}),
            "复盘日期": find_review_dates(review_book, code),
            "人工闸口": initial_gate_result(candidate)
        })
    return items


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选推送前人工闸口复核单",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 当前状态：{report['当前状态']}",
        f"- 推送前候选数量：{report['推送前候选数量']}",
        f"- 是否允许自动真实发送：{report['是否允许自动真实发送']}",
        f"- 总结：{report['结论']}",
        "",
        "## 全局人工确认事项",
        "",
    ]
    for item in report["全局人工确认事项"]:
        lines.append(f"- [ ] {item}")
    lines.extend(["", "## 候选逐只复核", ""])
    for item in report["逐只复核单"]:
        lines.extend([
            f"### {item['排序']}. {item['名称']}（{item['代码']}）",
            "",
            f"- 推送前评分：{item['推送前评分']}",
            f"- 最新价：{item['行情摘要'].get('现价')}；涨跌幅：{item['行情摘要'].get('涨跌幅')}%；成交额：{item['行情摘要'].get('成交额')}",
            f"- RSI14：{item['技术摘要'].get('RSI14')}；量比5日：{item['技术摘要'].get('量比5日')}",
            f"- 复盘日期：T+1={item['复盘日期'].get('T+1', '待确认')}，T+3={item['复盘日期'].get('T+3', '待确认')}，T+5={item['复盘日期'].get('T+5', '待确认')}",
            f"- 系统初始意见：{item['人工闸口']['系统初始意见']}",
            f"- 默认人工意见：{item['人工闸口']['默认人工意见']}",
            "",
            "风险和复核点：",
        ])
        for risk in item["风险和复核点"]:
            lines.append(f"- {risk}")
        lines.extend(["", "人工确认：", "- [ ] 已复核公告正文", "- [ ] 已复核财务摘要或定期报告", "- [ ] 已复核行业事件来源", "- [ ] 确认不构成投资建议、不形成买卖指令", "- 人工意见：", "- 人工备注：", ""])
    lines.extend(["## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选推送前人工闸口规则.json"
    candidate_path = root / "03数据" / "96推送前候选包" / "300只候选推送前候选包_最新.json"
    review_date_path = root / "03数据" / "98交易日历复盘日期" / "300只候选复盘日期账本_最新.json"

    rule = load_json(rule_path)
    candidate_package = load_json(candidate_path)
    review_book = load_json(review_date_path)
    candidates = candidate_package.get("推送前候选", [])
    review_items = build_review_items(candidates, review_book)
    safety = rule.get("安全边界", {})
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "推送前候选包": str(candidate_path),
            "复盘日期账本": str(review_date_path)
        },
        "当前状态": "人工闸口待确认，真实发送关闭",
        "推送前候选数量": len(candidates),
        "全局人工确认事项": rule.get("放行前必须满足", []),
        "逐只复核单": review_items,
        "是否允许自动真实发送": False,
        "是否允许进入企业微信真实发送流程": False,
        "人工闸口结论": "待人工逐只确认；未确认前不得进入真实发送。",
        "结论": "已生成推送前人工闸口复核单；公告、财务、行业事件正文未复核前，保持暂缓真实发送。",
        "安全边界": safety
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选推送前人工闸口复核单_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只候选推送前人工闸口复核单_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"推送前候选数量": len(candidates), "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
