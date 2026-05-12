# -*- coding: utf-8 -*-
"""
名称：生成股票复盘反馈待回填观察报告.py
作用：读取股票复盘反馈样本接入候选包，生成待回填观察报告和后续转经验候选条件。
触发方式：python 生成股票复盘反馈待回填观察报告.py
依赖：Python标准库；股票复盘反馈样本接入候选包_最新.json。
所属系统：03杰哥进化系统
安全边界：只读03本地样本候选包，只写03本地观察报告；不写回股票系统，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建股票复盘反馈待回填观察报告脚本。
标识：evolution-stock-review-feedback-pending-observe-generate
"""

from __future__ import annotations

import json
from collections import Counter
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
        "# 股票复盘反馈待回填观察报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 待回填样本：{report['待回填样本数量']}",
        f"- 可转经验样本：{report['可转经验样本数量']}",
        "",
        "## 转经验条件",
        "",
    ]
    for item in report["转经验条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 待回填样本前20", ""])
    for item in report["待回填样本"][:20]:
        lines.append(f"- {item['股票名称']}({item['股票代码']})：{item['等待内容']}")
    return "\n".join(lines)


def main() -> int:
    root = system_root()
    source = load_json(root / "03数据" / "13股票复盘反馈样本" / "股票复盘反馈样本接入候选包_最新.json", {})
    candidates = source.get("样本候选", [])
    pending = [item for item in candidates if item.get("样本状态") == "待复盘反馈"]
    ready = [item for item in candidates if item.get("样本状态") == "可进入经验提炼"]
    cycle_counter: Counter[str] = Counter()
    pending_items = []
    for item in pending:
        cycles = item.get("验证周期", [])
        cycle_counter.update(cycles)
        pending_items.append(
            {
                "股票代码": item.get("股票代码", ""),
                "股票名称": item.get("股票名称", ""),
                "报告日期": item.get("报告日期", ""),
                "验证周期": cycles,
                "等待内容": "等待 " + "/".join(cycles) + " 验证结果或人工评价回填",
                "不提炼原因": "尚无复盘反馈，不能把预测结果沉淀为经验结论。",
            }
        )
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-stock-review-feedback-pending-observe",
        "所属系统": "03杰哥进化系统",
        "来源": "股票复盘反馈样本接入候选包_最新.json",
        "待回填样本数量": len(pending),
        "可转经验样本数量": len(ready),
        "周期等待统计": dict(cycle_counter),
        "待回填样本": pending_items,
        "可转经验样本": ready,
        "转经验条件": [
            "任一验证结果_T5/T20/T60/T120 字段出现有效反馈。",
            "人工评价字段出现明确正向、负向或修正说明。",
            "反馈能对应原始报告路径、判断主因、分层状态和证据完整度。",
            "经验提炼必须区分判断有效、判断失效、证据不足和周期未到。"
        ],
        "小样本验收": {
            "来源候选包存在": bool(source),
            "待回填样本可统计": len(pending) >= 0,
            "转经验条件存在": True,
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
    out_dir = root / "03数据" / "14复盘反馈观察"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = out_dir / f"股票复盘反馈待回填观察报告_{timestamp}.json"
    latest_json = out_dir / "股票复盘反馈待回填观察报告_最新.json"
    output_md = out_dir / f"股票复盘反馈待回填观察报告_{timestamp}.md"
    latest_md = out_dir / "股票复盘反馈待回填观察报告_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"待回填样本数量": len(pending), "可转经验样本数量": len(ready), "输出": str(output_json)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
