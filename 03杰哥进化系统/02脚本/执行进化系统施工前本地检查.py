# -*- coding: utf-8 -*-
"""
名称：执行进化系统施工前本地检查.py
作用：读取规则本地检查项候选，执行03进化系统施工前本地检查，输出自动继续项、硬边界提示和下一步施工建议。
触发方式：python 执行进化系统施工前本地检查.py
依赖：Python标准库；规则本地检查项候选_最新.json。
所属系统：03杰哥进化系统
安全边界：只读03本地候选检查项，只写03本地检查报告；不修改其他系统业务代码，不修改总管进度口径，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建进化系统施工前本地检查脚本。
标识：evolution-prework-local-check-run
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
        "# 进化系统施工前本地检查",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体判定：{report['总体判定']}",
        f"- 自动继续项：{len(report['自动继续项'])}",
        f"- 硬边界提示：{len(report['硬边界提示'])}",
        "",
        "## 自动继续项",
        "",
    ]
    for item in report["自动继续项"]:
        lines.append(f"- {item['检查项ID']} {item['检查项名称']}：{item['默认动作']}")
    lines.extend(["", "## 硬边界提示", ""])
    for item in report["硬边界提示"]:
        lines.append(f"- {item['检查项ID']} {item['检查项名称']}：{item['默认动作']}")
    lines.extend(["", "## 下一步施工建议", ""])
    for item in report["下一步施工建议"]:
        lines.append(f"- {item}")
    return "\n".join(lines)


def main() -> int:
    root = system_root()
    candidates_report = load_json(root / "03数据" / "11本地检查项候选" / "规则本地检查项候选_最新.json", {})
    candidates = candidates_report.get("检查项候选", [])
    auto_items = [item for item in candidates if item.get("自动执行") is True]
    hard_items = [item for item in candidates if item.get("硬边界保留") is True]
    failures = []
    if not candidates:
        failures.append("本地检查项候选不存在")
    if not auto_items:
        failures.append("缺少自动继续检查项")
    if not hard_items:
        failures.append("缺少硬边界提示项")

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-prework-local-check",
        "所属系统": "03杰哥进化系统",
        "总体判定": "可继续低风险本地施工" if not failures else "需补齐检查项",
        "候选来源": "规则本地检查项候选_最新.json",
        "候选数量": len(candidates),
        "自动继续项": auto_items,
        "硬边界提示": hard_items,
        "失败项": failures,
        "下一步施工建议": [
            "继续推进03进化系统本地检查项正式验收脚本。",
            "继续接入股票复盘T+1/T+3/T+5真实反馈样本。",
            "继续把过期闸口纠偏为风险分级，不因旧文字停工。",
            "遇到真实外部动作或不可回滚生产改写时，只生成准入、回滚和验收，不自动执行。"
        ],
        "安全边界": {
            "修改其他系统业务代码": False,
            "修改总管进度口径": False,
            "发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False
        }
    }
    out_dir = root / "03数据" / "12施工前本地检查"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = out_dir / f"进化系统施工前本地检查_{timestamp}.json"
    latest_json = out_dir / "进化系统施工前本地检查_最新.json"
    output_md = out_dir / f"进化系统施工前本地检查_{timestamp}.md"
    latest_md = out_dir / "进化系统施工前本地检查_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体判定": report["总体判定"], "输出": str(output_json)}, ensure_ascii=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
