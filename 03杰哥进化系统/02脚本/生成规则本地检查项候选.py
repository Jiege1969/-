# -*- coding: utf-8 -*-
"""
名称：生成规则本地检查项候选.py
作用：把规则自动评审中的高价值规则转化为03进化系统本地检查项候选，供后续验收脚本和施工前检查读取。
触发方式：python 生成规则本地检查项候选.py
依赖：Python标准库；规则自动评审与去重评分报告_最新.json。
所属系统：03杰哥进化系统
安全边界：只写03进化系统本地候选检查项；不修改其他系统业务代码，不修改总管进度口径，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建规则本地检查项候选生成脚本。
标识：evolution-local-rule-check-candidates-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def candidate_for(review: dict[str, Any]) -> dict[str, Any]:
    category = review.get("规则分类", "")
    hard_boundary = bool(review.get("高风险真实动作")) or "硬阻断" in str(review.get("建议动作", ""))
    if hard_boundary:
        check_type = "硬边界检查"
        default_action = "只生成准入、回滚、验收和风险提示，不自动真实执行"
    elif "闸口" in category or "回滚" in category:
        check_type = "风险分级检查"
        default_action = "低风险本地施工继续，高风险真实动作进入硬边界"
    else:
        check_type = "施工前检查"
        default_action = "作为低风险本地检查项自动执行"
    return {
        "检查项ID": f"LRC-{review.get('规则ID', '').replace('EVR-', '')}",
        "来源规则ID": review.get("规则ID", ""),
        "检查项名称": category,
        "检查类型": check_type,
        "价值分": review.get("价值分", 0),
        "重复等级": review.get("重复等级", ""),
        "检查目标": review.get("下次施工约束", ""),
        "默认动作": default_action,
        "自动执行": not hard_boundary,
        "硬边界保留": hard_boundary,
        "失败处理": "记录阻断或纠偏建议；低风险项补齐后继续施工，高风险项不得自动真实执行。",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 规则本地检查项候选",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 候选数量：{report['候选数量']}",
        f"- 自动执行候选：{report['自动执行候选数量']}",
        f"- 硬边界候选：{report['硬边界候选数量']}",
        "",
        "## 候选检查项",
        "",
    ]
    for item in report["检查项候选"]:
        lines.extend(
            [
                f"### {item['检查项ID']} {item['检查项名称']}",
                f"- 类型：{item['检查类型']}",
                f"- 目标：{item['检查目标']}",
                f"- 默认动作：{item['默认动作']}",
                f"- 自动执行：{item['自动执行']}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    root = system_root()
    review_report = load_json(root / "03数据" / "10自动评审" / "规则自动评审与去重评分报告_最新.json", {})
    reviews = [
        item for item in review_report.get("规则评审", [])
        if item.get("价值等级") == "高价值" and item.get("重复等级") != "高重复"
    ]
    candidates = [candidate_for(item) for item in reviews]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-local-rule-check-candidates",
        "所属系统": "03杰哥进化系统",
        "来源": "规则自动评审与去重评分报告_最新.json",
        "候选数量": len(candidates),
        "自动执行候选数量": sum(1 for item in candidates if item["自动执行"]),
        "硬边界候选数量": sum(1 for item in candidates if item["硬边界保留"]),
        "检查项候选": candidates,
        "小样本验收": {
            "来源评审存在": bool(review_report),
            "候选数量不少于6": len(candidates) >= 6,
            "包含风险分级检查": any(item["检查类型"] == "风险分级检查" for item in candidates),
            "包含硬边界检查": any(item["检查类型"] == "硬边界检查" for item in candidates),
            "判定": "通过" if len(candidates) >= 6 else "需补充"
        },
        "安全边界": {
            "修改其他系统业务代码": False,
            "修改总管进度口径": False,
            "发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False
        }
    }
    out_dir = root / "03数据" / "11本地检查项候选"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = out_dir / f"规则本地检查项候选_{timestamp}.json"
    latest_json = out_dir / "规则本地检查项候选_最新.json"
    output_md = out_dir / f"规则本地检查项候选_{timestamp}.md"
    latest_md = out_dir / "规则本地检查项候选_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"候选数量": len(candidates), "输出": str(output_json), "判定": report["小样本验收"]["判定"]}, ensure_ascii=True))
    return 0 if report["小样本验收"]["判定"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
