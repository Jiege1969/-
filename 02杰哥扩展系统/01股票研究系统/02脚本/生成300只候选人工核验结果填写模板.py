# -*- coding: utf-8 -*-
"""
名称：生成300只候选人工核验结果填写模板.py
作用：基于100事件正文核验任务，生成可人工填写的核验结果模板和填写说明。
触发方式：python 生成300只候选人工核验结果填写模板.py
依赖：Python标准库；300只候选人工核验结果填写规则.json；300只候选公告财务行业事件正文核验任务_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取100事件正文核验任务并写入103模板；不覆盖100原始核验任务；不联网抓取；不下载正文；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选人工核验结果填写模板脚本。
标识：stock-trial-pool-300-human-verification-template-generate
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


def build_template_rows(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in tasks:
        result = task.get("核验结果", {})
        rows.append({
            "任务ID": task.get("任务ID", ""),
            "代码": task.get("代码", ""),
            "名称": task.get("名称", ""),
            "任务类型": task.get("任务类型", ""),
            "优先级": task.get("优先级", ""),
            "入口名称": task.get("入口名称", ""),
            "来源级别": task.get("来源级别", ""),
            "URL": task.get("URL", ""),
            "状态": result.get("状态", "待人工核验") or "待人工核验",
            "核验人": result.get("核验人", ""),
            "核验时间": result.get("核验时间", ""),
            "材料标题": result.get("材料标题", ""),
            "材料发布日期": result.get("材料发布日期", ""),
            "是否发现新增重大风险": result.get("是否发现新增重大风险", ""),
            "是否支持进入精选推送草案": result.get("是否支持进入精选推送草案", ""),
            "备注": result.get("备注", "")
        })
    return rows


def build_markdown(template: dict[str, Any]) -> str:
    lines = [
        "# 300只候选人工核验结果填写模板",
        "",
        f"生成时间：{template['生成时间']}",
        "",
        "## 使用方式",
        "",
        "1. 打开同目录 JSON 模板。",
        "2. 只填写 `填写区` 中每条任务的状态、核验人、核验时间、材料标题、材料发布日期、是否发现新增重大风险、是否支持进入精选推送草案、备注。",
        "3. 状态只能填写：待人工核验、通过、继续待核实、阻断。",
        "4. 填完后运行 `应用300只候选人工核验结果填写模板.py`。",
        "5. 应用脚本只生成103派生任务文件，不覆盖100原始核验任务。",
        "",
        "## 当前任务概览",
        "",
        f"- 任务数量：{template['任务数量']}",
        f"- 允许状态：{'、'.join(template['允许状态'])}",
        "",
        "## 待填写任务",
        "",
    ]
    for row in template["填写区"]:
        lines.extend([
            f"### {row['任务ID']} {row['名称']} {row['任务类型']}",
            "",
            f"- 入口：{row['入口名称']}（{row['来源级别']}）",
            f"- URL：{row['URL']}",
            f"- 状态：{row['状态']}",
            "- 核验人：",
            "- 核验时间：",
            "- 材料标题：",
            "- 材料发布日期：",
            "- 是否发现新增重大风险：",
            "- 是否支持进入精选推送草案：",
            "- 备注：",
            "",
        ])
    lines.extend(["## 安全边界", ""])
    for key, value in template["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选人工核验结果填写规则.json"
    task_path = root / "03数据" / "100事件正文核验任务" / "300只候选公告财务行业事件正文核验任务_最新.json"
    rule = load_json(rule_path)
    task_book = load_json(task_path)
    rows = build_template_rows(task_book.get("核验任务", []))
    template = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "来源任务文件": str(task_path),
        "任务数量": len(rows),
        "允许状态": rule.get("允许状态", []),
        "填写说明": rule.get("填写说明", {}),
        "填写区": rows,
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选人工核验结果填写模板_{stamp}.json"
    latest_json = output_dir / rule["输出"]["模板最新文件"]
    output_md = output_dir / f"300只候选人工核验结果填写模板_{stamp}.md"
    latest_md = output_dir / rule["输出"]["模板说明文件"]
    write_json(output_json, template)
    write_json(latest_json, template)
    markdown = build_markdown(template)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"任务数量": len(rows), "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
