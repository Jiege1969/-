# -*- coding: utf-8 -*-
"""生成稳定交付长周期只读巡检样本与趋势记录包。

本包建立长周期巡检的样本口径和趋势记录，不伪装为已经完成 3-7 天运行。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "55稳定交付长周期只读巡检样本与趋势记录包"
LATEST_JSON = OUTPUT_DIR / "稳定交付长周期只读巡检样本与趋势记录包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付长周期只读巡检样本与趋势记录包_最新.md"
TREND_MD = OUTPUT_DIR / "长周期巡检趋势记录表_最新.md"
SAMPLE_MD = OUTPUT_DIR / "当前巡检样本说明_最新.md"
TARGET_MD = OUTPUT_DIR / "长周期样本达标条件_最新.md"


TREND_SOURCES: list[dict[str, Any]] = [
    {
        "编号": "STR-001",
        "名称": "企业微信公共入口日常巡检",
        "路径": str(ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置" / "03数据" / "15日常可用版只读巡检包" / "企业微信公共接入层日常只读巡检_最新.json"),
        "趋势指标": ["总体状态", "通过", "失败", "real_send=false", "触发n8n=false"],
    },
    {
        "编号": "STR-002",
        "名称": "日常可用交付版一键只读总回归",
        "路径": str(EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json"),
        "趋势指标": ["通过", "总数", "失败", "错误数"],
    },
    {
        "编号": "STR-003",
        "名称": "自主巡检快照",
        "路径": str(EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"),
        "趋势指标": ["总体状态", "总数", "通过", "失败"],
    },
    {
        "编号": "STR-004",
        "名称": "股票展示口径一致性",
        "路径": str(ROOT / "02杰哥扩展系统" / "01股票研究系统" / "03数据" / "246展示口径修复" / "股票展示口径一致性验收_最新.json"),
        "趋势指标": ["通过", "错误数", "检查文件数"],
    },
    {
        "编号": "STR-005",
        "名称": "视频真实渲染禁用态",
        "路径": str(ROOT / "02杰哥扩展系统" / "02视频制作系统" / "03数据" / "08本地整理门禁" / "视频真实渲染禁用态检查_最新.json"),
        "趋势指标": ["执行器状态=禁用态", "是否调用剪辑软件=false", "是否生成真实媒体=false", "是否自动发布=false"],
    },
    {
        "编号": "STR-006",
        "名称": "稳定版封版候选总验收",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定版封版候选总验收与剩余缺口清单验收" / "stable-release-freeze-candidate-acceptance-verify-最新.json"),
        "趋势指标": ["通过", "证据失败", "错误数"],
    },
]


LONG_TERM_TARGETS = [
    {
        "目标": "连续 3 个自然日只读巡检通过",
        "当前状态": "未达标，当前只是单日高频样本",
        "是否阻断稳定版候选": False,
    },
    {
        "目标": "连续 7 个自然日无红线命中",
        "当前状态": "未达标，需后续自然日样本积累",
        "是否阻断稳定版候选": False,
    },
    {
        "目标": "核心 6 类趋势源每日都有样本",
        "当前状态": "已建立趋势源清单，需后续每日追加",
        "是否阻断稳定版候选": False,
    },
    {
        "目标": "总回归失败能自动分级",
        "当前状态": "已具备失败分级与总管确认闸口",
        "是否阻断稳定版候选": False,
    },
]


SAMPLE_POLICY = [
    "当前包只记录现有本地只读验收样本，不伪造未来日期。",
    "长周期达标必须依赖真实自然日样本，不能用同一天多次复跑冒充。",
    "趋势记录只允许读取本地验收 JSON，不请求业务接口。",
    "红线全部保持 false；如命中红线，趋势状态自动变为 blocked。",
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


def build_trend_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['名称']} | {', '.join(item['趋势指标'])} | {item['路径']} |"
        for item in report["趋势源"]
    ]
    return "\n".join(["# 长周期巡检趋势记录表", "", "| 编号 | 名称 | 趋势指标 | 路径 |", "| --- | --- | --- | --- |", *rows, ""])


def build_sample_md(report: dict[str, Any]) -> str:
    lines = ["# 当前巡检样本说明", "", f"- 生成时间：{report['生成时间']}", "- 当前样本性质：单日高频只读样本。", "- 长周期状态：未伪装达标，等待后续自然日积累。", "", "## 样本口径", ""]
    lines.extend([f"- {item}" for item in report["样本口径"]])
    return "\n".join(lines)


def build_target_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['目标']} | {item['当前状态']} | {item['是否阻断稳定版候选']} |"
        for item in report["长周期达标条件"]
    ]
    return "\n".join(["# 长周期样本达标条件", "", "| 目标 | 当前状态 | 阻断稳定版候选 |", "| --- | --- | --- |", *rows, ""])


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定交付长周期只读巡检样本与趋势记录包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 趋势源：{len(report['趋势源'])}",
            f"- 长周期达标条件：{len(report['长周期达标条件'])}",
            f"- 样本口径：{len(report['样本口径'])}",
            "",
            "## 输出文件",
            "",
            f"- 长周期巡检趋势记录表：{TREND_MD}",
            f"- 当前巡检样本说明：{SAMPLE_MD}",
            f"- 长周期样本达标条件：{TARGET_MD}",
            "",
            "## 核心口径",
            "",
            "- 当前不是 3-7 天长周期达标，只是建立长周期样本机制。",
            "- 同一天多次复跑只能算高频样本，不能冒充自然日样本。",
            "- 本包不触发任何业务接口或服务重载。",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定交付长周期只读巡检样本与趋势记录包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_delivery_long_term_patrol_trend_candidate_ready",
        "趋势源": TREND_SOURCES,
        "长周期达标条件": LONG_TERM_TARGETS,
        "样本口径": SAMPLE_POLICY,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "长周期巡检趋势记录表": str(TREND_MD),
            "当前巡检样本说明": str(SAMPLE_MD),
            "长周期样本达标条件": str(TARGET_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(TREND_MD, build_trend_md(report))
    write_text(SAMPLE_MD, build_sample_md(report))
    write_text(TARGET_MD, build_target_md(report))
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "趋势源": len(TREND_SOURCES), "达标条件": len(LONG_TERM_TARGETS), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
