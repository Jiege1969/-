# -*- coding: utf-8 -*-
"""
名称：生成300只候选复盘执行任务包.py
作用：基于交易日历和复盘账本生成T+1/T+3/T+5复盘执行任务；只安排任务，不抓行情、不发送、不交易。
触发方式：python 生成300只候选复盘执行任务包.py
依赖：Python标准库；300只候选复盘执行任务包规则.json；98复盘日期账本；101派生复盘账本；102精选推送草案；105真实发送前检查包。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写入106任务包；不联网抓取行情；不触发发送链路；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选复盘执行任务包脚本。
标识：stock-trial-pool-300-review-execution-task-package
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime
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


def parse_day(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def due_state(target_day: str, today: date) -> str:
    day = parse_day(target_day)
    if today < day:
        return "未到期"
    if today == day:
        return "今日到期"
    return "已到期待补复盘"


def index_by_code(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("代码")): item for item in items if item.get("代码")}


def build_task(
    candidate: dict[str, Any],
    cycle: str,
    target_day: str,
    rule: dict[str, Any],
    draft_by_code: dict[str, dict[str, Any]],
    today: date,
) -> dict[str, Any]:
    code = str(candidate.get("代码"))
    draft_item = draft_by_code.get(code, {})
    verification = candidate.get("事件正文核验回填", {})
    return {
        "任务ID": f"{code}-{cycle}",
        "代码": code,
        "名称": candidate.get("名称"),
        "周期": cycle,
        "信号日期": draft_item.get("复盘日期", {}).get("信号日期") or "2026-04-30",
        "目标复盘日": target_day,
        "到期状态": due_state(target_day, today),
        "执行状态": "待执行",
        "真实发送状态": "未发送",
        "真实交易状态": "未交易",
        "推送前评分": candidate.get("推送前评分"),
        "事件核验结论": verification.get("系统回填结论", "待人工核验"),
        "是否进入精选推送草案": bool(verification.get("是否可进入精选推送草案", False)),
        "草案状态": draft_item.get("草案状态", "未进入精选推送草案"),
        "复盘字段": list(rule.get("复盘字段", [])),
        "基准技术指标摘要": candidate.get("技术指标摘要", {}),
        "原候选依据": candidate.get("候选依据", []),
        "原风险和复核点": candidate.get("风险和复核点", []),
        "人工填写区": {
            "复盘日收盘价": "",
            "复盘日涨跌幅": "",
            "区间涨跌幅": "",
            "成交额变化": "",
            "技术形态变化": "",
            "新增公告财务行业风险": "",
            "是否验证原候选依据": "",
            "是否兑现原风险点": "",
            "复盘结论": "",
            "经验提炼标签": "",
            "复盘人": "",
            "复盘时间": "",
            "备注": ""
        },
        "执行边界": [
            "到期后仅做只读复盘或人工填写。",
            "本任务不构成投资建议，不形成买卖指令。",
            "不得调用券商接口，不得自动交易。",
            "不得触发企业微信真实发送或n8n。"
        ]
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选复盘执行任务包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 概览",
        "",
        f"- 信号日期：{report['信号日期']}",
        f"- 候选数量：{report['候选数量']}",
        f"- 任务数量：{report['任务数量']}",
        f"- 真实发送：{report['是否企业微信真实发送']}",
        f"- 自动交易：{report['是否自动交易']}",
        "",
        "## 到期分组",
        "",
    ]
    for day, tasks in report.get("按复盘日分组", {}).items():
        lines.append(f"### {day}")
        for task in tasks:
            lines.append(f"- {task['周期']}：{task['名称']}（{task['代码']}），状态：{task['到期状态']}，执行：{task['执行状态']}。")
        lines.append("")
    lines.extend(["## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选复盘执行任务包规则.json"
    rule = load_json(rule_path)
    date_ledger_path = root / "03数据" / "98交易日历复盘日期" / "300只候选复盘日期账本_最新.json"
    review_ledger_path = root / "03数据" / "101事件核验结果回填" / "300只候选复盘闭环账本_带事件核验结果_最新.json"
    draft_path = root / "03数据" / "102精选推送草案" / "300只候选精选推送草案_最新.json"
    precheck_path = root / "03数据" / "105真实发送前检查" / "300只候选真实发送前检查包_最新.json"
    date_ledger = load_json(date_ledger_path)
    review_ledger = load_json(review_ledger_path)
    draft = load_json(draft_path)
    precheck = load_json(precheck_path)
    candidates = list(review_ledger.get("复盘账本", []))
    draft_items = list(draft.get("入选草案", [])) + list(draft.get("暂缓候选", []))
    draft_by_code = index_by_code(draft_items)
    cycles = list(rule.get("任务周期", ["T+1", "T+3", "T+5"]))
    cycle_dates = dict(date_ledger.get("周期日期", {}))
    today = date.today()
    tasks = [
        build_task(candidate, cycle, cycle_dates[cycle], rule, draft_by_code, today)
        for candidate in candidates
        for cycle in cycles
        if cycle in cycle_dates
    ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        grouped[task["目标复盘日"]].append(task)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "98复盘日期账本": str(date_ledger_path),
            "101派生复盘账本": str(review_ledger_path),
            "102精选推送草案": str(draft_path),
            "105真实发送前检查": str(precheck_path)
        },
        "信号日期": date_ledger.get("信号日期"),
        "周期日期": cycle_dates,
        "候选数量": len(candidates),
        "任务数量": len(tasks),
        "复盘执行任务": tasks,
        "按复盘日分组": dict(sorted(grouped.items())),
        "真实发送前检查结论": precheck.get("当前结论"),
        "是否企业微信真实发送": False,
        "是否自动交易": False,
        "结论": "T+1/T+3/T+5复盘执行任务包已生成；当前仅安排只读复盘任务，不抓行情、不发送、不交易。",
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选复盘执行任务包_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只候选复盘执行任务包_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"候选数量": len(candidates), "任务数量": len(tasks), "输出": str(output_json)}, ensure_ascii=False))
    return 0 if tasks else 1


if __name__ == "__main__":
    raise SystemExit(main())
