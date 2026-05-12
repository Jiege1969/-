# -*- coding: utf-8 -*-
"""
名称：生成研究决策复盘闭环蓝图.py
作用：生成股票研究系统的四本账复盘闭环蓝图，作为股票系统和进化系统共同学习的依据。
触发方式：python 生成研究决策复盘闭环蓝图.py
依赖：Python标准库；研究决策复盘闭环规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读配置；只写新系统股票模块03数据与07文档；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建研究决策复盘闭环蓝图生成脚本。
标识：stock-review-evolution-loop-blueprint-generate
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


def ensure_ledger_dirs(root: Path, ledgers: list[dict[str, Any]]) -> list[str]:
    created: list[str] = []
    for ledger in ledgers:
        relative = str(ledger.get("保存位置", "")).strip()
        if not relative:
            continue
        path = root / relative
        path.mkdir(parents=True, exist_ok=True)
        created.append(str(path))
    return created


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 研究决策复盘闭环蓝图",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、核心逻辑",
        "",
        report["核心逻辑"],
        "",
        "## 二、四本账",
        "",
        "| 账本 | 保存位置 | 作用 |",
        "|---|---|---|",
    ]
    for ledger in report["四本账"]:
        lines.append(f"| {ledger['账本']} | {ledger['保存位置']} | {ledger['作用']} |")
    lines.extend(["", "## 三、归因矩阵", ""])
    for item in report["归因矩阵"]:
        lines.append(f"- {item['场景']}：{item['动作']}")
    lines.extend(["", "## 四、反馈入口", ""])
    for item in report["反馈入口"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、进化边界", ""])
    lines.append("允许：")
    for item in report["进化边界"]["允许"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("禁止：")
    for item in report["进化边界"]["禁止"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "研究决策复盘闭环规则.json"
    rules = load_json(rule_path)
    ledger_dirs = ensure_ledger_dirs(root, rules.get("四本账", []))
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "核心逻辑": rules.get("核心逻辑", ""),
        "四本账": rules.get("四本账", []),
        "账本目录": ledger_dirs,
        "归因矩阵": rules.get("归因矩阵", []),
        "验证周期": rules.get("验证周期", []),
        "反馈入口": rules.get("反馈入口", []),
        "进化边界": rules.get("进化边界", {}),
        "提炼标准": rules.get("提炼标准", {}),
        "对全系统的意义": rules.get("对全系统的意义", []),
        "结论": "研究决策复盘闭环已形成四本账结构，可作为股票系统和总进化系统共同学习的样板。",
        "安全边界": {
            "是否联网": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False
        }
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_dir = root / "03数据" / "10复盘闭环" / "00蓝图"
    doc_path = root / "07文档" / "研究决策复盘闭环蓝图.md"
    output = data_dir / f"研究决策复盘闭环蓝图_{timestamp}.json"
    latest = data_dir / "研究决策复盘闭环蓝图_最新.json"
    write_json(output, report)
    write_json(latest, report)
    write_text(doc_path, build_markdown(report))
    print(json.dumps({"输出": str(output), "文档": str(doc_path), "账本目录数": len(ledger_dirs)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
