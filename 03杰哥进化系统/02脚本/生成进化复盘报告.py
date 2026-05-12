"""
名称：生成进化复盘报告.py
作用：汇总进化系统中的经验卡片，生成阶段性复盘报告和方法资产候选。
触发方式：python 生成进化复盘报告.py
依赖：Python 标准库。
所属系统：03杰哥进化系统
安全边界：只读取 03杰哥进化系统经验数据，只写入复盘报告；不自动修改其他系统配置。
创建/修改记录：2026-04-26 创建进化复盘报告生成脚本。
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def card_dir() -> Path:
    target = system_root() / "03数据" / "01问题卡片"
    target.mkdir(parents=True, exist_ok=True)
    return target


def method_dir() -> Path:
    target = system_root() / "03数据" / "04通用方法"
    target.mkdir(parents=True, exist_ok=True)
    return target


def suggestion_dir() -> Path:
    target = system_root() / "03数据" / "05进化建议"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_cards() -> list[dict[str, Any]]:
    cards = []
    for path in sorted(card_dir().glob("*.json")):
        if path.name == "经验卡片_最新.json":
            continue
        try:
            card = json.loads(path.read_text(encoding="utf-8"))
            card["卡片文件"] = str(path)
            cards.append(card)
        except Exception:
            continue
    return cards


def build_report() -> dict[str, Any]:
    cards = load_cards()
    type_counter = Counter(card.get("卡片类型", "未分类") for card in cards)
    root_counter = Counter(card.get("根因分类", "未分类") for card in cards)
    method_candidates = [
        {
            "方法来源": card.get("卡片文件"),
            "可复用逻辑": card.get("可复用逻辑"),
            "可迁移场景": card.get("可迁移场景", []),
            "不可迁移边界": card.get("不可迁移边界", ""),
            "是否建议固化": card.get("是否建议固化", False),
        }
        for card in cards
        if card.get("可复用逻辑")
    ]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "经验卡片数量": len(cards),
        "经验类型统计": dict(type_counter),
        "根因分类统计": dict(root_counter),
        "方法资产候选数量": len(method_candidates),
        "方法资产候选": method_candidates,
        "结论": "仅生成复盘报告和方法候选，不自动固化配置。",
    }
    output = method_dir() / f"进化复盘报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = method_dir() / "进化复盘报告_最新.json"
    latest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    suggestion = {
        "生成时间": report["生成时间"],
        "建议类型": "方法资产固化候选",
        "建议数量": len([item for item in method_candidates if item.get("是否建议固化")]),
        "建议": [item for item in method_candidates if item.get("是否建议固化")],
        "安全边界": "必须人工确认并通过验收后才能固化到配置或脚本。",
    }
    suggestion_output = suggestion_dir() / f"进化建议_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    suggestion_output.write_text(json.dumps(suggestion, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_suggestion = suggestion_dir() / "进化建议_最新.json"
    latest_suggestion.write_text(json.dumps(suggestion, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"经验卡片数量": len(cards), "方法资产候选数量": len(method_candidates), "输出": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
