# -*- coding: utf-8 -*-
"""生成稳定交付版运行指挥台每日刷新入口包。

本包提供一个稳定版日常入口：刷新每日只读链路、刷新运行指挥台、完成验收。
不修改总管面板、不修改一键接续包、不触发外部真实动作。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "88稳定交付版运行指挥台每日刷新入口包"

LATEST_JSON = OUTPUT_DIR / "稳定交付版运行指挥台每日刷新入口包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付版运行指挥台每日刷新入口包_最新.md"
PLAN_JSON = OUTPUT_DIR / "稳定版运行指挥台每日刷新入口计划_最新.json"
PLAN_MD = OUTPUT_DIR / "稳定版运行指挥台每日刷新入口计划_最新.md"


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
    "预生成未来自然日样本": False,
}


TASKS = [
    {
        "id": "RDC-001",
        "名称": "稳定版每日一键只读刷新",
        "脚本": EVOLUTION_ROOT / "02脚本" / "执行稳定交付版每日一键只读刷新与日报汇总.py",
    },
    {
        "id": "RDC-002",
        "名称": "稳定版每日一键刷新验收",
        "脚本": EVOLUTION_ROOT / "02脚本" / "验证稳定交付版每日一键只读刷新与日报汇总包.py",
    },
    {
        "id": "RDC-003",
        "名称": "稳定版试运行反馈本地入账",
        "脚本": EVOLUTION_ROOT / "02脚本" / "执行稳定版试运行反馈本地入账.py",
    },
    {
        "id": "RDC-004",
        "名称": "稳定版试运行反馈本地入账验收",
        "脚本": EVOLUTION_ROOT / "02脚本" / "验证稳定版试运行反馈本地入账执行器包.py",
    },
    {
        "id": "RDC-005",
        "名称": "稳定版运行指挥台生成",
        "脚本": EVOLUTION_ROOT / "02脚本" / "生成稳定交付版运行指挥台索引包.py",
    },
    {
        "id": "RDC-006",
        "名称": "稳定版运行指挥台只读核对",
        "脚本": EVOLUTION_ROOT / "02脚本" / "执行稳定交付版运行指挥台只读核对.py",
    },
    {
        "id": "RDC-007",
        "名称": "稳定版运行指挥台验收",
        "脚本": EVOLUTION_ROOT / "02脚本" / "验证稳定交付版运行指挥台索引包.py",
    },
    {
        "id": "RDC-008",
        "名称": "自主巡检快照最终刷新",
        "脚本": EVOLUTION_ROOT / "02脚本" / "生成日常可用版自主巡检快照.py",
    },
]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_plan_md(plan: dict[str, Any]) -> str:
    rows = [f"| {item['id']} | {item['名称']} | {item['脚本']} |" for item in plan["任务"]]
    return "\n".join(
        [
            "# 稳定版运行指挥台每日刷新入口计划",
            "",
            f"- 生成时间：{plan['生成时间']}",
            "",
            "| ID | 任务 | 脚本 |",
            "| --- | --- | --- |",
            *rows,
            "",
        ]
    )


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定交付版运行指挥台每日刷新入口包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 任务数：{report['指标']['任务数']}",
            "",
            "## 每日使用命令",
            "",
            f"- `python \"{report['执行入口']}\"`",
            f"- `python \"{report['验收入口']}\"`",
            "",
            "## 边界",
            "",
            "- 只读刷新稳定版运行指挥台。",
            "- 不修改总管面板，不修改一键接续包。",
            "- 不触发企业微信真实发送、n8n、交易、税局、视频渲染发布或服务重载。",
            "",
        ]
    )


def main() -> int:
    plan = {
        "名称": "稳定版运行指挥台每日刷新入口计划",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务": [{**task, "脚本": str(task["脚本"])} for task in TASKS],
        "安全边界": SAFETY_BOUNDARY,
    }
    report = {
        "名称": "稳定交付版运行指挥台每日刷新入口包",
        "生成时间": plan["生成时间"],
        "状态": "stable_delivery_runtime_dashboard_daily_refresh_entry_ready",
        "刷新计划": str(PLAN_JSON),
        "执行入口": str(EVOLUTION_ROOT / "02脚本" / "执行稳定交付版运行指挥台每日刷新入口.py"),
        "验收入口": str(EVOLUTION_ROOT / "02脚本" / "验证稳定交付版运行指挥台每日刷新入口包.py"),
        "指标": {"任务数": len(TASKS), "安全边界关闭项": len(SAFETY_BOUNDARY)},
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "刷新计划JSON": str(PLAN_JSON),
            "刷新计划Markdown": str(PLAN_MD),
        },
    }
    write_json(PLAN_JSON, plan)
    write_text(PLAN_MD, build_plan_md(plan))
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "任务数": len(TASKS), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
