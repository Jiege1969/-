# -*- coding: utf-8 -*-
"""生成稳定版最后收口总回传与候选交付封面包。

只汇总既有只读证据，不触发外部系统，不改正式规则、服务配置、总管面板或一键接续包。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
PACKAGE_DIR = EVOLUTION_ROOT / "03数据" / "67稳定版最后收口总回传与候选交付封面包"

PACKAGE_JSON = PACKAGE_DIR / "稳定版最后收口总回传与候选交付封面包_最新.json"
PACKAGE_MD = PACKAGE_DIR / "稳定版最后收口总回传与候选交付封面包_最新.md"
COVER_MD = PACKAGE_DIR / "稳定版候选交付封面_最新.md"
EVIDENCE_MD = PACKAGE_DIR / "核心验收证据清单_最新.md"
NEXT_ACTION_MD = PACKAGE_DIR / "下一步最小动作_最新.md"
BOUNDARY_MD = PACKAGE_DIR / "只读安全边界_最新.md"


CORE_EVIDENCE: list[dict[str, Any]] = [
    {
        "编号": "COVER-EV-001",
        "名称": "自主巡检快照 33/33",
        "类别": "自主巡检快照",
        "路径": str(EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"),
        "验收口径": "总体状态 pass，汇总总数 33，通过 33，失败 0。",
        "期望": {"总数": 33, "通过": 33, "失败": 0},
    },
    {
        "编号": "COVER-EV-002",
        "名称": "总回归 11/11",
        "类别": "只读总回归",
        "路径": str(EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json"),
        "验收口径": "通过 true，指标总数 11，通过 11，失败 0，错误数 0。",
        "期望": {"总数": 11, "通过": 11, "失败": 0, "错误数": 0},
    },
    {
        "编号": "COVER-EV-003",
        "名称": "稳定候选最终复核",
        "类别": "最终复核",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定候选最终复核与日常版收口声明包验收" / "stable-candidate-final-review-daily-closeout-verify-最新.json"),
        "验收口径": "通过 true，复核失败 0，错误数 0。",
        "期望": {"通过": True, "失败": 0, "错误数": 0},
    },
    {
        "编号": "COVER-EV-004",
        "名称": "最终只读总验收",
        "类别": "最终只读总验收",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定候选最终只读总验收与收口回传包验收" / "stable-candidate-final-readonly-acceptance-closeout-verify-最新.json"),
        "验收口径": "通过 true，核对失败 0，错误数 0。",
        "期望": {"通过": True, "失败": 0, "错误数": 0},
    },
    {
        "编号": "COVER-EV-005",
        "名称": "并行合并验收（第二轮）",
        "类别": "并行合并验收",
        "路径": str(EVOLUTION_ROOT / "04日志" / "第二轮并行施工调度索引与合并验收准备包验收" / "parallel-round2-dispatch-merge-prepare-verify-最新.json"),
        "验收口径": "通过 true，并行任务不少于 3，合并验收项不少于 6，错误数 0。",
        "期望": {"通过": True, "并行任务不少于": 3, "合并验收项不少于": 6, "错误数": 0},
    },
]


AVAILABLE_CAPABILITIES = [
    "日常可用版自主巡检快照已形成 33/33 的通过证据，可作为当前稳定候选健康入口。",
    "一键只读总回归已形成 11/11 的通过证据，可作为交付前快速核对入口。",
    "稳定候选最终复核、最终只读总验收、第二轮并行合并验收均已有只读验收日志。",
    "稳定候选可用于阅读、交接、异常定位、只读复核和下一轮最小动作安排。",
]


BLOCKED_CAPABILITIES = [
    "不正式封版，不转正式规则。",
    "不真实发送企业微信，不触发 n8n。",
    "不连接券商或交易，不登录税局，不接财税软件。",
    "不真实渲染或发布视频。",
    "不重载 19310/19302，不修改服务配置、总管面板或一键接续包。",
]


READING_ENTRIES = [
    {"名称": "候选交付封面", "路径": str(COVER_MD)},
    {"名称": "核心验收证据清单", "路径": str(EVIDENCE_MD)},
    {"名称": "下一步最小动作", "路径": str(NEXT_ACTION_MD)},
    {"名称": "只读安全边界", "路径": str(BOUNDARY_MD)},
    {"名称": "机器可读总包", "路径": str(PACKAGE_JSON)},
]


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录税局": False,
    "接财税软件": False,
    "真实渲染视频": False,
    "发布视频": False,
    "转正式规则": False,
    "正式封版": False,
    "修改服务配置": False,
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


def build_evidence_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['类别']} | {item['名称']} | {item['验收口径']} | {item['路径']} |"
        for item in report["核心验收证据"]
    ]
    return "\n".join(
        [
            "# 核心验收证据清单",
            "",
            "| 编号 | 类别 | 名称 | 验收口径 | 路径 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def build_cover_md(report: dict[str, Any]) -> str:
    lines = [
        "# 稳定版候选交付封面",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 可用能力",
        "",
    ]
    lines.extend(f"- {item}" for item in report["可用能力"])
    lines.extend(["", "## 仍阻断能力", ""])
    lines.extend(f"- {item}" for item in report["仍阻断能力"])
    lines.extend(["", "## 阅读入口", ""])
    lines.extend(f"- {item['名称']}：{item['路径']}" for item in report["阅读入口"])
    lines.extend(["", "## 核心验收证据", ""])
    lines.extend(f"- {item['名称']}：{item['验收口径']}" for item in report["核心验收证据"])
    lines.extend(["", "## 下一步最小动作", ""])
    lines.extend(f"- {item}" for item in report["下一步最小动作"])
    lines.append("")
    return "\n".join(lines)


def build_next_action_md(report: dict[str, Any]) -> str:
    return "\n".join(["# 下一步最小动作", "", *(f"- {item}" for item in report["下一步最小动作"]), ""])


def build_boundary_md(report: dict[str, Any]) -> str:
    rows = [f"| {name} | {value} |" for name, value in report["只读安全边界"].items()]
    return "\n".join(["# 只读安全边界", "", "| 项目 | 状态 |", "| --- | --- |", *rows, ""])


def build_package_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版最后收口总回传与候选交付封面包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 当前结论：{report['当前结论']}",
            f"- 核心验收证据数：{len(report['核心验收证据'])}",
            "",
            "## 输出文件",
            "",
            *(f"- {name}：{path}" for name, path in report["输出文件"].items()),
            "",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定版最后收口总回传与候选交付封面包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_final_closeout_cover_ready",
        "当前结论": "稳定版候选已具备只读证据支撑的候选交付封面，可回传用于阅读、交接和最后收口；仍不代表正式封版或外部真实动作授权。",
        "可用能力": AVAILABLE_CAPABILITIES,
        "仍阻断能力": BLOCKED_CAPABILITIES,
        "阅读入口": READING_ENTRIES,
        "核心验收证据": CORE_EVIDENCE,
        "下一步最小动作": [
            "运行执行稳定版最后收口总回传只读核对.py，确认五项核心证据当前仍为通过。",
            "运行验证稳定版最后收口总回传与候选交付封面包.py，生成 stable-final-closeout-cover-verify-最新.json 且错误数为 0。",
            "由总管阅读候选交付封面与核心证据清单后，再另行决定是否进入正式封版授权流程。",
        ],
        "只读安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "候选交付封面": str(COVER_MD),
            "核心验收证据清单": str(EVIDENCE_MD),
            "下一步最小动作": str(NEXT_ACTION_MD),
            "只读安全边界": str(BOUNDARY_MD),
        },
    }

    write_json(PACKAGE_JSON, report)
    write_text(EVIDENCE_MD, build_evidence_md(report))
    write_text(COVER_MD, build_cover_md(report))
    write_text(NEXT_ACTION_MD, build_next_action_md(report))
    write_text(BOUNDARY_MD, build_boundary_md(report))
    write_text(PACKAGE_MD, build_package_md(report))

    print(json.dumps({"状态": report["状态"], "核心验收证据数": len(CORE_EVIDENCE), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
