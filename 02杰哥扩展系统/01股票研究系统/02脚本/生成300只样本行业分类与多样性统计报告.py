# -*- coding: utf-8 -*-
"""
名称：生成300只样本行业分类与多样性统计报告.py
作用：统计300只试运行池、10只轻扫描候选和5只推送前候选的行业/板块分布与样本多样性；只统计不改池。
触发方式：python 生成300只样本行业分类与多样性统计报告.py
依赖：Python标准库；300只样本行业分类与多样性统计规则.json；91/92/96/111最新产物。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写112统计报告；不修改股票池；不修改候选清单；不修改评分规则；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只样本行业分类与多样性统计报告脚本。
标识：stock-trial-pool-300-industry-diversity-statistics
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


def normalize_industry(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else "未分类"


def distribution(items: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(normalize_industry(item.get("行业")) for item in items)
    total = len(items)
    return {
        "总数": total,
        "分类数量": len(counts),
        "分布": dict(counts.most_common()),
        "未分类数量": counts.get("未分类", 0),
        "未分类比例": round(counts.get("未分类", 0) / total, 4) if total else 0,
        "最高集中类别": counts.most_common(1)[0][0] if counts else "",
        "最高集中比例": round(counts.most_common(1)[0][1] / total, 4) if counts and total else 0
    }


def infer_theme(name: str, industry: str) -> str:
    mapping = [
        ("半导体", ["兆易", "海光", "豪威", "芯", "半导体", "集成"]),
        ("通信光模块", ["光迅", "新易盛", "中际旭创", "光通信", "光模块"]),
        ("医药CXO", ["药明", "康德", "医药", "生物"]),
        ("有色金属", ["中钨", "钨", "金", "铜", "铝", "锂"]),
        ("新能源车", ["比亚迪", "宁德", "电池", "新能源"]),
        ("高端制造", ["机器人", "工业", "制造", "设备", "伟创"]),
        ("化工材料", ["正丹", "材料", "化工"]),
        ("综合贸易", ["中拓", "贸易", "供应链"])
    ]
    text = f"{name}{industry}"
    for theme, keywords in mapping:
        if any(keyword in text for keyword in keywords):
            return theme
    if industry and industry not in ("未分类", "主板", "创业板", "科创板"):
        return industry
    return "待补充行业分类"


def theme_distribution(items: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for item in items:
        theme = infer_theme(str(item.get("名称", "")), normalize_industry(item.get("行业")))
        rows.append({"代码": item.get("代码"), "名称": item.get("名称"), "原行业字段": normalize_industry(item.get("行业")), "主题归类": theme})
    counts = Counter(row["主题归类"] for row in rows)
    total = len(rows)
    return {
        "明细": rows,
        "主题数量": len(counts),
        "主题分布": dict(counts.most_common()),
        "最高集中主题": counts.most_common(1)[0][0] if counts else "",
        "最高集中比例": round(counts.most_common(1)[0][1] / total, 4) if counts and total else 0
    }


def build_suggestions(pool_dist: dict[str, Any], candidate_theme: dict[str, Any], hot_report: dict[str, Any]) -> list[str]:
    suggestions = []
    if pool_dist.get("未分类比例", 0) > 0.2:
        suggestions.append("300只试运行池行业字段未分类比例偏高，扩容到800-1000只前应补充更稳定的行业/主题标签来源。")
    if candidate_theme.get("最高集中比例", 0) >= 0.4:
        suggestions.append("5只推送前候选主题集中度偏高，后续精选推送应增加跨行业分散检查。")
    if hot_report.get("摘要", {}).get("短线过热中高候选"):
        suggestions.append("候选热度较高时，行业分散不能替代事件核验和复盘验证，仍需等待103和107结果。")
    suggestions.append("当前只生成多样性统计，不改变300只试运行池、10只轻扫描候选或5只推送前候选。")
    return suggestions


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只样本行业分类与多样性统计报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 总结",
        "",
        f"- 300只试运行池未分类比例：{report['统计摘要']['300只试运行池']['未分类比例']}",
        f"- 10只轻扫描候选未分类比例：{report['统计摘要']['10只轻扫描候选']['未分类比例']}",
        f"- 5只推送前候选主题数量：{report['推送前候选主题统计']['主题数量']}",
        f"- 5只推送前候选最高集中主题：{report['推送前候选主题统计']['最高集中主题']}（比例{report['推送前候选主题统计']['最高集中比例']}）",
        "",
        "## 推送前候选主题",
        ""
    ]
    for row in report["推送前候选主题统计"]["明细"]:
        lines.append(f"- {row['名称']}（{row['代码']}）：{row['主题归类']}，原行业字段：{row['原行业字段']}")
    lines.extend(["", "## 扩容建议", ""])
    for item in report.get("扩容补齐建议", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只样本行业分类与多样性统计规则.json"
    rule = load_json(rule_path)
    pool_path = root / "03数据" / "91试运行池" / "300只试运行池_行情补齐_最新.json"
    scan_path = root / "03数据" / "92盘后轻扫描" / "300只试运行池盘后轻扫描_最新.json"
    package_path = root / "03数据" / "96推送前候选包" / "300只候选推送前候选包_最新.json"
    hot_path = root / "03数据" / "111过热与量能持续性诊断" / "300只候选过热与量能持续性诊断报告_最新.json"
    pool = load_json(pool_path).get("股票池", [])
    scan = load_json(scan_path).get("候选清单", [])
    candidates = load_json(package_path).get("推送前候选", [])
    hot_report = load_json(hot_path)
    pool_dist = distribution(pool)
    scan_dist = distribution(scan)
    candidate_dist = distribution(candidates)
    candidate_theme = theme_distribution(candidates)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "91试运行池行情补齐": str(pool_path),
            "92盘后轻扫描": str(scan_path),
            "96推送前候选包": str(package_path),
            "111过热与量能持续性诊断": str(hot_path)
        },
        "统计摘要": {
            "300只试运行池": pool_dist,
            "10只轻扫描候选": scan_dist,
            "5只推送前候选": candidate_dist
        },
        "推送前候选主题统计": candidate_theme,
        "扩容补齐建议": build_suggestions(pool_dist, candidate_theme, hot_report),
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只样本行业分类与多样性统计报告_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只样本行业分类与多样性统计报告_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"股票池数量": len(pool), "推送前候选数量": len(candidates), "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
