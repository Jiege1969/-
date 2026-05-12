# -*- coding: utf-8 -*-
"""生成使用者入口导航与常用指令包。

只生成给使用者看的入口导航、常用指令和安全边界说明，不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "88使用者入口导航与常用指令包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "使用者入口导航与常用指令包验收"

SOURCES = {
    "总巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "最终交付收尾": EVOLUTION_ROOT / "03数据" / "80日常可用版与稳定交付版最终交付收尾包" / "日常可用版与稳定交付版最终交付收尾包_最新.json",
    "运行指挥台": EVOLUTION_ROOT / "03数据" / "87稳定交付版运行指挥台索引包" / "稳定交付版运行指挥台索引包_最新.json",
    "周报看板": EVOLUTION_ROOT / "03数据" / "85运行期周报与状态看板数据包" / "运行期周报与状态看板数据包_最新.json",
    "故障恢复索引": EVOLUTION_ROOT / "03数据" / "87运行期故障恢复与回滚总索引包" / "运行期故障恢复与回滚总索引包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "使用者入口导航与常用指令包_最新.json"
PACKAGE_MD = DATA_DIR / "使用者入口导航与常用指令包_最新.md"
NAV_MD = DATA_DIR / "使用者入口导航_最新.md"
COMMANDS_JSON = DATA_DIR / "常用指令清单_最新.json"
COMMANDS_MD = DATA_DIR / "常用指令清单_最新.md"
SAFETY_MD = DATA_DIR / "使用安全边界速查_最新.md"
GEN_LOG = LOG_DIR / "生成使用者入口导航与常用指令包_最新.json"

SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "真实触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "执行真实回滚": False,
    "写正式规则": False,
    "自动转正式规则": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_commands() -> list[dict[str, Any]]:
    return [
        {"场景": "看系统状态", "建议指令": "系统现在整体状态怎么样", "预期输出": "总巡检、总回归、交付状态、红线状态摘要", "红线": False},
        {"场景": "税收资料草案", "建议指令": "税收业务：软件产品即征即退需要准备哪些资料", "预期输出": "税收分析助手-待复核草案摘要", "红线": False},
        {"场景": "股票研究", "建议指令": "分析天齐锂业", "预期输出": "研究价值、风险复核、当前操作建议等去交易化内容", "红线": False},
        {"场景": "视频脚本预检", "建议指令": "生成一个视频脚本草案并做发布预检", "预期输出": "脚本/分镜/预检结果，真实渲染和发布保持阻断", "红线": False},
        {"场景": "看运行日报", "建议指令": "查看稳定交付版每日运行日报", "预期输出": "日报、次日待办、问题状态", "红线": False},
        {"场景": "继续低风险搭建", "建议指令": "继续", "预期输出": "只读巡检、候选资产、验收脚本、状态包或回归清单", "红线": False},
        {"场景": "触碰外部动作", "建议指令": "真实发送/触发n8n/交易/登录税局/真实渲染/发布/重载服务", "预期输出": "暂停并登记需总管确认", "红线": True},
    ]


def main() -> int:
    source_summary = {}
    for name, path in SOURCES.items():
        data = read_json(path)
        source_summary[name] = {
            "路径": str(path),
            "存在": path.exists(),
            "状态": data.get("状态") or data.get("总体状态") or data.get("通过") or data.get("passed"),
            "汇总": data.get("汇总") or data.get("指标") or data.get("metrics") or {},
        }
    commands = build_commands()
    package = {
        "名称": "使用者入口导航与常用指令包",
        "生成时间": now_text(),
        "状态": "user_entry_navigation_ready" if all(item["存在"] for item in source_summary.values()) else "user_entry_navigation_blocked",
        "用途": "把交付后的常用入口、常用指令、预期输出和红线停机口径整理成使用者可读导航。",
        "入口索引": source_summary,
        "常用指令": commands,
        "使用原则": [
            "把系统当作参谋、预演和只读运行管理平台。",
            "看到待复核、候选、预检、阻断等口径时，由使用者最终判断。",
            "出现真实外部动作、正式规则、服务重载时立即暂停并登记。",
        ],
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "使用者入口导航": str(NAV_MD),
            "常用指令JSON": str(COMMANDS_JSON),
            "常用指令Markdown": str(COMMANDS_MD),
            "使用安全边界速查": str(SAFETY_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    write_json(COMMANDS_JSON, {"名称": "常用指令清单", "常用指令": commands, "安全边界": SAFETY_BOUNDARY})
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    command_rows = [f"| {item['场景']} | {item['建议指令']} | {item['预期输出']} | {item['红线']} |" for item in commands]
    package_md = "\n".join([
        "# 使用者入口导航与常用指令包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 状态：{package['状态']}",
        "- 结论：这是使用者导航，不执行任何外部动作。",
        "",
        "| 入口 | 存在 | 状态 | 路径 |",
        "| --- | --- | --- | --- |",
        *source_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(NAV_MD, package_md)
    write_text(COMMANDS_MD, "\n".join(["# 常用指令清单", "", "| 场景 | 建议指令 | 预期输出 | 红线 |", "| --- | --- | --- | --- |", *command_rows]))
    write_text(SAFETY_MD, "\n".join(["# 使用安全边界速查", "", *[f"- {key}：{value}" for key, value in SAFETY_BOUNDARY.items()]]))
    write_json(GEN_LOG, {"名称": "生成使用者入口导航与常用指令包", "生成时间": now_text(), "通过": package["状态"] == "user_entry_navigation_ready", "错误数": 0 if package["状态"] == "user_entry_navigation_ready" else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "入口": len(source_summary), "指令": len(commands), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if package["状态"] == "user_entry_navigation_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
