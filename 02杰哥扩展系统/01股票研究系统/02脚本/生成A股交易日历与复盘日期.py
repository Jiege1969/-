# -*- coding: utf-8 -*-
"""
名称：生成A股交易日历与复盘日期.py
作用：将300只试运行池推送前候选账本中的T+1/T+3/T+5验证占位转换为具体A股交易日。
触发方式：python 生成A股交易日历与复盘日期.py
依赖：Python标准库；A股交易日历与复盘日期规则.json；300只候选复盘闭环账本_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写新系统交易日历复盘日期文件；不联网；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建A股交易日历与复盘日期脚本。
标识：stock-a-share-trading-calendar-review-date-generate
"""

from __future__ import annotations

import copy
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_date(value: str) -> date:
    return datetime.strptime(value[:10], "%Y-%m-%d").date()


def date_text(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def build_calendar(rule: dict[str, Any]) -> dict[str, Any]:
    calendar_rule = rule["交易日历"]
    start = parse_date(calendar_rule["本轮覆盖开始"])
    end = parse_date(calendar_rule["本轮覆盖结束"])
    holidays = set(calendar_rule.get("节假日休市日期", []))
    extra_weekend_closed = set(calendar_rule.get("额外周末休市日期", []))
    rows = []
    cursor = start
    while cursor <= end:
        text = date_text(cursor)
        weekday = cursor.weekday()
        is_weekend = weekday >= 5
        is_closed = (is_weekend and calendar_rule.get("周末休市规则", True)) or text in holidays or text in extra_weekend_closed
        reason = ""
        if text in holidays:
            reason = "节假日休市"
        elif text in extra_weekend_closed:
            reason = "周末休市"
        elif is_weekend:
            reason = "周末休市"
        else:
            reason = "正常交易日"
        rows.append({
            "日期": text,
            "星期": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][weekday],
            "是否交易日": not is_closed,
            "说明": reason,
        })
        cursor += timedelta(days=1)
    return {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "年份": calendar_rule["年份"],
        "市场": calendar_rule["市场"],
        "覆盖开始": calendar_rule["本轮覆盖开始"],
        "覆盖结束": calendar_rule["本轮覆盖结束"],
        "官方依据": rule.get("官方依据", []),
        "日历": rows,
        "交易日": [item["日期"] for item in rows if item["是否交易日"]],
        "休市日": [item["日期"] for item in rows if not item["是否交易日"]],
        "安全边界": {
            "是否联网": False,
            "是否写正式库": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否重启服务": False,
        },
    }


def nth_trading_day_after(base_date: str, trading_days: list[str], offset: int) -> str:
    base = parse_date(base_date)
    after = [item for item in trading_days if parse_date(item) > base]
    if len(after) < offset:
        return "交易日历覆盖不足"
    return after[offset - 1]


def update_review_plan(item: dict[str, Any], signal_date: str, trading_days: list[str], cycles: dict[str, int]) -> dict[str, Any]:
    output = copy.deepcopy(item)
    for plan in output.get("验证计划", []):
        cycle = plan.get("周期")
        if cycle in cycles:
            target = nth_trading_day_after(signal_date, trading_days, int(cycles[cycle]))
            plan["信号日期"] = signal_date
            plan["目标交易日"] = target
            plan["交易日历状态"] = "已确认" if target != "交易日历覆盖不足" else "覆盖不足"
            plan["日期确认依据"] = "A股交易日历与复盘日期规则；交易所2026年劳动节休市公告。"
    return output


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选复盘日期报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结果概览",
        "",
        f"- 信号日期：{report['信号日期']}",
        f"- 入账候选数量：{report['入账候选数量']}",
        f"- T+1：{report['周期日期'].get('T+1')}",
        f"- T+3：{report['周期日期'].get('T+3')}",
        f"- T+5：{report['周期日期'].get('T+5')}",
        "- 真实发送：关闭",
        "- 自动交易：关闭",
        "",
        "## 候选摘要",
        "",
    ]
    for index, item in enumerate(report.get("复盘账本", []), start=1):
        plans = {plan["周期"]: plan["目标交易日"] for plan in item.get("验证计划", [])}
        lines.append(f"{index}. {item['名称']}（{item['代码']}）：T+1 {plans.get('T+1')}，T+3 {plans.get('T+3')}，T+5 {plans.get('T+5')}。")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "A股交易日历与复盘日期规则.json"
    rule = load_json(rule_path)
    source_path = root / rule["输入"]["复盘闭环账本"]
    source = load_json(source_path)
    calendar = build_calendar(rule)
    signal_date = source.get("生成时间", "")[:10] or rule["交易日历"]["本轮覆盖开始"]
    cycles = rule.get("复盘周期", {"T+1": 1, "T+3": 3, "T+5": 5})
    cycle_dates = {cycle: nth_trading_day_after(signal_date, calendar["交易日"], int(offset)) for cycle, offset in cycles.items()}
    updated_ledger = [update_review_plan(item, signal_date, calendar["交易日"], cycles) for item in source.get("复盘账本", [])]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "原复盘闭环账本": str(source_path),
        "信号日期": signal_date,
        "入账候选数量": len(updated_ledger),
        "周期日期": cycle_dates,
        "官方依据": rule.get("官方依据", []),
        "复盘账本": updated_ledger,
        "结论": "已将T+1/T+3/T+5验证占位转换为具体A股交易日；真实发送和自动交易保持关闭。",
        "安全边界": {
            "是否联网": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否写正式库": False,
            "是否写旧系统": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否重启服务": False,
        },
    }

    output_dir = root / rule["输出"]["数据目录"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    calendar_output = output_dir / f"A股交易日历_2026_{timestamp}.json"
    calendar_latest = output_dir / rule["输出"]["交易日历最新文件"]
    ledger_output = output_dir / f"300只候选复盘日期账本_{timestamp}.json"
    ledger_latest = output_dir / rule["输出"]["复盘日期账本最新文件"]
    markdown = output_dir / f"300只候选复盘日期报告_{timestamp}.md"
    markdown_latest = output_dir / rule["输出"]["报告文件"]
    write_json(calendar_output, calendar)
    write_json(calendar_latest, calendar)
    write_json(ledger_output, report)
    write_json(ledger_latest, report)
    markdown_text = build_markdown(report)
    markdown.write_text(markdown_text, encoding="utf-8")
    markdown_latest.write_text(markdown_text, encoding="utf-8")
    print(json.dumps({"信号日期": signal_date, "周期日期": cycle_dates, "入账候选数量": len(updated_ledger), "输出": str(ledger_output)}, ensure_ascii=False))
    return 0 if updated_ledger and all(value != "交易日历覆盖不足" for value in cycle_dates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
