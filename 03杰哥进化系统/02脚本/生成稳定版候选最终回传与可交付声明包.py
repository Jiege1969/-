# -*- coding: utf-8 -*-
"""生成稳定版候选最终回传与可交付声明包。

本包只生成稳定版候选交付声明，不执行正式封版，不修改正式规则或运行配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "58稳定版候选最终回传与可交付声明包"
LATEST_JSON = OUTPUT_DIR / "稳定版候选最终回传与可交付声明包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版候选最终回传与可交付声明包_最新.md"
DELIVERY_MD = OUTPUT_DIR / "稳定版候选可交付声明_最新.md"
FINAL_RETURN_MD = OUTPUT_DIR / "稳定版候选最终回传_最新.md"
USER_NOTICE_MD = OUTPUT_DIR / "稳定版使用者注意事项_最新.md"


CORE_EVIDENCE = [
    {
        "名称": "稳定版封版候选总验收与剩余缺口清单",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定版封版候选总验收与剩余缺口清单验收" / "stable-release-freeze-candidate-acceptance-verify-最新.json"),
        "要求": "通过=true，错误数=0，证据失败=0。",
    },
    {
        "名称": "稳定版最终候选索引与接续包",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定版最终候选索引与接续包验收" / "stable-final-candidate-index-continue-verify-最新.json"),
        "要求": "通过=true，错误数=0，索引缺失=0。",
    },
    {
        "名称": "日常可用交付版一键只读总回归",
        "路径": str(EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json"),
        "要求": "通过=true，错误数=0，总数=11，失败=0。",
    },
    {
        "名称": "日常可用版自主巡检快照",
        "路径": str(EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"),
        "要求": "总体状态=pass，失败=0。",
    },
    {
        "名称": "使用者交付摘要与非技术操作手册",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定交付使用者交付摘要与非技术操作手册包验收" / "stable-delivery-user-handoff-manual-verify-最新.json"),
        "要求": "通过=true，错误数=0。",
    },
]


DELIVERY_STATEMENT = {
    "声明级别": "稳定版候选可交付",
    "声明含义": "当前系统具备本地参谋、预演、只读验收、异常定位、复跑队列、交接说明等稳定交付候选能力。",
    "不代表": [
        "不代表正式封版。",
        "不代表真正自主运行。",
        "不代表真实企业微信发送、n8n 编排、券商交易、税局/财税软件接入、视频真实渲染/发布已开放。",
    ],
    "适合使用": [
        "日常本地问答预演。",
        "税收待复核草案摘要。",
        "股票研究和风险复核展示。",
        "视频脚本/分镜/放行前检查。",
        "进化候选、只读验收和稳定交付资料维护。",
    ],
}


REMAINING_LIMITS = [
    "19310/19302 重载仍需总管确认。",
    "长周期自然日巡检样本仍未达标，当前只是趋势机制建立。",
    "视频真实渲染环境未识别，真实发布仍阻断。",
    "税收不接税局和财税软件，不生成正式税务结论。",
    "股票不接券商、不交易。",
    "进化候选不自动转正式规则。",
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


def build_delivery_md(report: dict[str, Any]) -> str:
    statement = report["可交付声明"]
    lines = [
        "# 稳定版候选可交付声明",
        "",
        f"- 声明级别：{statement['声明级别']}",
        f"- 声明含义：{statement['声明含义']}",
        "",
        "## 不代表",
        "",
    ]
    lines.extend([f"- {item}" for item in statement["不代表"]])
    lines.extend(["", "## 适合使用", ""])
    lines.extend([f"- {item}" for item in statement["适合使用"]])
    return "\n".join(lines)


def build_final_return_md(report: dict[str, Any]) -> str:
    rows = [f"| {item['名称']} | {item['要求']} | {item['路径']} |" for item in report["核心证据"]]
    return "\n".join(
        [
            "# 稳定版候选最终回传",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            "",
            "| 核心证据 | 要求 | 路径 |",
            "| --- | --- | --- |",
            *rows,
            "",
            "## 结论",
            "",
            "- 稳定版候选可交付声明可以成立，但不是正式封版。",
            "- 红线保持关闭，正式规则变更仍需总管确认。",
        ]
    )


def build_user_notice_md(report: dict[str, Any]) -> str:
    lines = ["# 稳定版使用者注意事项", "", "当前版本适合作为本地智能参谋和预演系统使用。", "", "## 仍有限制", ""]
    lines.extend([f"- {item}" for item in report["剩余限制"]])
    lines.extend(["", "## 使用建议", "", "- 每次阶段施工后先看一键只读总回归和自主巡检快照。", "- 出现 L3-L5 级别问题时停止，等待总管确认。"])
    return "\n".join(lines)


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版候选最终回传与可交付声明包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 核心证据：{len(report['核心证据'])}",
            f"- 剩余限制：{len(report['剩余限制'])}",
            "",
            "## 输出文件",
            "",
            f"- 稳定版候选可交付声明：{DELIVERY_MD}",
            f"- 稳定版候选最终回传：{FINAL_RETURN_MD}",
            f"- 稳定版使用者注意事项：{USER_NOTICE_MD}",
            "",
            "## 核心口径",
            "",
            "- 这是稳定版候选可交付声明，不是正式封版。",
            "- 不修改总管面板、不修改一键接续包、不写正式规则。",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定版候选最终回传与可交付声明包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_candidate_final_delivery_statement_ready",
        "核心证据": CORE_EVIDENCE,
        "可交付声明": DELIVERY_STATEMENT,
        "剩余限制": REMAINING_LIMITS,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "稳定版候选可交付声明": str(DELIVERY_MD),
            "稳定版候选最终回传": str(FINAL_RETURN_MD),
            "稳定版使用者注意事项": str(USER_NOTICE_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(DELIVERY_MD, build_delivery_md(report))
    write_text(FINAL_RETURN_MD, build_final_return_md(report))
    write_text(USER_NOTICE_MD, build_user_notice_md(report))
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "核心证据": len(CORE_EVIDENCE), "剩余限制": len(REMAINING_LIMITS), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
