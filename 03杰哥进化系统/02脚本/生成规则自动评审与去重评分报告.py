# -*- coding: utf-8 -*-
"""
名称：生成规则自动评审与去重评分报告.py
作用：读取规则沉淀闭环和闸口纠偏规则包，自动评审规则价值、重复度、过时闸口风险和下一步施工动作。
触发方式：python 生成规则自动评审与去重评分报告.py
依赖：Python标准库；规则自动评审与去重评分规则.json。
所属系统：03杰哥进化系统
安全边界：只读03进化系统本地规则包，只写03本地评审报告；不修改其他系统业务代码，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建规则自动评审与去重评分报告脚本。
标识：evolution-rule-auto-review-dedupe-generate
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


def similarity(a: str, b: str) -> float:
    left = tokens(a)
    right = tokens(b)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def rule_text(rule: dict[str, Any]) -> str:
    return "|".join(str(rule.get(key, "")) for key in ["规则分类", "问题", "复盘", "规则", "下次施工约束", "固化级别"])


def score_rule(rule: dict[str, Any], config: dict[str, Any]) -> tuple[int, list[str], bool]:
    text = rule_text(rule)
    category = str(rule.get("规则分类", ""))
    source_count = int(rule.get("来源报告数量", 0) or 0)
    score = min(25, source_count // 2)
    reasons = [f"来源报告{source_count}份"]

    if all(rule.get(key) for key in ["问题", "复盘", "规则", "下次施工约束"]):
        score += 20
        reasons.append("闭环字段完整")

    if any(keyword in text for keyword in ["高风险", "真实发送", "n8n", "券商", "自动交易", "写正式库", "生产"]):
        score += 20
        reasons.append("降低高风险动作误触发")
    elif category in {"影子与dry-run先行", "上游验收闸口", "证据来源与降级边界", "分阶段治理"}:
        score += 20
        reasons.append("降低切换或治理误推进风险")

    positive_hit = any(keyword in text for keyword in config.get("持续施工正向关键词", []))
    if positive_hit or category in {"影子与dry-run先行", "上游验收闸口", "分阶段治理", "回滚与停止开关"}:
        score += 20
        reasons.append("促进持续施工")

    if rule.get("可自动固化"):
        score += 15
        reasons.append("可自动验收或固化为本地检查项")

    stale_gate = (
        any(keyword in text for keyword in config.get("过时闸口关键词", []))
        and not positive_hit
        and category not in {"高风险动作默认关闭", "人工确认闸口", "回滚与停止开关"}
        and not rule.get("可自动固化")
    )
    if stale_gate:
        score = max(0, score - 20)
        reasons.append("疑似过时停工闸口")

    return min(100, score), reasons, stale_gate


def level_for(score: int) -> str:
    if score >= 70:
        return "高价值"
    if score >= 40:
        return "中价值"
    return "低价值"


def action_for(score: int, duplicate_level: str, stale_gate: bool, hard_risk: bool, config: dict[str, Any]) -> str:
    actions = config.get("建议动作", {})
    if stale_gate:
        return actions.get("过时闸口", "生成纠偏建议")
    if hard_risk:
        return actions.get("高风险真实动作", "保留硬阻断")
    if score >= 70 and duplicate_level == "高重复":
        return actions.get("高价值高重复", "合并同类表达")
    if score >= 70:
        return actions.get("高价值低重复", "进入本地检查项候选")
    return "保留观察，继续积累样本"


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 规则自动评审与去重评分报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 评审规则数量：{report['评审规则数量']}",
        f"- 高价值数量：{report['高价值数量']}",
        f"- 高重复数量：{report['高重复数量']}",
        f"- 过时闸口风险数量：{report['过时闸口风险数量']}",
        "",
        "## 下一步施工队列",
        "",
    ]
    for item in report["下一步施工队列"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 规则评分", ""])
    for item in report["规则评审"]:
        lines.extend(
            [
                f"### {item['规则ID']} {item['规则分类']}",
                f"- 价值分：{item['价值分']}（{item['价值等级']}）",
                f"- 重复等级：{item['重复等级']}",
                f"- 建议动作：{item['建议动作']}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    root = system_root()
    config = load_json(root / "01配置" / "规则自动评审与去重评分规则.json", {})
    loop = load_json(root / "03数据" / "08规则沉淀" / "验收报告规则沉淀闭环_最新.json", {})
    gate = load_json(root / "03数据" / "09闸口纠偏" / "闸口纠偏持续施工规则包_最新.json", {})
    rules = list(loop.get("提取规则", []))
    hard_terms = set(gate.get("仍需硬阻断的真实动作", []))

    reviews: list[dict[str, Any]] = []
    texts = [rule_text(item) for item in rules]
    for index, rule in enumerate(rules):
        sims = [similarity(texts[index], other) for other_index, other in enumerate(texts) if other_index != index]
        max_sim = max(sims) if sims else 0.0
        if max_sim >= float(config.get("重复判定", {}).get("高重复阈值", 0.72)):
            duplicate_level = "高重复"
        elif max_sim >= float(config.get("重复判定", {}).get("中重复阈值", 0.50)):
            duplicate_level = "中重复"
        else:
            duplicate_level = "低重复"
        score, reasons, stale_gate = score_rule(rule, config)
        text = rule_text(rule)
        hard_risk = any(term in text for term in hard_terms) or any(term in text for term in ["券商", "自动交易", "下单", "资金账户"])
        reviews.append(
            {
                "规则ID": rule.get("规则ID", ""),
                "规则分类": rule.get("规则分类", ""),
                "价值分": score,
                "价值等级": level_for(score),
                "评分理由": reasons,
                "最大重复度": round(max_sim, 3),
                "重复等级": duplicate_level,
                "过时闸口风险": stale_gate,
                "高风险真实动作": hard_risk,
                "建议动作": action_for(score, duplicate_level, stale_gate, hard_risk, config),
                "下次施工约束": rule.get("下次施工约束", ""),
            }
        )

    queue = [
        "将高价值低重复规则转为03进化系统本地检查项候选。",
        "将人工确认类旧口径统一改写为风险分级口径。",
        "对中重复和高重复规则生成合并摘要，避免规则山。",
        "继续接入真实复盘反馈样本，验证规则是否能降低后续施工复杂度。"
    ]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-rule-auto-review-dedupe",
        "所属系统": "03杰哥进化系统",
        "评审规则数量": len(reviews),
        "高价值数量": sum(1 for item in reviews if item["价值等级"] == "高价值"),
        "高重复数量": sum(1 for item in reviews if item["重复等级"] == "高重复"),
        "过时闸口风险数量": sum(1 for item in reviews if item["过时闸口风险"]),
        "下一步施工队列": queue,
        "规则评审": reviews,
        "小样本验收": {
            "规则来源存在": bool(rules),
            "闸口纠偏规则存在": bool(gate),
            "全部规则有建议动作": all(bool(item["建议动作"]) for item in reviews),
            "未发现未纠偏过时闸口": all(not item["过时闸口风险"] for item in reviews),
            "判定": "通过" if rules and all(not item["过时闸口风险"] for item in reviews) else "需纠偏"
        },
        "安全边界": {
            "修改其他系统业务代码": False,
            "修改总管进度口径": False,
            "发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False
        }
    }

    out_dir = root / "03数据" / "10自动评审"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = out_dir / f"规则自动评审与去重评分报告_{timestamp}.json"
    latest_json = out_dir / "规则自动评审与去重评分报告_最新.json"
    output_md = out_dir / f"规则自动评审与去重评分报告_{timestamp}.md"
    latest_md = out_dir / "规则自动评审与去重评分报告_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"评审规则数量": len(reviews), "判定": report["小样本验收"]["判定"], "输出": str(output_json)}, ensure_ascii=True))
    return 0 if report["小样本验收"]["判定"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
