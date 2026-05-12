"""
名称：提炼通用方法库.py
作用：从经验卡片中提炼可复用通用方法，生成方法库草案和固化候选。
触发方式：python 提炼通用方法库.py
依赖：Python 标准库。
所属系统：03杰哥进化系统
安全边界：只读取经验卡片并写入通用方法目录；不自动修改配置、提示词、脚本或工作流。
创建/修改记录：2026-04-26 创建通用方法库提炼脚本。
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def card_dir() -> Path:
    return system_root() / "03数据" / "01问题卡片"


def method_dir() -> Path:
    target = system_root() / "03数据" / "04通用方法"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_cards() -> list[dict[str, Any]]:
    cards = []
    for path in sorted(card_dir().glob("EXP-*.json")):
        try:
            card = load_json(path)
            card["卡片文件"] = str(path)
            cards.append(card)
        except Exception:
            continue
    return cards


def method_name_for(card: dict[str, Any]) -> str:
    logic = card.get("可复用逻辑", "")
    if "自" in logic and "排除自身" in logic:
        return "自动发现边界控制"
    if "编码" in logic or "无歧义" in logic:
        return "机器输出与人类文档编码分层"
    if "控制文件" in logic or "元数据" in logic:
        return "控制数据与业务数据分层"
    if "回环" in logic or "真实联调" in logic:
        return "先回环后真实联调"
    if "高风险" in logic or "可信" in logic:
        return "高风险依据分层"
    if "配置和代码边界" in logic or "跨语言" in logic:
        return "跨语法边界检查"
    return "通用根因复盘"


def build_method_assets() -> dict[str, Any]:
    cards = load_cards()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        grouped[method_name_for(card)].append(card)

    methods = []
    for name, items in sorted(grouped.items()):
        scenarios = sorted({scenario for card in items for scenario in card.get("可迁移场景", [])})
        boundaries = sorted({card.get("不可迁移边界", "") for card in items if card.get("不可迁移边界")})
        methods.append(
            {
                "方法名": name,
                "来源卡片": [card.get("卡片ID") for card in items],
                "核心逻辑": "；".join(sorted({card.get("可复用逻辑", "") for card in items if card.get("可复用逻辑")})),
                "适用场景": scenarios,
                "不可迁移边界": boundaries,
                "验证方式": [
                    "先生成草案或回环结果",
                    "运行对应底座验收",
                    "通过总体验收后再建议固化",
                    "涉及真实发送、写库、接管生产时必须人工确认"
                ],
                "建议固化": any(card.get("是否建议固化") for card in items),
                "固化状态": "候选",
            }
        )

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "经验卡片数量": len(cards),
        "通用方法数量": len(methods),
        "是否自动固化": False,
        "通用方法": methods,
        "结论": "仅生成通用方法库候选，固化到配置或脚本前必须人工确认并验收。",
    }
    output = method_dir() / f"通用方法库_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = method_dir() / "通用方法库_最新.json"
    latest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通用方法数量": len(methods), "输出": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_method_assets()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
