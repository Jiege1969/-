# -*- coding: utf-8 -*-
"""
名称：受控导入300只候选人工核验批量填报到103.py
作用：将119批量填报表受控导入103；默认只预演，显式--execute和确认口令齐全才写103。
触发方式：python 受控导入300只候选人工核验批量填报到103.py [--execute --confirm 确认导入103人工核验结果]
依赖：Python标准库；300只候选人工核验批量受控导入103规则.json；119 CSV；121闸口；103模板。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：默认只读119/121/103并写122报告；默认不写入核验结果；默认不修改103；不应用103派生任务；不刷新101/102；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-05-01 创建人工核验批量受控导入103工具。
标识：stock-trial-pool-300-manual-verification-controlled-import-to-103
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
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


def filled(row: dict[str, str]) -> bool:
    fields = ["拟填写状态", "核验人", "核验时间", "材料标题", "材料发布日期", "是否发现新增重大风险", "是否支持进入精选推送草案", "备注"]
    return any(text(row.get(field)) for field in fields)


def collect_changes(rows: list[dict[str, str]], template: dict[str, Any], mapping: dict[str, str]) -> list[dict[str, Any]]:
    template_rows = {text(row.get("任务ID")): row for row in template.get("填写区", [])}
    changes: list[dict[str, Any]] = []
    for row in rows:
        if not filled(row):
            continue
        task_id = text(row.get("任务ID"))
        target = template_rows.get(task_id)
        if not target:
            continue
        field_changes = []
        for csv_field, target_field in mapping.items():
            new_value = text(row.get(csv_field))
            if csv_field == "拟填写状态" and not new_value:
                continue
            if csv_field != "拟填写状态" and not new_value:
                continue
            old_value = text(target.get(target_field))
            if old_value != new_value:
                field_changes.append({"字段": target_field, "原值": old_value, "新值": new_value})
        if field_changes:
            changes.append({
                "任务ID": task_id,
                "代码": row.get("代码"),
                "名称": row.get("名称"),
                "字段变更": field_changes
            })
    return changes


def apply_changes(template: dict[str, Any], changes: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {text(row.get("任务ID")): row for row in template.get("填写区", [])}
    for item in changes:
        row = by_id.get(text(item.get("任务ID")))
        if not row:
            continue
        for change in item.get("字段变更", []):
            row[change["字段"]] = change["新值"]
    template["最后修改时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    template["最后修改来源"] = "122人工核验批量受控导入103"
    template["最后修改任务数量"] = len(changes)
    return template


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选人工核验批量受控导入103报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 执行模式：{report['执行模式']}",
        f"- 121是否放行：{report['121是否放行']}",
        f"- 将变更任务数：{report['将变更任务数']}",
        f"- 是否实际写入103：{report['是否实际写入103']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 阻断原因",
        ""
    ]
    if report.get("阻断原因"):
        for item in report["阻断原因"]:
            lines.append(f"- {item}")
    else:
        lines.append("- 无阻断原因。")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="显式执行写入103；默认只预演")
    parser.add_argument("--confirm", default="", help="执行确认口令")
    args = parser.parse_args()

    root = module_root()
    rule_path = root / "01配置" / "300只候选人工核验批量受控导入103规则.json"
    rule = load_json(rule_path)
    csv_path = root / "03数据" / "119人工核验批量填报模板" / "300只候选人工核验批量填报模板_最新.csv"
    gate_path = root / "03数据" / "121人工核验批量导入执行闸口" / "300只候选人工核验批量导入执行闸口报告_最新.json"
    template_path = root / "03数据" / "103人工核验结果填写" / "300只候选人工核验结果填写模板_最新.json"
    rows = read_csv(csv_path)
    gate = load_json(gate_path)
    template = load_json(template_path)
    changes = collect_changes(rows, template, rule.get("可导入字段映射", {}))
    gate_allowed = gate.get("闸口结论", {}).get("是否允许进入人工确认导入103") is True
    reasons: list[str] = []
    if not gate_allowed:
        reasons.append("121闸口未放行")
    if args.execute and args.confirm != rule.get("执行确认口令"):
        reasons.append("执行确认口令不匹配")
    if args.execute and not changes:
        reasons.append("无可导入字段变更")
    actual_write = args.execute and gate_allowed and not reasons
    backup_path = ""
    if actual_write:
        backup_dir = root / "03数据" / "122人工核验批量受控导入103" / "103导入前备份"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"300只候选人工核验结果填写模板_导入前备份_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy2(template_path, backup)
        backup_path = str(backup)
        updated = apply_changes(template, changes)
        write_json(template_path, updated)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "119批量填报CSV": str(csv_path),
            "121执行闸口": str(gate_path),
            "103模板": str(template_path)
        },
        "执行模式": "执行写入" if args.execute else "默认预演",
        "121是否放行": gate_allowed,
        "将变更任务数": len(changes),
        "字段变更预览": changes,
        "阻断原因": reasons,
        "是否实际写入103": actual_write,
        "103导入前备份": backup_path,
        "当前结论": "已受控写入103。" if actual_write else "未写入103；仅生成受控导入预演报告。",
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选人工核验批量受控导入103报告_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新JSON"]
    output_md = output_dir / f"300只候选人工核验批量受控导入103报告_{stamp}.md"
    latest_md = output_dir / rule["输出"]["最新Markdown"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"执行模式": report["执行模式"], "是否实际写入103": actual_write, "将变更任务数": len(changes), "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
