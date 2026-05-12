# -*- coding: utf-8 -*-
"""
名称：应用300只候选人工核验结果填写模板.py
作用：读取103人工填写模板，将填写结果应用到100事件正文核验任务副本，生成带人工填写结果的103派生任务文件。
触发方式：python 应用300只候选人工核验结果填写模板.py
依赖：Python标准库；300只候选人工核验结果填写规则.json；300只候选人工核验结果填写模板_最新.json；300只候选公告财务行业事件正文核验任务_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成103派生任务文件；不覆盖100原始核验任务；不覆盖101回填包；不联网抓取；不下载正文；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选人工核验结果填写模板应用脚本。
标识：stock-trial-pool-300-human-verification-template-apply
"""

from __future__ import annotations

import copy
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


def normalize_bool_text(value: Any) -> str:
    text = str(value or "").strip()
    if text in {"true", "True", "1", "是", "有", "发现"}:
        return "是"
    if text in {"false", "False", "0", "否", "无", "未发现"}:
        return "否"
    return text


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选人工核验结果应用报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 任务数量：{report['任务数量']}",
        f"- 已应用任务数量：{report['已应用任务数量']}",
        f"- 状态统计：{json.dumps(report['状态统计'], ensure_ascii=False)}",
        f"- 是否覆盖100原始核验任务：{report['是否覆盖100原始核验任务']}",
        f"- 总结：{report['结论']}",
        "",
        "## 输出",
        "",
        f"- 派生任务文件：{report['输出文件']}",
        "",
        "## 安全边界",
        "",
    ]
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选人工核验结果填写规则.json"
    rule = load_json(rule_path)
    output_dir = root / rule["输出"]["数据目录"]
    template_path = output_dir / rule["输出"]["模板最新文件"]
    original_task_path = root / "03数据" / "100事件正文核验任务" / "300只候选公告财务行业事件正文核验任务_最新.json"

    template = load_json(template_path)
    task_book = load_json(original_task_path)
    allowed = set(rule.get("允许状态", []))
    rows = {str(row.get("任务ID", "")): row for row in template.get("填写区", [])}
    derived = copy.deepcopy(task_book)
    applied = 0
    status_counter: Counter[str] = Counter()
    invalid: list[dict[str, Any]] = []
    for task in derived.get("核验任务", []):
        task_id = str(task.get("任务ID", ""))
        row = rows.get(task_id)
        if not row:
            continue
        status = str(row.get("状态", "待人工核验") or "待人工核验").strip()
        if status not in allowed:
            invalid.append({"任务ID": task_id, "状态": status})
            status = "待人工核验"
        task["核验结果"] = {
            "状态": status,
            "核验人": row.get("核验人", ""),
            "核验时间": row.get("核验时间", ""),
            "材料标题": row.get("材料标题", ""),
            "材料发布日期": row.get("材料发布日期", ""),
            "是否发现新增重大风险": normalize_bool_text(row.get("是否发现新增重大风险", "")),
            "是否支持进入精选推送草案": normalize_bool_text(row.get("是否支持进入精选推送草案", "")),
            "备注": row.get("备注", "")
        }
        applied += 1
        status_counter[status] += 1
    derived["生成时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    derived["派生来源"] = "103人工核验结果填写模板"
    derived["是否覆盖100原始核验任务"] = False
    derived["人工填写应用统计"] = {
        "已应用任务数量": applied,
        "状态统计": dict(status_counter),
        "非法状态数量": len(invalid),
        "非法状态明细": invalid
    }

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选公告财务行业事件正文核验任务_带人工填写结果_{stamp}.json"
    latest_json = output_dir / rule["输出"]["应用结果文件"]
    write_json(output_json, derived)
    write_json(latest_json, derived)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "模板文件": str(template_path),
        "原始任务文件": str(original_task_path),
        "输出文件": str(latest_json),
        "任务数量": len(derived.get("核验任务", [])),
        "已应用任务数量": applied,
        "状态统计": dict(status_counter),
        "非法状态数量": len(invalid),
        "非法状态明细": invalid,
        "是否覆盖100原始核验任务": False,
        "结论": "已生成带人工填写结果的103派生任务文件；后续101回填包会优先读取该派生文件。",
        "安全边界": rule.get("安全边界", {})
    }
    report_json = output_dir / f"300只候选人工核验结果应用报告_{stamp}.json"
    latest_report_json = output_dir / "300只候选人工核验结果应用报告_最新.json"
    report_md = output_dir / f"300只候选人工核验结果应用报告_{stamp}.md"
    latest_report_md = output_dir / rule["输出"]["应用报告文件"]
    write_json(report_json, report)
    write_json(latest_report_json, report)
    markdown = build_markdown(report)
    write_text(report_md, markdown)
    write_text(latest_report_md, markdown)
    print(json.dumps({"已应用任务数量": applied, "非法状态数量": len(invalid), "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if not invalid else 1


if __name__ == "__main__":
    raise SystemExit(main())
