# -*- coding: utf-8 -*-
"""生成并行施工调度索引与合并验收准备包。

只记录本轮并行施工的分工、写入边界和合并验收准备，不修改正式规则或服务配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "66并行施工调度索引与合并验收准备包"
LATEST_JSON = OUTPUT_DIR / "并行施工调度索引与合并验收准备包_最新.json"
LATEST_MD = OUTPUT_DIR / "并行施工调度索引与合并验收准备包_最新.md"
DISPATCH_MD = OUTPUT_DIR / "并行施工分工索引_最新.md"
MERGE_MD = OUTPUT_DIR / "并行施工合并验收清单_最新.md"


PARALLEL_TASKS: list[dict[str, Any]] = [
    {
        "编号": "PWT-001",
        "名称": "稳定候选最终只读总验收与收口回传包",
        "负责人": "Worker A",
        "数据目录": str(EVOLUTION_ROOT / "03数据" / "63稳定候选最终只读总验收与收口回传包"),
        "验收日志": str(EVOLUTION_ROOT / "04日志" / "稳定候选最终只读总验收与收口回传包验收" / "stable-candidate-final-readonly-acceptance-closeout-verify-最新.json"),
        "合并条件": "验收通过且错误数=0。",
    },
    {
        "编号": "PWT-002",
        "名称": "完全交付使用版缺口拆解与红线解锁路线图包",
        "负责人": "Worker B",
        "数据目录": str(EVOLUTION_ROOT / "03数据" / "64完全交付使用版缺口拆解与红线解锁路线图包"),
        "验收日志": str(EVOLUTION_ROOT / "04日志" / "完全交付使用版缺口拆解与红线解锁路线图包验收" / "验证完全交付使用版缺口拆解与红线解锁路线图包_最新.json"),
        "合并条件": "验收通过且错误数=0；不得开放红线。",
    },
    {
        "编号": "PWT-003",
        "名称": "三日巡检续跑准备与自然日样本模板包",
        "负责人": "Worker C",
        "数据目录": str(EVOLUTION_ROOT / "03数据" / "65三日巡检续跑准备与自然日样本模板包"),
        "验收日志": str(EVOLUTION_ROOT / "04日志" / "三日巡检续跑准备与自然日样本模板包验收" / "three-day-patrol-rerun-template-verify-最新.json"),
        "合并条件": "验收通过且错误数=0；不得伪造第2/3自然日样本。",
    },
]


MERGE_CHECKS = [
    "三个 worker 只写各自分配目录和脚本。",
    "三个验收日志均存在且通过。",
    "并行产物不修改总管面板、不修改一键接续包、不修改服务配置。",
    "并行产物不重载 19310/19302。",
    "并行产物不触发真实外部动作。",
    "主控统一接入自主巡检快照后复跑一键只读总回归。",
]


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "触发n8n": False,
    "接n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "生成正式税务结论": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
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


def build_dispatch_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['名称']} | {item['负责人']} | {item['数据目录']} | {item['验收日志']} |"
        for item in report["并行任务"]
    ]
    return "\n".join(["# 并行施工分工索引", "", "| 编号 | 名称 | 负责人 | 数据目录 | 验收日志 |", "| --- | --- | --- | --- | --- |", *rows, ""])


def build_merge_md(report: dict[str, Any]) -> str:
    lines = ["# 并行施工合并验收清单", ""]
    lines.extend([f"- {item}" for item in report["合并验收项"]])
    return "\n".join(lines)


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 并行施工调度索引与合并验收准备包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 并行任务：{len(report['并行任务'])}",
            f"- 合并验收项：{len(report['合并验收项'])}",
            "",
            "## 输出文件",
            "",
            f"- 并行施工分工索引：{DISPATCH_MD}",
            f"- 并行施工合并验收清单：{MERGE_MD}",
            "",
            "## 核心口径",
            "",
            "- worker 并行施工，主控统一合并验收。",
            "- 不让 worker 修改共享快照脚本，避免冲突。",
        ]
    )


def main() -> int:
    report = {
        "名称": "并行施工调度索引与合并验收准备包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "parallel_work_dispatch_merge_prepare_ready",
        "并行任务": PARALLEL_TASKS,
        "合并验收项": MERGE_CHECKS,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "并行施工分工索引": str(DISPATCH_MD),
            "并行施工合并验收清单": str(MERGE_MD),
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
