# -*- coding: utf-8 -*-
"""
名称：生成研发费用加计扣除政策链补齐预演.py
作用：只读梳理本地已有研发费用加计扣除资料，形成分层政策证据链补齐预演。
安全边界：不联网、不下载、不写正式规则、不生成正式税务结论、不接电子税务局或财税软件。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
SOURCE = ROOT / "03数据" / "15关联附件下载预演" / "运行报告" / "税收附件与关联链接受控下载预演_最新.json"
QUERY_REPORT = ROOT / "03数据" / "13智能政策下载管道" / "运行报告" / "税收政策智能查询下载管道报告_最新.json"
OUT_DIR = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案"
OUT_JSON = OUT_DIR / "研发费用加计扣除政策链补齐预演_最新.json"
OUT_MD = OUT_DIR / "研发费用加计扣除政策链补齐预演_最新.md"

FORMAL_LEVELS = {"法律", "行政法规", "财税文件", "税务规范性文件", "部门规章"}
CURRENT_ALLOWED = {"全文有效", "人工确认有效"}


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_text(path_text: str) -> str:
    if not path_text:
        return ""
    path = Path(path_text)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def relevant(item: dict[str, Any]) -> bool:
    text = json.dumps(item, ensure_ascii=False)
    markers = ["研发费用", "加计扣除", "研究开发费用", "A107012", "企业所得税法"]
    return any(marker in text for marker in markers)


def evidence_level(item: dict[str, Any]) -> str:
    title = str(item.get("标题", ""))
    if "企业所得税法" in title:
        return "法律"
    if "实施条例" in title:
        return "行政法规"
    if "财政部" in title or "财税" in title or "研究开发费用税前加计扣除政策" in title:
        return "财税文件"
    if "公告" in title:
        return "税务规范性文件"
    if "指引" in title or "解读" in title:
        return "政策解读"
    if "案例" in title or "问答" in title:
        return "案例"
    if item.get("文件类型") == "附件" or item.get("资料类别") == "附件":
        return "附件"
    return "关联材料"


def material_role(level: str) -> str:
    if level in FORMAL_LEVELS:
        return "正式依据候选"
    if level == "政策解读":
        return "解释辅助"
    if level == "案例":
        return "事实识别与风险提示"
    if level == "附件":
        return "附件入口"
    return "关联线索"


def extract_doc_no(text: str) -> str:
    match = re.search(r"(财税〔\d{4}〕\d+号)", text)
    return match.group(1) if match else ""


def extract_issue_date(text: str) -> str:
    match = re.search(r"成文日期：(\d{4})-(\d{2})-(\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if match:
        return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
    return ""


def extract_effective_date(text: str) -> str:
    match = re.search(r"本通知自(\d{4})年(\d{1,2})月(\d{1,2})日起执行", text)
    if match:
        return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
    return ""


def extract_page_note(text: str) -> str:
    marker = "该文件非由国家税务总局牵头制定，查询结果仅供参考"
    return marker if marker in text else ""


def extract_key_clauses(text: str) -> list[str]:
    clauses = []
    markers = ["本通知所称研发活动", "允许加计扣除的研发费用", "下列活动不适用税前加计扣除政策", "本通知适用于", "本通知自"]
    compact = re.sub(r"\s+", " ", text)
    sentences = [item.strip() for item in re.split(r"(?<=[。；])", compact) if item.strip()]
    for sentence in sentences:
        if any(marker in sentence for marker in markers):
            clauses.append(sentence[:260])
        if len(clauses) >= 5:
            break
    return clauses


def block_reasons(item: dict[str, Any], level: str) -> list[str]:
    reasons: list[str] = []
    if not item.get("来源链接") and not item.get("最终链接"):
        reasons.append("来源链接缺失。")
    if not item.get("本地原文路径"):
        reasons.append("本地原文路径缺失。")
    if item.get("文件类型") == "网页正文" and not item.get("本地解析文本路径"):
        reasons.append("本地解析文本路径缺失。")
    if item.get("文件时效") not in CURRENT_ALLOWED:
        reasons.append(f"文件时效未进入当前适用候选：{item.get('文件时效') or '缺失'}。")
    if level not in FORMAL_LEVELS:
        reasons.append(f"{level}不能单独支撑当前适用依据。")
    if "案例" in level:
        reasons.append("案例只能用于事实识别和风险提示，不能替代正式依据。")
    if level == "附件" and not item.get("本地解析文本路径"):
        reasons.append("附件未完成正式正文解析。")
    return reasons


def build_card(item: dict[str, Any]) -> dict[str, Any]:
    text = read_text(item.get("本地解析文本路径", ""))
    title = item.get("标题", "")
    level = evidence_level(item)
    is_formal = level in FORMAL_LEVELS
    reasons = block_reasons(item, level)
    page_note = extract_page_note(text) if is_formal else ""
    if page_note:
        reasons.append("页面提示该文件非由国家税务总局牵头制定，需回到财政部等联合发文来源复核。")
    current_candidate = level in FORMAL_LEVELS and item.get("文件时效") in CURRENT_ALLOWED and not reasons
    if level == "法律" and item.get("文件时效") in CURRENT_ALLOWED:
        reasons.append("上位法可作导航依据，但不能单独支撑研发费用加计扣除具体适用。")
    return {
        "资料ID": item.get("资料ID", ""),
        "标题": title,
        "文号": item.get("文号", "") or (extract_doc_no(text) if is_formal else ""),
        "发文机关": item.get("发文机关", "") or ("财政部 国家税务总局 科技部" if is_formal and "财政部 国家税务总局 科技部" in text else ""),
        "依据层级": level,
        "资料角色": material_role(level),
        "发布日期": item.get("发布日期", "") or (extract_issue_date(text) if is_formal else ""),
        "施行日期": item.get("施行日期", "") or (extract_effective_date(text) if is_formal else ""),
        "文件时效": item.get("文件时效", ""),
        "页面提示": page_note,
        "来源名称": item.get("来源名称", ""),
        "来源链接": item.get("最终链接") or item.get("来源链接", ""),
        "原文哈希": item.get("原文哈希", ""),
        "本地原文路径": item.get("本地原文路径", ""),
        "本地解析文本路径": item.get("本地解析文本路径", ""),
        "本地元数据路径": item.get("本地元数据路径", ""),
        "是否当前适用依据候选": current_candidate,
        "关键条款摘录": extract_key_clauses(text) if is_formal else [],
        "阻断原因": reasons,
        "人工复核状态": item.get("人工复核状态", "未人工复核"),
    }


def chain_gaps(cards: list[dict[str, Any]]) -> list[str]:
    gaps = []
    titles = " ".join(card.get("标题", "") for card in cards)
    has_119 = any("119" in card.get("标题", "") or "完善研究开发费用税前加计扣除政策" in card.get("标题", "") for card in cards)
    has_current_119 = any(
        ("119" in card.get("标题", "") or "完善研究开发费用税前加计扣除政策" in card.get("标题", ""))
        and card.get("文件时效") in CURRENT_ALLOWED
        for card in cards
    )
    if "企业所得税法" not in titles:
        gaps.append("缺少企业所得税法研发费用上位法条款的可复核卡片。")
    if not has_119:
        gaps.append("缺少财税〔2015〕119号或同等核心财税文件入口。")
    if has_119 and not has_current_119:
        gaps.append("财税〔2015〕119号相关资料已有本地入口，但文件时效未确认，不能进入当前适用候选。")
    if not any(card.get("依据层级") == "行政法规" for card in cards):
        gaps.append("缺少企业所得税法实施条例等行政法规层级的可复核卡片。")
    if not any("比例" in card.get("标题", "") or "延续" in card.get("标题", "") or "提高" in card.get("标题", "") for card in cards):
        gaps.append("后续比例、延续、行业范围政策链未闭环。")
    if any(card.get("依据层级") == "附件" and not card.get("本地解析文本路径") for card in cards):
        gaps.append("部分附件尚未完成正式正文解析，不能引用附件内容。")
    return gaps


def query_candidate_cards(report: dict[str, Any]) -> list[dict[str, Any]]:
    cards = []
    for item in report.get("官方查询", {}).get("候选资料", []):
        if not relevant(item):
            continue
        level = evidence_level(item)
        cards.append({
            "标题": item.get("标题", ""),
            "文号": item.get("文号", ""),
            "依据层级": level,
            "资料角色": material_role(level),
            "发布日期": item.get("发布日期", ""),
            "文件时效": item.get("文件时效", ""),
            "来源名称": item.get("来源名称", ""),
            "来源链接": item.get("来源链接", ""),
            "处理状态": "官方查询候选，尚未下载正文，尚未形成本地证据卡。",
            "阻断原因": [
                "尚未下载并计算原文哈希。",
                "尚未生成本地解析文本和元数据路径。",
                "尚未人工核验文件时效和适用层级。",
            ],
        })
    return cards


def build_report() -> dict[str, Any]:
    source = load_json(SOURCE, {"下载结果": []})
    query_report = load_json(QUERY_REPORT, {"官方查询": {"候选资料": []}})
    cards = [build_card(item) for item in source.get("下载结果", []) if relevant(item)]
    query_cards = query_candidate_cards(query_report)
    current_candidates = [card for card in cards if card.get("是否当前适用依据候选")]
    gaps = chain_gaps(cards)
    if query_cards:
        gaps.append("已发现新的官方查询候选，但尚未下载正文、生成哈希和本地解析文本。")
    status = "evidence_ready" if len(current_candidates) >= 2 and not gaps else "pending_review"
    return {
        "名称": "研发费用加计扣除政策链补齐预演",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "资产身份": "政策证据底座，不是税务结论库，不是办税执行系统。",
        "模式": "local_only_policy_chain_preview",
        "证据来源": str(SOURCE),
        "官方查询报告": str(QUERY_REPORT),
        "资料数量": len(cards),
        "官方查询候选数量": len(query_cards),
        "当前适用依据候选数量": len(current_candidates),
        "链条状态": status,
        "输出边界": "仅输出政策证据链、分层、缺口和人工复核项；不输出能否享受研发费用加计扣除的正式税务结论。",
        "证据卡片": cards,
        "官方查询候选": query_cards,
        "政策链缺口": gaps,
        "人工复核项": [
            "核验财税〔2015〕119号及后续比例、延续、行业范围政策的全文有效状态。",
            "核验企业所得税法、实施条例、财税文件、税务规范性文件之间的上下位关系。",
            "核验企业主体、所属期间、研发项目事实、费用归集、辅助账和留存备查资料。",
            "案例和指引只能作为解释、风险提示或事实字段线索，不得替代正式依据。",
        ],
        "安全边界": {
            "是否联网": False,
            "是否下载": False,
            "是否覆盖原始资料": False,
            "是否写正式业务规则": False,
            "是否生成正式税务结论": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 研发费用加计扣除政策链补齐预演",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 链条状态：{report['链条状态']}",
        f"- 资料数量：{report['资料数量']}",
        f"- 官方查询候选数量：{report['官方查询候选数量']}",
        f"- 当前适用依据候选数量：{report['当前适用依据候选数量']}",
        f"- 输出边界：{report['输出边界']}",
        "",
        "## 政策链缺口",
        "",
    ]
    for gap in report.get("政策链缺口", []):
        lines.append(f"- {gap}")
    lines.extend(["", "## 证据卡片", ""])
    for card in report.get("证据卡片", []):
        lines.extend([
            f"### {card.get('标题')}",
            f"- 文号：{card.get('文号') or '待核验'}",
            f"- 发文机关：{card.get('发文机关') or '待核验'}",
            f"- 依据层级：{card.get('依据层级')}",
            f"- 资料角色：{card.get('资料角色')}",
            f"- 发布日期：{card.get('发布日期') or '待核验'}",
            f"- 施行日期：{card.get('施行日期') or '待核验'}",
            f"- 文件时效：{card.get('文件时效')}",
            f"- 当前适用依据候选：{card.get('是否当前适用依据候选')}",
            f"- 来源链接：{card.get('来源链接')}",
            f"- 页面提示：{card.get('页面提示') or '无'}",
            f"- 阻断原因：{'；'.join(card.get('阻断原因', [])) or '无'}",
            "",
        ])
        if card.get("关键条款摘录"):
            lines.append("关键条款摘录：")
            for clause in card.get("关键条款摘录", []):
                lines.append(f"- {clause}")
            lines.append("")
    lines.extend(["## 官方查询候选", ""])
    for card in report.get("官方查询候选", []):
        lines.extend([
            f"- {card.get('标题')} | {card.get('文号') or '文号待核验'} | {card.get('文件时效') or '时效待核验'}",
            f"  {card.get('来源链接')}",
        ])
    lines.extend(["## 人工复核项", ""])
    for item in report.get("人工复核项", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    write_json(OUT_JSON, report)
    write_text(OUT_MD, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "链条状态": report["链条状态"],
        "资料数量": report["资料数量"],
        "当前适用依据候选数量": report["当前适用依据候选数量"],
        "输出": str(OUT_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
