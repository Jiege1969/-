# -*- coding: utf-8 -*-
"""
名称：生成股票周复盘_轻量.py
作用：基于L5进入记录、AI分析报告和用户反馈生成轻量周复盘。
触发方式：python 生成股票周复盘_轻量.py
依赖：L5进入记录_最新.json；AI分析报告_最新.json；反馈日志.json（可选）。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地记录；只写03数据/137复盘报告与04日志/用户反馈；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
标识：stock-weekly-review-lite-generate
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"必需文件不存在: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票周复盘（轻量）- {report['数据日期']}",
        "",
        "## 一、L5出现次数排行",
        "",
    ]
    for item in report["L5出现次数排行"]:
        lines.append(f"- {item['代码']} {item['名称']}：{item['出现次数']}次，行业：{item['行业']}")
    lines.extend(["", "## 二、行业分布", ""])
    for industry, count in report["行业分布"].items():
        lines.append(f"- {industry}：{count}只次")
    lines.extend(["", "## 三、用户增强命中", ""])
    lines.append(f"- 用户增强命中只次：{report['用户增强命中只次']}")
    lines.extend(["", "## 四、反馈统计", ""])
    if report["反馈统计"]:
        for feedback, count in report["反馈统计"].items():
            lines.append(f"- {feedback}：{count}")
    else:
        lines.append("- 暂无反馈。")
    lines.extend([
        "",
        "## 五、说明",
        "",
        "- 当前为轻量复盘，只统计L5进入记录、行业分布和用户反馈。",
        "- 后续可接入5日相对沪深300表现和规则反校准。",
        "- 本复盘不构成投资建议，不触发推送或交易。",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    today = now.strftime("%Y-%m-%d")
    history_path = root / "03数据" / "134深度研究池" / "L5进入记录_最新.json"
    feedback_path = root / "04日志" / "用户反馈" / "反馈日志.json"
    output_dir = root / "03数据" / "137复盘报告"
    output_json = output_dir / f"股票周复盘_轻量_{stamp}.json"
    output_md = output_dir / f"股票周复盘_轻量_{stamp}.md"
    latest_json = output_dir / "股票周复盘_轻量_最新.json"
    latest_md = output_dir / "股票周复盘_轻量_最新.md"

    history = load_json(history_path, required=True)
    feedback = load_json(feedback_path, required=False)
    records = list(history.get("历史记录", []))
    counter = Counter(item.get("代码") for item in records if item.get("代码"))
    first_by_code: dict[str, dict[str, Any]] = {}
    industry_counter = Counter()
    user_enhance_hits = 0
    for item in records:
        code = item.get("代码")
        if code and code not in first_by_code:
            first_by_code[code] = item
        industry_counter[item.get("行业") or "待映射"] += 1
        if item.get("是否用户增强"):
            user_enhance_hits += 1

    ranking = []
    for code, count in counter.most_common(20):
        item = first_by_code.get(code, {})
        ranking.append({
            "代码": code,
            "名称": item.get("名称", ""),
            "行业": item.get("行业", ""),
            "出现次数": count,
        })
    feedback_counter = Counter(item.get("反馈类型") for item in feedback.get("反馈记录", []) if item.get("反馈类型"))
    report = {
        "名称": "股票周复盘轻量版",
        "版本": "2026-05-01",
        "数据日期": today,
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票周复盘_轻量.py",
        "数据健康度": {
            "L5历史记录数": len(records),
            "反馈记录数": len(feedback.get("反馈记录", [])),
            "是否完整": len(records) > 0,
        },
        "L5出现次数排行": ranking,
        "行业分布": dict(industry_counter.most_common()),
        "用户增强命中只次": user_enhance_hits,
        "反馈统计": dict(feedback_counter),
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写旧系统": False,
            "是否写正式库": False,
        },
    }
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({
        "状态": "完成",
        "L5历史记录数": len(records),
        "反馈记录数": len(feedback.get("反馈记录", [])),
        "Markdown": str(output_md),
        "JSON": str(output_json),
    }, ensure_ascii=False))
    return 0 if report["数据健康度"]["是否完整"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
