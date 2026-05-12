# -*- coding: utf-8 -*-
"""
名称：生成300只候选人工核验录入辅助包.py
作用：生成103人工核验录入辅助清单和命令模板；只辅助人工录入，不写结果。
触发方式：python 生成300只候选人工核验录入辅助包.py
依赖：Python标准库；300只候选人工核验录入辅助包规则.json；103模板；116优先级清单；117完整性闸口。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写118辅助包；不写入核验结果；不修改103；不联网；不下载正文；不刷新101/102；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选人工核验录入辅助包脚本。
标识：stock-trial-pool-300-manual-verification-entry-helper
"""

from __future__ import annotations

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


def text(value: Any) -> str:
    return str(value or "").strip()


def missing_fields(row: dict[str, Any], fields: list[str]) -> list[str]:
    return [field for field in fields if not text(row.get(field))]


def quote_arg(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def command_template(task_id: str) -> str:
    script = "D:\\杰哥智能化系统\\02杰哥扩展系统\\01股票研究系统\\02脚本\\记录单条人工核验结果.py"
    return (
        f"python {quote_arg(script)} --task-id {task_id} --status 通过 "
        "--person \"核验人\" --title \"人工确认的材料标题\" --date YYYY-MM-DD "
        "--major-risk 否 --support-draft 是 --note \"人工核验说明\""
    )


def build_entry(priority_row: dict[str, Any], template_by_id: dict[str, dict[str, Any]], required_fields: list[str]) -> dict[str, Any]:
    task_id = text(priority_row.get("任务ID"))
    template_row = template_by_id.get(task_id, {})
    merged = {**priority_row, **template_row}
    missing = missing_fields(merged, required_fields)
    return {
        "全局排序": priority_row.get("全局排序"),
        "建议执行批次": priority_row.get("建议执行批次"),
        "任务ID": task_id,
        "代码": merged.get("代码"),
        "名称": merged.get("名称"),
        "任务类型": merged.get("任务类型"),
        "入口名称": merged.get("入口名称"),
        "来源级别": merged.get("来源级别"),
        "URL": merged.get("URL"),
        "当前状态": text(merged.get("状态")) or "待人工核验",
        "待填写字段": missing,
        "填写判断": {
            "通过": "仅在人工确认官方/正式材料、字段完整、未发现新增重大风险且支持进入精选草案时使用。",
            "继续待核实": "材料未找到、标题或日期无法确认、来源不够正式或结论仍不确定时使用。",
            "阻断": "发现新增重大风险、正式入口否定关键信息或明确不支持进入精选草案时使用。",
            "待人工核验": "尚未打开入口核验前保持该状态。"
        },
        "放行相关": "公告正文核验和财务报告核验优先影响117闸口。",
        "单条录入命令模板": command_template(task_id)
    }


def build_candidate_summary(entries: list[dict[str, Any]], gate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    names: dict[str, str] = {}
    for row in entries:
        code = text(row.get("代码")).lower()
        grouped[code].append(row)
        names[code] = text(row.get("名称"))
    gate_by_code = {text(row.get("代码")).lower(): row for row in gate_rows}
    result = []
    for code, rows in grouped.items():
        first_batch = [row for row in rows if "第一批" in text(row.get("建议执行批次"))]
        official = [row for row in rows if any(key in text(row.get("来源级别")) for key in ["官方", "交易所", "正式"])]
        gate = gate_by_code.get(code, {})
        result.append({
            "代码": code,
            "名称": names.get(code, ""),
            "任务数量": len(rows),
            "第一批任务数量": len(first_batch),
            "官方或正式入口任务数量": len(official),
            "117是否允许放行": gate.get("是否允许进入101/102放行刷新", False),
            "117阻断原因": gate.get("阻断原因", []),
            "建议下一步": "先补公告正文和财务报告官方/正式入口核验，再跑117。"
        })
    return result


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选人工核验录入辅助包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 任务数量：{report['摘要']['任务数量']}",
        f"- 第一批任务数量：{report['摘要']['第一批任务数量']}",
        f"- 当前可放行候选数量：{report['摘要']['当前可放行候选数量']}",
        f"- 当前结论：{report['摘要']['当前结论']}",
        "",
        "## 前10项录入清单",
        ""
    ]
    for row in report.get("录入辅助清单", [])[:10]:
        lines.append(f"- {row['全局排序']}. {row['名称']}（{row['代码']}）{row['任务类型']}：{row['入口名称']}；状态={row['当前状态']}；待填={','.join(row['待填写字段'])}")
    lines.extend(["", "## 单条录入命令模板", ""])
    if report.get("录入辅助清单"):
        lines.append("```powershell")
        lines.append(report["录入辅助清单"][0]["单条录入命令模板"])
        lines.append("```")
    lines.extend(["", "## 候选汇总", ""])
    for row in report.get("候选汇总", []):
        lines.append(f"- {row['名称']}（{row['代码']}）：117放行={row['117是否允许放行']}；原因={';'.join(row['117阻断原因'])}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选人工核验录入辅助包规则.json"
    rule = load_json(rule_path)
    template_path = root / "03数据" / "103人工核验结果填写" / "300只候选人工核验结果填写模板_最新.json"
    priority_path = root / "03数据" / "116人工核验任务优先级清单" / "300只候选人工核验任务优先级清单_最新.json"
    gate_path = root / "03数据" / "117人工核验完整性闸口" / "300只候选人工核验填写结果完整性闸口报告_最新.json"
    template = load_json(template_path)
    priority = load_json(priority_path)
    gate = load_json(gate_path)
    template_rows = template.get("填写区", [])
    template_by_id = {text(row.get("任务ID")): row for row in template_rows}
    required_fields = rule.get("放行必填字段", rule.get("录入字段", []))
    priority_rows = sorted(priority.get("优先级清单", []), key=lambda row: row.get("全局排序", 9999))
    entries = [build_entry(row, template_by_id, required_fields) for row in priority_rows]
    batch_counter = Counter(text(row.get("建议执行批次")) for row in entries)
    status_counter = Counter(text(row.get("当前状态")) for row in entries)
    candidate_summary = build_candidate_summary(entries, gate.get("候选闸口结果", []))
    allowed_count = sum(1 for row in candidate_summary if row["117是否允许放行"])
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "103人工核验结果填写模板": str(template_path),
            "116人工核验任务优先级清单": str(priority_path),
            "117人工核验完整性闸口": str(gate_path)
        },
        "摘要": {
            "任务数量": len(entries),
            "第一批任务数量": batch_counter.get("第一批：优先核验", 0),
            "批次统计": dict(batch_counter),
            "状态统计": dict(status_counter),
            "当前可放行候选数量": allowed_count,
            "当前结论": "仅生成录入辅助材料；103尚需人工核验填写，不能直接放行。"
        },
        "放行前最低要求": rule.get("放行前最低要求", []),
        "候选汇总": candidate_summary,
        "录入辅助清单": entries,
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选人工核验录入辅助包_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只候选人工核验录入辅助包_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"任务数量": len(entries), "当前可放行候选数量": allowed_count, "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
