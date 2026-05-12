# -*- coding: utf-8 -*-
"""
名称：生成300只候选权重建议生成闸口报告.py
作用：检查是否具备生成评分权重建议候选的条件；无真实复盘结果时必须阻断，不生成调参建议。
触发方式：python 生成300只候选权重建议生成闸口报告.py
依赖：Python标准库；300只候选权重建议生成闸口规则.json；107/113/114最新产物。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写115闸口报告；不生成正式权重变更；不写入评分规则；不修改候选清单；不写入复盘结论；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选权重建议生成闸口报告脚本。
标识：stock-trial-pool-300-weight-suggestion-gate
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


def text(value: Any) -> str:
    return str(value or "").strip()


def review_result_quality(task: dict[str, Any]) -> dict[str, Any]:
    manual = task.get("人工填写区", {})
    required = ["区间涨跌幅", "是否验证原候选依据", "是否兑现原风险点", "复盘结论"]
    filled = [field for field in required if text(manual.get(field))]
    missing = [field for field in required if field not in filled]
    return {
        "任务ID": task.get("任务ID"),
        "代码": task.get("代码"),
        "名称": task.get("名称"),
        "周期": task.get("周期"),
        "目标复盘日": task.get("目标复盘日"),
        "已填关键字段": filled,
        "缺失关键字段": missing,
        "是否具备权重建议输入资格": len(missing) == 0
    }


def build_candidate_suggestions(qualified: list[dict[str, Any]]) -> list[dict[str, Any]]:
    suggestions = []
    for item in qualified:
        suggestions.append({
            "任务ID": item.get("任务ID"),
            "代码": item.get("代码"),
            "名称": item.get("名称"),
            "建议类型": "待人工复核的权重建议候选",
            "建议内容": "已有关键复盘字段，可进入后续权重建议候选分析；本层不直接建议加减权重。",
            "是否可自动写入评分规则": False
        })
    return suggestions


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选权重建议生成闸口报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 是否允许生成权重建议候选：{report['闸口结论']['是否允许生成权重建议候选']}",
        f"- 权重建议候选数量：{report['闸口结论']['权重建议候选数量']}",
        f"- 阻断原因：{report['闸口结论']['阻断原因']}",
        "",
        "## 关键字段质量",
        ""
    ]
    for item in report.get("复盘关键字段质量", [])[:15]:
        lines.append(f"- {item['任务ID']}：缺失{len(item['缺失关键字段'])}项，资格：{item['是否具备权重建议输入资格']}")
    lines.extend(["", "## 准入条件", ""])
    for item in report.get("准入条件", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选权重建议生成闸口规则.json"
    rule = load_json(rule_path)
    review_path = root / "03数据" / "107复盘结果填写" / "300只候选复盘执行任务包_带人工复盘结果_最新.json"
    placeholder_path = root / "03数据" / "113复盘权重反校准占位账本" / "300只候选复盘权重反校准占位账本_最新.json"
    due_path = root / "03数据" / "114复盘到期提醒与人工填写清单" / "300只候选复盘到期提醒与人工填写清单_最新.json"
    review = load_json(review_path)
    placeholder = load_json(placeholder_path)
    due = load_json(due_path)
    tasks = review.get("复盘执行任务", [])
    quality = [review_result_quality(task) for task in tasks]
    qualified = [item for item in quality if item["是否具备权重建议输入资格"]]
    suggestions = build_candidate_suggestions(qualified)
    allowed = bool(suggestions)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "107复盘结果派生文件": str(review_path),
            "113复盘权重反校准占位账本": str(placeholder_path),
            "114复盘到期提醒与人工填写清单": str(due_path)
        },
        "输入摘要": {
            "复盘任务数量": len(tasks),
            "113是否允许当前改权重": placeholder.get("摘要", {}).get("是否允许当前改权重"),
            "114最近复盘日期": due.get("摘要", {}).get("最近复盘日期")
        },
        "复盘关键字段质量": quality,
        "闸口结论": {
            "是否允许生成权重建议候选": allowed,
            "权重建议候选数量": len(suggestions),
            "阻断原因": "" if allowed else "当前没有具备关键字段完整性的人工复盘结果，禁止生成权重建议候选。",
            "是否可自动写入评分规则": False
        },
        "权重建议候选": suggestions,
        "准入条件": rule.get("准入条件", []),
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选权重建议生成闸口报告_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只候选权重建议生成闸口报告_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否允许生成权重建议候选": allowed, "权重建议候选数量": len(suggestions), "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
