# -*- coding: utf-8 -*-
"""生成稳定版使用者一页操作卡与灯号说明包。

给使用者一个最短操作面：每天跑什么、看什么、绿黄红灯怎么处理。
只读生成文档，不触发任何外部真实动作。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "89稳定版使用者一页操作卡与灯号说明包"

LATEST_JSON = OUTPUT_DIR / "稳定版使用者一页操作卡与灯号说明包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版使用者一页操作卡与灯号说明包_最新.md"
OP_CARD_MD = OUTPUT_DIR / "稳定版使用者一页操作卡_最新.md"
LIGHTS_MD = OUTPUT_DIR / "稳定版运行灯号说明_最新.md"

DASHBOARD = EVOLUTION_ROOT / "03数据" / "87稳定交付版运行指挥台索引包" / "稳定版运行指挥台_最新.json"
DASHBOARD_MD = EVOLUTION_ROOT / "03数据" / "87稳定交付版运行指挥台索引包" / "稳定版运行指挥台_最新.md"
DAILY_ENTRY = EVOLUTION_ROOT / "02脚本" / "执行稳定交付版运行指挥台每日刷新入口.py"
DAILY_ENTRY_VERIFY = EVOLUTION_ROOT / "02脚本" / "验证稳定交付版运行指挥台每日刷新入口包.py"
DAILY_REPORT_MD = EVOLUTION_ROOT / "03数据" / "85稳定交付版每日运行日报与次日待办包" / "稳定版每日运行日报_最新.md"
NEXT_TODO_MD = EVOLUTION_ROOT / "03数据" / "85稳定交付版每日运行日报与次日待办包" / "稳定版次日待办清单_最新.md"


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


def build_operation_card(dashboard: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版使用者一页操作卡",
            "",
            "## 每天先做",
            "",
            f"```powershell\npython \"{DAILY_ENTRY}\"\n```",
            "",
            "## 跑完再验收",
            "",
            f"```powershell\npython \"{DAILY_ENTRY_VERIFY}\"\n```",
            "",
            "## 然后看这三个文件",
            "",
            f"- 运行指挥台：{DASHBOARD_MD}",
            f"- 每日运行日报：{DAILY_REPORT_MD}",
            f"- 次日待办清单：{NEXT_TODO_MD}",
            "",
            "## 当前灯号",
            "",
            f"- 运行灯号：{dashboard.get('运行灯号')}",
            f"- 今日结论：{dashboard.get('今日结论')}",
            f"- 三日稳定达标：{dashboard.get('三日稳定', {}).get('达标')}",
            f"- 仍缺自然日样本：{dashboard.get('三日稳定', {}).get('仍缺样本数')}",
            "",
            "## 使用边界",
            "",
            "- 这是只读稳定版运行入口。",
            "- 看到绿灯可以继续观察使用。",
            "- 看到黄灯先看日报和待办。",
            "- 看到红灯或需总管确认，不要继续自动处理。",
            "",
        ]
    )


def build_lights_md() -> str:
    return "\n".join(
        [
            "# 稳定版运行灯号说明",
            "",
            "| 灯号 | 含义 | 使用者动作 |",
            "| --- | --- | --- |",
            "| green | 今日只读刷新、总巡检、总回归没有失败 | 继续观察使用，等待真实自然日样本补齐 |",
            "| yellow | 出现非红线问题或样本未补齐 | 查看日报和次日待办，按问题台账登记 |",
            "| red | 触碰红线、服务重载、正式规则或外部真实动作风险 | 停止继续自动处理，登记需总管确认 |",
            "",
            "## 不能自动处理的情况",
            "",
            "- 需要重载 19310/19302。",
            "- 需要真实发送企业微信或触发 n8n。",
            "- 需要交易、登录税局、接财税软件、真实渲染或发布视频。",
            "- 需要把候选转成正式规则。",
            "",
        ]
    )


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版使用者一页操作卡与灯号说明包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 运行灯号：{report['运行灯号']}",
            f"- 三日达标：{report['三日达标']}",
            f"- 仍缺自然日样本：{report['仍缺自然日样本']}",
            "",
            "## 产物",
            "",
            f"- 使用者一页操作卡：{OP_CARD_MD}",
            f"- 运行灯号说明：{LIGHTS_MD}",
            "",
        ]
    )


def main() -> int:
    dashboard = read_json(DASHBOARD)
    report = {
        "名称": "稳定版使用者一页操作卡与灯号说明包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_user_one_page_operation_card_ready",
        "运行灯号": dashboard.get("运行灯号"),
        "今日结论": dashboard.get("今日结论"),
        "三日达标": dashboard.get("三日稳定", {}).get("达标"),
        "仍缺自然日样本": dashboard.get("三日稳定", {}).get("仍缺样本数"),
        "每日入口": str(DAILY_ENTRY),
        "每日入口验收": str(DAILY_ENTRY_VERIFY),
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "使用者一页操作卡": str(OP_CARD_MD),
            "运行灯号说明": str(LIGHTS_MD),
        },
        "安全边界": SAFETY_BOUNDARY,
    }
    write_text(OP_CARD_MD, build_operation_card(dashboard))
    write_text(LIGHTS_MD, build_lights_md())
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "运行灯号": report["运行灯号"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
