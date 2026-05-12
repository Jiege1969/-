# -*- coding: utf-8 -*-
"""
名称：生成研发费用加计扣除核心正式依据时效补齐预演.py
作用：把研发费用加计扣除核心正式依据整理为时效核验矩阵。
安全边界：只读本地政策链预演和复核清单；不联网、不下载、不写正式业务规则、不生成正式税务结论。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
RULE = ROOT / "01配置" / "研发费用加计扣除核心正式依据时效补齐规则.json"
CHAIN_PREVIEW = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案" / "研发费用加计扣除政策链补齐预演_最新.json"
REVIEW_LIST = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案" / "研发费用加计扣除专项人工复核清单_最新.json"
OUT_DIR = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案"
OUT_JSON = OUT_DIR / "研发费用加计扣除核心正式依据时效补齐预演_最新.json"
OUT_MD = OUT_DIR / "研发费用加计扣除核心正式依据时效补齐预演_最新.md"


CURRENT_ALLOWED = {"全文有效", "人工确认有效"}


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def text_blob(item: dict[str, Any]) -> str:
    return json.dumps(item, ensure_ascii=False)


def matches_keywords(item: dict[str, Any], keywords: list[str]) -> bool:
    text = text_blob(item)
    return any(keyword in text for keyword in keywords)


def matches_slot(item: dict[str, Any], slot: dict[str, Any]) -> bool:
    text = text_blob(item)
    slot_id = slot.get("槽位ID")
    if slot_id == "rd-rate-extension":
        return "研发" in text and any(keyword in text for keyword in ["比例", "延续", "提高", "行业"])
    if slot_id == "rd-filing-form":
        return any(keyword in text for keyword in ["预缴纳税申报", "年度纳税申报表", "A107012"])
    return matches_keywords(item, as_list(slot.get("关键词")))


def compact_evidence(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "资料ID": item.get("资料ID", ""),
        "标题": item.get("标题", ""),
        "文号": item.get("文号", ""),
        "发文机关": item.get("发文机关", ""),
        "依据层级": item.get("依据层级", ""),
        "资料角色": item.get("资料角色", ""),
        "发布日期": item.get("发布日期", ""),
        "施行日期": item.get("施行日期", ""),
        "文件时效": item.get("文件时效", ""),
        "来源链接": item.get("来源链接", ""),
        "原文哈希": item.get("原文哈希", ""),
        "本地原文路径": item.get("本地原文路径", ""),
        "本地解析文本路径": item.get("本地解析文本路径", ""),
        "是否当前适用依据候选": item.get("是否当前适用依据候选", False),
        "阻断原因": item.get("阻断原因", []),
    }


def compact_query(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "标题": item.get("标题", ""),
        "文号": item.get("文号", ""),
        "依据层级": item.get("依据层级", ""),
        "文件时效": item.get("文件时效", ""),
        "来源链接": item.get("来源链接", ""),
        "处理状态": item.get("处理状态", "官方查询候选"),
        "阻断原因": item.get("阻断原因", []),
    }


def slot_status(matches: list[dict[str, Any]], query_matches: list[dict[str, Any]]) -> tuple[str, str, bool, list[str]]:
    gaps: list[str] = []
    if not matches and query_matches:
        return "query_candidate_only", "待下载正文、生成哈希和本地证据卡", False, [
            "仅存在官方查询候选，尚未形成本地证据卡。",
            "需下载正文、计算原文哈希、生成解析文本和元数据后再核验时效。",
        ]
    if not matches:
        return "missing_local_evidence", "缺少本地证据", False, [
            "未发现匹配的本地证据卡。",
            "需从官方来源入口补齐资料登记、原文哈希、解析文本和元数据。",
        ]

    has_formal = any(item.get("资料角色") == "正式依据候选" for item in matches)
    has_current = any(item.get("文件时效") in CURRENT_ALLOWED for item in matches)
    missing_validity = [item for item in matches if item.get("文件时效") not in CURRENT_ALLOWED]
    if missing_validity:
        gaps.append("存在本地证据但文件时效缺失或未进入允许状态。")
    if not has_formal:
        gaps.append("匹配资料不是正式依据候选，只能作为解释辅助、案例或线索。")
        return "blocked_auxiliary_only", "辅助材料不得进入当前适用依据候选", False, gaps
    if has_current and not missing_validity:
        return "evidence_ready_pending_human_validity", "已有全文有效或人工确认有效线索，仍需人工复核上下位关系和适用期间", True, gaps
    return "local_evidence_present_but_validity_missing", "本地证据存在但时效缺失或待人工确认", False, gaps


def build_slot(slot: dict[str, Any], cards: list[dict[str, Any]], query_cards: list[dict[str, Any]]) -> dict[str, Any]:
    matches = [card for card in cards if matches_slot(card, slot)]
    query_matches = [card for card in query_cards if matches_slot(card, slot)]
    status, validity_status, enters_candidate, gaps = slot_status(matches, query_matches)
    review_items = [
        f"人工核验{slot.get('槽位名称')}的官方来源、发布机关、文号、发布日期和施行日期。",
        f"人工核验{slot.get('槽位名称')}的全文有效、部分有效、废止、失效或待核实状态。",
        f"人工确认{slot.get('槽位名称')}在研发费用加计扣除政策链中的上下位角色。",
    ]
    if status in {"query_candidate_only", "missing_local_evidence"}:
        review_items.append("补齐本地原文、原文哈希、解析文本和元数据后再进入下一轮时效核验。")
    if status == "local_evidence_present_but_validity_missing":
        review_items.append("不得因本地存在原文就自动认定为当前有效依据。")
    return {
        "槽位ID": slot.get("槽位ID"),
        "槽位名称": slot.get("槽位名称"),
        "期望依据层级": slot.get("期望依据层级"),
        "槽位状态": status,
        "匹配证据": [compact_evidence(item) for item in matches],
        "官方查询候选": [compact_query(item) for item in query_matches],
        "时效核验状态": validity_status,
        "缺口": gaps,
        "人工复核项": review_items,
        "是否进入当前适用依据候选": enters_candidate,
        "是否生成正式税务结论": False,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 研发费用加计扣除核心正式依据时效补齐预演",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 运行状态：{report['运行状态']}",
        f"- 槽位数量：{report['槽位数量']}",
        f"- 可进入当前适用依据候选槽位数量：{report['可进入当前适用依据候选槽位数量']}",
        f"- 仍需补齐槽位数量：{report['仍需补齐槽位数量']}",
        f"- 输出边界：{report['输出边界']}",
        "",
        "## 核心依据时效矩阵",
        "",
    ]
    for slot in report["核心依据时效矩阵"]:
        lines.extend([
            f"### {slot['槽位名称']}",
            f"- 槽位ID：{slot['槽位ID']}",
            f"- 期望依据层级：{slot['期望依据层级']}",
            f"- 槽位状态：{slot['槽位状态']}",
            f"- 时效核验状态：{slot['时效核验状态']}",
            f"- 是否进入当前适用依据候选：{slot['是否进入当前适用依据候选']}",
            f"- 匹配证据数量：{len(slot['匹配证据'])}",
            f"- 官方查询候选数量：{len(slot['官方查询候选'])}",
            "",
        ])
        if slot["匹配证据"]:
            lines.append("匹配证据：")
            for item in slot["匹配证据"]:
                lines.append(f"- {item.get('标题')} | {item.get('文号') or '文号待核验'} | {item.get('文件时效') or '时效待核验'}")
            lines.append("")
        if slot["官方查询候选"]:
            lines.append("官方查询候选：")
            for item in slot["官方查询候选"]:
                lines.append(f"- {item.get('标题')} | {item.get('文号') or '文号待核验'} | {item.get('文件时效') or '时效待核验'}")
            lines.append("")
        lines.append("缺口：")
        for item in slot["缺口"] or ["无"]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("人工复核项：")
        for item in slot["人工复核项"]:
            lines.append(f"- {item}")
        lines.append("")
    lines.extend(["## 总缺口", ""])
    for item in report["总缺口"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rule = load_json(RULE)
    chain = load_json(CHAIN_PREVIEW)
    review = load_json(REVIEW_LIST)
    slots = [
        build_slot(slot, as_list(chain.get("证据卡片")), as_list(chain.get("官方查询候选")))
        for slot in as_list(rule.get("核心依据槽位"))
    ]
    gaps = []
    for slot in slots:
        if not slot["是否进入当前适用依据候选"]:
            gaps.append(f"{slot['槽位名称']}：{slot['时效核验状态']}")
    report = {
        "名称": "研发费用加计扣除核心正式依据时效补齐预演",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则来源": str(RULE),
        "政策链预演来源": str(CHAIN_PREVIEW),
        "专项人工复核清单来源": str(REVIEW_LIST),
        "运行状态": rule.get("运行状态"),
        "资产身份": rule.get("资产身份"),
        "槽位数量": len(slots),
        "可进入当前适用依据候选槽位数量": sum(1 for slot in slots if slot["是否进入当前适用依据候选"]),
        "仍需补齐槽位数量": sum(1 for slot in slots if not slot["是否进入当前适用依据候选"]),
        "原政策链状态": chain.get("链条状态"),
        "原专项复核链条状态": review.get("链条状态"),
        "核心依据时效矩阵": slots,
        "总缺口": gaps,
        "输出边界": "只输出核心依据槽位、时效核验状态、缺口和人工复核项；不输出适用判断或正式税务结论。",
        "安全边界": rule.get("安全边界", {}),
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "状态": "完成",
        "槽位数量": report["槽位数量"],
        "仍需补齐槽位数量": report["仍需补齐槽位数量"],
        "输出": str(OUT_MD),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
