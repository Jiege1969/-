# -*- coding: utf-8 -*-
"""生成稳定交付版每日一键只读刷新与日报汇总包。

把稳定版每日运行所需的只读刷新动作串成一个可执行计划：
总回归、三日判定、次日闸口、日报、总巡检快照。全程不触发外部真实动作。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "86稳定交付版每日一键只读刷新与日报汇总包"

LATEST_JSON = OUTPUT_DIR / "稳定交付版每日一键只读刷新与日报汇总包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付版每日一键只读刷新与日报汇总包_最新.md"
PLAN_JSON = OUTPUT_DIR / "稳定版每日一键只读刷新计划_最新.json"
PLAN_MD = OUTPUT_DIR / "稳定版每日一键只读刷新计划_最新.md"


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
        "id": "DRR-001",
        "名称": "日常可用交付版一键只读总回归",
        "脚本": EVOLUTION_ROOT / "02脚本" / "执行日常可用交付版一键只读总回归.py",
        "类别": "总回归",
    },
    {
        "id": "DRR-002",
        "名称": "一键只读总回归验收",
        "脚本": EVOLUTION_ROOT / "02脚本" / "验证日常可用交付版一键只读总回归.py",
        "类别": "总回归验收",
    },
    {
        "id": "DRR-003",
        "名称": "稳定版首日复验与问题回收",
        "脚本": EVOLUTION_ROOT / "02脚本" / "执行稳定交付版首日只读复验与问题回收.py",
        "类别": "复验",
    },
    {
        "id": "DRR-004",
        "名称": "稳定版首日复验验收",
        "脚本": EVOLUTION_ROOT / "02脚本" / "验证稳定交付版首日复验执行与问题回收包.py",
        "类别": "复验验收",
    },
    {
        "id": "DRR-005",
        "名称": "次日复验待执行闸口生成",
        "脚本": EVOLUTION_ROOT / "02脚本" / "生成稳定交付版次日复验待执行闸口包.py",
        "类别": "次日闸口",
    },
    {
        "id": "DRR-006",
        "名称": "次日复验待执行闸口只读核对",
        "脚本": EVOLUTION_ROOT / "02脚本" / "执行稳定交付版次日复验待执行闸口只读核对.py",
        "类别": "次日闸口",
    },
    {
        "id": "DRR-007",
        "名称": "次日复验待执行闸口验收",
        "脚本": EVOLUTION_ROOT / "02脚本" / "验证稳定交付版次日复验待执行闸口包.py",
        "类别": "次日闸口验收",
    },
    {
        "id": "DRR-008",
        "名称": "三日达标判定器生成",
        "脚本": EVOLUTION_ROOT / "02脚本" / "生成稳定交付版三日达标判定器与样本采集标准包.py",
        "类别": "三日判定",
    },
    {
        "id": "DRR-009",
        "名称": "三日达标判定器只读核对",
        "脚本": EVOLUTION_ROOT / "02脚本" / "执行稳定交付版三日达标判定器只读核对.py",
        "类别": "三日判定",
    },
    {
        "id": "DRR-010",
        "名称": "三日达标判定器验收",
        "脚本": EVOLUTION_ROOT / "02脚本" / "验证稳定交付版三日达标判定器与样本采集标准包.py",
        "类别": "三日判定验收",
    },
    {
        "id": "DRR-011",
        "名称": "每日运行日报生成",
        "脚本": EVOLUTION_ROOT / "02脚本" / "生成稳定交付版每日运行日报与次日待办包.py",
        "类别": "日报",
    },
    {
        "id": "DRR-012",
        "名称": "每日运行日报只读核对",
        "脚本": EVOLUTION_ROOT / "02脚本" / "执行稳定交付版每日运行日报只读核对.py",
        "类别": "日报",
    },
    {
        "id": "DRR-013",
        "名称": "每日运行日报验收",
        "脚本": EVOLUTION_ROOT / "02脚本" / "验证稳定交付版每日运行日报与次日待办包.py",
        "类别": "日报验收",
    },
    {
        "id": "DRR-014",
        "名称": "总巡检快照刷新",
        "脚本": EVOLUTION_ROOT / "02脚本" / "生成日常可用版自主巡检快照.py",
        "类别": "总巡检",
    },
]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_plan_md(plan: dict[str, Any]) -> str:
    rows = [
        f"| {item['id']} | {item['名称']} | {item['类别']} | {item['脚本']} |"
        for item in plan["任务"]
    ]
    return "\n".join(
        [
            "# 稳定版每日一键只读刷新计划",
            "",
            f"- 生成时间：{plan['生成时间']}",
            "",
            "| ID | 任务 | 类别 | 脚本 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定交付版每日一键只读刷新与日报汇总包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 任务数：{report['指标']['任务数']}",
            "",
            "## 使用入口",
            "",
            f"- 执行脚本：{report['执行入口']}",
            f"- 验收脚本：{report['验收入口']}",
            "",
            "## 边界",
            "",
            "- 只执行本地只读刷新和验收。",
            "- 不真实发送、不触发 n8n、不交易、不登录税局、不渲染发布、不重载服务。",
            "- 不生成未来自然日样本。",
            "",
        ]
    )


def main() -> int:
    plan = {
        "名称": "稳定版每日一键只读刷新计划",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务": [{**task, "脚本": str(task["脚本"])} for task in TASKS],
        "安全边界": SAFETY_BOUNDARY,
    }
    report = {
        "名称": "稳定交付版每日一键只读刷新与日报汇总包",
        "生成时间": plan["生成时间"],
        "状态": "stable_delivery_daily_one_click_readonly_refresh_ready",
        "刷新计划": str(PLAN_JSON),
        "执行入口": str(EVOLUTION_ROOT / "02脚本" / "执行稳定交付版每日一键只读刷新与日报汇总.py"),
        "验收入口": str(EVOLUTION_ROOT / "02脚本" / "验证稳定交付版每日一键只读刷新与日报汇总包.py"),
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
