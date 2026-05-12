# -*- coding: utf-8 -*-
"""
名称：执行知识库可追溯问答入口.py
作用：提供可被本地路由层调用的知识库问答入口；每个确定性回答必须带来源文件、分块号和证据摘录，无证据则拒答。
触发方式：python 执行知识库可追溯问答入口.py 问题1 [问题2 ...]
依赖：Python标准库；知识库全文索引_最新.json。
所属系统：01杰哥智能系统/知识库
安全边界：只读取01智能系统知识库全文索引；只写入03数据/知识库/08可追溯问答入口；不覆盖正式知识库原始文档、清洗文本或索引；不调用模型推理；不生成向量；不写正式向量库/数据库；不触发n8n；不发送企业微信；不联网；不读取旧系统。
创建/修改记录：2026-05-05 创建知识库可追溯问答本地入口。
标识：knowledge-traceable-qa-entry-execute
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SMART_ROOT = Path("D:/杰哥智能化系统/01杰哥智能系统")
INDEX_PATH = SMART_ROOT / "03数据" / "知识库" / "03索引清单" / "知识库全文索引_最新.json"
OUTPUT_DIR = SMART_ROOT / "03数据" / "知识库" / "08可追溯问答入口"


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
    stop_words = {
        "什么",
        "哪些",
        "一下",
        "当前",
        "这个",
        "系统",
        "杰哥",
        "智能",
        "智能化",
        "怎么",
        "多少",
        "有没有",
    }
    return [item for item in tokens if item and item not in stop_words]


def score_chunk(tokens: list[str], chunk: dict[str, Any]) -> dict[str, Any]:
    content = str(chunk.get("内容", ""))
    lower_content = content.lower()
    hits = sorted({token for token in tokens if token in lower_content})
    return {
        "得分": sum(len(token) for token in hits),
        "命中词": hits,
        "文件名": chunk.get("文件名", ""),
        "来源文件": chunk.get("路径", ""),
        "分块序号": int(chunk.get("分块序号", 0) or 0),
        "内容": content,
    }


def compact_excerpt(content: str, hits: list[str], max_chars: int = 150) -> str:
    clean = re.sub(r"\s+", " ", content).strip()
    if not clean:
        return ""
    position = -1
    for hit in hits:
        position = clean.find(hit)
        if position >= 0:
            break
    if position < 0:
        return clean[:max_chars]
    start = max(position - 45, 0)
    end = min(start + max_chars, len(clean))
    return clean[start:end]


def answer_one(question: str, chunks: list[dict[str, Any]], max_evidence: int = 3) -> dict[str, Any]:
    tokens = tokenize(question)
    if any(marker in question for marker in ["未入库", "未登记", "未收录", "没有入库"]):
        return {
            "问题": question,
            "状态": "refused_no_evidence",
            "回答": f"问题中明确包含未入库或未登记资料：“{question}”。按可追溯问答规则，本入口不能用其他泛词命中的资料拼接答案，请先把对应资料入库或转人工复核。",
            "来源引用": [],
            "检索词": tokens,
        }
    scored = [score_chunk(tokens, chunk) for chunk in chunks]
    evidence = [
        item
        for item in sorted(scored, key=lambda item: item["得分"], reverse=True)
        if item["得分"] >= 4 and len(item.get("命中词", [])) >= 2
    ][:max_evidence]
    if not evidence:
        return {
            "问题": question,
            "状态": "refused_no_evidence",
            "回答": f"当前知识库没有检索到足够来源文件支撑“{question}”。按可追溯问答规则，本入口拒绝给出确定答案，请先补充资料或转人工复核。",
            "来源引用": [],
            "检索词": tokens,
        }

    references: list[dict[str, Any]] = []
    answer_lines = [f"根据已登记知识库来源，关于“{question}”的可追溯回答如下："]
    for index, item in enumerate(evidence, start=1):
        source_path = str(item.get("来源文件", ""))
        excerpt = compact_excerpt(str(item.get("内容", "")), item.get("命中词", []))
        references.append(
            {
                "引用编号": f"S{index}",
                "来源文件": source_path,
                "来源文件存在": Path(source_path).exists(),
                "分块序号": item.get("分块序号", 0),
                "命中词": item.get("命中词", []),
                "证据摘录": excerpt,
            }
        )
        answer_lines.append(f"[S{index}] {excerpt}")
    answer_lines.append("说明：以上内容只来自列出的来源文件；未被来源支撑的信息不作为确定结论。")
    return {
        "问题": question,
        "状态": "answered_with_sources",
        "回答": "\n".join(answer_lines),
        "来源引用": references,
        "检索词": tokens,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 知识库可追溯问答入口输出",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 状态：{report['汇总']['状态']}",
        f"- 问题数量：{report['汇总']['问题数量']}",
        f"- 带来源回答数量：{report['汇总']['带来源回答数量']}",
        f"- 无证据拒答数量：{report['汇总']['无证据拒答数量']}",
        "",
    ]
    for item in report["问答结果"]:
        lines.append(f"## {item['问题']}")
        lines.append("")
        lines.append(item["回答"])
        lines.append("")
        if item["来源引用"]:
            lines.append("来源引用：")
            for ref in item["来源引用"]:
                lines.append(f"- {ref['引用编号']}：{ref['来源文件']}；分块 {ref['分块序号']}；命中词 {', '.join(ref['命中词'])}")
        else:
            lines.append("来源引用：无，已按规则拒答。")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    index = load_json(INDEX_PATH, {})
    chunks = index.get("分块", [])
    questions = sys.argv[1:] or [
        "知识库当前读取边界是什么",
        "杰哥智能化系统当前能力有哪些",
        "这个未入库的外部合同金额是多少",
    ]
    results = [answer_one(str(question), chunks) for question in questions]
    answered = sum(1 for item in results if item["状态"] == "answered_with_sources")
    refused = sum(1 for item in results if item["状态"] == "refused_no_evidence")
    all_answered_sources_exist = all(
        ref.get("来源文件存在") is True
        for item in results
        if item["状态"] == "answered_with_sources"
        for ref in item.get("来源引用", [])
    )
    status = "pass" if results and answered + refused == len(results) and all_answered_sources_exist else "attention_required"
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    report = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-traceable-qa-entry-output",
        "所属系统": "01杰哥智能系统/知识库",
        "汇总": {
            "状态": status,
            "问题数量": len(results),
            "带来源回答数量": answered,
            "无证据拒答数量": refused,
            "来源文件均存在": all_answered_sources_exist,
            "调用模型推理": False,
            "生成向量": False,
            "写正式向量库": False,
            "写正式数据库": False,
            "触发n8n": False,
            "企业微信真实发送": False,
        },
        "入口契约": {
            "输入": "一个或多个自然语言问题",
            "输出": "回答状态、回答文本、来源文件、分块序号、证据摘录、安全边界",
            "可被路由层调用": True,
            "正式发送前置": "企业微信桥接层必须继续保留真实发送门禁；本入口只返回本地问答结果。",
        },
        "索引文件": str(INDEX_PATH),
        "问答结果": results,
        "安全边界": {
            "修改股票研究系统脚本": False,
            "修改总管进度标准文件": False,
            "修改进化系统规则固化代码": False,
            "覆盖正式知识库": False,
            "调用模型推理": False,
            "生成向量": False,
            "写正式向量库": False,
            "写正式数据库": False,
            "触发n8n": False,
            "企业微信真实发送": False,
            "联网检索": False,
            "读取旧系统": False,
        },
    }
    output_json = OUTPUT_DIR / f"知识库可追溯问答入口输出_{timestamp}.json"
    latest_json = OUTPUT_DIR / "知识库可追溯问答入口输出_最新.json"
    output_md = OUTPUT_DIR / f"知识库可追溯问答入口输出_{timestamp}.md"
    latest_md = OUTPUT_DIR / "知识库可追溯问答入口输出_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": status, "带来源回答数量": answered, "无证据拒答数量": refused, "输出": str(output_json)}, ensure_ascii=False))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
