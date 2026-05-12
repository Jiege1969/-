# -*- coding: utf-8 -*-
"""
名称：生成300只候选人工核验批量填报模板.py
作用：基于118录入辅助包生成可批量填写的人工核验CSV/JSON模板；不导入、不写103。
触发方式：python 生成300只候选人工核验批量填报模板.py
依赖：Python标准库；300只候选人工核验批量填报模板规则.json；118人工核验录入辅助包。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读118并写119模板；不写入核验结果；不修改103；不联网；不下载正文；不刷新101/102；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选人工核验批量填报模板脚本。
标识：stock-trial-pool-300-manual-verification-batch-form
"""

from __future__ import annotations

import csv
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


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def text(value: Any) -> str:
    return str(value or "").strip()


def build_row(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "全局排序": entry.get("全局排序"),
        "建议执行批次": entry.get("建议执行批次"),
        "任务ID": entry.get("任务ID"),
        "代码": entry.get("代码"),
        "名称": entry.get("名称"),
        "任务类型": entry.get("任务类型"),
        "入口名称": entry.get("入口名称"),
        "来源级别": entry.get("来源级别"),
        "URL": entry.get("URL"),
        "当前状态": entry.get("当前状态"),
        "拟填写状态": "",
        "核验人": "",
        "核验时间": "",
        "材料标题": "",
        "材料发布日期": "",
        "是否发现新增重大风险": "",
        "是否支持进入精选推送草案": "",
        "备注": ""
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选人工核验批量填报模板",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 任务数量：{report['摘要']['任务数量']}",
        f"- 第一批任务数量：{report['摘要']['第一批任务数量']}",
        f"- 当前填报状态：{report['摘要']['当前填报状态']}",
        "",
        "## 填写说明",
        "",
        "- 只填写人工填写列，不改任务ID、代码、名称、URL等参考列。",
        "- 拟填写状态只能填：待人工核验、通过、继续待核实、阻断。",
        "- 通过时必须填写核验人、核验时间、材料标题、材料发布日期，新增重大风险填否，支持进入精选推送草案填是。",
        "- 填完后先运行校验脚本，只校验不导入103。",
        "",
        "## 输出文件",
        "",
        f"- CSV模板：{report['输出文件']['CSV模板']}",
        f"- JSON模板：{report['输出文件']['JSON模板']}",
        "",
        "## 前10项",
        ""
    ]
    for row in report.get("填报行", [])[:10]:
        lines.append(f"- {row['全局排序']}. {row['名称']}（{row['代码']}）{row['任务类型']}：{row['入口名称']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选人工核验批量填报模板规则.json"
    rule = load_json(rule_path)
    helper_path = root / "03数据" / "118人工核验录入辅助包" / "300只候选人工核验录入辅助包_最新.json"
    helper = load_json(helper_path)
    headers = rule["模板列"]
    rows = [build_row(entry) for entry in helper.get("录入辅助清单", [])]
    batch_counter = Counter(text(row.get("建议执行批次")) for row in rows)
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = output_dir / rule["输出"]["最新JSON"]
    latest_csv = output_dir / rule["输出"]["最新CSV"]
    latest_md = output_dir / rule["输出"]["最新Markdown"]
    stamped_json = output_dir / f"300只候选人工核验批量填报模板_{stamp}.json"
    stamped_csv = output_dir / f"300只候选人工核验批量填报模板_{stamp}.csv"
    stamped_md = output_dir / f"300只候选人工核验批量填报模板_{stamp}.md"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "118人工核验录入辅助包": str(helper_path)
        },
        "摘要": {
            "任务数量": len(rows),
            "第一批任务数量": batch_counter.get("第一批：优先核验", 0),
            "批次统计": dict(batch_counter),
            "当前填报状态": "空白批量填报模板已生成，等待人工填写。"
        },
        "模板列": headers,
        "人工填写列": rule.get("人工填写列", []),
        "填报行": rows,
        "输出文件": {
            "CSV模板": str(latest_csv),
            "JSON模板": str(latest_json),
            "Markdown说明": str(latest_md)
        },
        "安全边界": rule.get("安全边界", {})
    }
    write_json(stamped_json, report)
    write_json(latest_json, report)
    write_csv(stamped_csv, headers, rows)
    write_csv(latest_csv, headers, rows)
    markdown = build_markdown(report)
    write_text(stamped_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"任务数量": len(rows), "CSV": str(latest_csv), "JSON": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
