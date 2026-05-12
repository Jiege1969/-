# -*- coding: utf-8 -*-
"""
名称：生成300只候选公告财务行业事件正文核验任务.py
作用：基于推送前候选包和公告财务行业事件只读入口，生成逐只候选的人工正文核验任务清单。
触发方式：python 生成300只候选公告财务行业事件正文核验任务.py
依赖：Python标准库；300只候选公告财务行业事件正文核验任务规则.json；300只候选推送前候选包_最新.json；300只候选公告财务行业事件只读入口_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地候选包和只读入口并写入03数据；不联网抓取；不下载正文；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选公告财务行业事件正文核验任务脚本。
标识：stock-trial-pool-300-event-body-verification-task-generate
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


def find_entry(entry_package: dict[str, Any], code: str) -> dict[str, Any]:
    for item in entry_package.get("候选入口", []):
        if item.get("代码") == code:
            return item
    return {}


def task_priority(kind: str, level: str) -> str:
    if "公告" in kind and ("官方" in level or "交易所" in level):
        return "高"
    if "财务" in kind and ("官方" in level or "交易所" in level):
        return "高"
    if "正式优先" in level:
        return "高"
    return "中"


def build_tasks(candidate_package: dict[str, Any], entry_package: dict[str, Any]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for candidate in candidate_package.get("推送前候选", []):
        code = str(candidate.get("代码", ""))
        entry = find_entry(entry_package, code)
        task_groups = [
            ("公告正文核验", entry.get("公告入口", [])),
            ("财务报告核验", entry.get("财务入口", [])),
            ("行业事件线索核验", entry.get("行业事件入口", [])),
        ]
        task_no = 1
        for kind, sources in task_groups:
            for source in sources:
                level = str(source.get("级别", ""))
                tasks.append({
                    "任务ID": f"{code}-{task_no:02d}",
                    "代码": code,
                    "名称": candidate.get("名称", ""),
                    "任务类型": kind,
                    "优先级": task_priority(kind, level),
                    "入口名称": source.get("名称", ""),
                    "来源级别": level,
                    "URL": source.get("URL", ""),
                    "核验用途": source.get("用途", ""),
                    "入口限制": source.get("限制", ""),
                    "人工核验动作": [
                        "人工打开入口链接。",
                        "检索或确认股票代码、公司名称和最新公告/报告/事件。",
                        "记录标题、发布日期、来源入口和是否与候选逻辑相关。",
                        "官方入口材料优先；补充入口只作为线索。",
                        "将结论填写为：通过、继续待核实、阻断。"
                    ],
                    "核验结果": {
                        "状态": "待人工核验",
                        "核验人": "",
                        "核验时间": "",
                        "材料标题": "",
                        "材料发布日期": "",
                        "是否发现新增重大风险": "",
                        "是否支持进入精选推送草案": "",
                        "备注": ""
                    }
                })
                task_no += 1
    return tasks


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选公告财务行业事件正文核验任务",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 推送前候选数量：{report['推送前候选数量']}",
        f"- 核验任务数量：{report['核验任务数量']}",
        f"- 当前状态：{report['当前状态']}",
        f"- 总结：{report['结论']}",
        "",
        "## 核验要求",
        "",
    ]
    for item in report["核验要求"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 任务清单", ""])
    grouped: dict[str, list[dict[str, Any]]] = {}
    for task in report["核验任务"]:
        grouped.setdefault(f"{task['名称']}（{task['代码']}）", []).append(task)
    for stock, tasks in grouped.items():
        lines.extend([f"### {stock}", ""])
        for task in tasks:
            lines.extend([
                f"- 任务ID：{task['任务ID']}",
                f"  - 类型：{task['任务类型']}；优先级：{task['优先级']}",
                f"  - 入口：{task['入口名称']}（{task['来源级别']}）",
                f"  - URL：{task['URL']}",
                "  - 核验结果：待人工核验",
            ])
        lines.append("")
    lines.extend(["## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选公告财务行业事件正文核验任务规则.json"
    candidate_path = root / "03数据" / "96推送前候选包" / "300只候选推送前候选包_最新.json"
    entry_path = root / "03数据" / "95公告财务行业事件只读入口" / "300只候选公告财务行业事件只读入口_最新.json"
    gate_path = root / "03数据" / "99推送前人工闸口" / "300只候选推送前人工闸口复核单_最新.json"

    rule = load_json(rule_path)
    candidate_package = load_json(candidate_path)
    entry_package = load_json(entry_path)
    tasks = build_tasks(candidate_package, entry_package)
    candidate_count = len(candidate_package.get("推送前候选", []))
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "推送前候选包": str(candidate_path),
            "公告财务行业事件只读入口": str(entry_path),
            "推送前人工闸口": str(gate_path)
        },
        "推送前候选数量": candidate_count,
        "核验任务数量": len(tasks),
        "当前状态": "待人工核验，不抓正文，不真实发送",
        "核验要求": rule.get("核验要求", []),
        "核验任务": tasks,
        "结论": "已生成公告、财务、行业事件正文核验任务清单；当前只作为人工核验任务，不自动抓取正文，不写正式库，不进入真实发送。",
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选公告财务行业事件正文核验任务_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只候选公告财务行业事件正文核验任务_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"推送前候选数量": candidate_count, "核验任务数量": len(tasks), "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
