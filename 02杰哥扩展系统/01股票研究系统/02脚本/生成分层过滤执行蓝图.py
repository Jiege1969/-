# -*- coding: utf-8 -*-
"""
名称：生成分层过滤执行蓝图.py
作用：根据分层过滤规则生成可执行蓝图，为后续指标计算、候选筛选、日报生成提供统一依据。
触发方式：python 生成分层过滤执行蓝图.py
依赖：Python标准库；分层过滤规则.json；旧草案吸收规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读配置；只写新系统股票模块03数据与07文档；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建分层过滤执行蓝图生成脚本。
标识：stock-layered-filter-blueprint-generate
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


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 分层过滤执行蓝图",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、优化原则",
        "",
    ]
    for item in report["优化原则"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 二、运行模式", ""])
    for name, item in report["运行模式"].items():
        lines.append(f"- {name}：上限 {item['样本上限']}，{item['说明']}")
    lines.extend(["", "## 三、过滤阶段", ""])
    for stage in report["过滤阶段"]:
        lines.append(f"### {stage['阶段']}")
        lines.append(f"- 输入层：{stage['输入层']}")
        lines.append(f"- 输出层：{stage['输出层']}")
        lines.append(f"- 目标规模：{stage['目标规模']}")
        for rule in stage["规则"]:
            lines.append(f"- {rule['字段']}：{rule['条件']}，权重 {rule['权重']}")
        lines.append("")
    lines.extend(["## 四、禁止事项", ""])
    for item in report["禁止事项"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rules = load_json(root / "01配置" / "分层过滤规则.json")
    absorption = load_json(root / "01配置" / "旧草案吸收规则.json")
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(root / "01配置" / "分层过滤规则.json"),
        "来源吸收规则": str(root / "01配置" / "旧草案吸收规则.json"),
        "优化原则": rules.get("优化原则", []),
        "运行模式": rules.get("运行模式", {}),
        "层级权限": rules.get("层级权限", {}),
        "过滤阶段": rules.get("过滤阶段", []),
        "数据健康度": rules.get("数据健康度", {}),
        "反馈优化": rules.get("反馈优化", {}),
        "禁止事项": rules.get("禁止事项", []),
        "草案吸收项": len(absorption.get("已吸收内容", [])),
        "结论": "旧草案漏斗逻辑已优化为可配置、可验收、可逐步放量的分层执行蓝图。"
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_dir = root / "03数据" / "09分层过滤"
    doc_path = root / "07文档" / "分层过滤执行蓝图.md"
    output = data_dir / f"分层过滤执行蓝图_{timestamp}.json"
    latest = data_dir / "分层过滤执行蓝图_最新.json"
    write_json(output, report)
    write_json(latest, report)
    write_text(doc_path, build_markdown(report))
    print(json.dumps({"输出": str(output), "文档": str(doc_path), "阶段数": len(report["过滤阶段"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
