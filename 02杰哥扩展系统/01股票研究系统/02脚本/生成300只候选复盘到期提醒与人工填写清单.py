# -*- coding: utf-8 -*-
"""
名称：生成300只候选复盘到期提醒与人工填写清单.py
作用：按T+1/T+3/T+5复盘日期生成到期提醒和人工填写清单；不创建系统定时任务、不抓行情、不写复盘结论。
触发方式：python 生成300只候选复盘到期提醒与人工填写清单.py
依赖：Python标准库；300只候选复盘到期提醒与人工填写清单规则.json；107复盘模板/派生文件；113占位账本。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写114提醒清单；不创建系统定时任务；不联网抓取行情；不写入复盘结论；不修改评分规则；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选复盘到期提醒与人工填写清单脚本。
标识：stock-trial-pool-300-review-due-manual-checklist
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


def parse_date(text: str) -> date:
    return datetime.strptime(text, "%Y-%m-%d").date()


def days_until(target: str) -> int:
    return (parse_date(target) - date.today()).days


def index_placeholder(placeholder: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("任务ID", "")): item
        for item in placeholder.get("任务级反校准占位", [])
        if item.get("任务ID")
    }


def filled_required_count(task: dict[str, Any], required: list[str]) -> int:
    manual = task.get("人工填写区", {})
    return sum(1 for field in required if str(manual.get(field, "")).strip())


def build_due_groups(tasks: list[dict[str, Any]], placeholder_map: dict[str, dict[str, Any]], required: list[str]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        grouped[str(task.get("目标复盘日"))].append(task)
    groups = []
    for due_date in sorted(grouped):
        rows = []
        for task in grouped[due_date]:
            item = placeholder_map.get(str(task.get("任务ID")), {})
            rows.append({
                "任务ID": task.get("任务ID"),
                "代码": task.get("代码"),
                "名称": task.get("名称"),
                "周期": task.get("周期"),
                "到期状态": task.get("到期状态"),
                "执行状态": task.get("执行状态"),
                "复盘状态": item.get("复盘状态", "等待复盘结果"),
                "短线过热等级": item.get("复盘观察标签", {}).get("短线过热等级", ""),
                "量能持续等级": item.get("复盘观察标签", {}).get("量能持续等级", ""),
                "主题归类": item.get("复盘观察标签", {}).get("主题归类", ""),
                "必填字段数量": len(required),
                "已填字段数量": filled_required_count(task, required),
                "待填字段": [field for field in required if not str(task.get("人工填写区", {}).get(field, "")).strip()],
                "填写方式": "使用107复盘结果填写模板或记录单条复盘结果.py录入",
                "禁止动作": [
                    "不自动抓行情",
                    "不自动写复盘结论",
                    "不自动调整评分权重",
                    "不触发企业微信真实发送",
                    "不调用券商接口"
                ]
            })
        groups.append({
            "复盘日期": due_date,
            "距离当前天数": days_until(due_date),
            "任务数量": len(rows),
            "任务": rows
        })
    return groups


def build_summary(groups: list[dict[str, Any]]) -> dict[str, Any]:
    total_tasks = sum(group.get("任务数量", 0) for group in groups)
    nearest = min(groups, key=lambda item: item["距离当前天数"]) if groups else {}
    return {
        "复盘日期数量": len(groups),
        "复盘任务数量": total_tasks,
        "最近复盘日期": nearest.get("复盘日期", ""),
        "最近复盘距离当前天数": nearest.get("距离当前天数", ""),
        "当前结论": "复盘到期提醒清单已生成；仅作为人工执行清单，不创建系统定时任务，不自动抓行情，不自动写结论。"
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选复盘到期提醒与人工填写清单",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 总结",
        "",
        f"- 复盘日期数量：{report['摘要']['复盘日期数量']}",
        f"- 复盘任务数量：{report['摘要']['复盘任务数量']}",
        f"- 最近复盘日期：{report['摘要']['最近复盘日期']}（距离当前{report['摘要']['最近复盘距离当前天数']}天）",
        f"- 当前结论：{report['摘要']['当前结论']}",
        "",
        "## 到期清单",
        ""
    ]
    for group in report.get("按日期提醒清单", []):
        lines.append(f"### {group['复盘日期']}（{group['任务数量']}项）")
        for task in group.get("任务", []):
            lines.append(
                f"- {task['名称']}（{task['代码']}，{task['周期']}）：过热{task['短线过热等级']}，量能{task['量能持续等级']}，"
                f"主题{task['主题归类']}，待填字段{len(task['待填字段'])}个"
            )
        lines.append("")
    lines.extend([
        "## 后续联动",
        ""
    ])
    for item in report.get("后续联动", []):
        lines.append(f"- {item}")
    lines.extend([
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
    rule_path = root / "01配置" / "300只候选复盘到期提醒与人工填写清单规则.json"
    rule = load_json(rule_path)
    template_path = root / "03数据" / "107复盘结果填写" / "300只候选复盘结果填写模板_最新.json"
    review_path = root / "03数据" / "107复盘结果填写" / "300只候选复盘执行任务包_带人工复盘结果_最新.json"
    placeholder_path = root / "03数据" / "113复盘权重反校准占位账本" / "300只候选复盘权重反校准占位账本_最新.json"
    template = load_json(template_path)
    review = load_json(review_path)
    placeholder = load_json(placeholder_path)
    tasks = review.get("复盘执行任务", [])
    required = rule.get("人工必填字段", [])
    groups = build_due_groups(tasks, index_placeholder(placeholder), required)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "107复盘结果填写模板": str(template_path),
            "107复盘结果派生文件": str(review_path),
            "113复盘权重反校准占位账本": str(placeholder_path)
        },
        "107模板任务数量": template.get("任务数量", len(template.get("复盘结果填写模板", []))),
        "摘要": build_summary(groups),
        "按日期提醒清单": groups,
        "人工必填字段": required,
        "后续联动": rule.get("后续联动", []),
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选复盘到期提醒与人工填写清单_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只候选复盘到期提醒与人工填写清单_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"复盘日期数量": len(groups), "复盘任务数量": sum(group["任务数量"] for group in groups), "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
