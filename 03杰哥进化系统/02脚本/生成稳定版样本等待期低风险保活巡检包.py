# -*- coding: utf-8 -*-
"""生成稳定版样本等待期低风险保活巡检包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
SCRIPT_DIR = EVOLUTION_ROOT / "02脚本"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "100稳定版样本等待期低风险保活巡检包"

LATEST_JSON = OUTPUT_DIR / "稳定版样本等待期低风险保活巡检包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版样本等待期低风险保活巡检包_最新.md"
KEEPALIVE_CARD_MD = OUTPUT_DIR / "样本等待期低风险保活巡检卡_最新.md"
RUN_SCRIPT = SCRIPT_DIR / "执行稳定版样本等待期低风险保活巡检.py"
RUN_RESULT = OUTPUT_DIR / "稳定版样本等待期低风险保活巡检执行结果_最新.json"

SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "接n8n": False,
    "触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "生成正式税务结论": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "写正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
    "新增三日自然日样本": False,
    "预生成未来自然日样本": False,
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_keepalive_card() -> str:
    return "\n".join(
        [
            "# 样本等待期低风险保活巡检卡",
            "",
            "## 什么时候用",
            "",
            "- 当前自然日样本已经记录，但还没到下一自然日。",
            "- 需要继续观察反馈、刷新指挥台、确认没有新增阻断。",
            "- 不想误增三日样本时使用。",
            "",
            "## 只跑这个",
            "",
            "```powershell",
            f'python "{RUN_SCRIPT}"',
            "```",
            "",
            "## 它不会做",
            "",
            "- 不新增三日自然日样本。",
            "- 不生成未来样本。",
            "- 不重载 19310/19302。",
            "- 不触发企业微信真实发送、n8n、券商、税局、财税软件或视频发布。",
            "",
        ]
    )


def build_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版样本等待期低风险保活巡检包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            "- 用途：在三日自然日样本等待期继续做低风险保活巡检，不误增样本。",
            "",
            "## 执行命令",
            "",
            "```powershell",
            report["执行命令"],
            "```",
            "",
            "## 巡检内容",
            "",
            *[f"- {item}" for item in report["巡检内容"]],
            "",
            "## 输出文件",
            "",
            *[f"- {key}：{value}" for key, value in report["输出文件"].items()],
            "",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定版样本等待期低风险保活巡检包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_sample_waiting_keepalive_patrol_ready",
        "执行命令": f'python "{RUN_SCRIPT}"',
        "巡检内容": [
            "刷新次日自然日样本防重复闸口",
            "扫描试运行反馈本地收件箱",
            "刷新稳定版运行指挥台索引",
            "刷新自主巡检快照",
            "输出等待期状态摘要",
        ],
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "保活巡检卡": str(KEEPALIVE_CARD_MD),
            "执行结果": str(RUN_RESULT),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(KEEPALIVE_CARD_MD, build_keepalive_card())
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"状态": report["状态"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
