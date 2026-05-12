# -*- coding: utf-8 -*-
"""
名称：执行股票验收报告知识库可追溯问答入口.py
作用：基于 07 股票证据验收包和 12 股票验收报告问答样本，提供本地可调用的可追溯问答交付入口。
触发方式：python 执行股票验收报告知识库可追溯问答入口.py 问题1 [问题2 ...]
依赖：Python 标准库；知识库股票证据可追溯问答验收包_最新.json；股票验收报告知识库问答样本_最新.json。
所属系统：01杰哥智能系统/知识库
安全边界：只读知识库验收包和样本包；只写 13 股票验收报告问答交付入口；不修改股票脚本、不修改总管配置、不修改进化规则、不发送企业微信、不触发 n8n、不写正式库、不调用券商接口、不自动交易。
标识：knowledge-stock-acceptance-traceable-qa-entry-execute
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SMART_ROOT = Path("D:/杰哥智能化系统/01杰哥智能系统")
KNOWLEDGE_ROOT = SMART_ROOT / "03数据" / "知识库"
TRACEABLE_PACKAGE = KNOWLEDGE_ROOT / "07可追溯问答验收" / "知识库股票证据可追溯问答验收包_最新.json"
INDEXED_SAMPLE_PACKAGE = KNOWLEDGE_ROOT / "12股票验收报告问答样本" / "股票验收报告知识库问答样本_最新.json"
OUTPUT_DIR = KNOWLEDGE_ROOT / "13股票验收报告问答交付入口"


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


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fff]{2,}", text.lower())
    tokens: list[str] = []
    for word in words:
        if re.fullmatch(r"[\u4e00-\u9fff]{2,}", word):
            tokens.append(word)
            tokens.extend(word[index : index + 2] for index in range(max(len(word) - 1, 0)))
        else:
            tokens.append(word)
    stop_words = {"什么", "是否", "已经", "可以", "怎么", "如何", "为什么", "这个", "一下", "系统"}
    return [item for item in tokens if item and item not in stop_words]


def normalize_sources(sample: dict[str, Any], source_package: str) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for ref in sample.get("来源", []):
        source_file = ref.get("知识库来源文件") or ref.get("来源文件")
        original_file = ref.get("原始股票验收报告") or ref.get("来源文件")
        normalized.append(
            {
                "来源包": source_package,
                "来源标签": ref.get("来源标签", ""),
                "来源文件": source_file,
                "原始证据文件": original_file,
                "来源文件存在": Path(str(source_file)).exists(),
                "来源字段或章节": ref.get("来源字段或章节", ""),
                "分块序号": ref.get("分块序号", 0),
                "证据摘录": ref.get("证据摘录") or str(ref.get("证据值", ""))[:260],
                "命中词": ref.get("命中词", []),
            }
        )
    return normalized


def load_question_bank() -> list[dict[str, Any]]:
    bank: list[dict[str, Any]] = []
    traceable = load_json(TRACEABLE_PACKAGE, {})
    for sample in traceable.get("小样本问答", []):
        bank.append(
            {
                "问题": sample.get("问题", ""),
                "回答结论": sample.get("回答结论", ""),
                "验收状态": sample.get("验收状态", ""),
                "风险边界": sample.get("风险边界", ""),
                "来源": normalize_sources(sample, str(TRACEABLE_PACKAGE)),
                "样本层级": "交付级股票证据验收包",
            }
        )
    indexed = load_json(INDEXED_SAMPLE_PACKAGE, {})
    for sample in indexed.get("问答样本", []):
        bank.append(
            {
                "问题": sample.get("问题", ""),
                "回答结论": sample.get("回答结论", ""),
                "验收状态": sample.get("验收状态", ""),
                "风险边界": sample.get("风险边界", ""),
                "来源": normalize_sources(sample, str(INDEXED_SAMPLE_PACKAGE)),
                "样本层级": "已入知识库索引样本",
            }
        )
    unique: dict[str, dict[str, Any]] = {}
    for item in bank:
        question = item["问题"]
        if not question:
            continue
        if question not in unique or item["样本层级"] == "交付级股票证据验收包":
            unique[question] = item
    return list(unique.values())


def score_question(query: str, candidate: str) -> int:
    query_tokens = set(tokenize(query))
    candidate_tokens = set(tokenize(candidate))
    if query.strip() == candidate.strip():
        return 10000
    overlap = query_tokens & candidate_tokens
    return sum(len(item) for item in overlap) + len(overlap) * 3


def answer_one(question: str, bank: list[dict[str, Any]]) -> dict[str, Any]:
    scored = sorted(((score_question(question, item["问题"]), item) for item in bank), key=lambda item: item[0], reverse=True)
    score, best = scored[0] if scored else (0, {})
    if score < 8:
        return {
            "问题": question,
            "状态": "refused_no_evidence",
            "回答结论": f"当前股票验收报告知识库交付入口没有足够证据回答“{question}”。按可追溯规则拒答，请先补充本地证据文件或转人工复核。",
            "来源": [],
            "验收状态": "无可追溯验收来源，不判定。",
            "风险边界": "拒答不代表事实不存在；本入口不使用聊天记忆补答案，不触发外部动作。",
            "匹配问题": "",
            "匹配得分": score,
        }
    return {
        "问题": question,
        "状态": "answered_with_trace",
        "回答结论": best["回答结论"],
        "来源": best["来源"],
        "验收状态": best["验收状态"],
        "风险边界": best["风险边界"],
        "匹配问题": best["问题"],
        "匹配得分": score,
        "样本层级": best["样本层级"],
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票验收报告知识库可追溯问答入口输出",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 状态：{report['汇总']['状态']}",
        f"- 问题数量：{report['汇总']['问题数量']}",
        f"- 带追溯回答数量：{report['汇总']['带追溯回答数量']}",
        f"- 拒答数量：{report['汇总']['拒答数量']}",
        "",
    ]
    for item in report["问答结果"]:
        lines.append(f"## {item['问题']}")
        lines.append("")
        lines.append(f"- 回答结论：{item['回答结论']}")
        lines.append(f"- 验收状态：{item['验收状态']}")
        lines.append(f"- 风险边界：{item['风险边界']}")
        if item["来源"]:
            lines.append("- 来源：")
            for ref in item["来源"]:
                lines.append(f"  - {ref['来源标签']}：{ref['来源文件']}")
                lines.append(f"    - 字段或章节：{ref['来源字段或章节']}")
                if ref.get("分块序号"):
                    lines.append(f"    - 分块序号：{ref['分块序号']}")
                lines.append(f"    - 摘录：{ref['证据摘录']}")
        else:
            lines.append("- 来源：无，已按规则拒答。")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    bank = load_question_bank()
    default_questions = [
        "股票系统是否已交付？",
        "历史 K 线 _最新 是否已带备份刷新？",
        "正式成交额口径依据是什么？",
        "企业微信是否已经真实发送？",
        "是否可以扩大真实发送范围？",
        "失败时如何回滚？",
        "新易盛成交额阈值为什么这样算？",
        "企业微信短回复是否会真实发送？",
        "没有入库的合同金额是多少？",
    ]
    questions = sys.argv[1:] or default_questions
    results = [answer_one(question, bank) for question in questions]
    answered = sum(1 for item in results if item["状态"] == "answered_with_trace")
    refused = sum(1 for item in results if item["状态"] == "refused_no_evidence")
    sources_ok = all(
        ref.get("来源文件存在") is True and ref.get("来源文件") and ref.get("来源字段或章节")
        for item in results
        if item["状态"] == "answered_with_trace"
        for ref in item.get("来源", [])
    )
    status = "通过" if answered + refused == len(results) and sources_ok else "待复核"
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    report = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-stock-acceptance-traceable-qa-entry-output",
        "所属系统": "01杰哥智能系统/知识库",
        "汇总": {
            "状态": status,
            "问题数量": len(results),
            "带追溯回答数量": answered,
            "拒答数量": refused,
            "来源文件均存在": sources_ok,
            "问题库数量": len(bank),
            "企业微信真实发送": False,
            "触发n8n": False,
            "写正式库": False,
        },
        "入口契约": {
            "输入": "一个或多个自然语言问题",
            "输出": "回答结论、来源文件、来源字段或章节、分块序号或证据摘录、验收状态、风险边界",
            "无证据处理": "拒答并提示补本地证据或人工复核",
            "可被本地路由层调用": True,
        },
        "输入证据包": [str(TRACEABLE_PACKAGE), str(INDEXED_SAMPLE_PACKAGE)],
        "问答结果": results,
        "安全边界": {
            "修改股票系统核心脚本": False,
            "修改总管进度口径配置": False,
            "修改进化系统规则代码": False,
            "覆盖正式知识库": False,
            "调用模型推理": False,
            "生成向量": False,
            "写正式库": False,
            "触发n8n": False,
            "企业微信真实发送": False,
            "调用外部正式发送接口": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_json = OUTPUT_DIR / f"股票验收报告知识库可追溯问答入口输出_{timestamp}.json"
    latest_json = OUTPUT_DIR / "股票验收报告知识库可追溯问答入口输出_最新.json"
    output_md = OUTPUT_DIR / f"股票验收报告知识库可追溯问答入口输出_{timestamp}.md"
    latest_md = OUTPUT_DIR / "股票验收报告知识库可追溯问答入口输出_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": status, "带追溯回答数量": answered, "拒答数量": refused, "输出": str(output_json)}, ensure_ascii=False))
    return 0 if status == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
