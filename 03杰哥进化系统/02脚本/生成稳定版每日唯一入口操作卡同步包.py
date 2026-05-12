# -*- coding: utf-8 -*-
"""生成稳定版每日唯一入口操作卡同步包。

把稳定版每日运行入口收束到“自然日样本采集与达标刷新入口”，避免使用者每天重复跑旧入口。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
SCRIPT_DIR = EVOLUTION_ROOT / "02脚本"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "98稳定版每日唯一入口操作卡同步包"

LATEST_JSON = OUTPUT_DIR / "稳定版每日唯一入口操作卡同步包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版每日唯一入口操作卡同步包_最新.md"
CARD_MD = OUTPUT_DIR / "稳定版每日唯一入口操作卡_最新.md"
ENTRY_MATRIX_JSON = OUTPUT_DIR / "稳定版每日入口关系表_最新.json"

PRIMARY_SCRIPT = SCRIPT_DIR / "执行稳定版自然日样本采集与达标刷新.py"
PRIMARY_PACKAGE = EVOLUTION_ROOT / "03数据" / "97稳定版自然日样本采集与达标刷新入口包" / "稳定版自然日样本采集与达标刷新入口包_最新.json"
PRIMARY_RUN_RESULT = EVOLUTION_ROOT / "03数据" / "97稳定版自然日样本采集与达标刷新入口包" / "稳定版自然日样本采集与达标刷新执行结果_最新.json"
INTERNAL_DASHBOARD_SCRIPT = SCRIPT_DIR / "执行稳定交付版运行指挥台每日刷新入口.py"
RUNTIME_DASHBOARD = EVOLUTION_ROOT / "03数据" / "87稳定交付版运行指挥台索引包" / "稳定版运行指挥台_最新.md"
LEGACY_OPERATION_CARD = EVOLUTION_ROOT / "03数据" / "89稳定版使用者一页操作卡与灯号说明包" / "稳定版使用者一页操作卡与灯号说明包_最新.json"


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
    "预生成未来自然日样本": False,
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_card(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版每日唯一入口操作卡",
            "",
            "## 每天只跑这个",
            "",
            "```powershell",
            f'python "{PRIMARY_SCRIPT}"',
            "```",
            "",
            "## 跑完看这里",
            "",
            f"- 运行指挥台：{RUNTIME_DASHBOARD}",
            f"- 执行结果：{PRIMARY_RUN_RESULT}",
            "",
            "## 入口关系",
            "",
            "- 推荐每日入口：稳定版自然日样本采集与达标刷新入口。",
            "- 运行指挥台每日刷新入口：已经被推荐入口包含，作为内部子入口使用。",
            "- 同一自然日重复运行：只覆盖当天样本，不增加样本天数。",
            "- 三日达标：必须来自三个不同真实自然日的通过样本。",
            "",
            "## 不做的事",
            "",
            "- 不真实发送企业微信。",
            "- 不接 n8n、不触发 n8n。",
            "- 不接券商、不交易。",
            "- 不登录电子税务局、不接财税软件、不生成正式税务结论。",
            "- 不真实渲染或自动发布视频。",
            "- 不写正式规则，不重载 19310/19302。",
            "",
        ]
    )


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['名称']} | {item['定位']} | {item['是否推荐手动运行']} | {item['路径']} |"
        for item in report["入口关系表"]
    ]
    return "\n".join(
        [
            "# 稳定版每日唯一入口操作卡同步包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 推荐入口：{report['推荐每日入口命令']}",
            f"- 三日达标：{report['当前运行摘要'].get('三日达标')}",
            f"- 仍缺自然日样本数：{report['当前运行摘要'].get('仍缺自然日样本数')}",
            "",
            "## 入口关系表",
            "",
            "| 名称 | 定位 | 是否推荐手动运行 | 路径 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
            "## 输出文件",
            "",
            *[f"- {key}：{value}" for key, value in report["输出文件"].items()],
            "",
        ]
    )


def main() -> int:
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    primary_package = read_json(PRIMARY_PACKAGE)
    run_result = read_json(PRIMARY_RUN_RESULT)
    legacy_card = read_json(LEGACY_OPERATION_CARD)
    entry_matrix = [
        {
            "名称": "稳定版自然日样本采集与达标刷新入口",
            "定位": "推荐每日唯一手动入口",
            "是否推荐手动运行": True,
            "路径": str(PRIMARY_SCRIPT),
        },
        {
            "名称": "稳定交付版运行指挥台每日刷新入口",
            "定位": "推荐入口内部子入口",
            "是否推荐手动运行": False,
            "路径": str(INTERNAL_DASHBOARD_SCRIPT),
        },
        {
            "名称": "稳定版运行指挥台",
            "定位": "跑完后查看结果",
            "是否推荐手动运行": False,
            "路径": str(RUNTIME_DASHBOARD),
        },
    ]
    report = {
        "名称": "稳定版每日唯一入口操作卡同步包",
        "生成时间": now_text,
        "状态": "stable_daily_single_entry_operation_card_ready",
        "推荐每日入口命令": f'python "{PRIMARY_SCRIPT}"',
        "当前运行摘要": {
            "入口包状态": primary_package.get("状态"),
            "最近执行状态": run_result.get("总体状态"),
            "三日达标": run_result.get("运行摘要", {}).get("三日达标"),
            "不同自然日通过样本数": run_result.get("运行摘要", {}).get("不同自然日通过样本数"),
            "仍缺自然日样本数": run_result.get("运行摘要", {}).get("仍缺自然日样本数"),
            "旧操作卡存在": bool(legacy_card),
        },
        "入口关系表": entry_matrix,
        "同步策略": [
            "以后稳定版每日开工优先运行 97 自然日样本采集与达标刷新入口",
            "88 运行指挥台每日刷新入口作为 97 内部步骤保留",
            "89 旧一页操作卡不删除，本包作为最新稳定版入口说明覆盖",
            "不修改总管面板和一键接续包",
        ],
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "每日唯一入口操作卡": str(CARD_MD),
            "入口关系表": str(ENTRY_MATRIX_JSON),
        },
    }
    write_json(ENTRY_MATRIX_JSON, entry_matrix)
    write_json(LATEST_JSON, report)
    write_text(CARD_MD, build_card(report))
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"状态": report["状态"], "三日达标": report["当前运行摘要"]["三日达标"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
