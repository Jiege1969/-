# -*- coding: utf-8 -*-
"""生成完全交付使用版红线解锁分项确认单草案与授权边界包。

只把既有红线解锁申请材料拆成可人工签收的确认单草案；不让任何红线生效。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
SOURCE_106 = EVOLUTION_ROOT / "03数据" / "106完全交付使用版红线解锁申请材料总索引包" / "完全交付使用版红线解锁申请材料总索引包_最新.json"
SOURCE_107_GATE = EVOLUTION_ROOT / "03数据" / "107完全交付使用版红线解锁申请只读风险评审与禁止生效闸口包" / "红线解锁禁止生效闸口_最新.json"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "108完全交付使用版红线解锁分项确认单草案与授权边界包"
LATEST_JSON = OUTPUT_DIR / "完全交付使用版红线解锁分项确认单草案与授权边界包_最新.json"
LATEST_MD = OUTPUT_DIR / "完全交付使用版红线解锁分项确认单草案与授权边界包_最新.md"
CARDS_JSON = OUTPUT_DIR / "红线解锁分项确认单草案_最新.json"
BOUNDARY_MD = OUTPUT_DIR / "红线解锁分项授权边界说明_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def source_redline_items(source: dict[str, Any]) -> list[dict[str, Any]]:
    return (
        source.get("红线解锁申请材料总索引")
        or source.get("绾㈢嚎瑙ｉ攣鐢宠鏉愭枡鎬荤储寮?")
        or []
    )


def item_value(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in item:
            return item[key]
    return None


def build_confirmation_cards(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for idx, item in enumerate(items, start=1):
        redline = item_value(item, "红线", "绾㈢嚎") or f"未命名红线{idx}"
        material = item_value(item, "材料", "鏉愭枡") or "未登记材料"
        current_status = item_value(item, "当前状态", "褰撳墠鐘舵€?") or "未确认"
        cards.append(
            {
                "序号": idx,
                "红线": redline,
                "来源材料摘要": material,
                "当前状态": current_status,
                "确认单状态": "草案",
                "总管确认状态": "未确认",
                "允许生效": False,
                "允许自动执行": False,
                "单次授权边界": {
                    "必须明确对象": True,
                    "必须明确入口": True,
                    "必须明确范围": True,
                    "必须明确责任人": True,
                    "禁止一次授权扩展到其他红线": True,
                },
                "生效前必填项": [
                    "解锁对象",
                    "解锁入口",
                    "影响范围",
                    "责任人",
                    "回滚路径",
                    "成功样本",
                    "失败样本",
                    "拒收样本",
                    "外部影响说明",
                    "是否涉及19310/19302重载",
                ],
                "默认处置": "保持禁止生效，等待人工逐项确认",
            }
        )
    return cards


def build_package() -> dict[str, Any]:
    source = read_json(SOURCE_106)
    gate = read_json(SOURCE_107_GATE)
    items = source_redline_items(source)
    cards = build_confirmation_cards(items)
    package = {
        "名称": "完全交付使用版红线解锁分项确认单草案与授权边界包",
        "生成时间": now_text(),
        "状态": "full_delivery_redline_unlock_confirmation_draft_ready",
        "用途": "把红线解锁申请材料拆成分项确认单草案，供后续人工逐项确认；本包不代表解锁。",
        "来源": {
            "106材料总索引": str(SOURCE_106),
            "107禁止生效闸口": str(SOURCE_107_GATE),
        },
        "上游禁止生效闸口": {
            "存在": SOURCE_107_GATE.exists(),
            "闸口状态": gate.get("闸口状态"),
            "允许生效数量": gate.get("允许生效数量"),
            "红线解锁生效": gate.get("红线解锁生效"),
        },
        "分项确认单草案": cards,
        "授权边界总则": [
            "每次只允许确认一个明确红线对象，不允许打包解锁。",
            "未写明回滚路径和验收样本前，不允许进入生效步骤。",
            "涉及19310/19302时，只登记为需总管确认，不允许自动重载。",
            "涉及外部真实动作时，必须先形成单独签收记录和回滚记录。",
            "股票交易、税局登录、财税软件接入属于更高风险，不进入当前解锁范围。",
        ],
        "安全边界": {
            "真实发送企业微信": False,
            "真实触发n8n": False,
            "接券商": False,
            "交易": False,
            "登录电子税务局": False,
            "接财税软件": False,
            "真实渲染视频": False,
            "自动发布视频": False,
            "写正式规则": False,
            "自动转正式规则": False,
            "红线解锁生效": False,
            "修改总管面板": False,
            "修改一键接续包": False,
            "重载19310": False,
            "重载19302": False,
        },
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "分项确认单草案": str(CARDS_JSON),
            "授权边界说明": str(BOUNDARY_MD),
        },
    }
    return package


def build_markdown(package: dict[str, Any]) -> str:
    rows = [
        f"| {card['序号']} | {card['红线']} | {card['确认单状态']} | {card['总管确认状态']} | {card['允许生效']} | {card['允许自动执行']} |"
        for card in package["分项确认单草案"]
    ]
    return "\n".join(
        [
            "# 完全交付使用版红线解锁分项确认单草案与授权边界包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 状态：{package['状态']}",
            f"- 分项确认单数量：{len(package['分项确认单草案'])}",
            "- 结论：本包只生成草案，所有红线继续禁止生效。",
            "",
            "| 序号 | 红线 | 确认单状态 | 总管确认状态 | 允许生效 | 允许自动执行 |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
            "## 授权边界总则",
            "",
            *[f"- {item}" for item in package["授权边界总则"]],
            "",
            "## 安全边界",
            "",
            "- 不真实发送企业微信，不真实触发 n8n。",
            "- 不接券商，不交易，不登录税局，不接财税软件。",
            "- 不真实渲染/发布视频，不写正式规则，不自动解锁红线。",
            "- 不修改总管面板，不修改一键接续包，不重载 19310/19302。",
        ]
    )


def build_boundary_markdown(package: dict[str, Any]) -> str:
    lines = [
        "# 红线解锁分项授权边界说明",
        "",
        "本说明只用于后续人工确认前的边界约束，不构成生效授权。",
        "",
    ]
    for card in package["分项确认单草案"]:
        lines.extend(
            [
                f"## {card['序号']}. {card['红线']}",
                "",
                f"- 总管确认状态：{card['总管确认状态']}",
                f"- 允许生效：{card['允许生效']}",
                f"- 允许自动执行：{card['允许自动执行']}",
                f"- 默认处置：{card['默认处置']}",
                "- 生效前必填项：" + "、".join(card["生效前必填项"]),
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    package = build_package()
    write_json(LATEST_JSON, package)
    write_json(CARDS_JSON, package["分项确认单草案"])
    write_text(LATEST_MD, build_markdown(package))
    write_text(BOUNDARY_MD, build_boundary_markdown(package))
    print(
        json.dumps(
            {
                "状态": package["状态"],
                "确认单数量": len(package["分项确认单草案"]),
                "允许生效数量": sum(1 for card in package["分项确认单草案"] if card["允许生效"]),
                "输出": str(LATEST_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
