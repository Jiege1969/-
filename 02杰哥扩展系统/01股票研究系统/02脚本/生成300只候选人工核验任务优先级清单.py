# -*- coding: utf-8 -*-
"""
名称：生成300只候选人工核验任务优先级清单.py
作用：对30个公告、财务、行业事件正文核验任务进行人工执行优先级排序；只排序，不联网、不下载、不写核验结果。
触发方式：python 生成300只候选人工核验任务优先级清单.py
依赖：Python标准库；300只候选人工核验任务优先级清单规则.json；100/103/96/111/112最新产物。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写116优先级清单；不执行人工核验；不联网打开入口；不下载正文；不写入核验结果；不修改候选清单；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选人工核验任务优先级清单脚本。
标识：stock-trial-pool-300-manual-verification-priority-list
"""

from __future__ import annotations

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


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", "-", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def index_by_code(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("代码", "")).lower(): item for item in items if item.get("代码")}


def index_template(template: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("任务ID", "")): item
        for item in template.get("填写区", [])
        if item.get("任务ID")
    }


def theme_map(diversity: dict[str, Any]) -> dict[str, str]:
    return {
        str(item.get("代码", "")).lower(): str(item.get("主题归类", "待补充行业分类"))
        for item in diversity.get("推送前候选主题统计", {}).get("明细", [])
        if item.get("代码")
    }


def source_score(source: str) -> tuple[int, str]:
    if "官方/交易所" in source or "交易所指定" in source:
        return 35, "官方/交易所指定入口优先"
    if "官方入口" in source:
        return 32, "官方入口优先"
    if "正式优先" in source:
        return 28, "正式优先入口"
    if "公开补充" in source:
        return 8, "公开补充入口靠后"
    return 12, "来源级别一般"


def task_type_score(task_type: str) -> tuple[int, str]:
    if "公告正文" in task_type:
        return 20, "公告正文核验优先"
    if "财务报告" in task_type:
        return 18, "财务报告核验优先"
    if "行业事件" in task_type:
        return 14, "行业事件线索核验"
    return 8, "一般核验任务"


def manual_priority_score(priority: str) -> int:
    return {"高": 12, "中": 6, "低": 2}.get(priority, 0)


def risk_score(hot: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    if hot.get("短线过热等级") == "高":
        score += 12
        reasons.append("短线过热高，需优先排查事件风险")
    elif hot.get("短线过热等级") == "中":
        score += 6
        reasons.append("短线过热中，保持风险核验")
    if hot.get("量能持续等级") == "弱":
        score += 8
        reasons.append("量能持续性弱，需优先核验支撑因素")
    elif hot.get("量能持续等级") == "一般":
        score += 4
        reasons.append("量能持续性一般，需观察")
    return score, reasons


def build_row(task: dict[str, Any], candidate: dict[str, Any], hot: dict[str, Any], theme: str, template_item: dict[str, Any]) -> dict[str, Any]:
    source_points, source_reason = source_score(str(task.get("来源级别", "")))
    type_points, type_reason = task_type_score(str(task.get("任务类型", "")))
    risk_points, risk_reasons = risk_score(hot)
    score_points = round(as_float(candidate.get("推送前评分")) / 10, 4)
    priority_points = manual_priority_score(str(task.get("优先级", "")))
    theme_points = 5 if theme == "半导体" else 0
    total = round(source_points + type_points + risk_points + score_points + priority_points + theme_points, 4)
    status = template_item.get("状态", task.get("核验结果", {}).get("状态", "待人工核验"))
    return {
        "任务ID": task.get("任务ID"),
        "代码": task.get("代码"),
        "名称": task.get("名称"),
        "任务类型": task.get("任务类型"),
        "入口名称": task.get("入口名称"),
        "来源级别": task.get("来源级别"),
        "原优先级": task.get("优先级"),
        "人工核验状态": status,
        "候选推送前评分": candidate.get("推送前评分"),
        "短线过热等级": hot.get("短线过热等级"),
        "量能持续等级": hot.get("量能持续等级"),
        "主题归类": theme,
        "优先级分": total,
        "排序依据": [source_reason, type_reason, f"推送前评分折算 +{score_points}", f"原优先级{task.get('优先级')} +{priority_points}"] + risk_reasons + (["主题集中，优先完成官方核验 +5"] if theme == "半导体" else []),
        "建议执行批次": "",
        "URL": task.get("URL"),
        "执行边界": [
            "只供人工打开入口核验，不由脚本联网。",
            "核验结果仍需写入103模板或单条录入脚本。",
            "未完成官方/正式材料核验前，不进入精选推送。"
        ]
    }


def assign_batches(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_rows = sorted(rows, key=lambda item: item["优先级分"], reverse=True)
    for index, row in enumerate(sorted_rows, start=1):
        row["全局排序"] = index
        if index <= 10:
            row["建议执行批次"] = "第一批：优先核验"
        elif index <= 20:
            row["建议执行批次"] = "第二批：随后核验"
        else:
            row["建议执行批次"] = "第三批：补充线索核验"
    return sorted_rows


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "任务数量": len(rows),
        "待人工核验数量": sum(1 for row in rows if row.get("人工核验状态") == "待人工核验"),
        "批次统计": dict(Counter(row.get("建议执行批次") for row in rows)),
        "类型统计": dict(Counter(row.get("任务类型") for row in rows)),
        "来源统计": dict(Counter(row.get("来源级别") for row in rows)),
        "当前结论": "人工核验优先级清单已生成；本层只排序，不打开网页、不下载正文、不写核验结果。"
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选人工核验任务优先级清单",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 总结",
        "",
        f"- 任务数量：{report['摘要']['任务数量']}",
        f"- 待人工核验数量：{report['摘要']['待人工核验数量']}",
        f"- 当前结论：{report['摘要']['当前结论']}",
        "",
        "## 第一批优先核验",
        ""
    ]
    for row in report.get("优先级清单", [])[:10]:
        lines.append(
            f"- {row['全局排序']}. {row['名称']}（{row['代码']}）{row['任务类型']} / {row['入口名称']}："
            f"优先级分{row['优先级分']}，{row['来源级别']}，过热{row['短线过热等级']}，量能{row['量能持续等级']}"
        )
    lines.extend(["", "## 执行边界", ""])
    lines.extend([
        "- 本清单不打开网页，不下载正文。",
        "- 人工核验结果必须写入103模板或单条录入脚本。",
        "- 未核验前不得进入精选推送和真实发送。"
    ])
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选人工核验任务优先级清单规则.json"
    rule = load_json(rule_path)
    task_path = root / "03数据" / "100事件正文核验任务" / "300只候选公告财务行业事件正文核验任务_最新.json"
    template_path = root / "03数据" / "103人工核验结果填写" / "300只候选人工核验结果填写模板_最新.json"
    candidate_path = root / "03数据" / "96推送前候选包" / "300只候选推送前候选包_最新.json"
    hot_path = root / "03数据" / "111过热与量能持续性诊断" / "300只候选过热与量能持续性诊断报告_最新.json"
    diversity_path = root / "03数据" / "112行业分类与样本多样性统计" / "300只样本行业分类与多样性统计报告_最新.json"
    tasks = load_json(task_path).get("核验任务", [])
    template_map = index_template(load_json(template_path))
    candidate_map = index_by_code(load_json(candidate_path).get("推送前候选", []))
    hot_map = index_by_code(load_json(hot_path).get("候选诊断", []))
    themes = theme_map(load_json(diversity_path))
    rows = []
    for task in tasks:
        code = str(task.get("代码", "")).lower()
        rows.append(build_row(task, candidate_map.get(code, {}), hot_map.get(code, {}), themes.get(code, "待补充行业分类"), template_map.get(str(task.get("任务ID")), {})))
    sorted_rows = assign_batches(rows)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "100事件正文核验任务": str(task_path),
            "103人工核验结果填写模板": str(template_path),
            "96推送前候选包": str(candidate_path),
            "111过热与量能持续性诊断": str(hot_path),
            "112行业分类与样本多样性统计": str(diversity_path)
        },
        "摘要": build_summary(sorted_rows),
        "排序原则": rule.get("排序原则", []),
        "优先级清单": sorted_rows,
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选人工核验任务优先级清单_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只候选人工核验任务优先级清单_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"任务数量": len(sorted_rows), "第一批数量": sum(1 for row in sorted_rows if row["建议执行批次"].startswith("第一批")), "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
