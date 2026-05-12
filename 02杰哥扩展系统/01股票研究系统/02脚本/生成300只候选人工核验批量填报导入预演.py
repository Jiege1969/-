# -*- coding: utf-8 -*-
"""
名称：生成300只候选人工核验批量填报导入预演.py
作用：预演119批量填报CSV导入103时的字段变更；只生成预览，不修改103。
触发方式：python 生成300只候选人工核验批量填报导入预演.py
依赖：Python标准库；300只候选人工核验批量填报导入预演规则.json；119 CSV；103模板。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读119和103并写120预演报告；不写入核验结果；不修改103；不导入填报表；不应用103派生任务；不联网；不下载正文；不刷新101/102；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选人工核验批量填报导入预演脚本。
标识：stock-trial-pool-300-manual-verification-batch-import-preview
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def text(value: Any) -> str:
    return str(value or "").strip()


def is_filled(row: dict[str, str]) -> bool:
    fields = ["拟填写状态", "核验人", "核验时间", "材料标题", "材料发布日期", "是否发现新增重大风险", "是否支持进入精选推送草案", "备注"]
    return any(text(row.get(field)) for field in fields)


def row_issues(row: dict[str, str], rule: dict[str, Any], valid_task_ids: set[str]) -> list[str]:
    issues: list[str] = []
    task_id = text(row.get("任务ID"))
    status = text(row.get("拟填写状态"))
    risk = text(row.get("是否发现新增重大风险"))
    support = text(row.get("是否支持进入精选推送草案"))
    if task_id not in valid_task_ids:
        issues.append("任务ID不在103模板中")
    if is_filled(row) and status not in set(rule.get("允许状态", [])):
        issues.append(f"拟填写状态非法或为空：{status or '空'}")
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


def build_changes(row: dict[str, str], template_row: dict[str, Any], mapping: dict[str, str]) -> list[dict[str, Any]]:
    changes = []
    for csv_field, target_field in mapping.items():
        new_value = text(row.get(csv_field))
        if csv_field == "拟填写状态" and not new_value:
            continue
        if csv_field != "拟填写状态" and not new_value:
            continue
        old_value = text(template_row.get(target_field))
        if old_value != new_value:
            changes.append({
                "字段": target_field,
                "原值": old_value,
                "新值": new_value
            })
    return changes


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选人工核验批量填报导入预演",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- CSV行数：{report['摘要']['CSV行数']}",
        f"- 已填写行数：{report['摘要']['已填写行数']}",
        f"- 将产生变更的任务数：{report['摘要']['将产生变更的任务数']}",
        f"- 问题数量：{report['摘要']['问题数量']}",
        f"- 是否可进入导入前人工确认：{report['摘要']['是否可进入导入前人工确认']}",
        f"- 当前结论：{report['摘要']['当前结论']}",
        "",
        "## 变更预览",
        ""
    ]
    previews = report.get("变更预览", [])
    if previews:
        for row in previews[:20]:
            lines.append(f"- {row['任务ID']} {row['名称']}：{len(row['字段变更'])}项字段变更")
    else:
        lines.append("- 当前没有任何待导入变更。")
    lines.extend(["", "## 问题明细", ""])
    if report.get("问题明细"):
        for row in report["问题明细"][:20]:
            lines.append(f"- 行{row['行号']} {row['任务ID']}：{';'.join(row['问题'])}")
    else:
        lines.append("- 未发现格式问题。")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选人工核验批量填报导入预演规则.json"
    rule = load_json(rule_path)
    csv_path = root / "03数据" / "119人工核验批量填报模板" / "300只候选人工核验批量填报模板_最新.csv"
    template_path = root / "03数据" / "103人工核验结果填写" / "300只候选人工核验结果填写模板_最新.json"
    rows = read_csv(csv_path)
    template = load_json(template_path)
    template_rows = {text(row.get("任务ID")): row for row in template.get("填写区", [])}
    status_counter: Counter[str] = Counter()
    previews = []
    issues = []
    filled_count = 0
    for index, row in enumerate(rows, start=2):
        status = text(row.get("拟填写状态")) or "未填写"
        status_counter[status] += 1
        task_id = text(row.get("任务ID"))
        filled = is_filled(row)
        if filled:
            filled_count += 1
        current_issues = row_issues(row, rule, set(template_rows.keys()))
        if current_issues:
            issues.append({"行号": index, "任务ID": task_id, "问题": current_issues})
            continue
        if not filled:
            continue
        target = template_rows.get(task_id, {})
        changes = build_changes(row, target, rule.get("可导入字段映射", {}))
        if changes:
            previews.append({
                "行号": index,
                "任务ID": task_id,
                "代码": row.get("代码"),
                "名称": row.get("名称"),
                "任务类型": row.get("任务类型"),
                "字段变更": changes
            })
    can_confirm = filled_count > 0 and not issues and bool(previews)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "119批量填报CSV": str(csv_path),
            "103人工核验结果填写模板": str(template_path)
        },
        "摘要": {
            "CSV行数": len(rows),
            "103任务数": len(template_rows),
            "已填写行数": filled_count,
            "状态统计": dict(status_counter),
            "将产生变更的任务数": len(previews),
            "问题数量": len(issues),
            "是否可进入导入前人工确认": can_confirm,
            "当前结论": "当前填报表为空，尚无可导入变更。" if filled_count == 0 else ("可进入导入前人工确认，但本脚本不导入。" if can_confirm else "存在问题或无有效变更，禁止导入。")
        },
        "变更预览": previews,
        "问题明细": issues,
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选人工核验批量填报导入预演_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新JSON"]
    output_md = output_dir / f"300只候选人工核验批量填报导入预演_{stamp}.md"
    latest_md = output_dir / rule["输出"]["最新Markdown"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"已填写行数": filled_count, "将产生变更的任务数": len(previews), "问题数量": len(issues), "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
