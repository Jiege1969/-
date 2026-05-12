# -*- coding: utf-8 -*-
"""
名称：执行问题分型修复复核能力只读检查.py
作用：只读检查系统是否已把“问题分型、事实双账、修复复核、样本代表性判断”内化为系统能力。
触发方式：python 执行问题分型修复复核能力只读检查.py
安全边界：只读扫描规则、契约、回执、面板、接续包和开机自检脚本；只在总管03数据输出报告；不删除、不移动、不重启、不触发n8n、不发送企业微信。
标识：problem-typing-repair-review-capability-readonly-check
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
OUT_DIR = ROOT / "00杰哥系统总管" / "03数据" / "运行状态"
OUT_JSON = OUT_DIR / "问题分型修复复核能力只读检查_最新.json"
OUT_MD = OUT_DIR / "问题分型修复复核能力只读检查_最新.md"

CONTRACT_MD = ROOT / "03杰哥进化系统" / "规则库" / "杰哥智能系统内生理念与能力契约_v1.0.md"
CONTRACT_JSON = ROOT / "03杰哥进化系统" / "规则库" / "杰哥智能系统内生理念与能力契约_v1.0.json"
LAYER_MD = ROOT / "03杰哥进化系统" / "规则库" / "四大系统与子系统内生能力分层落地规则_v1.0.md"
LAYER_JSON = ROOT / "03杰哥进化系统" / "规则库" / "四大系统与子系统内生能力分层落地规则_v1.0.json"
ABILITY_RULE_MD = ROOT / "03杰哥进化系统" / "规则库" / "同日修复后复核入账规则_v1.0.md"
ABILITY_RULE_JSON = ROOT / "03杰哥进化系统" / "规则库" / "同日修复后复核入账规则_v1.0.json"
FS03_MD = ROOT / "00杰哥系统总管" / "03数据" / "运行状态" / "FS_03_稳定版问题回收与升级规则复核_20260508.md"
FS06_REVIEW_JSON = ROOT / "00杰哥系统总管" / "03数据" / "运行状态" / "FS_06_第二自然日同日修复后复核入账回执_20260509.json"
PANEL = ROOT / "00杰哥系统总管" / "07文档" / "当前施工面板.md"
PACKAGE = ROOT / "00杰哥系统总管" / "03数据" / "开工上下文" / "一键接续施工包_最新.md"
STARTUP = ROOT / "00杰哥系统总管" / "02脚本" / "执行开机施工准备自检.ps1"


CHECKS = [
    ("内生理念契约Markdown", CONTRACT_MD, ["问题分型与修复复核", "原始失败的真实", "修复复验后的真实", "样本代表性判断"]),
    ("内生理念契约JSON", CONTRACT_JSON, ["问题分型与修复复核能力", "事实双账", "复核判断", "经验回流"]),
    ("分层落地规则Markdown", LAYER_MD, ["问题分型", "复核入账", "事实双账", "局部职责缺口"]),
    ("分层落地规则JSON", LAYER_JSON, ["问题分型与复核入账分层能力", "总管系统", "扩展系统", "子系统"]),
    ("同日修复后复核规则Markdown", ABILITY_RULE_MD, ["原始失败", "问题性质分型", "修复动作可追溯", "复验覆盖原失败项"]),
    ("同日修复后复核规则JSON", ABILITY_RULE_JSON, ["判断链", "输出要求", "能力要求"]),
    ("FS-03细分规则", FS03_MD, ["P1-A", "P1-B", "P1-C", "P1-D", "同日修复后复核"]),
    ("FS-06同日复核回执", FS06_REVIEW_JSON, ["P1-B 局部职责/路由缺口", "同日修复后复核入账", "原始失败回执保留"]),
    ("当前施工面板", PANEL, ["同日修复后复核", "P1-B", "第二自然日样本已补入账"]),
    ("一键接续施工包", PACKAGE, ["同日修复后复核", "P1-B", "第三自然日执行卡"]),
    ("开机自检脚本接入", STARTUP, ["problem-typing-repair-review-capability", "problem typing repair review check needs attention"]),
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def inspect_item(name: str, path: Path, keywords: list[str]) -> dict[str, Any]:
    text = read_text(path)
    missing = [keyword for keyword in keywords if keyword not in text]
    return {
        "名称": name,
        "路径": str(path),
        "存在": path.exists(),
        "状态": "pass" if path.exists() and not missing else "needs_attention",
        "缺少关键词": missing,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 问题分型修复复核能力只读检查",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{report['总体状态']}",
        "",
        "| 检查项 | 状态 | 缺少关键词 |",
        "| --- | --- | --- |",
    ]
    for item in report["检查结果"]:
        missing = "、".join(item["缺少关键词"]) if item["缺少关键词"] else "无"
        lines.append(f"| {item['名称']} | {item['状态']} | {missing} |")
    lines.extend([
        "",
        "## 结论",
        "",
        report["结论"],
        "",
        "## 安全边界",
        "",
        "- 未删除文件。",
        "- 未移动文件。",
        "- 未停止或重启服务。",
        "- 未触发 n8n。",
        "- 未发送企业微信。",
        "- 未写正式库。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = [inspect_item(name, path, keywords) for name, path, keywords in CHECKS]
    failed = [item for item in results if item["状态"] != "pass"]
    overall = "pass" if not failed else "needs_attention"
    report = {
        "生成时间": datetime.now().isoformat(timespec="seconds"),
        "总体状态": overall,
        "检查结果": results,
        "结论": "问题分型、事实双账、修复复核和样本代表性判断已落到契约、分层规则、回执、面板、接续包和开机自检。" if overall == "pass" else "问题分型修复复核能力仍有落点缺失。",
        "安全边界": {
            "删除文件": False,
            "移动文件": False,
            "停止或重启服务": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写正式库": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({"总体状态": overall, "输出": [str(OUT_JSON), str(OUT_MD)]}, ensure_ascii=False))
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
