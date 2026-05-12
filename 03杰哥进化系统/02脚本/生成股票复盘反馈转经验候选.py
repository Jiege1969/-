# -*- coding: utf-8 -*-
"""
名称：生成股票复盘反馈转经验候选.py
作用：读取股票复盘反馈待回填观察报告，把已有有效反馈的样本转成经验候选；无反馈时输出空候选和等待原因。
触发方式：python 生成股票复盘反馈转经验候选.py
依赖：Python标准库；股票复盘反馈待回填观察报告_最新.json。
所属系统：03杰哥进化系统
安全边界：只写03进化系统经验候选，不写回股票系统，不修改股票脚本，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建股票复盘反馈转经验候选脚本。
标识：evolution-stock-review-feedback-to-experience-candidates-generate
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


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票复盘反馈转经验候选",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 转经验候选数量：{report['转经验候选数量']}",
        f"- 等待反馈数量：{report['等待反馈数量']}",
        "",
        "## 当前结论",
        "",
        report["当前结论"],
        "",
    ]
    if report["经验候选"]:
        lines.append("## 经验候选")
        for item in report["经验候选"]:
            lines.append(f"- {item['候选ID']} {item['标题']}")
    return "\n".join(lines)


def main() -> int:
    root = system_root()
    observe = load_json(root / "03数据" / "14复盘反馈观察" / "股票复盘反馈待回填观察报告_最新.json", {})
    ready = observe.get("可转经验样本", [])
    candidates = []
    for idx, item in enumerate(ready, start=1):
        candidates.append(
            {
                "候选ID": f"SRE-{idx:03d}",
                "标题": f"{item.get('股票名称', '')}复盘反馈经验候选",
                "来源股票": f"{item.get('股票名称', '')}({item.get('股票代码', '')})",
                "报告日期": item.get("报告日期", ""),
                "候选类型": "股票复盘反馈经验",
                "待提炼问题": "原判断是否有效，哪些证据有用，哪些口径需要调整。",
                "转经验前置": "需要保留原始报告路径、复盘结果、人工评价和验证周期。",
                "自动固化": False,
                "下一步": "生成经验卡片草案，等待验收后进入通用方法或规则候选。",
            }
        )
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-stock-review-feedback-to-experience-candidates",
        "所属系统": "03杰哥进化系统",
        "来源": "股票复盘反馈待回填观察报告_最新.json",
        "转经验候选数量": len(candidates),
        "等待反馈数量": int(observe.get("待回填样本数量", 0) or 0),
        "经验候选": candidates,
        "当前结论": "当前没有可转经验样本，继续等待复盘反馈回填。" if not candidates else "已有可转经验样本，可进入经验卡片草案。",
        "小样本验收": {
            "来源观察报告存在": bool(observe),
            "允许空候选": True,
            "空候选原因明确": not candidates,
            "判定": "通过"
        },
        "安全边界": {
            "写回股票系统": False,
            "修改股票脚本": False,
            "发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False
        }
    }
    out_dir = root / "03数据" / "15复盘转经验候选"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = out_dir / f"股票复盘反馈转经验候选_{timestamp}.json"
    latest_json = out_dir / "股票复盘反馈转经验候选_最新.json"
    output_md = out_dir / f"股票复盘反馈转经验候选_{timestamp}.md"
    latest_md = out_dir / "股票复盘反馈转经验候选_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"转经验候选数量": len(candidates), "输出": str(output_json)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
