# -*- coding: utf-8 -*-
"""生成稳定版最终候选索引与接续包。

本包只写入 03杰哥进化系统 的候选索引资料，不修改总管面板或原一键接续包。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "57稳定版最终候选索引与接续包"
LATEST_JSON = OUTPUT_DIR / "稳定版最终候选索引与接续包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版最终候选索引与接续包_最新.md"
INDEX_MD = OUTPUT_DIR / "稳定版候选资料总索引_最新.md"
CONTINUE_MD = OUTPUT_DIR / "稳定版后续接续说明_最新.md"
HANDOVER_MD = OUTPUT_DIR / "稳定版交接阅读顺序_最新.md"


PACKAGE_INDEX: list[dict[str, Any]] = [
    {
        "编号": "SFI-001",
        "名称": "最终日常可用交付候选回传",
        "类型": "日常可用收口",
        "路径": str(EVOLUTION_ROOT / "03数据" / "48最终日常可用交付候选回传" / "最终日常可用交付候选回传_最新.md"),
        "作用": "说明日常可用版候选通过情况。",
    },
    {
        "编号": "SFI-002",
        "名称": "稳定交付异常恢复与日志索引包",
        "类型": "异常定位",
        "路径": str(EVOLUTION_ROOT / "03数据" / "49稳定交付异常恢复与日志索引包" / "稳定交付异常恢复与日志索引包_最新.md"),
        "作用": "定位失败先看哪些日志和证据。",
    },
    {
        "编号": "SFI-003",
        "名称": "稳定交付异常复跑队列与低风险自动续建包",
        "类型": "复跑队列",
        "路径": str(EVOLUTION_ROOT / "03数据" / "50稳定交付异常复跑队列与低风险自动续建包" / "稳定交付异常复跑队列与低风险自动续建包_最新.md"),
        "作用": "定义哪些只读验收可自动复跑。",
    },
    {
        "编号": "SFI-004",
        "名称": "稳定交付失败自动分级与总管确认闸口包",
        "类型": "确认闸口",
        "路径": str(EVOLUTION_ROOT / "03数据" / "51稳定交付失败自动分级与总管确认闸口包" / "稳定交付失败自动分级与总管确认闸口包_最新.md"),
        "作用": "区分 L1/L2 可自动处理和 L3-L5 必须汇报。",
    },
    {
        "编号": "SFI-005",
        "名称": "稳定交付日常运行台账与交接验收包",
        "类型": "日常运行",
        "路径": str(EVOLUTION_ROOT / "03数据" / "52稳定交付日常运行台账与交接验收包" / "稳定交付日常运行台账与交接验收包_最新.md"),
        "作用": "给日常值守、交接、异常记录提供模板。",
    },
    {
        "编号": "SFI-006",
        "名称": "稳定交付跨业务回归证据链与版本冻结候选包",
        "类型": "证据链",
        "路径": str(EVOLUTION_ROOT / "03数据" / "53稳定交付跨业务回归证据链与版本冻结候选包" / "稳定交付跨业务回归证据链与版本冻结候选包_最新.md"),
        "作用": "串联企业微信、税收、股票、视频、进化候选的证据链。",
    },
    {
        "编号": "SFI-007",
        "名称": "稳定版封版候选总验收与剩余缺口清单",
        "类型": "封版候选",
        "路径": str(EVOLUTION_ROOT / "03数据" / "54稳定版封版候选总验收与剩余缺口清单" / "稳定版封版候选总验收与剩余缺口清单_最新.md"),
        "作用": "确认稳定版封版候选成立，并列出剩余缺口。",
    },
    {
        "编号": "SFI-008",
        "名称": "稳定交付长周期只读巡检样本与趋势记录包",
        "类型": "趋势样本",
        "路径": str(EVOLUTION_ROOT / "03数据" / "55稳定交付长周期只读巡检样本与趋势记录包" / "稳定交付长周期只读巡检样本与趋势记录包_最新.md"),
        "作用": "建立长周期自然日样本口径，不伪装达标。",
    },
    {
        "编号": "SFI-009",
        "名称": "稳定交付使用者交付摘要与非技术操作手册包",
        "类型": "使用者交付",
        "路径": str(EVOLUTION_ROOT / "03数据" / "56稳定交付使用者交付摘要与非技术操作手册包" / "稳定交付使用者交付摘要与非技术操作手册包_最新.md"),
        "作用": "把技术验收结果翻译成使用者说明。",
    },
]


NEXT_CONTINUATION = [
    {
        "顺序": 1,
        "动作": "先看稳定版候选资料总索引",
        "目标": "确认当前稳定版支撑包是否齐全。",
    },
    {
        "顺序": 2,
        "动作": "复跑日常可用交付版一键只读总回归",
        "目标": "确认 11/11 仍通过。",
    },
    {
        "顺序": 3,
        "动作": "复跑自主巡检快照",
        "目标": "确认所有候选验收仍失败=0。",
    },
    {
        "顺序": 4,
        "动作": "继续补长周期自然日样本",
        "目标": "不要用同日多次复跑冒充 3-7 天样本。",
    },
    {
        "顺序": 5,
        "动作": "继续补异常样例库和使用者交付说明",
        "目标": "提升稳定版可信度和交接便利性。",
    },
]


READING_ORDER = [
    "使用者交付摘要_最新.md",
    "稳定版封版候选总验收与剩余缺口清单_最新.md",
    "稳定版候选资料总索引_最新.md",
    "失败分级规则_最新.md",
    "异常恢复手册_最新.md",
    "日常运行检查手册_最新.md",
    "长周期样本达标条件_最新.md",
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


def build_index_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['名称']} | {item['类型']} | {item['作用']} | {item['路径']} |"
        for item in report["候选资料索引"]
    ]
    return "\n".join(["# 稳定版候选资料总索引", "", "| 编号 | 名称 | 类型 | 作用 | 路径 |", "| --- | --- | --- | --- | --- |", *rows, ""])


def build_continue_md(report: dict[str, Any]) -> str:
    rows = [f"| {item['顺序']} | {item['动作']} | {item['目标']} |" for item in report["后续接续步骤"]]
    return "\n".join(["# 稳定版后续接续说明", "", "| 顺序 | 动作 | 目标 |", "| --- | --- | --- |", *rows, "", "说明：本接续说明只属于进化系统候选资料，不修改原一键接续包。"])


def build_handover_md(report: dict[str, Any]) -> str:
    lines = ["# 稳定版交接阅读顺序", ""]
    lines.extend([f"{index}. {name}" for index, name in enumerate(report["交接阅读顺序"], start=1)])
    return "\n".join(lines)


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版最终候选索引与接续包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 候选资料索引：{len(report['候选资料索引'])}",
            f"- 后续接续步骤：{len(report['后续接续步骤'])}",
            f"- 交接阅读顺序：{len(report['交接阅读顺序'])}",
            "",
            "## 输出文件",
            "",
            f"- 稳定版候选资料总索引：{INDEX_MD}",
            f"- 稳定版后续接续说明：{CONTINUE_MD}",
            f"- 稳定版交接阅读顺序：{HANDOVER_MD}",
            "",
            "## 核心口径",
            "",
            "- 本包是稳定版最终候选索引，不是正式封版。",
            "- 本包不修改总管面板，不修改原一键接续包。",
            "- 后续仍以只读总回归、自主快照和自然日样本为准。",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定版最终候选索引与接续包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_final_candidate_index_continue_ready",
        "候选资料索引": PACKAGE_INDEX,
        "后续接续步骤": NEXT_CONTINUATION,
        "交接阅读顺序": READING_ORDER,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "稳定版候选资料总索引": str(INDEX_MD),
            "稳定版后续接续说明": str(CONTINUE_MD),
            "稳定版交接阅读顺序": str(HANDOVER_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(INDEX_MD, build_index_md(report))
    write_text(CONTINUE_MD, build_continue_md(report))
    write_text(HANDOVER_MD, build_handover_md(report))
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "索引": len(PACKAGE_INDEX), "接续步骤": len(NEXT_CONTINUATION), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
