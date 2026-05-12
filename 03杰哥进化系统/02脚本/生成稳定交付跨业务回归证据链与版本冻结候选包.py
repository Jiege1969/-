# -*- coding: utf-8 -*-
"""生成稳定交付跨业务回归证据链与版本冻结候选包。

本包只形成候选证据链和冻结条件，不写正式规则，不修改运行配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "53稳定交付跨业务回归证据链与版本冻结候选包"
LATEST_JSON = OUTPUT_DIR / "稳定交付跨业务回归证据链与版本冻结候选包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付跨业务回归证据链与版本冻结候选包_最新.md"
EVIDENCE_MD = OUTPUT_DIR / "跨业务回归证据链_最新.md"
FREEZE_MD = OUTPUT_DIR / "稳定交付版本冻结候选条件_最新.md"
ROLLBACK_MD = OUTPUT_DIR / "版本冻结候选回退说明_最新.md"


EVIDENCE_CHAIN: list[dict[str, Any]] = [
    {
        "编号": "SFE-001",
        "业务线": "企业微信公共接入层",
        "证据名称": "公共入口日常只读巡检",
        "证据路径": str(ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置" / "03数据" / "15日常可用版只读巡检包" / "企业微信公共接入层日常只读巡检_最新.json"),
        "冻结口径": "19310 在线，税收三条通过，职责分流通过，real_send=false，触发n8n=false。",
    },
    {
        "编号": "SFE-002",
        "业务线": "税收业务",
        "证据名称": "工作秘书税收新链路三样本",
        "证据路径": str(ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置" / "03数据" / "15日常可用版只读巡检包" / "企业微信公共接入层日常只读巡检_最新.json"),
        "冻结口径": "三条税收输入均返回待复核草案摘要，事项识别分别正确，不生成正式税务结论。",
    },
    {
        "编号": "SFE-003",
        "业务线": "股票研究系统",
        "证据名称": "股票展示口径一致性验收",
        "证据路径": str(ROOT / "02杰哥扩展系统" / "01股票研究系统" / "03数据" / "246展示口径修复" / "股票展示口径一致性验收_最新.json"),
        "冻结口径": "无推荐/回避冲突，无交易化表达残留，不接券商、不交易。",
    },
    {
        "编号": "SFE-004",
        "业务线": "股票研究系统",
        "证据名称": "股票第九批低风险影子验收",
        "证据路径": str(ROOT / "02杰哥扩展系统" / "01股票研究系统" / "03数据" / "245L3评分基础资产" / "股票线第九批统一影子验收总表验收结果_最新.json"),
        "冻结口径": "低风险候选资产通过影子验收，real_system_triggered=false。",
    },
    {
        "编号": "SFE-005",
        "业务线": "视频制作系统",
        "证据名称": "视频制作系统状态摘要验收",
        "证据路径": str(ROOT / "02杰哥扩展系统" / "02视频制作系统" / "04日志" / "video-production-system-status-summary-verify-最新.json"),
        "冻结口径": "脚本/分镜/人工复核/放行前检查状态可读，状态摘要验收失败=0。",
    },
    {
        "编号": "SFE-006",
        "业务线": "视频制作系统",
        "证据名称": "视频真实渲染禁用态检查",
        "证据路径": str(ROOT / "02杰哥扩展系统" / "02视频制作系统" / "03数据" / "08本地整理门禁" / "视频真实渲染禁用态检查_最新.json"),
        "冻结口径": "真实渲染与自动发布保持禁用态，不调用剪辑软件，不生成真实媒体。",
    },
    {
        "编号": "SFE-007",
        "业务线": "智能进化候选层",
        "证据名称": "日常可用交付版一键只读总回归验收",
        "证据路径": str(EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json"),
        "冻结口径": "总回归 11/11 通过，错误数=0。",
    },
    {
        "编号": "SFE-008",
        "业务线": "智能进化候选层",
        "证据名称": "稳定交付失败自动分级闸口验收",
        "证据路径": str(EVOLUTION_ROOT / "04日志" / "稳定交付失败自动分级与总管确认闸口包验收" / "stable-delivery-failure-gate-package-verify-最新.json"),
        "冻结口径": "L0-L5 分级完整，L3-L5 需总管确认，当前评估 L0。",
    },
    {
        "编号": "SFE-009",
        "业务线": "智能进化候选层",
        "证据名称": "日常运行台账与交接验收包验收",
        "证据路径": str(EVOLUTION_ROOT / "04日志" / "稳定交付日常运行台账与交接验收包验收" / "stable-delivery-daily-ledger-handoff-package-verify-最新.json"),
        "冻结口径": "日常检查、交接清单、异常记录字段齐备并通过只读汇总。",
    },
]


FREEZE_CONDITIONS = [
    "跨业务证据链全部存在且当前只读汇总通过。",
    "日常可用交付版一键只读总回归通过，失败=0。",
    "企业微信公共入口保持 real_send=false、触发n8n=false。",
    "股票侧仍不接券商、不交易、无交易化表达残留。",
    "税收侧仍只输出待复核草案摘要，不生成正式税务结论。",
    "视频侧真实渲染和真实发布仍保持 blocked。",
    "进化侧仅为候选，不自动转正式规则。",
    "19310/19302 无未确认重载动作。",
]


ROLLBACK_NOTES = [
    "冻结候选不是正式规则封版；如任一证据链失败，撤回冻结候选状态即可。",
    "如涉及服务运行态异常，只登记需总管确认，不自动重载。",
    "如出现红线风险，停止后续自动施工，保留对应日志和证据链快照。",
    "如只是候选资料缺失，允许重建候选包并复跑只读验收。",
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


def build_evidence_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['业务线']} | {item['证据名称']} | {item['冻结口径']} | {item['证据路径']} |"
        for item in report["跨业务回归证据链"]
    ]
    return "\n".join(["# 跨业务回归证据链", "", "| 编号 | 业务线 | 证据名称 | 冻结口径 | 证据路径 |", "| --- | --- | --- | --- | --- |", *rows, ""])


def build_freeze_md(report: dict[str, Any]) -> str:
    lines = ["# 稳定交付版本冻结候选条件", "", "满足以下条件时，只能标记为“冻结候选”，不能自动变成正式规则封版。", ""]
    lines.extend([f"- {item}" for item in report["冻结候选条件"]])
    return "\n".join(lines)


def build_rollback_md(report: dict[str, Any]) -> str:
    lines = ["# 版本冻结候选回退说明", ""]
    lines.extend([f"- {item}" for item in report["回退说明"]])
    return "\n".join(lines)


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定交付跨业务回归证据链与版本冻结候选包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 证据链条目：{len(report['跨业务回归证据链'])}",
            f"- 冻结候选条件：{len(report['冻结候选条件'])}",
            f"- 回退说明：{len(report['回退说明'])}",
            "",
            "## 输出文件",
            "",
            f"- 跨业务回归证据链：{EVIDENCE_MD}",
            f"- 稳定交付版本冻结候选条件：{FREEZE_MD}",
            f"- 版本冻结候选回退说明：{ROLLBACK_MD}",
            "",
            "## 核心口径",
            "",
            "- 本包只是稳定交付版本冻结候选，不是正式封版。",
            "- 冻结候选必须由证据链支撑，且红线全部保持 false。",
            "- 任一证据链失败，候选状态自动不成立。",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定交付跨业务回归证据链与版本冻结候选包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_delivery_evidence_freeze_candidate_ready",
        "跨业务回归证据链": EVIDENCE_CHAIN,
        "冻结候选条件": FREEZE_CONDITIONS,
        "回退说明": ROLLBACK_NOTES,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "跨业务回归证据链": str(EVIDENCE_MD),
            "稳定交付版本冻结候选条件": str(FREEZE_MD),
            "版本冻结候选回退说明": str(ROLLBACK_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(EVIDENCE_MD, build_evidence_md(report))
    write_text(FREEZE_MD, build_freeze_md(report))
    write_text(ROLLBACK_MD, build_rollback_md(report))
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "证据链": len(EVIDENCE_CHAIN), "冻结条件": len(FREEZE_CONDITIONS), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
