# -*- coding: utf-8 -*-
"""
名称：执行主动纠错防机械执行只读检查.py
作用：只读检查系统是否已吸收“规则服务目标、低风险问题主动纠错、红线动作才确认”的防机械执行能力。
触发方式：python 执行主动纠错防机械执行只读检查.py
安全边界：只读扫描规则、面板、接续包和开机自检脚本；只在总管03数据输出报告；不删除、不移动、不重启、不触发n8n、不发送企业微信。
标识：anti-mechanical-execution-readonly-check
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
OUT_DIR = ROOT / "00杰哥系统总管" / "03数据" / "运行状态"
OUT_JSON = OUT_DIR / "主动纠错防机械执行只读检查_最新.json"
OUT_MD = OUT_DIR / "主动纠错防机械执行只读检查_最新.md"

RULE_MD = ROOT / "03杰哥进化系统" / "规则库" / "主动纠错与防机械执行规则_v1.0.md"
RULE_JSON = ROOT / "03杰哥进化系统" / "规则库" / "主动纠错与防机械执行规则_v1.0.json"
CONTRACT_MD = ROOT / "03杰哥进化系统" / "规则库" / "杰哥智能系统内生理念与能力契约_v1.0.md"
CONTRACT_JSON = ROOT / "03杰哥进化系统" / "规则库" / "杰哥智能系统内生理念与能力契约_v1.0.json"
PANEL = ROOT / "00杰哥系统总管" / "07文档" / "当前施工面板.md"
PACKAGE = ROOT / "00杰哥系统总管" / "03数据" / "开工上下文" / "一键接续施工包_最新.md"
STARTUP = ROOT / "00杰哥系统总管" / "02脚本" / "执行开机施工准备自检.ps1"


REQUIRED_RULE_KEYWORDS = [
    "规则不是目的",
    "主动纠错",
    "受控推进",
    "必须确认",
    "不得以等待确认代替解决",
    "D:\\01杰哥智能系统",
    "19310",
]

REQUIRED_CONTRACT_KEYWORDS = [
    "主动纠错",
    "不机械执行",
    "规则服务目标",
]

REQUIRED_RUNTIME_KEYWORDS = [
    "anti-mechanical-execution",
    "mechanical execution check needs attention",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def check_keywords(name: str, path: Path, keywords: list[str]) -> dict[str, Any]:
    text = read_text(path)
    missing = [item for item in keywords if item not in text]
    return {
        "名称": name,
        "路径": str(path),
        "存在": path.exists(),
        "状态": "pass" if path.exists() and not missing else "needs_attention",
        "缺少关键词": missing,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 主动纠错防机械执行只读检查",
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
        "- 未触发n8n。",
        "- 未发送企业微信。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    checks = [
        check_keywords("规则库Markdown", RULE_MD, REQUIRED_RULE_KEYWORDS),
        check_keywords("内生理念契约Markdown", CONTRACT_MD, REQUIRED_CONTRACT_KEYWORDS),
        check_keywords("内生理念契约JSON", CONTRACT_JSON, REQUIRED_CONTRACT_KEYWORDS),
        check_keywords("开机自检脚本接入", STARTUP, REQUIRED_RUNTIME_KEYWORDS),
        check_keywords("当前施工面板", PANEL, ["主动纠错", "防机械执行"]),
        check_keywords("一键接续施工包", PACKAGE, ["主动纠错", "防机械执行"]),
    ]
    failed = [item for item in checks if item["状态"] != "pass"]
    overall = "pass" if not failed else "needs_attention"
    report = {
        "生成时间": datetime.now().isoformat(timespec="seconds"),
        "总体状态": overall,
        "检查结果": checks,
        "结论": "防机械执行能力已落到规则库、契约、开机自检、面板和接续包。" if overall == "pass" else "防机械执行能力仍有落点缺失。",
        "安全边界": {
            "删除文件": False,
            "移动文件": False,
            "停止或重启服务": False,
            "触发n8n": False,
            "发送企业微信": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({"总体状态": overall, "输出": [str(OUT_JSON), str(OUT_MD)]}, ensure_ascii=False))
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
