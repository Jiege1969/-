# -*- coding: utf-8 -*-
"""
名称：生成300只候选事件核验结果回填包.py
作用：读取事件正文核验任务清单，将人工核验状态聚合后生成回填包、人工闸口派生账本和复盘闭环派生账本。
触发方式：python 生成300只候选事件核验结果回填包.py
依赖：Python标准库；300只候选事件核验结果回填规则.json；300只候选公告财务行业事件正文核验任务_最新.json；300只候选推送前人工闸口复核单_最新.json；300只候选复盘闭环账本_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地产物并写入101派生结果；不覆盖原始99人工闸口；不覆盖原始97复盘账本；不联网抓取；不下载正文；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选事件核验结果回填包脚本。
标识：stock-trial-pool-300-event-verification-backfill-generate
"""

from __future__ import annotations

import copy
import json
from collections import Counter, defaultdict
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


def normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip()
    return text in {"是", "true", "True", "1", "有", "发现"}


def group_tasks(tasks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        grouped[str(task.get("代码", ""))].append(task)
    return grouped


def task_status(task: dict[str, Any]) -> str:
    return str(task.get("核验结果", {}).get("状态", "待人工核验") or "待人工核验")


def is_high_priority(task: dict[str, Any]) -> bool:
    if task.get("优先级") == "高":
        return True
    level = str(task.get("来源级别", ""))
    return "官方" in level or "交易所" in level or "正式优先" in level


def summarize_stock(code: str, tasks: list[dict[str, Any]]) -> dict[str, Any]:
    status_counter = Counter(task_status(task) for task in tasks)
    type_counter = Counter(str(task.get("任务类型", "")) for task in tasks)
    high_tasks = [task for task in tasks if is_high_priority(task)]
    high_all_passed = bool(high_tasks) and all(task_status(task) == "通过" for task in high_tasks)
    has_block = any(task_status(task) == "阻断" for task in tasks)
    has_pending = any(task_status(task) == "待人工核验" for task in tasks)
    has_uncertain = any(task_status(task) == "继续待核实" for task in tasks)
    has_major_risk = any(normalize_bool(task.get("核验结果", {}).get("是否发现新增重大风险", "")) for task in tasks)
    type_pass = {
        kind: any(task_status(task) == "通过" for task in tasks if task.get("任务类型") == kind)
        for kind in ["公告正文核验", "财务报告核验", "行业事件线索核验"]
    }
    can_enter_draft = (
        not has_block
        and not has_pending
        and not has_uncertain
        and not has_major_risk
        and high_all_passed
        and all(type_pass.values())
    )
    if can_enter_draft:
        conclusion = "可进入精选推送草案"
        default_gate_opinion = "允许进入精选推送草案"
    elif has_block or has_major_risk:
        conclusion = "阻断本轮精选推送草案"
        default_gate_opinion = "剔除本轮候选"
    elif has_pending or has_uncertain:
        conclusion = "继续待人工核验"
        default_gate_opinion = "暂缓，等待公告财务行业正文核验"
    else:
        conclusion = "继续观察，暂不推送"
        default_gate_opinion = "继续观察，暂不推送"
    return {
        "代码": code,
        "名称": next((str(task.get("名称", "")) for task in tasks if task.get("名称")), ""),
        "任务数量": len(tasks),
        "任务类型统计": dict(type_counter),
        "核验状态统计": dict(status_counter),
        "高优先级任务数量": len(high_tasks),
        "高优先级任务是否全部通过": high_all_passed,
        "是否存在阻断": has_block,
        "是否存在待人工核验": has_pending,
        "是否存在继续待核实": has_uncertain,
        "是否存在新增重大风险": has_major_risk,
        "分类型通过情况": type_pass,
        "是否可进入精选推送草案": can_enter_draft,
        "系统回填结论": conclusion,
        "建议人工闸口意见": default_gate_opinion,
        "任务明细": [
            {
                "任务ID": task.get("任务ID"),
                "任务类型": task.get("任务类型"),
                "入口名称": task.get("入口名称"),
                "来源级别": task.get("来源级别"),
                "优先级": task.get("优先级"),
                "核验结果": task.get("核验结果", {})
            }
            for task in tasks
        ]
    }


def build_gate_derivative(gate: dict[str, Any], summaries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    derived = copy.deepcopy(gate)
    derived["生成时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    derived["派生来源"] = "事件核验结果回填包"
    derived["是否覆盖原始人工闸口"] = False
    for item in derived.get("逐只复核单", []):
        code = str(item.get("代码", ""))
        summary = summaries.get(code, {})
        item["事件正文核验回填"] = summary
        gate_info = item.setdefault("人工闸口", {})
        if summary:
            gate_info["事件核验后系统建议"] = summary.get("建议人工闸口意见")
            gate_info["事件核验后是否可进入精选推送草案"] = summary.get("是否可进入精选推送草案")
            gate_info["事件核验后结论"] = summary.get("系统回填结论")
    derived["人工闸口结论"] = "已生成事件核验结果派生回填；原始人工闸口未覆盖，真实发送仍关闭。"
    derived["是否允许自动真实发送"] = False
    derived["是否允许进入企业微信真实发送流程"] = False
    return derived


def build_review_derivative(review_book: dict[str, Any], summaries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    derived = copy.deepcopy(review_book)
    derived["生成时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    derived["派生来源"] = "事件核验结果回填包"
    derived["是否覆盖原始复盘账本"] = False
    for item in derived.get("复盘账本", []):
        code = str(item.get("代码", ""))
        summary = summaries.get(code, {})
        item["事件正文核验回填"] = summary
        item.setdefault("推送记录", {})["事件核验后状态"] = summary.get("系统回填结论", "无核验任务")
        item.setdefault("推送记录", {})["是否允许进入真实发送"] = False
    derived["结论"] = "已生成事件核验结果派生复盘账本；原始复盘账本未覆盖，真实发送仍关闭。"
    return derived


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选事件核验结果回填包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 当前状态：{report['当前状态']}",
        f"- 候选数量：{report['候选数量']}",
        f"- 核验任务数量：{report['核验任务数量']}",
        f"- 可进入精选推送草案数量：{report['可进入精选推送草案数量']}",
        f"- 总结：{report['结论']}",
        "",
        "## 逐只回填结果",
        "",
    ]
    for item in report["逐只回填结果"]:
        lines.extend([
            f"### {item['名称']}（{item['代码']}）",
            "",
            f"- 任务数量：{item['任务数量']}",
            f"- 状态统计：{json.dumps(item['核验状态统计'], ensure_ascii=False)}",
            f"- 高优先级任务是否全部通过：{item['高优先级任务是否全部通过']}",
            f"- 是否可进入精选推送草案：{item['是否可进入精选推送草案']}",
            f"- 系统回填结论：{item['系统回填结论']}",
            f"- 建议人工闸口意见：{item['建议人工闸口意见']}",
            "",
        ])
    lines.extend(["## 派生文件", ""])
    for key, value in report["派生文件"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选事件核验结果回填规则.json"
    filled_task_path = root / "03数据" / "103人工核验结果填写" / "300只候选公告财务行业事件正文核验任务_带人工填写结果_最新.json"
    original_task_path = root / "03数据" / "100事件正文核验任务" / "300只候选公告财务行业事件正文核验任务_最新.json"
    task_path = filled_task_path if filled_task_path.exists() else original_task_path
    gate_path = root / "03数据" / "99推送前人工闸口" / "300只候选推送前人工闸口复核单_最新.json"
    review_path = root / "03数据" / "97候选复盘闭环" / "300只候选复盘闭环账本_最新.json"

    rule = load_json(rule_path)
    task_book = load_json(task_path)
    gate = load_json(gate_path)
    review_book = load_json(review_path)
    grouped = group_tasks(task_book.get("核验任务", []))
    summaries = {code: summarize_stock(code, tasks) for code, tasks in grouped.items()}
    summary_list = list(summaries.values())

    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_json = output_dir / f"300只候选事件核验结果回填包_{stamp}.json"
    latest_md = output_dir / rule["输出"]["报告文件"]
    output_md = output_dir / f"300只候选事件核验结果回填包_{stamp}.md"
    gate_derivative_path = output_dir / rule["输出"]["人工闸口派生文件"]
    review_derivative_path = output_dir / rule["输出"]["复盘闭环派生文件"]

    gate_derivative = build_gate_derivative(gate, summaries)
    review_derivative = build_review_derivative(review_book, summaries)
    write_json(gate_derivative_path, gate_derivative)
    write_json(review_derivative_path, review_derivative)

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "事件正文核验任务": str(task_path),
            "事件正文核验任务来源": "103人工核验结果填写派生任务" if task_path == filled_task_path else "100原始事件正文核验任务",
            "推送前人工闸口": str(gate_path),
            "复盘闭环账本": str(review_path)
        },
        "候选数量": len(summary_list),
        "核验任务数量": len(task_book.get("核验任务", [])),
        "当前状态": "事件核验结果回填预演，原始账本未覆盖，真实发送关闭",
        "逐只回填结果": summary_list,
        "可进入精选推送草案数量": sum(1 for item in summary_list if item["是否可进入精选推送草案"]),
        "派生文件": {
            "人工闸口派生账本": str(gate_derivative_path),
            "复盘闭环派生账本": str(review_derivative_path)
        },
        "结论": "已生成事件核验结果回填包和两个派生账本；当前核验任务未人工填写时，所有候选继续暂缓真实发送。",
        "安全边界": rule.get("安全边界", {})
    }
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"候选数量": report["候选数量"], "核验任务数量": report["核验任务数量"], "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
