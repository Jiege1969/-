# -*- coding: utf-8 -*-
"""生成稳定版试运行回传入口导航与闭环索引包。

把使用者操作卡、试运行问题回传模板、首周试用场景、问题台账和每日指挥台串成只读导航。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "91稳定版试运行回传入口导航与闭环索引包"

LATEST_JSON = OUTPUT_DIR / "稳定版试运行回传入口导航与闭环索引包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版试运行回传入口导航与闭环索引包_最新.md"
NAV_MD = OUTPUT_DIR / "稳定版试运行回传入口导航_最新.md"
CLOSE_LOOP_MD = OUTPUT_DIR / "稳定版试运行问题闭环索引_最新.md"


SOURCES = {
    "使用者一页操作卡": EVOLUTION_ROOT / "03数据" / "89稳定版使用者一页操作卡与灯号说明包" / "稳定版使用者一页操作卡_最新.md",
    "运行灯号说明": EVOLUTION_ROOT / "03数据" / "89稳定版使用者一页操作卡与灯号说明包" / "稳定版运行灯号说明_最新.md",
    "运行指挥台": EVOLUTION_ROOT / "03数据" / "87稳定交付版运行指挥台索引包" / "稳定版运行指挥台_最新.md",
    "每日刷新入口包": EVOLUTION_ROOT / "03数据" / "88稳定交付版运行指挥台每日刷新入口包" / "稳定交付版运行指挥台每日刷新入口包_最新.md",
    "试运行问题回传模板": EVOLUTION_ROOT / "03数据" / "90稳定版试运行问题回传模板与入账预演包" / "稳定版试运行问题回传模板_最新.md",
    "试运行问题处理口径": EVOLUTION_ROOT / "03数据" / "90稳定版试运行问题回传模板与入账预演包" / "稳定版试运行问题处理口径_最新.md",
    "首周试用场景": EVOLUTION_ROOT / "03数据" / "90使用者首周试用场景演练包" / "首周试用场景清单_最新.md",
    "问题入账预演台账": EVOLUTION_ROOT / "03数据" / "90稳定版试运行问题回传模板与入账预演包" / "稳定版试运行问题入账预演台账_最新.md",
}


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "接n8n": False,
    "触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "生成正式税务结论": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "写正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def source_rows() -> list[dict[str, Any]]:
    return [{"名称": name, "路径": str(path), "存在": path.exists()} for name, path in SOURCES.items()]


def build_nav_md() -> str:
    return "\n".join(
        [
            "# 稳定版试运行回传入口导航",
            "",
            "## 每天先刷新",
            "",
            f"```powershell\npython \"{EVOLUTION_ROOT / '02脚本' / '执行稳定交付版运行指挥台每日刷新入口.py'}\"\n```",
            "",
            "## 使用时看",
            "",
            f"- 操作卡：{SOURCES['使用者一页操作卡']}",
            f"- 运行指挥台：{SOURCES['运行指挥台']}",
            f"- 首周试用场景：{SOURCES['首周试用场景']}",
            "",
            "## 出问题时填",
            "",
            f"- 问题回传模板：{SOURCES['试运行问题回传模板']}",
            f"- 处理口径：{SOURCES['试运行问题处理口径']}",
            f"- 入账预演台账：{SOURCES['问题入账预演台账']}",
            "",
        ]
    )


def build_close_loop_md() -> str:
    return "\n".join(
        [
            "# 稳定版试运行问题闭环索引",
            "",
            "1. 使用者按一页操作卡每日刷新。",
            "2. 按首周试用场景实际使用税收、股票、视频和公共入口。",
            "3. 出现问题时按回传模板登记。",
            "4. P0 或涉及红线的问题只登记需总管确认。",
            "5. P1-P4 问题进入候选台账和只读复验，不自动转正式规则。",
            "6. 修复后复跑每日刷新入口和总巡检快照。",
            "",
            "## 关键边界",
            "",
            "- 不真实发送企业微信，不触发 n8n。",
            "- 不接券商、不交易，不登录税局、不接财税软件。",
            "- 不真实渲染或发布视频。",
            "- 不自动转正式规则，不重载服务。",
            "",
        ]
    )


def build_summary_md(report: dict[str, Any]) -> str:
    rows = [f"| {item['名称']} | {item['存在']} | {item['路径']} |" for item in report["来源索引"]]
    return "\n".join(
        [
            "# 稳定版试运行回传入口导航与闭环索引包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 来源存在：{report['指标']['来源存在数']} / {report['指标']['来源数']}",
            "",
            "| 来源 | 存在 | 路径 |",
            "| --- | --- | --- |",
            *rows,
            "",
        ]
    )


def main() -> int:
    sources = source_rows()
    report = {
        "名称": "稳定版试运行回传入口导航与闭环索引包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_trial_feedback_navigation_loop_index_ready",
        "来源索引": sources,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "回传入口导航": str(NAV_MD),
            "问题闭环索引": str(CLOSE_LOOP_MD),
        },
        "指标": {
            "来源数": len(sources),
            "来源存在数": sum(1 for item in sources if item["存在"]),
            "安全边界关闭项": len(SAFETY_BOUNDARY),
        },
        "安全边界": SAFETY_BOUNDARY,
    }
    write_text(NAV_MD, build_nav_md())
    write_text(CLOSE_LOOP_MD, build_close_loop_md())
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "来源存在数": report["指标"]["来源存在数"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
