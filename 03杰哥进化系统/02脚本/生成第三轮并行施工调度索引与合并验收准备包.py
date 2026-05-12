# -*- coding: utf-8 -*-
"""生成第三轮并行施工调度索引与合并验收准备包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "74第三轮并行施工调度索引与合并验收准备包"
LATEST_JSON = OUTPUT_DIR / "第三轮并行施工调度索引与合并验收准备包_最新.json"
LATEST_MD = OUTPUT_DIR / "第三轮并行施工调度索引与合并验收准备包_最新.md"
DISPATCH_MD = OUTPUT_DIR / "第三轮并行施工分工索引_最新.md"
MERGE_MD = OUTPUT_DIR / "第三轮并行施工合并验收清单_最新.md"


PARALLEL_TASKS = [
    {
        "编号": "P3W-001",
        "名称": "稳定版候选正式封版申请草案与最终交付封面收紧包",
        "负责人": "Worker G",
        "数据目录": str(EVOLUTION_ROOT / "03数据" / "71稳定版候选正式封版申请草案与最终交付封面收紧包"),
        "验收日志": str(EVOLUTION_ROOT / "04日志" / "稳定版候选正式封版申请草案与最终交付封面收紧包验收" / "stable-candidate-formal-freeze-request-draft-verify-最新.json"),
        "合并条件": "验收通过且错误数=0；不得正式封版。",
    },
    {
        "编号": "P3W-002",
        "名称": "完全交付低风险模板落地包",
        "负责人": "Worker H",
        "数据目录": str(EVOLUTION_ROOT / "03数据" / "72完全交付低风险模板落地包"),
        "验收日志": str(EVOLUTION_ROOT / "04日志" / "完全交付低风险模板落地包验收" / "full-delivery-low-risk-template-landing-verify-最新.json"),
        "合并条件": "验收通过且错误数=0；模板红线=false。",
    },
    {
        "编号": "P3W-003",
        "名称": "三日巡检第2天待执行链路与防伪检查包",
        "负责人": "Worker I",
        "数据目录": str(EVOLUTION_ROOT / "03数据" / "73三日巡检第2天待执行链路与防伪检查包"),
        "验收日志": str(EVOLUTION_ROOT / "04日志" / "三日巡检第2天待执行链路与防伪检查包验收" / "three-day-patrol-day2-pending-chain-verify-最新.json"),
        "合并条件": "验收通过且错误数=0；不得生成第2/3天样本。",
    },
]


MERGE_CHECKS = [
    "三个 worker 只写各自分配目录和脚本。",
    "三个验收日志均存在且通过。",
    "不修改总管面板、一键接续包、服务配置。",
    "不重载 19310/19302。",
    "不触发真实外部动作，不开放红线。",
    "主控统一接入自主巡检快照后复跑一键只读总回归。",
]


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
    "正式封版": False,
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_dispatch_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['名称']} | {item['负责人']} | {item['数据目录']} | {item['验收日志']} |"
        for item in report["并行任务"]
    ]
    return "\n".join(["# 第三轮并行施工分工索引", "", "| 编号 | 名称 | 负责人 | 数据目录 | 验收日志 |", "| --- | --- | --- | --- | --- |", *rows, ""])


def build_merge_md(report: dict[str, Any]) -> str:
    lines = ["# 第三轮并行施工合并验收清单", ""]
    lines.extend([f"- {item}" for item in report["合并验收项"]])
    return "\n".join(lines)


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 第三轮并行施工调度索引与合并验收准备包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 并行任务：{len(report['并行任务'])}",
            f"- 合并验收项：{len(report['合并验收项'])}",
            "",
            f"- 分工索引：{DISPATCH_MD}",
            f"- 合并验收清单：{MERGE_MD}",
        ]
    )


def main() -> int:
    report = {
        "名称": "第三轮并行施工调度索引与合并验收准备包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "parallel_round3_dispatch_merge_prepare_ready",
        "并行任务": PARALLEL_TASKS,
        "合并验收项": MERGE_CHECKS,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "第三轮并行施工分工索引": str(DISPATCH_MD),
            "第三轮并行施工合并验收清单": str(MERGE_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(DISPATCH_MD, build_dispatch_md(report))
    write_text(MERGE_MD, build_merge_md(report))
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "并行任务": len(PARALLEL_TASKS), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
