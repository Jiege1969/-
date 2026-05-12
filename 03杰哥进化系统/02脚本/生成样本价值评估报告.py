"""
名称：生成样本价值评估报告.py
作用：按照样本生命周期和经验价值评分规则评估经验卡片，生成归档候选和清理候选报告。
触发方式：python 生成样本价值评估报告.py
依赖：Python 标准库。
所属系统：03杰哥进化系统
安全边界：只生成评估报告和候选清单；不删除、不移动、不压缩任何样本文件。
创建/修改记录：2026-04-26 创建样本价值评估报告脚本。
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def config_dir() -> Path:
    return system_root() / "01配置"


def card_dir() -> Path:
    return system_root() / "03数据" / "01问题卡片"


def report_dir() -> Path:
    target = system_root() / "03数据" / "05进化建议"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def load_cards() -> list[dict[str, Any]]:
    cards = []
    for path in sorted(card_dir().glob("*.json")):
        if path.name in {"经验卡片_最新.json", "首批真实经验卡片_最新.json"}:
            continue
        try:
            card = load_json(path)
            card["样本文件"] = str(path)
            card["sha256"] = file_sha256(path)
            cards.append(card)
        except Exception:
            continue
    return cards


def score_card(card: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons = []
    if card.get("根本原因"):
        score += 25
        reasons.append("揭示根因")
    if card.get("可迁移场景"):
        score += 20
        reasons.append("可迁移")
    if card.get("可复用逻辑"):
        score += 20
        reasons.append("已产生方法资产候选")
    if card.get("是否建议固化"):
        score += 5
        reasons.append("建议固化")
    text = json.dumps(card, ensure_ascii=False)
    if any(keyword in text for keyword in ["真实发送", "写入", "涉税", "投资", "生产", "接管", "Qdrant"]):
        score += 15
        reasons.append("涉及高风险边界")
    return score, reasons


def level_for(score: int, levels: list[dict[str, Any]]) -> str:
    ordered = sorted(levels, key=lambda item: int(item.get("最低分", 0)), reverse=True)
    for item in ordered:
        if score >= int(item.get("最低分", 0)):
            return item.get("等级", "未分级")
    return "未分级"


def duplicate_groups(cards: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        key = "|".join([
            card.get("问题现象", ""),
            card.get("根本原因", ""),
            card.get("可复用逻辑", ""),
        ])
        groups[key].append(card)
    return {key: value for key, value in groups.items() if len(value) > 1}


def build_report() -> dict[str, Any]:
    lifecycle = load_json(config_dir() / "样本生命周期规则.json")
    score_rules = load_json(config_dir() / "经验价值评分规则.json")
    cards = load_cards()
    groups = duplicate_groups(cards)
    duplicate_paths = {card["样本文件"] for group in groups.values() for card in group[1:]}

    evaluated = []
    archive_candidates = []
    cleanup_candidates = []
    for card in cards:
        score, reasons = score_card(card)
        level = level_for(score, score_rules.get("等级", []))
        status = card.get("经验状态", "待复盘")
        item = {
            "卡片ID": card.get("卡片ID", ""),
            "样本文件": card.get("样本文件"),
            "sha256": card.get("sha256"),
            "卡片类型": card.get("卡片类型"),
            "经验状态": status,
            "价值分": score,
            "价值等级": level,
            "评分理由": reasons,
            "是否重复样本": card.get("样本文件") in duplicate_paths,
            "摘要": card.get("问题现象", "")[:160],
        }
        evaluated.append(item)
        if status in {"已提炼", "建议固化", "已固化"}:
            archive_candidates.append(item)
        if item["是否重复样本"] and status in {"已提炼", "已固化"}:
            cleanup_candidates.append({**item, "清理建议": "重复样本候选，仅保留摘要和哈希，等待用户确认。"})

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "样本数量": len(cards),
        "生命周期原则": lifecycle.get("核心原则"),
        "是否执行清理": False,
        "是否移动文件": False,
        "是否删除文件": False,
        "高价值数量": sum(1 for item in evaluated if item["价值等级"] == "高价值"),
        "归档候选数量": len(archive_candidates),
        "清理候选数量": len(cleanup_candidates),
        "样本评估": evaluated,
        "归档候选": archive_candidates,
        "清理候选": cleanup_candidates,
        "清理前置条件": lifecycle.get("清理前置条件", []),
        "结论": "仅生成价值评估和清理候选；任何清理必须人工确认。",
    }
    output = report_dir() / f"样本价值评估报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = report_dir() / "样本价值评估报告_最新.json"
    latest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"样本数量": len(cards), "清理候选数量": len(cleanup_candidates), "输出": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
