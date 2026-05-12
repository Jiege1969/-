# -*- coding: utf-8 -*-
"""
名称：校验300只候选人工核验批量填报表.py
作用：校验人工核验批量填报CSV的列、任务ID、状态和通过条件；只校验不导入103。
触发方式：python 校验300只候选人工核验批量填报表.py [--csv 路径]
依赖：Python标准库；300只候选人工核验批量填报模板规则.json；119批量填报CSV。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读CSV并写校验报告；不写入核验结果；不修改103；不导入填报表；不联网；不下载正文；不刷新101/102；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建人工核验批量填报表校验脚本。
标识：stock-trial-pool-300-manual-verification-batch-form-check
"""

from __future__ import annotations

import argparse
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


def text(value: Any) -> str:
    return str(value or "").strip()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), list(reader)


def row_issues(row: dict[str, str], rule: dict[str, Any], valid_task_ids: set[str]) -> list[str]:
    issues: list[str] = []
    task_id = text(row.get("任务ID"))
    status = text(row.get("拟填写状态"))
    risk = text(row.get("是否发现新增重大风险"))
    support = text(row.get("是否支持进入精选推送草案"))
    if task_id not in valid_task_ids:
        issues.append("任务ID不在119模板中")
    if status not in set(rule.get("允许状态", [])):
        issues.append(f"拟填写状态非法：{status}")
    if risk not in set(rule.get("允许是否字段", [])):
        issues.append(f"是否发现新增重大风险非法：{risk}")
    if support not in set(rule.get("允许是否字段", [])):
        issues.append(f"是否支持进入精选推送草案非法：{support}")
    if status == "通过":
        missing = [field for field in rule.get("通过时必填列", []) if not text(row.get(field))]
        if missing:
            issues.append("通过状态缺失字段：" + "、".join(missing))
        if risk != "否":
            issues.append("通过状态下新增重大风险必须为否")
        if support != "是":
            issues.append("通过状态下支持进入精选推送草案必须为是")
    if status == "阻断" and support == "是":
        issues.append("阻断状态不应同时支持进入精选推送草案")
    return issues


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选人工核验批量填报模板规则.json"
    rule = load_json(rule_path)
    default_csv = root / rule["输出"]["数据目录"] / rule["输出"]["最新CSV"]
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=str(default_csv), help="待校验的人工核验批量填报CSV")
    args = parser.parse_args()
    csv_path = Path(args.csv)
    template_json = root / rule["输出"]["数据目录"] / rule["输出"]["最新JSON"]
    template = load_json(template_json)
    valid_task_ids = {text(row.get("任务ID")) for row in template.get("填报行", [])}
    headers, rows = read_csv(csv_path)
    missing_headers = [header for header in rule["模板列"] if header not in headers]
    extra_headers = [header for header in headers if header not in rule["模板列"]]
    details = []
    status_counter: Counter[str] = Counter()
    for index, row in enumerate(rows, start=2):
        status = text(row.get("拟填写状态"))
        status_counter[status or "未填写"] += 1
        issues = row_issues(row, rule, valid_task_ids)
        if issues:
            details.append({"行号": index, "任务ID": row.get("任务ID", ""), "问题": issues})
    completed = [row for row in rows if text(row.get("拟填写状态")) and text(row.get("拟填写状态")) != "待人工核验"]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "校验CSV": str(csv_path),
        "摘要": {
            "行数": len(rows),
            "模板任务数": len(valid_task_ids),
            "缺失列": missing_headers,
            "额外列": extra_headers,
            "状态统计": dict(status_counter),
            "已填写任务数量": len(completed),
            "问题数量": len(details),
            "是否可进入导入前人工确认": not missing_headers and not details and len(rows) == len(valid_task_ids)
        },
        "问题明细": details,
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"300只候选人工核验批量填报表校验报告_{stamp}.json"
    latest = output_dir / rule["输出"]["校验报告"]
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"行数": len(rows), "问题数量": len(details), "输出": str(latest)}, ensure_ascii=False))
    return 0 if not missing_headers and not details and len(rows) == len(valid_task_ids) else 1


if __name__ == "__main__":
    raise SystemExit(main())
