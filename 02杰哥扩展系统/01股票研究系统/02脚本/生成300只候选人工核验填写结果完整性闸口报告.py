# -*- coding: utf-8 -*-
"""
名称：生成300只候选人工核验填写结果完整性闸口报告.py
作用：检查103人工核验填写结果是否足以放行101/102；只检查不写结果、不刷新链路。
触发方式：python 生成300只候选人工核验填写结果完整性闸口报告.py
依赖：Python标准库；300只候选人工核验填写结果完整性闸口规则.json；103模板/派生任务；116优先级清单。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写117闸口报告；不写入核验结果；不修改103；不刷新101/102；不修改候选清单；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选人工核验填写结果完整性闸口报告脚本。
标识：stock-trial-pool-300-manual-verification-completeness-gate
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


def is_formal_source(item: dict[str, Any]) -> bool:
    source = text(item.get("来源级别"))
    return "官方" in source or "交易所" in source or "正式优先" in source


def required_missing(item: dict[str, Any]) -> list[str]:
    required = ["核验人", "核验时间", "材料标题", "材料发布日期", "是否发现新增重大风险", "是否支持进入精选推送草案"]
    return [field for field in required if not text(item.get(field))]


def task_quality(item: dict[str, Any]) -> dict[str, Any]:
    status = text(item.get("状态"))
    risk = text(item.get("是否发现新增重大风险"))
    support = text(item.get("是否支持进入精选推送草案"))
    missing = required_missing(item)
    formal = is_formal_source(item)
    usable = status == "通过" and formal and not missing and risk == "否" and support == "是"
    blocking = status == "阻断" or risk == "是" or support == "否"
    reasons = []
    if status != "通过":
        reasons.append(f"状态不是通过：{status or '空'}")
    if not formal:
        reasons.append("不是官方/交易所/正式优先来源")
    if missing:
        reasons.append("缺失字段：" + "、".join(missing))
    if risk and risk != "否":
        reasons.append(f"新增重大风险字段为：{risk}")
    if support and support != "是":
        reasons.append(f"支持进入精选字段为：{support}")
    return {
        "任务ID": item.get("任务ID"),
        "代码": item.get("代码"),
        "名称": item.get("名称"),
        "任务类型": item.get("任务类型"),
        "来源级别": item.get("来源级别"),
        "状态": status,
        "是否正式来源": formal,
        "缺失字段": missing,
        "是否可作为放行依据": usable,
        "是否形成阻断": blocking,
        "问题说明": reasons or ["可作为放行依据"]
    }


def candidate_gate(code: str, name: str, rows: list[dict[str, Any]], priority_rows: list[dict[str, Any]]) -> dict[str, Any]:
    usable = [row for row in rows if row["是否可作为放行依据"]]
    blockers = [row for row in rows if row["是否形成阻断"]]
    announcement_ok = any("公告正文" in text(row.get("任务类型")) for row in usable)
    finance_ok = any("财务报告" in text(row.get("任务类型")) for row in usable)
    priority_top = [row for row in priority_rows if str(row.get("代码", "")).lower() == code.lower() and row.get("全局排序", 999) <= 10]
    missing = []
    if not announcement_ok:
        missing.append("缺少公告正文官方/正式通过核验")
    if not finance_ok:
        missing.append("缺少财务报告官方/正式通过核验")
    if blockers:
        missing.append("存在阻断或重大风险任务")
    allow = not missing
    return {
        "代码": code,
        "名称": name,
        "任务数量": len(rows),
        "可作为放行依据数量": len(usable),
        "阻断任务数量": len(blockers),
        "第一批优先任务数量": len(priority_top),
        "公告正文是否满足": announcement_ok,
        "财务报告是否满足": finance_ok,
        "是否允许进入101/102放行刷新": allow,
        "阻断原因": missing,
        "下一步动作": "可运行108联动刷新前仍需人工确认" if allow else "按116优先级清单补齐103人工核验填写"
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选人工核验填写结果完整性闸口报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 是否允许刷新101/102放行：{report['闸口结论']['是否允许刷新101/102放行']}",
        f"- 可放行候选数量：{report['闸口结论']['可放行候选数量']}",
        f"- 阻断候选数量：{report['闸口结论']['阻断候选数量']}",
        f"- 当前结论：{report['闸口结论']['当前结论']}",
        "",
        "## 候选闸口",
        ""
    ]
    for row in report.get("候选闸口结果", []):
        lines.append(f"- {row['名称']}（{row['代码']}）：放行={row['是否允许进入101/102放行刷新']}；原因：{('；'.join(row['阻断原因']) or '满足')}")
    lines.extend(["", "## 放行条件", ""])
    for item in report.get("候选放行条件", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选人工核验填写结果完整性闸口规则.json"
    rule = load_json(rule_path)
    template_path = root / "03数据" / "103人工核验结果填写" / "300只候选人工核验结果填写模板_最新.json"
    applied_path = root / "03数据" / "103人工核验结果填写" / "300只候选公告财务行业事件正文核验任务_带人工填写结果_最新.json"
    priority_path = root / "03数据" / "116人工核验任务优先级清单" / "300只候选人工核验任务优先级清单_最新.json"
    template = load_json(template_path)
    applied = load_json(applied_path)
    priority = load_json(priority_path)
    items = applied.get("核验任务", template.get("填写区", []))
    quality_rows = [task_quality(item) for item in items]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    names: dict[str, str] = {}
    for row in quality_rows:
        code = str(row.get("代码", "")).lower()
        grouped[code].append(row)
        names[code] = text(row.get("名称"))
    priority_rows = priority.get("优先级清单", [])
    candidate_rows = [candidate_gate(code, names.get(code, ""), rows, priority_rows) for code, rows in grouped.items()]
    allowed = [row for row in candidate_rows if row["是否允许进入101/102放行刷新"]]
    status_counter = Counter(row.get("状态") or "未填写" for row in quality_rows)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "103人工核验结果填写模板": str(template_path),
            "103人工核验派生任务": str(applied_path),
            "116人工核验任务优先级清单": str(priority_path)
        },
        "任务质量统计": {
            "任务数量": len(quality_rows),
            "状态统计": dict(status_counter),
            "可作为放行依据数量": sum(1 for row in quality_rows if row["是否可作为放行依据"]),
            "阻断任务数量": sum(1 for row in quality_rows if row["是否形成阻断"])
        },
        "候选闸口结果": candidate_rows,
        "闸口结论": {
            "是否允许刷新101/102放行": len(allowed) == len(candidate_rows) and bool(candidate_rows),
            "可放行候选数量": len(allowed),
            "阻断候选数量": len(candidate_rows) - len(allowed),
            "当前结论": "人工核验填写尚不完整，禁止刷新101/102放行。" if len(allowed) != len(candidate_rows) else "人工核验填写满足最低放行条件，可进入108联动刷新前人工确认。"
        },
        "候选放行条件": rule.get("候选放行条件", []),
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选人工核验填写结果完整性闸口报告_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只候选人工核验填写结果完整性闸口报告_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"可放行候选数量": len(allowed), "阻断候选数量": len(candidate_rows) - len(allowed), "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
