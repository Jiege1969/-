# -*- coding: utf-8 -*-
"""生成稳定候选补强与三日巡检启动包。

只建立三日只读巡检样本机制和稳定候选补强说明，不创建外部自动化，不修改正式规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "59稳定候选补强与三日巡检启动包"
LATEST_JSON = OUTPUT_DIR / "稳定候选补强与三日巡检启动包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定候选补强与三日巡检启动包_最新.md"
START_MD = OUTPUT_DIR / "三日只读巡检启动说明_最新.md"
HARDEN_MD = OUTPUT_DIR / "稳定候选补强说明_最新.md"
SAMPLE_LEDGER_JSON = OUTPUT_DIR / "三日只读巡检样本台账_最新.json"


PATROL_SOURCES: list[dict[str, Any]] = [
    {
        "编号": "D3P-001",
        "名称": "企业微信公共入口日常巡检",
        "路径": str(ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置" / "03数据" / "15日常可用版只读巡检包" / "企业微信公共接入层日常只读巡检_最新.json"),
        "通过口径": "总体状态=pass，失败=0。",
    },
    {
        "编号": "D3P-002",
        "名称": "日常可用交付版一键只读总回归",
        "路径": str(EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json"),
        "通过口径": "通过=true，错误数=0。",
    },
    {
        "编号": "D3P-003",
        "名称": "自主巡检快照",
        "路径": str(EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"),
        "通过口径": "总体状态=pass，失败=0。",
    },
    {
        "编号": "D3P-004",
        "名称": "稳定版候选可交付声明",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定版候选最终回传与可交付声明包验收" / "stable-candidate-final-delivery-statement-verify-最新.json"),
        "通过口径": "通过=true，错误数=0。",
    },
]


THREE_DAY_RULES = [
    "每天只能记录一个自然日样本，同一天多次复跑只能刷新当日样本，不能增加自然日计数。",
    "三日达标必须满足 3 个不同自然日样本均通过。",
    "任一自然日样本出现红线、服务重载未确认或总回归失败，三日计数重新评估。",
    "本启动包不创建定时任务；后续可由人工或总管确认后的自动化机制每日复跑。",
]


HARDENING_NOTES = [
    "稳定版候选已经可交付，但仍需要自然日样本提高置信度。",
    "当前不开放真实外部动作，因此稳定候选侧重本地参谋、预演、只读验收和交接能力。",
    "对 19310/19302 的任何重载仍保持需总管确认。",
    "进化候选继续与正式规则隔离，避免一次验收通过就改变全局行为。",
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
    "创建外部定时任务": False,
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_start_md(report: dict[str, Any]) -> str:
    rows = [f"| {item['编号']} | {item['名称']} | {item['通过口径']} | {item['路径']} |" for item in report["三日巡检源"]]
    lines = [
        "# 三日只读巡检启动说明",
        "",
        "本包启动三日自然日样本记录，但当前不会伪装为三日达标。",
        "",
        "| 编号 | 巡检源 | 通过口径 | 路径 |",
        "| --- | --- | --- | --- |",
        *rows,
        "",
        "## 计数规则",
        "",
    ]
    lines.extend([f"- {item}" for item in report["三日计数规则"]])
    return "\n".join(lines)


def build_harden_md(report: dict[str, Any]) -> str:
    lines = ["# 稳定候选补强说明", ""]
    lines.extend([f"- {item}" for item in report["补强说明"]])
    return "\n".join(lines)


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定候选补强与三日巡检启动包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 三日巡检源：{len(report['三日巡检源'])}",
            f"- 三日计数规则：{len(report['三日计数规则'])}",
            f"- 补强说明：{len(report['补强说明'])}",
            "",
            "## 输出文件",
            "",
            f"- 三日只读巡检启动说明：{START_MD}",
            f"- 稳定候选补强说明：{HARDEN_MD}",
            f"- 三日只读巡检样本台账：{SAMPLE_LEDGER_JSON}",
            "",
            "## 核心口径",
            "",
            "- 首日样本不等于三日达标。",
            "- 不创建外部定时任务，不修改原一键接续包。",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定候选补强与三日巡检启动包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_candidate_hardening_three_day_patrol_start_ready",
        "三日巡检源": PATROL_SOURCES,
        "三日计数规则": THREE_DAY_RULES,
        "补强说明": HARDENING_NOTES,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "三日只读巡检启动说明": str(START_MD),
            "稳定候选补强说明": str(HARDEN_MD),
            "三日只读巡检样本台账": str(SAMPLE_LEDGER_JSON),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(START_MD, build_start_md(report))
    write_text(HARDEN_MD, build_harden_md(report))
    if not SAMPLE_LEDGER_JSON.exists():
        write_json(
            SAMPLE_LEDGER_JSON,
            {
                "名称": "三日只读巡检样本台账",
                "创建时间": report["生成时间"],
                "自然日样本": [],
                "三日达标": False,
            },
        )
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "巡检源": len(PATROL_SOURCES), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
