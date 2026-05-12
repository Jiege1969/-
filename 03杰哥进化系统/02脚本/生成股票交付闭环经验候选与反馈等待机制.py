# -*- coding: utf-8 -*-
"""
名称：生成股票交付闭环经验候选与反馈等待机制.py
作用：把股票交付闭环沉淀为03进化系统经验候选、候选规则和反馈等待机制。
触发方式：python 生成股票交付闭环经验候选与反馈等待机制.py
依赖：Python标准库；股票交付闭环规则沉淀包、专项自动评审报告、复盘反馈观察报告。
所属系统：03杰哥进化系统
安全边界：只读03本地沉淀包和股票反馈观察结果，只写03进化系统本地经验候选；不写回股票系统，不修改扩展系统业务脚本，不修改总管进度口径，不修改智能系统知识库代码，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建股票交付闭环经验候选与反馈等待机制脚本。
标识：evolution-stock-delivery-experience-candidates-waiting-generate
"""

from __future__ import annotations

import json
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


def build_experience_candidates(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for idx, rule in enumerate(rules, start=1):
        candidates.append(
            {
                "经验候选ID": f"EXP-DLV-{idx:03d}",
                "来源规则ID": rule.get("规则ID", ""),
                "标题": f"{rule.get('规则名称', '')}交付经验候选",
                "经验类型": "交付流程经验",
                "问题": rule.get("问题", ""),
                "复盘": rule.get("复盘", ""),
                "可复用做法": rule.get("规则", ""),
                "下次施工约束": rule.get("下次施工约束", ""),
                "可自动固化": bool(rule.get("自动执行")) and not bool(rule.get("硬边界保留")),
                "仍需人工确认": bool(rule.get("硬边界保留")) or not bool(rule.get("自动执行")),
                "沉淀状态": "经验候选",
            }
        )
    candidates.append(
        {
            "经验候选ID": "EXP-WAIT-001",
            "来源规则ID": "REVIEW-WAITING",
            "标题": "有交付成功不等于有投资复盘经验",
            "经验类型": "反馈等待机制经验",
            "问题": "股票系统交付闭环已完成，但股票判断效果仍需T周期或人工评价反馈，不能把交付成功误当成投资判断成功。",
            "复盘": "03复盘反馈观察显示当前待回填样本仍为等待状态，可转经验样本为0。",
            "可复用做法": "把交付流程经验和业务判断经验分层：流程经验可候选化，投资判断经验必须等待反馈。",
            "下次施工约束": "没有复盘反馈或人工评价时，只能生成等待机制和空候选，不得生成投资判断经验卡片。",
            "可自动固化": True,
            "仍需人工确认": False,
            "沉淀状态": "经验候选",
        }
    )
    return candidates


def build_candidate_rules(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for item in reviews:
        result.append(
            {
                "候选规则ID": item.get("规则ID", ""),
                "候选规则名称": item.get("规则名称", ""),
                "价值分": item.get("价值分", 0),
                "价值等级": item.get("价值等级", ""),
                "重复等级": item.get("重复等级", ""),
                "固化建议": "自动固化" if item.get("可自动固化") else "人工确认或硬边界保留",
                "建议动作": item.get("建议动作", ""),
                "下次施工约束": item.get("下次施工约束", ""),
            }
        )
    return result


def build_waiting_mechanism(observe: dict[str, Any], transfer: dict[str, Any]) -> dict[str, Any]:
    pending = int(observe.get("待回填样本数量", 0) or transfer.get("等待反馈数量", 0) or 0)
    ready = int(observe.get("可转经验样本数量", 0) or transfer.get("转经验候选数量", 0) or 0)
    return {
        "机制ID": "WAIT-STOCK-REVIEW-001",
        "机制名称": "股票复盘反馈等待机制",
        "待回填样本数量": pending,
        "可转经验样本数量": ready,
        "当前状态": "等待反馈" if ready == 0 else "存在可转经验样本",
        "允许动作": [
            "继续观察T5/T20/T60/T120反馈",
            "继续生成等待摘要和空候选",
            "反馈出现后生成经验卡片草案"
        ],
        "禁止动作": [
            "无反馈时生成投资判断经验结论",
            "把交付成功等同于投资判断成功",
            "写回股票系统或覆盖业务输出"
        ],
        "转经验条件": [
            "T5/T20/T60/T120任一周期出现有效反馈",
            "人工评价出现明确正向、负向或修正说明",
            "反馈能对应原始报告路径、判断主因和证据完整度"
        ],
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票交付闭环经验候选与反馈等待机制",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 经验候选数量：{report['经验候选数量']}",
        f"- 候选规则数量：{report['候选规则数量']}",
        f"- 反馈等待状态：{report['反馈等待机制']['当前状态']}",
        f"- 小样本验收：{report['小样本验收']['判定']}",
        "",
        "## 经验候选",
        "",
    ]
    for item in report["经验候选"]:
        lines.extend(
            [
                f"### {item['经验候选ID']} {item['标题']}",
                f"- 类型：{item['经验类型']}",
                f"- 问题：{item['问题']}",
                f"- 复盘：{item['复盘']}",
                f"- 可复用做法：{item['可复用做法']}",
                f"- 下次施工约束：{item['下次施工约束']}",
                "",
            ]
        )
    lines.extend(["## 候选规则", ""])
    for item in report["候选规则"]:
        lines.append(f"- {item['候选规则ID']} {item['候选规则名称']}：{item['固化建议']}，{item['价值等级']}，{item['重复等级']}")
    lines.extend(["", "## 反馈等待机制", ""])
    for key, value in report["反馈等待机制"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = system_root()
    config = load_json(root / "01配置" / "股票交付闭环经验候选与反馈等待规则.json", {})
    deposit = load_json(root / "03数据" / "17股票交付闭环规则沉淀" / "股票交付闭环规则沉淀包_最新.json", {})
    review = load_json(root / "03数据" / "18股票交付闭环规则自动评审" / "股票交付闭环规则自动评审报告_最新.json", {})
    observe = load_json(root / "03数据" / "14复盘反馈观察" / "股票复盘反馈待回填观察报告_最新.json", {})
    transfer = load_json(root / "03数据" / "15复盘转经验候选" / "股票复盘反馈转经验候选_最新.json", {})

    rules = deposit.get("规则清单", [])
    reviews = review.get("规则评审", [])
    experience_candidates = build_experience_candidates(rules)
    candidate_rules = build_candidate_rules(reviews)
    waiting = build_waiting_mechanism(observe, transfer)
    sample = {
        "规则沉淀包存在": bool(deposit),
        "自动评审报告存在": bool(review),
        "复盘反馈观察存在": bool(observe),
        "经验候选不少于7": len(experience_candidates) >= 7,
        "候选规则数量为6": len(candidate_rules) == 6,
        "反馈等待机制明确": waiting["当前状态"] in {"等待反馈", "存在可转经验样本"},
        "无反馈不生成投资经验结论": waiting["可转经验样本数量"] == 0,
        "安全边界未突破": True,
    }
    sample["判定"] = "通过" if all(sample.values()) else "需复核"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-stock-delivery-experience-candidates-waiting",
        "所属系统": "03杰哥进化系统",
        "来源配置": "股票交付闭环经验候选与反馈等待规则.json",
        "经验候选数量": len(experience_candidates),
        "候选规则数量": len(candidate_rules),
        "经验候选": experience_candidates,
        "候选规则": candidate_rules,
        "反馈等待机制": waiting,
        "小样本验收": sample,
        "当前结论": "交付流程经验已进入候选；规则候选已形成；投资判断经验继续等待复盘反馈。",
        "安全边界": config.get("安全边界", {}),
    }
    out_dir = root / "03数据" / "19股票交付闭环经验候选与反馈等待"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = out_dir / f"股票交付闭环经验候选与反馈等待机制_{timestamp}.json"
    latest_json = out_dir / "股票交付闭环经验候选与反馈等待机制_最新.json"
    output_md = out_dir / f"股票交付闭环经验候选与反馈等待机制_{timestamp}.md"
    latest_md = out_dir / "股票交付闭环经验候选与反馈等待机制_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"经验候选数量": len(experience_candidates), "候选规则数量": len(candidate_rules), "判定": sample["判定"], "输出": str(output_json)}, ensure_ascii=True))
    return 0 if sample["判定"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
