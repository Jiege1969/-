# -*- coding: utf-8 -*-
"""
名称：执行业务子系统问题分型模板只读检查.py
作用：只读检查业务子系统是否具备问题分型、修复复核、经验回流的统一回执模板。
触发方式：python 执行业务子系统问题分型模板只读检查.py
安全边界：只读扫描规则库、分层规则、面板、接续包和开机自检脚本；只在总管03数据输出报告；不删除、不移动、不重启、不触发n8n、不发送企业微信。
标识：business-subsystem-typing-template-readonly-check
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
OUT_DIR = ROOT / "00杰哥系统总管" / "03数据" / "运行状态"
OUT_JSON = OUT_DIR / "业务子系统问题分型模板只读检查_最新.json"
OUT_MD = OUT_DIR / "业务子系统问题分型模板只读检查_最新.md"

TEMPLATE_MD = ROOT / "03杰哥进化系统" / "规则库" / "业务子系统问题分型与复核回执模板_v1.0.md"
TEMPLATE_JSON = ROOT / "03杰哥进化系统" / "规则库" / "业务子系统问题分型与复核回执模板_v1.0.json"
LAYER_MD = ROOT / "03杰哥进化系统" / "规则库" / "四大系统与子系统内生能力分层落地规则_v1.0.md"
LAYER_JSON = ROOT / "03杰哥进化系统" / "规则库" / "四大系统与子系统内生能力分层落地规则_v1.0.json"
PANEL = ROOT / "00杰哥系统总管" / "07文档" / "当前施工面板.md"
PACKAGE = ROOT / "00杰哥系统总管" / "03数据" / "开工上下文" / "一键接续施工包_最新.md"
STARTUP = ROOT / "00杰哥系统总管" / "02脚本" / "执行开机施工准备自检.ps1"


CHECKS = [
    ("模板Markdown", TEMPLATE_MD, ["股票研究系统模板", "税收业务系统模板", "视频制作系统模板", "企业微信公共接入层模板", "总管回收要求"]),
    ("模板JSON", TEMPLATE_JSON, ["股票研究系统", "税收业务系统", "视频制作系统", "企业微信公共接入层", "总管回收要求"]),
    ("分层规则Markdown", LAYER_MD, ["业务子系统问题分型与复核回执模板", "原始事实", "问题分型", "经验回流"]),
    ("分层规则JSON", LAYER_JSON, ["业务子系统回执结构", "子系统模板", "复验证据", "安全边界"]),
    ("当前施工面板", PANEL, ["业务子系统问题分型", "股票、税收、视频、企业微信公共接入层"]),
    ("一键接续施工包", PACKAGE, ["业务子系统问题分型", "子系统回执"]),
    ("开机自检脚本接入", STARTUP, ["business-subsystem-typing-template", "business subsystem typing template check needs attention"]),
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
        "# 业务子系统问题分型模板只读检查",
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
        "结论": "业务子系统问题分型与复核回执模板已覆盖股票、税收、视频、企业微信公共接入层，并接入分层规则、面板、接续包和开机自检。" if overall == "pass" else "业务子系统问题分型模板仍有落点缺失。",
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
