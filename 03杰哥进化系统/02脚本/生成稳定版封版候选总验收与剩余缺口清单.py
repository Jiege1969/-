# -*- coding: utf-8 -*-
"""生成稳定版封版候选总验收与剩余缺口清单。

本包只形成稳定版封版候选验收资料，不写正式规则，不修改运行配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "54稳定版封版候选总验收与剩余缺口清单"
LATEST_JSON = OUTPUT_DIR / "稳定版封版候选总验收与剩余缺口清单_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版封版候选总验收与剩余缺口清单_最新.md"
ACCEPTANCE_MD = OUTPUT_DIR / "稳定版封版候选总验收清单_最新.md"
GAPS_MD = OUTPUT_DIR / "稳定版剩余缺口清单_最新.md"
NEXT_MD = OUTPUT_DIR / "稳定版后续施工建议_最新.md"


ACCEPTANCE_EVIDENCE: list[dict[str, Any]] = [
    {
        "编号": "SFA-001",
        "名称": "自主巡检快照",
        "路径": str(EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"),
        "通过口径": "总体状态=pass，失败=0。",
    },
    {
        "编号": "SFA-002",
        "名称": "日常可用交付版一键只读总回归验收",
        "路径": str(EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json"),
        "通过口径": "通过=true，错误数=0，总数=11，失败=0。",
    },
    {
        "编号": "SFA-003",
        "名称": "稳定交付异常恢复与日志索引包验收",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定交付异常恢复与日志索引包验收" / "stable-delivery-recovery-log-index-verify-最新.json"),
        "通过口径": "通过=true，错误数=0。",
    },
    {
        "编号": "SFA-004",
        "名称": "稳定交付异常复跑队列与低风险自动续建包验收",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定交付异常复跑队列与低风险自动续建包验收" / "stable-delivery-rerun-rebuild-package-verify-最新.json"),
        "通过口径": "通过=true，错误数=0，复跑失败数=0。",
    },
    {
        "编号": "SFA-005",
        "名称": "稳定交付失败自动分级与总管确认闸口包验收",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定交付失败自动分级与总管确认闸口包验收" / "stable-delivery-failure-gate-package-verify-最新.json"),
        "通过口径": "通过=true，错误数=0，当前失败级别=L0。",
    },
    {
        "编号": "SFA-006",
        "名称": "稳定交付日常运行台账与交接验收包验收",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定交付日常运行台账与交接验收包验收" / "stable-delivery-daily-ledger-handoff-package-verify-最新.json"),
        "通过口径": "通过=true，错误数=0，只读汇总失败=0。",
    },
    {
        "编号": "SFA-007",
        "名称": "稳定交付跨业务回归证据链与版本冻结候选包验收",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定交付跨业务回归证据链与版本冻结候选包验收" / "stable-delivery-evidence-freeze-candidate-verify-最新.json"),
        "通过口径": "通过=true，错误数=0，证据链失败=0。",
    },
    {
        "编号": "SFA-008",
        "名称": "最终日常可用交付候选回传验收",
        "路径": str(EVOLUTION_ROOT / "04日志" / "最终日常可用交付候选回传验收" / "final-daily-usable-delivery-candidate-verify-最新.json"),
        "通过口径": "通过=true，错误数=0。",
    },
    {
        "编号": "SFA-009",
        "名称": "企业微信公共入口日常巡检",
        "路径": str(ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置" / "03数据" / "15日常可用版只读巡检包" / "企业微信公共接入层日常只读巡检_最新.json"),
        "通过口径": "总体状态=pass，real_send=false，触发n8n=false。",
    },
]


REMAINING_GAPS: list[dict[str, Any]] = [
    {
        "编号": "SGP-001",
        "缺口": "19310/19302 服务重载仍需人工确认",
        "影响": "稳定版可控，但无法做到无人值守自恢复。",
        "当前处理": "已有重载申请模板和确认闸口。",
        "是否阻断稳定版候选": False,
    },
    {
        "编号": "SGP-002",
        "缺口": "n8n 真实触发关闭",
        "影响": "不能自动编排跨系统动作。",
        "当前处理": "检查项可读，真实触发关闭。",
        "是否阻断稳定版候选": False,
    },
    {
        "编号": "SGP-003",
        "缺口": "视频真实渲染环境未识别",
        "影响": "不能交付自动成片和自动发布。",
        "当前处理": "真实渲染/发布保持 blocked。",
        "是否阻断稳定版候选": False,
    },
    {
        "编号": "SGP-004",
        "缺口": "税收不接税局和财税软件",
        "影响": "不能基于真实账套/申报数据做正式判断。",
        "当前处理": "只输出待复核草案摘要。",
        "是否阻断稳定版候选": False,
    },
    {
        "编号": "SGP-005",
        "缺口": "股票不接券商、不交易",
        "影响": "只能研究分析和风险复核，不能自动交易。",
        "当前处理": "展示口径已去交易化。",
        "是否阻断稳定版候选": False,
    },
    {
        "编号": "SGP-006",
        "缺口": "进化候选不自动转正式规则",
        "影响": "系统会总结经验，但正式能力提升仍需人工确认。",
        "当前处理": "候选与正式规则隔离。",
        "是否阻断稳定版候选": False,
    },
    {
        "编号": "SGP-007",
        "缺口": "缺少长周期压力运行样本",
        "影响": "稳定版候选已具备证据链，但还需要更多自然日样本提高置信度。",
        "当前处理": "已有日常台账、总回归和异常分级。",
        "是否阻断稳定版候选": False,
    },
]


NEXT_ACTIONS = [
    "继续补长周期只读巡检样本，把 1 天样本扩展到 3-7 天样本。",
    "继续补业务线异常样例库，覆盖公共入口、税收、股票、视频、进化候选。",
    "继续补稳定版使用者交接摘要，减少依赖开发者解释。",
    "继续保持真实外部动作关闭，直到明确进入单项红线评审。",
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
    "请求19302业务接口": False,
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_acceptance_md(report: dict[str, Any]) -> str:
    rows = [f"| {item['编号']} | {item['名称']} | {item['通过口径']} | {item['路径']} |" for item in report["总验收证据"]]
    return "\n".join(["# 稳定版封版候选总验收清单", "", "| 编号 | 名称 | 通过口径 | 路径 |", "| --- | --- | --- | --- |", *rows, ""])


def build_gaps_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['缺口']} | {item['影响']} | {item['当前处理']} | {item['是否阻断稳定版候选']} |"
        for item in report["剩余缺口"]
    ]
    return "\n".join(["# 稳定版剩余缺口清单", "", "| 编号 | 缺口 | 影响 | 当前处理 | 阻断稳定版候选 |", "| --- | --- | --- | --- | --- |", *rows, ""])


def build_next_md(report: dict[str, Any]) -> str:
    lines = ["# 稳定版后续施工建议", ""]
    lines.extend([f"- {item}" for item in report["后续施工建议"]])
    return "\n".join(lines)


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版封版候选总验收与剩余缺口清单",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 总验收证据：{len(report['总验收证据'])}",
            f"- 剩余缺口：{len(report['剩余缺口'])}",
            f"- 后续施工建议：{len(report['后续施工建议'])}",
            "",
            "## 输出文件",
            "",
            f"- 稳定版封版候选总验收清单：{ACCEPTANCE_MD}",
            f"- 稳定版剩余缺口清单：{GAPS_MD}",
            f"- 稳定版后续施工建议：{NEXT_MD}",
            "",
            "## 核心口径",
            "",
            "- 本包是稳定版封版候选，不是正式封版。",
            "- 剩余缺口不阻断当前稳定版候选，但阻断真正自主运行版。",
            "- 所有红线继续保持 false。",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定版封版候选总验收与剩余缺口清单",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_release_freeze_candidate_acceptance_ready",
        "总验收证据": ACCEPTANCE_EVIDENCE,
        "剩余缺口": REMAINING_GAPS,
        "后续施工建议": NEXT_ACTIONS,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "稳定版封版候选总验收清单": str(ACCEPTANCE_MD),
            "稳定版剩余缺口清单": str(GAPS_MD),
            "稳定版后续施工建议": str(NEXT_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(ACCEPTANCE_MD, build_acceptance_md(report))
    write_text(GAPS_MD, build_gaps_md(report))
    write_text(NEXT_MD, build_next_md(report))
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "总验收证据": len(ACCEPTANCE_EVIDENCE), "剩余缺口": len(REMAINING_GAPS), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
