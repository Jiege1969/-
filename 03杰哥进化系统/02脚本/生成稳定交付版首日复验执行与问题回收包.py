# -*- coding: utf-8 -*-
"""生成稳定交付版首日复验执行与问题回收包。

本包面向稳定版交付后的真实运行观察：只编排只读复验、问题登记和复验建议，
不修改正式规则、不触发外部系统、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "82稳定交付版首日复验执行与问题回收包"

LATEST_JSON = OUTPUT_DIR / "稳定交付版首日复验执行与问题回收包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付版首日复验执行与问题回收包_最新.md"
PLAN_JSON = OUTPUT_DIR / "稳定版首日只读复验执行计划_最新.json"
LEDGER_JSON = OUTPUT_DIR / "稳定版首日问题回收台账_最新.json"
LEDGER_MD = OUTPUT_DIR / "稳定版首日问题回收台账_最新.md"


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


READONLY_TASKS = [
    {
        "id": "SD-D1-001",
        "名称": "日常可用交付版一键只读总回归",
        "脚本": EVOLUTION_ROOT / "02脚本" / "执行日常可用交付版一键只读总回归.py",
        "验证脚本": EVOLUTION_ROOT / "02脚本" / "验证日常可用交付版一键只读总回归.py",
        "类别": "总回归",
        "失败级别": "P1",
    },
    {
        "id": "SD-D1-002",
        "名称": "日常可用版自主巡检快照",
        "脚本": EVOLUTION_ROOT / "02脚本" / "生成日常可用版自主巡检快照.py",
        "验证脚本": None,
        "类别": "总巡检",
        "失败级别": "P1",
    },
    {
        "id": "SD-D1-003",
        "名称": "稳定交付版运行观察基线",
        "脚本": EVOLUTION_ROOT / "02脚本" / "执行稳定交付版运行观察基线只读核对.py",
        "验证脚本": EVOLUTION_ROOT / "02脚本" / "验证稳定交付版运行观察基线与改进闭环包.py",
        "类别": "运行观察",
        "失败级别": "P2",
    },
    {
        "id": "SD-D1-004",
        "名称": "交付后首日运行观察与问题登记",
        "脚本": None,
        "验证脚本": EVOLUTION_ROOT / "02脚本" / "验证交付后首日运行观察与问题登记包.py",
        "类别": "问题登记",
        "失败级别": "P2",
    },
    {
        "id": "SD-D1-005",
        "名称": "日常可用版与稳定交付版最终交付收尾",
        "脚本": None,
        "验证脚本": EVOLUTION_ROOT / "02脚本" / "验证日常可用版与稳定交付版最终交付收尾包.py",
        "类别": "交付收尾",
        "失败级别": "P2",
    },
]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_empty_ledger() -> dict[str, Any]:
    return {
        "名称": "稳定版首日问题回收台账",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "说明": "执行脚本会按只读复验结果自动填入问题项；无失败时保持空问题清单。",
        "问题项": [],
        "字段": [
            "来源任务",
            "问题级别",
            "现象",
            "复现脚本",
            "标准输出摘要",
            "错误输出摘要",
            "是否触碰红线",
            "是否需总管确认",
            "建议动作",
        ],
    }


def build_ledger_md(ledger: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版首日问题回收台账",
            "",
            f"- 生成时间：{ledger['生成时间']}",
            f"- 说明：{ledger['说明']}",
            "",
            "| 字段 |",
            "| --- |",
            *[f"| {field} |" for field in ledger["字段"]],
            "",
        ]
    )


def build_summary_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {task['id']} | {task['名称']} | {task['类别']} | {task['失败级别']} |"
        for task in report["只读复验任务"]
    ]
    return "\n".join(
        [
            "# 稳定交付版首日复验执行与问题回收包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 性质：{report['性质']}",
            f"- 任务数：{report['指标']['只读复验任务数']}",
            "",
            "| ID | 任务 | 类别 | 失败级别 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
            "## 执行边界",
            "",
            "- 只运行本地只读复验和验证脚本。",
            "- 失败只登记问题，不自动改正式规则。",
            "- 涉及红线、服务重载、正式规则变更时登记需总管确认。",
            "",
        ]
    )


def main() -> int:
    plan = {
        "名称": "稳定版首日只读复验执行计划",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务": [
            {
                **task,
                "脚本": str(task["脚本"]) if task["脚本"] else "",
                "验证脚本": str(task["验证脚本"]) if task["验证脚本"] else "",
            }
            for task in READONLY_TASKS
        ],
        "安全边界": SAFETY_BOUNDARY,
    }
    ledger = build_empty_ledger()
    report = {
        "名称": "稳定交付版首日复验执行与问题回收包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_delivery_day1_recheck_issue_intake_ready",
        "性质": "稳定版交付后只读复验与问题回收包，不是正式规则",
        "只读复验任务": plan["任务"],
        "问题回收台账": str(LEDGER_JSON),
        "指标": {
            "只读复验任务数": len(READONLY_TASKS),
            "安全边界关闭项": len(SAFETY_BOUNDARY),
        },
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "执行计划JSON": str(PLAN_JSON),
            "问题回收台账JSON": str(LEDGER_JSON),
            "问题回收台账Markdown": str(LEDGER_MD),
        },
    }
    write_json(PLAN_JSON, plan)
    write_json(LEDGER_JSON, ledger)
    write_text(LEDGER_MD, build_ledger_md(ledger))
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "任务数": len(READONLY_TASKS), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
