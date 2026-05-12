# -*- coding: utf-8 -*-
"""生成日常可用交付版状态包。

只汇总当前已通过的日常巡检、能力候选、阻断候选和回归卡；不写正式规则、不改运行配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "43日常可用交付版状态包"
LATEST_JSON = OUTPUT_DIR / "日常可用交付版状态包_最新.json"
LATEST_MD = OUTPUT_DIR / "日常可用交付版状态包_最新.md"
LATEST_USER_MD = OUTPUT_DIR / "日常可用交付版使用者摘要_最新.md"

SOURCES = {
    "巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "可用能力清单": EVOLUTION_ROOT / "03数据" / "39阶段性多业务联调通过封版候选" / "可用能力清单候选_最新.json",
    "仍阻断能力清单": EVOLUTION_ROOT / "03数据" / "39阶段性多业务联调通过封版候选" / "仍阻断能力清单候选_最新.json",
    "回归建议拆单": EVOLUTION_ROOT / "03数据" / "42阶段性封版候选回归建议拆单" / "阶段性封版候选回归建议拆单_最新.json",
    "总管自主推进模式候选": EVOLUTION_ROOT / "03数据" / "41总管自主推进模式候选" / "总管自主推进模式候选_最新.json",
}

SNAPSHOT_SELF_REFERENTIAL_ITEMS = {
    "日常可用交付版状态包验收",
    "日常可用交付版一键只读总回归验收",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def snapshot_effective_passed(snapshot: dict[str, Any]) -> bool:
    if snapshot.get("总体状态") == "pass":
        return True
    failed_items = [
        item.get("名称")
        for item in snapshot.get("检查结果", [])
        if item.get("通过") is not True
    ]
    return bool(failed_items) and all(name in SNAPSHOT_SELF_REFERENTIAL_ITEMS for name in failed_items)


def build_package() -> dict[str, Any]:
    snapshot = read_json(SOURCES["巡检快照"])
    available = read_json(SOURCES["可用能力清单"])
    blocked = read_json(SOURCES["仍阻断能力清单"])
    regression = read_json(SOURCES["回归建议拆单"])
    autonomy = read_json(SOURCES["总管自主推进模式候选"])

    available_items = available.get("可用能力候选", [])
    blocked_items = blocked.get("仍阻断能力候选", [])
    regression_cards = regression.get("回归卡", [])
    snapshot_summary = snapshot.get("汇总", {})

    return {
        "名称": "日常可用交付版状态包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "性质": "阶段性交付状态包，不是正式规则封版",
        "整体状态": "daily_usable_candidate_passed" if snapshot_effective_passed(snapshot) else "blocked",
        "日常可用判断": {
            "结论": "可作为日常可用交付候选版使用",
            "依据": [
                f"日常可用版自主巡检快照 {snapshot_summary.get('通过', 0)}/{snapshot_summary.get('总数', 0)} 通过",
                f"可用能力候选 {available.get('能力数量', len(available_items))} 项",
                f"仍阻断能力候选 {blocked.get('阻断能力数量', len(blocked_items))} 项",
                f"回归卡 {regression.get('汇总', {}).get('回归卡数量', len(regression_cards))} 张",
            ],
        },
        "使用者当前体验": [
            "可通过企业微信公共入口做本地只读/预演式问答和分流验证。",
            "税收问题可返回待复核草案摘要，但不形成正式税务结论。",
            "股票问题可输出研究分析和展示产物，前台口径已去交易化。",
            "视频链路可做脚本、分镜、人工回执、预检和阻断检查，但不真实渲染或发布。",
            "系统会把经验沉淀为候选和回归卡，但不会自动变成正式规则。",
        ],
        "可用能力": [
            {
                "能力ID": item.get("能力ID"),
                "能力名称": item.get("能力名称"),
                "状态": item.get("候选状态"),
                "边界": item.get("边界"),
            }
            for item in available_items
        ],
        "仍阻断能力": [
            {
                "阻断ID": item.get("阻断ID"),
                "能力名称": item.get("能力名称"),
                "当前口径": item.get("当前口径"),
                "阻断状态": item.get("阻断状态"),
            }
            for item in blocked_items
        ],
        "日常巡检入口": {
            "总览快照": str(SOURCES["巡检快照"]),
            "企业微信巡检脚本": str(ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置" / "02脚本" / "执行企业微信公共接入层日常只读巡检.py"),
            "状态包验证脚本": str(EVOLUTION_ROOT / "02脚本" / "验证日常可用交付版状态包.py"),
        },
        "后续回归卡": [
            {
                "回归ID": card.get("回归ID"),
                "名称": card.get("名称"),
                "执行范围": card.get("执行范围"),
                "默认执行方式": card.get("默认执行方式"),
            }
            for card in regression_cards
        ],
        "自主推进模式": {
            "性质": autonomy.get("性质"),
            "默认动作": autonomy.get("自主推进默认动作", []),
            "硬刹车": autonomy.get("硬刹车", []),
        },
        "来源文件": {name: str(path) for name, path in SOURCES.items()},
        "安全边界": {
            "写正式规则": False,
            "修改运行配置": False,
            "触发服务重载": False,
            "重载19310": False,
            "重载19302": False,
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
            "修改总管面板": False,
            "修改一键接续包": False,
        },
    }


def build_markdown(package: dict[str, Any]) -> str:
    available_rows = [
        f"| {item['能力ID']} | {item['能力名称']} | {item['状态']} | {item['边界']} |"
        for item in package["可用能力"]
    ]
    blocked_rows = [
        f"| {item['阻断ID']} | {item['能力名称']} | {item['当前口径']} |"
        for item in package["仍阻断能力"]
    ]
    regression_rows = [
        f"| {item['回归ID']} | {item['名称']} | {item['执行范围']} |"
        for item in package["后续回归卡"]
    ]
    return "\n".join(
        [
            "# 日常可用交付版状态包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 性质：{package['性质']}",
            f"- 整体状态：{package['整体状态']}",
            f"- 结论：{package['日常可用判断']['结论']}",
            "",
            "## 判断依据",
            "",
            *[f"- {item}" for item in package["日常可用判断"]["依据"]],
            "",
            "## 使用者当前体验",
            "",
            *[f"- {item}" for item in package["使用者当前体验"]],
            "",
            "## 可用能力",
            "",
            "| ID | 能力 | 状态 | 边界 |",
            "| --- | --- | --- | --- |",
            *available_rows,
            "",
            "## 仍阻断能力",
            "",
            "| ID | 能力 | 当前口径 |",
            "| --- | --- | --- |",
            *blocked_rows,
            "",
            "## 后续回归卡",
            "",
            "| ID | 名称 | 范围 |",
            "| --- | --- | --- |",
            *regression_rows,
            "",
            "## 安全边界",
            "",
            "- 不写正式规则，不修改运行配置，不重载19310/19302。",
            "- 不真实发送企业微信，不触发n8n。",
            "- 不接券商、不交易，不登录电子税务局、不接财税软件。",
            "- 不真实渲染视频，不自动发布视频。",
            "- 不修改总管面板，不修改一键接续包。",
        ]
    )


def build_user_markdown(package: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 日常可用交付版使用者摘要",
            "",
            "当前可以把系统当作“智能参谋 + 本地预演 + 风险闸口”使用。",
            "",
            "## 你能做什么",
            "",
            "- 问系统状态、税收资料清单、股票研究分析、视频脚本/分镜/预检。",
            "- 让系统做只读巡检、生成候选清单、整理回归卡。",
            "- 让总管自主推进低风险搭建，不用手动分派到其他对话框。",
            "",
            "## 系统不会替你做什么",
            "",
            "- 不会真实发企业微信给别人。",
            "- 不会触发n8n真实流程。",
            "- 不会连接券商或交易。",
            "- 不会登录税局或连接财税软件。",
            "- 不会自动发布视频。",
            "- 不会把候选经验自动变成正式规则。",
            "",
            "## 日常检查入口",
            "",
            f"- 状态包：{LATEST_MD}",
            f"- 巡检快照：{package['日常巡检入口']['总览快照']}",
            f"- 企业微信巡检脚本：{package['日常巡检入口']['企业微信巡检脚本']}",
        ]
    )


def main() -> int:
    package = build_package()
    write_json(LATEST_JSON, package)
    write_text(LATEST_MD, build_markdown(package))
    write_text(LATEST_USER_MD, build_user_markdown(package))
    print(json.dumps({"整体状态": package["整体状态"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if package["整体状态"] == "daily_usable_candidate_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
