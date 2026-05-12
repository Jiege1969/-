# -*- coding: utf-8 -*-
"""
名称：生成知识库本地问答预演.py
作用：基于知识库本地全文索引生成问答预演结果，为后续企业微信查资料入口提供低风险本地能力。
触发方式：python 生成知识库本地问答预演.py [问题]
依赖：Python标准库；知识库本地问答预演规则.json；知识库全文索引_最新.json。
所属系统：01杰哥智能系统/知识库
安全边界：只读取本系统01配置和03数据/知识库索引；只写入03数据/知识库/06问答预演；不调用模型推理；不生成向量；不写正式向量库；不触发n8n；不发送企业微信；不联网；不读取旧系统；不接入税收业务。
创建/修改记录：2026-04-29 创建知识库本地问答预演脚本。
标识：knowledge-local-qa-preview-generate
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[2]


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
            tokens.extend(word[i : i + 2] for i in range(max(len(word) - 1, 0)))
        else:
            tokens.append(word)
    stop_words = {"什么", "哪些", "一下", "当前", "这个", "系统", "杰哥"}
    return [item for item in tokens if item and item not in stop_words]


def score_chunk(question_tokens: list[str], chunk: dict[str, Any]) -> dict[str, Any]:
    content = str(chunk.get("内容", ""))
    lower_content = content.lower()
    hits = [token for token in question_tokens if token in lower_content]
    score = sum(len(token) for token in hits)
    return {
        "得分": score,
        "命中词": sorted(set(hits)),
        "文件名": chunk.get("文件名", ""),
        "路径": chunk.get("路径", ""),
        "分块序号": chunk.get("分块序号", 0),
        "内容": content,
    }


def make_answer(question: str, evidence: list[dict[str, Any]], max_chars: int) -> str:
    if not evidence:
        return "本地知识库当前没有检索到足够证据。建议先补充资料或进入人工确认队列。"
    top = evidence[0]["内容"].strip().replace("\r", "")
    top = re.sub(r"\n{2,}", "\n", top)
    if len(top) > max_chars:
        top = top[:max_chars].rstrip() + "..."
    return f"根据本地知识库证据，关于“{question}”：\n{top}\n\n说明：这是本地关键词问答预演结果，未调用模型推理，正式答复仍需后续接入检索增强和人工复核。"


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 知识库本地问答预演",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{report['汇总']['状态']}",
        f"- 问题数量：{report['汇总']['问题数量']}",
        f"- 有证据问题：{report['汇总']['有证据问题数量']}",
        "",
        "## 问答预演",
        "",
    ]
    for item in report["问答结果"]:
        lines.append(f"### {item['问题']}")
        lines.append("")
        lines.append(item["回答预演"])
        lines.append("")
        lines.append(f"- 证据数量：{len(item['证据'])}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    rule = load_json(root / "01配置" / "知识库本地问答预演规则.json", {})
    index = load_json(root / "03数据" / "知识库" / "03索引清单" / "知识库全文索引_最新.json", {})
    questions = sys.argv[1:] or rule.get("默认问题", [])
    params = rule.get("检索参数", {})
    max_evidence = int(params.get("最大证据片段数", 3) or 3)
    min_score = int(params.get("最小命中字符数", 1) or 1)
    max_chars = int(params.get("摘要最大字符数", 260) or 260)
    chunks = index.get("分块", [])
    results: list[dict[str, Any]] = []

    for question in questions:
        tokens = tokenize(str(question))
        scored = [score_chunk(tokens, chunk) for chunk in chunks]
        evidence = [item for item in sorted(scored, key=lambda item: item["得分"], reverse=True) if item["得分"] >= min_score][:max_evidence]
        results.append(
            {
                "问题": str(question),
                "检索词": tokens,
                "证据": evidence,
                "回答预演": make_answer(str(question), evidence, max_chars),
                "调用模型推理": False,
                "写正式向量库": False,
                "触发n8n": False,
                "企业微信真实发送": False,
            }
        )

    evidence_count = sum(1 for item in results if item["证据"])
    status = "healthy" if results and evidence_count == len(results) else "degraded"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-local-qa-preview",
        "所属系统": "01杰哥智能系统/知识库",
        "汇总": {
            "状态": status,
            "问题数量": len(results),
            "有证据问题数量": evidence_count,
            "执行模式": rule.get("执行模式", "local_keyword_qa_preview"),
        },
        "问答结果": results,
        "索引文件": str(root / "03数据" / "知识库" / "03索引清单" / "知识库全文索引_最新.json"),
        "安全边界": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "知识库" / "06问答预演"
    output_json = output_dir / "knowledge-local-qa-preview-最新.json"
    output_md = output_dir / "知识库本地问答预演_最新.md"
    write_json(output_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    print(json.dumps({"状态": status, "问题数量": len(results), "有证据问题数量": evidence_count, "输出": str(output_json)}, ensure_ascii=False))
    return 0 if status == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
