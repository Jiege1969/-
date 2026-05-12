# -*- coding: utf-8 -*-
"""生成稳定候选最终只读总验收与收口回传包。

只聚合已有稳定候选证据，不触发外部系统，不修改正式规则、服务配置、总管面板或一键接续包。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "63稳定候选最终只读总验收与收口回传包"

LATEST_JSON = OUTPUT_DIR / "稳定候选最终只读总验收与收口回传包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定候选最终只读总验收与收口回传包_最新.md"
EVIDENCE_MD = OUTPUT_DIR / "最终只读总验收证据清单_最新.md"
CLOSEOUT_MD = OUTPUT_DIR / "稳定候选收口回传说明_最新.md"
BOUNDARY_MD = OUTPUT_DIR / "最终只读总验收安全边界_最新.md"


EVIDENCE_ITEMS: list[dict[str, Any]] = [
    {
        "编号": "FRA-001",
        "名称": "日常可用交付版一键只读总回归",
        "类别": "日常总回归",
        "路径": str(
            EVOLUTION_ROOT
            / "04日志"
            / "日常可用交付版一键只读总回归验收"
            / "daily-usable-readonly-regression-verify-最新.json"
        ),
        "通过口径": "通过=true，错误数=0。",
    },
    {
        "编号": "FRA-002",
        "名称": "日常可用版自主巡检快照",
        "类别": "自主巡检快照",
        "路径": str(EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"),
        "通过口径": "总体状态=pass，失败=0。",
    },
    {
        "编号": "FRA-003",
        "名称": "稳定候选最终复核与日常版收口声明包验收",
        "类别": "稳定候选最终复核",
        "路径": str(
            EVOLUTION_ROOT
            / "04日志"
            / "稳定候选最终复核与日常版收口声明包验收"
            / "stable-candidate-final-review-daily-closeout-verify-最新.json"
        ),
        "通过口径": "通过=true，错误数=0。",
    },
    {
        "编号": "FRA-004",
        "名称": "稳定版候选最终总索引与收口验收包验收",
        "类别": "最终总索引",
        "路径": str(
            EVOLUTION_ROOT
            / "04日志"
            / "稳定版候选最终总索引与收口验收包验收"
            / "stable-candidate-final-master-index-closeout-verify-最新.json"
        ),
        "通过口径": "通过=true，错误数=0。",
    },
    {
        "编号": "FRA-005",
        "名称": "稳定版候选最终回传与可交付声明包验收",
        "类别": "可交付声明",
        "路径": str(
            EVOLUTION_ROOT
            / "04日志"
            / "稳定版候选最终回传与可交付声明包验收"
            / "stable-candidate-final-delivery-statement-verify-最新.json"
        ),
        "通过口径": "通过=true，错误数=0。",
    },
    {
        "编号": "FRA-006",
        "名称": "三日巡检当日样本记录",
        "类别": "三日首日样本",
        "路径": str(EVOLUTION_ROOT / "03数据" / "59稳定候选补强与三日巡检启动包" / "三日巡检当日样本记录_最新.json"),
        "通过口径": "当日状态=pass，已记录自然日数>=1；三日达标=false 仅表示首日样本，不作为失败。",
    },
    {
        "编号": "FRA-007",
        "名称": "稳定候选异常样例库与演练包验收",
        "类别": "异常演练",
        "路径": str(
            EVOLUTION_ROOT
            / "04日志"
            / "稳定候选异常样例库与演练包验收"
            / "stable-candidate-exception-samples-drill-verify-最新.json"
        ),
        "通过口径": "通过=true，错误数=0，异常分级覆盖 L1-L5。",
    },
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
    "发布视频": False,
    "转正式规则": False,
    "修改服务配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
}


CLOSEOUT_NOTES = [
    "本包是稳定候选最终只读总验收与收口回传包，只聚合当前已有证据。",
    "当前候选具备日常可用交付版收口、最终总索引、可交付声明、首日巡检样本和异常演练证据。",
    "三日巡检目前只确认首日样本通过，不冒充三日长周期达标。",
    "正式封版、真实外部发送、真实交易、税局登录、财税软件连接、视频真实渲染发布仍需另行授权。",
]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_evidence_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['类别']} | {item['名称']} | {item['通过口径']} | {item['路径']} |"
        for item in report["证据清单"]
    ]
    return "\n".join(
        [
            "# 最终只读总验收证据清单",
            "",
            "| 编号 | 类别 | 名称 | 通过口径 | 路径 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def build_closeout_md(report: dict[str, Any]) -> str:
    lines = [
        "# 稳定候选收口回传说明",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 状态：{report['状态']}",
        f"- 证据数量：{len(report['证据清单'])}",
        "",
        "## 收口口径",
        "",
    ]
    lines.extend(f"- {item}" for item in report["收口说明"])
    lines.extend(
        [
            "",
            "## 回传结论",
            "",
            "- 可作为稳定候选最终只读验收材料回传。",
            "- 不转正式规则，不执行真实外部动作，不重载服务。",
        ]
    )
    return "\n".join(lines)


def build_boundary_md(report: dict[str, Any]) -> str:
    rows = [f"| {name} | {value} |" for name, value in report["安全边界"].items()]
    return "\n".join(["# 最终只读总验收安全边界", "", "| 项目 | 状态 |", "| --- | --- |", *rows, ""])


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定候选最终只读总验收与收口回传包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 证据数量：{len(report['证据清单'])}",
            "",
            "## 输出文件",
            "",
            f"- 总包 JSON：{LATEST_JSON}",
            f"- 总包 Markdown：{LATEST_MD}",
            f"- 证据清单：{EVIDENCE_MD}",
            f"- 收口回传说明：{CLOSEOUT_MD}",
            f"- 安全边界：{BOUNDARY_MD}",
            "",
            "## 稳定候选结论",
            "",
            "- 当前包只读聚合日常总回归、自主巡检快照、最终复核、最终总索引、可交付声明、三日首日样本和异常演练。",
            "- 后续仍需通过只读核对与验收验证脚本确认错误数为 0。",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定候选最终只读总验收与收口回传包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_candidate_final_readonly_acceptance_closeout_ready",
        "证据清单": EVIDENCE_ITEMS,
        "收口说明": CLOSEOUT_NOTES,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "证据清单": str(EVIDENCE_MD),
            "收口回传说明": str(CLOSEOUT_MD),
            "安全边界": str(BOUNDARY_MD),
        },
    }

    write_json(LATEST_JSON, report)
    write_text(EVIDENCE_MD, build_evidence_md(report))
    write_text(CLOSEOUT_MD, build_closeout_md(report))
    write_text(BOUNDARY_MD, build_boundary_md(report))
    write_text(LATEST_MD, build_summary_md(report))

    print(json.dumps({"状态": report["状态"], "证据数量": len(EVIDENCE_ITEMS), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
