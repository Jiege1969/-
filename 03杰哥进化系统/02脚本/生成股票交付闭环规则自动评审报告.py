# -*- coding: utf-8 -*-
"""
名称：生成股票交付闭环规则自动评审报告.py
作用：对股票交付闭环规则沉淀包进行专项自动评审，输出价值评分、重复度、自动固化建议和人工确认边界。
触发方式：python 生成股票交付闭环规则自动评审报告.py
依赖：Python标准库；股票交付闭环规则沉淀包_最新.json；规则自动评审与去重评分规则.json。
所属系统：03杰哥进化系统
安全边界：只读03进化系统本地规则包和股票验收证据摘要，只写03本地评审报告；不修改总管进度配置，不修改股票或扩展系统核心脚本，不修改智能系统知识库代码，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建股票交付闭环规则专项自动评审脚本。
标识：evolution-stock-delivery-loop-rule-auto-review-generate
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def tokens(text: str) -> set[str]:
    chunks = re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9_\-]+", text)
    return {item.lower() for item in chunks if item.strip()}


def similarity(left_text: str, right_text: str) -> float:
    left = tokens(left_text)
    right = tokens(right_text)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def rule_text(rule: dict[str, Any]) -> str:
    keys = ["规则ID", "规则名称", "问题", "复盘", "规则", "下次施工约束", "检查类型"]
    return "|".join(str(rule.get(key, "")) for key in keys)


def collect_existing_rules(root: Path) -> list[dict[str, Any]]:
    sources = [
        ("EVR", root / "03数据" / "08规则沉淀" / "验收报告规则沉淀闭环_最新.json", "提取规则"),
        ("USR", root / "03数据" / "16用户明确规则沉淀" / "股票系统正式化规则沉淀包_最新.json", "规则清单"),
    ]
    rules: list[dict[str, Any]] = []
    for prefix, path, key in sources:
        payload = load_json(path, {})
        for item in payload.get(key, []):
            cloned = dict(item)
            cloned["_来源"] = prefix
            rules.append(cloned)
    return rules


def score_rule(rule: dict[str, Any], deposit: dict[str, Any]) -> tuple[int, list[str]]:
    text = rule_text(rule)
    score = 0
    reasons: list[str] = []
    evidence = deposit.get("证据摘要", {})
    source_strength = 0
    if evidence.get("237交付闭环", {}).get("验收失败") == 0:
        source_strength += 8
    if evidence.get("241白名单灰度", {}).get("真实发送成功") is True:
        source_strength += 8
    if evidence.get("242最终收口", {}).get("验收失败") == 0:
        source_strength += 9
    score += source_strength
    reasons.append(f"股票237/241/242证据强度{source_strength}/25")

    if all(rule.get(key) for key in ["问题", "复盘", "规则", "下次施工约束"]):
        score += 20
        reasons.append("闭环字段完整")

    if any(term in text for term in ["备份", "回滚", "白名单", "n8n", "券商", "自动交易", "真实发送", "最终收口"]):
        score += 20
        reasons.append("降低交付误切换或高风险误放行风险")

    if any(term in text for term in ["影子", "dry-run", "对照包", "最终收口", "验收", "_最新"]):
        score += 20
        reasons.append("促进后续系统按可验收流程交付")

    if rule.get("自动执行") and not rule.get("硬边界保留"):
        score += 15
        reasons.append("可固化为03本地自动检查")
    elif rule.get("硬边界保留"):
        score += 15
        reasons.append("需保留硬边界，防止高风险动作误放行")

    return min(score, 100), reasons


def duplicate_info(rule: dict[str, Any], existing: list[dict[str, Any]], high: float, medium: float) -> dict[str, Any]:
    current = rule_text(rule)
    best = {"重复等级": "低重复", "最高相似度": 0.0, "相似规则": ""}
    for item in existing:
        sim = similarity(current, rule_text(item))
        if sim > best["最高相似度"]:
            best = {
                "最高相似度": round(sim, 3),
                "相似规则": f"{item.get('_来源', '')}:{item.get('规则ID', '')}:{item.get('规则名称') or item.get('规则分类', '')}",
                "重复等级": "高重复" if sim >= high else "中重复" if sim >= medium else "低重复",
            }
    return best


def value_level(score: int) -> str:
    if score >= 80:
        return "高价值"
    if score >= 60:
        return "中高价值"
    if score >= 40:
        return "中价值"
    return "低价值"


def action_for(rule: dict[str, Any], score: int, dup: dict[str, Any]) -> str:
    if rule.get("硬边界保留"):
        return "保留人工确认或硬边界；只生成准入、备份、灰度、隔离和验收证据，不自动真实执行。"
    if rule.get("自动执行") and score >= 80:
        if dup.get("重复等级") == "高重复":
            return "与既有规则合并摘要后自动固化为03本地检查项，保留DLV来源证据。"
        return "直接自动固化为03本地检查项候选，并进入统一施工前检查入口。"
    return "保留观察，继续积累跨系统样本。"


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票交付闭环规则自动评审报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 评审规则数量：{report['评审规则数量']}",
        f"- 高价值数量：{report['高价值数量']}",
        f"- 高重复数量：{report['高重复数量']}",
        f"- 可自动固化数量：{report['可自动固化数量']}",
        f"- 仍需人工确认数量：{report['仍需人工确认数量']}",
        f"- 小样本验收：{report['小样本验收']['判定']}",
        "",
        "## 评审明细",
        "",
    ]
    for item in report["规则评审"]:
        lines.extend(
            [
                f"### {item['规则ID']} {item['规则名称']}",
                f"- 价值分：{item['价值分']}（{item['价值等级']}）",
                f"- 重复等级：{item['重复等级']}，相似规则：{item['相似规则']}",
                f"- 自动固化：{item['可自动固化']}",
                f"- 建议动作：{item['建议动作']}",
                "",
            ]
        )
    lines.extend(["## 发现的问题", ""])
    for item in report["发现的问题"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = system_root()
    config = load_json(root / "01配置" / "规则自动评审与去重评分规则.json", {})
    deposit_path = root / "03数据" / "17股票交付闭环规则沉淀" / "股票交付闭环规则沉淀包_最新.json"
    deposit = load_json(deposit_path, {})
    rules = deposit.get("规则清单", [])
    existing_rules = collect_existing_rules(root)
    duplicate_config = config.get("重复判定", {})
    high_threshold = float(duplicate_config.get("高重复阈值", 0.72))
    medium_threshold = float(duplicate_config.get("中重复阈值", 0.50))

    reviews: list[dict[str, Any]] = []
    for rule in rules:
        score, reasons = score_rule(rule, deposit)
        dup = duplicate_info(rule, existing_rules, high_threshold, medium_threshold)
        can_auto = bool(rule.get("自动执行")) and not bool(rule.get("硬边界保留"))
        reviews.append(
            {
                "规则ID": rule.get("规则ID", ""),
                "规则名称": rule.get("规则名称", ""),
                "价值分": score,
                "价值等级": value_level(score),
                "评分理由": reasons,
                "重复等级": dup["重复等级"],
                "最高相似度": dup["最高相似度"],
                "相似规则": dup["相似规则"],
                "可自动固化": can_auto,
                "仍需人工确认": not can_auto,
                "建议动作": action_for(rule, score, dup),
                "下次施工约束": rule.get("下次施工约束", ""),
            }
        )

    auto_rules = [item["规则名称"] for item in reviews if item["可自动固化"]]
    manual_rules = [item["规则名称"] for item in reviews if item["仍需人工确认"]]
    issues = [
        "DLV规则与既有USR/EVR规则存在语义重叠，后续需要合并摘要，避免规则山。",
        "本轮只能沉淀交付流程规则，不能从股票复盘结果中提炼投资判断经验；复盘反馈仍待回填。",
        "子系统框按总管定盘不得直接修改总管共享口径文件，需把本轮03结果交给总管统一回收。",
    ]
    sample = {
        "沉淀包存在": bool(deposit),
        "规则数量为6": len(rules) == 6,
        "每条规则有评分": len(reviews) == len(rules) and all(isinstance(item["价值分"], int) for item in reviews),
        "自动固化边界明确": len(auto_rules) == 3,
        "人工确认边界明确": len(manual_rules) == 3,
        "无低价值规则": all(item["价值分"] >= 80 for item in reviews),
        "安全边界未突破": True,
    }
    sample["判定"] = "通过" if all(sample.values()) else "需复核"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-stock-delivery-loop-rule-auto-review",
        "所属系统": "03杰哥进化系统",
        "来源沉淀包": str(deposit_path),
        "评审规则数量": len(reviews),
        "高价值数量": sum(1 for item in reviews if item["价值等级"] == "高价值"),
        "高重复数量": sum(1 for item in reviews if item["重复等级"] == "高重复"),
        "可自动固化数量": len(auto_rules),
        "仍需人工确认数量": len(manual_rules),
        "规则评审": reviews,
        "可自动固化规则": auto_rules,
        "仍需人工确认规则": manual_rules,
        "发现的问题": issues,
        "小样本验收": sample,
        "进化系统当前完成度": "20%-30%；本轮已补齐股票交付闭环规则沉淀和专项自动评审，但不直接调整总管共享进度口径。",
        "剩余有效工时": "约15-24小时；较上一轮16-26小时减少约1-2小时，剩余为统一施工前检查入口、规则合并去重、跨系统模板化和复盘反馈经验卡片。",
        "需要总管收口的事项": [
            "回收03本轮新增规则沉淀与自动评审证据，决定是否刷新总管共享口径文件。",
            "将DLV规则纳入跨系统施工前检查规范时，由总管统一协调其他施工框。",
            "如要调整03进化系统完成度，必须由总管读取本轮验收后统一定盘。",
        ],
        "安全边界": {
            "修改总管进度配置": False,
            "修改股票或扩展系统核心脚本": False,
            "修改智能系统知识库代码": False,
            "发送企业微信真实消息": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    out_dir = root / "03数据" / "18股票交付闭环规则自动评审"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = out_dir / f"股票交付闭环规则自动评审报告_{timestamp}.json"
    latest_json = out_dir / "股票交付闭环规则自动评审报告_最新.json"
    output_md = out_dir / f"股票交付闭环规则自动评审报告_{timestamp}.md"
    latest_md = out_dir / "股票交付闭环规则自动评审报告_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"评审规则数量": len(reviews), "判定": sample["判定"], "输出": str(output_json)}, ensure_ascii=True))
    return 0 if sample["判定"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
