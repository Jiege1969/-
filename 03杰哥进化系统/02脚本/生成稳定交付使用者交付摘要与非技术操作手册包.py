# -*- coding: utf-8 -*-
"""生成稳定交付使用者交付摘要与非技术操作手册包。

只生成面向使用者的候选交付资料，不修改总管面板或一键接续包。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "56稳定交付使用者交付摘要与非技术操作手册包"
LATEST_JSON = OUTPUT_DIR / "稳定交付使用者交付摘要与非技术操作手册包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付使用者交付摘要与非技术操作手册包_最新.md"
USER_SUMMARY_MD = OUTPUT_DIR / "使用者交付摘要_最新.md"
MANUAL_MD = OUTPUT_DIR / "非技术操作手册_最新.md"
DO_DONT_MD = OUTPUT_DIR / "使用者可做与不可做清单_最新.md"
STATUS_CARD_MD = OUTPUT_DIR / "当前系统状态卡_最新.md"


CAPABILITIES: list[dict[str, Any]] = [
    {
        "模块": "企业微信公共接入层",
        "你能做什么": "通过本地接口预演系统管家、工作秘书、视频助理的回复和职责分流。",
        "你会看到什么": "系统状态、税收待复核草案摘要、股票转交提示、视频阻断提示等。",
        "当前限制": "不会真实发给企业微信联系人或群，不触发 n8n。",
    },
    {
        "模块": "税收业务",
        "你能做什么": "输入税收业务问题，获得待复核草案摘要、事项识别和资料方向。",
        "你会看到什么": "标题为【税收分析助手-待复核草案摘要】的内容。",
        "当前限制": "不登录税局、不接财税软件、不生成正式税务结论。",
    },
    {
        "模块": "股票研究",
        "你能做什么": "查看研究价值、风险复核、图文报告和前台展示结果。",
        "你会看到什么": "研究价值评分、当前操作建议、风险复核信号等非交易化表达。",
        "当前限制": "不接券商、不交易、不下单、不做仓位动作。",
    },
    {
        "模块": "视频制作",
        "你能做什么": "生成或查看脚本草案、分镜草案、人工复核、放行前检查。",
        "你会看到什么": "真实渲染和真实发布 blocked 的预检结果。",
        "当前限制": "不真实渲染成片，不自动上传发布。",
    },
    {
        "模块": "智能进化候选",
        "你能做什么": "让系统沉淀候选经验、只读验收建议和封版候选资料。",
        "你会看到什么": "候选包、验收日志、进度校准、稳定交付支撑资料。",
        "当前限制": "不会自动转正式规则，不会自己修改运行配置。",
    },
]


USER_WORKFLOWS: list[dict[str, Any]] = [
    {
        "场景": "看今天系统能不能用",
        "使用方式": "查看日常可用交付版一键只读总回归和自主巡检快照。",
        "通过口径": "总回归 11/11 通过，自主快照失败=0。",
        "如果失败": "按失败分级包处理；L3-L5 停止并等总管确认。",
    },
    {
        "场景": "问税收问题",
        "使用方式": "用工作秘书输入“税收业务：...”格式的问题。",
        "通过口径": "返回待复核草案摘要，事项识别正确。",
        "如果失败": "先看公共入口巡检和税收新链路三样本，不直接改税收判断。",
    },
    {
        "场景": "看股票研究",
        "使用方式": "查看股票分析/图文报告/企业微信短回复产物。",
        "通过口径": "无重点推荐、常规推荐、买入信号、加仓减仓等交易化词。",
        "如果失败": "只修展示层，不能改评分引擎和推荐名单生成逻辑。",
    },
    {
        "场景": "推进视频任务",
        "使用方式": "看脚本、分镜、人工复核、生成放行、发布预检。",
        "通过口径": "真实渲染和真实发布保持 blocked，阻断原因清楚。",
        "如果失败": "不得真实渲染或发布，只补预检和放行链复核。",
    },
    {
        "场景": "继续自主搭建",
        "使用方式": "只推进候选包、只读验收、低风险展示层修复和文档化支撑。",
        "通过口径": "红线全部 false，总回归通过。",
        "如果失败": "触碰服务重载、正式规则或真实外部动作时立即停下汇报。",
    },
]


DO_LIST = [
    "可以查看待复核草案、研究报告、预检结果和只读验收。",
    "可以让系统继续生成候选包、交接资料、异常恢复资料。",
    "可以复跑只读巡检和只读总回归。",
    "可以把失败回传交给总管判断通过/未通过/需总管确认。",
]


DONT_LIST = [
    "不要把候选包当成正式规则。",
    "不要要求系统自行重载 19310/19302。",
    "不要让系统真实发送企业微信或触发 n8n。",
    "不要让系统接券商、交易、登录税局、接财税软件。",
    "不要让系统真实渲染或自动发布视频。",
]


STATUS_CARD = {
    "日常可用交付版": "候选基本可用，仍需少量收口样本。",
    "稳定交付版": "稳定版封版候选已成立，仍需长周期自然日样本。",
    "完全交付使用版": "仍受真实外部动作、视频生产、税务/财务真实数据接入限制。",
    "真正自主运行版": "红线保持期间不会高估，仍属于远期目标。",
}


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


def build_user_summary(report: dict[str, Any]) -> str:
    lines = ["# 使用者交付摘要", "", "这套系统当前适合当作“本地智能参谋与多业务预演系统”使用，而不是无人值守外部执行系统。", ""]
    for item in report["能力摘要"]:
        lines.extend(
            [
                f"## {item['模块']}",
                "",
                f"- 你能做什么：{item['你能做什么']}",
                f"- 你会看到什么：{item['你会看到什么']}",
                f"- 当前限制：{item['当前限制']}",
                "",
            ]
        )
    return "\n".join(lines)


def build_manual(report: dict[str, Any]) -> str:
    lines = ["# 非技术操作手册", "", "按场景使用，不需要理解脚本细节。", ""]
    for item in report["使用场景"]:
        lines.extend(
            [
                f"## {item['场景']}",
                "",
                f"- 使用方式：{item['使用方式']}",
                f"- 通过口径：{item['通过口径']}",
                f"- 如果失败：{item['如果失败']}",
                "",
            ]
        )
    return "\n".join(lines)


def build_do_dont(report: dict[str, Any]) -> str:
    lines = ["# 使用者可做与不可做清单", "", "## 可以做", ""]
    lines.extend([f"- {item}" for item in report["可以做"]])
    lines.extend(["", "## 不可以做", ""])
    lines.extend([f"- {item}" for item in report["不可以做"]])
    return "\n".join(lines)


def build_status_card(report: dict[str, Any]) -> str:
    lines = ["# 当前系统状态卡", ""]
    for key, value in report["状态卡"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines)


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定交付使用者交付摘要与非技术操作手册包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 能力摘要：{len(report['能力摘要'])}",
            f"- 使用场景：{len(report['使用场景'])}",
            f"- 可以做：{len(report['可以做'])}",
            f"- 不可以做：{len(report['不可以做'])}",
            "",
            "## 输出文件",
            "",
            f"- 使用者交付摘要：{USER_SUMMARY_MD}",
            f"- 非技术操作手册：{MANUAL_MD}",
            f"- 使用者可做与不可做清单：{DO_DONT_MD}",
            f"- 当前系统状态卡：{STATUS_CARD_MD}",
            "",
            "## 核心口径",
            "",
            "- 面向使用者说明当前体验，不承诺尚未开放的真实外部执行能力。",
            "- 本包不修改总管面板、不修改一键接续包。",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定交付使用者交付摘要与非技术操作手册包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_delivery_user_handoff_manual_candidate_ready",
        "能力摘要": CAPABILITIES,
        "使用场景": USER_WORKFLOWS,
        "可以做": DO_LIST,
        "不可以做": DONT_LIST,
        "状态卡": STATUS_CARD,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "使用者交付摘要": str(USER_SUMMARY_MD),
            "非技术操作手册": str(MANUAL_MD),
            "使用者可做与不可做清单": str(DO_DONT_MD),
            "当前系统状态卡": str(STATUS_CARD_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(USER_SUMMARY_MD, build_user_summary(report))
    write_text(MANUAL_MD, build_manual(report))
    write_text(DO_DONT_MD, build_do_dont(report))
    write_text(STATUS_CARD_MD, build_status_card(report))
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "能力摘要": len(CAPABILITIES), "使用场景": len(USER_WORKFLOWS), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
