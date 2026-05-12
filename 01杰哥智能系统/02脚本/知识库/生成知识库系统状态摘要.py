# -*- coding: utf-8 -*-
"""
名称：生成知识库系统状态摘要.py
作用：汇总知识库目录、检索增强链路、R02本地入库预演器、本地问答预演和安全边界状态，生成日常可读状态摘要。
触发方式：python 生成知识库系统状态摘要.py
依赖：Python标准库；知识库检索增强链路验收日志；R02知识库本地入库预演器验收日志；知识库本地问答预演验收日志。
所属系统：01杰哥智能系统/知识库
安全边界：只读取01杰哥智能系统知识库本地文件和日志；只写入03数据/知识库/05状态摘要；不生成向量；不写正式库；不触发n8n；不发送企业微信；不写旧系统；不接入税收业务。
创建/修改记录：2026-04-29 创建知识库系统状态摘要生成脚本；2026-04-29 纳入知识库本地问答预演状态。
标识：knowledge-system-status-summary-generate
"""

from __future__ import annotations

import json
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


def latest_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"存在": False, "路径": ""}
    data = load_json(path, {})
    return {"存在": True, "路径": str(path), "内容": data}


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    stack = [path]
    while stack:
        current = stack.pop()
        for item in current.iterdir():
            if item.is_file():
                total += 1
            elif item.is_dir():
                stack.append(item)
    return total


def state_from_verify(report: dict[str, Any]) -> dict[str, Any]:
    if not report.get("存在"):
        return {"存在": False, "通过": 0, "失败": 1, "状态": "missing"}
    content = report.get("内容", {})
    summary = content.get("汇总") or {}
    passed = int(summary.get("通过", 0))
    failed = int(summary.get("失败", 0))
    status = "healthy" if failed == 0 and passed > 0 else "degraded"
    return {"存在": True, "通过": passed, "失败": failed, "状态": status, "日志": report.get("路径", "")}


def build_markdown(report: dict[str, Any]) -> str:
    summary = report["汇总"]
    retrieval = report["检索增强链路"]
    ingest = report["R02本地入库预演器"]
    qa_preview = report["本地问答预演"]
    lines = [
        "# 知识库系统状态摘要",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{summary['状态']}",
        f"- 原始文档数：{summary['原始文档数']}",
        f"- 清洗文本数：{summary['清洗文本数']}",
        f"- 索引清单数：{summary['索引清单数']}",
        f"- 检索增强链路：{retrieval['状态']}（通过 {retrieval['通过']}，失败 {retrieval['失败']}）",
        f"- R02本地入库预演器：{ingest['状态']}（通过 {ingest['通过']}，失败 {ingest['失败']}）",
        f"- 本地问答预演：{qa_preview['状态']}（通过 {qa_preview['通过']}，失败 {qa_preview['失败']}）",
        "",
        "## 安全边界",
        "",
        "- 当前摘要只代表知识库链路已具备预演和验收能力。",
        "- 正式向量生成、正式写库、n8n触发、企业微信发送均保持关闭。",
        "- 税收业务未接入；旧系统只读借鉴，不写入。",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    data_root = root / "03数据" / "知识库"
    log_dir = root / "04日志" / "知识库"
    output_dir = data_root / "05状态摘要"

    retrieval_report = latest_json(log_dir / "knowledge-retrieval-enhancement-chain-verify-最新.json")
    ingest_report = latest_json(log_dir / "r02-knowledge-local-ingest-executor-verify-最新.json")
    qa_preview_report = latest_json(log_dir / "knowledge-local-qa-preview-verify-最新.json")
    retrieval_state = state_from_verify(retrieval_report)
    ingest_state = state_from_verify(ingest_report)
    qa_preview_state = state_from_verify(qa_preview_report)

    summary_state = "healthy" if retrieval_state["状态"] == "healthy" and ingest_state["状态"] == "healthy" and qa_preview_state["状态"] == "healthy" else "degraded"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-system-status-summary",
        "所属系统": "01杰哥智能系统/知识库",
        "汇总": {
            "状态": summary_state,
            "原始文档数": count_files(data_root / "01原始文档"),
            "清洗文本数": count_files(data_root / "02清洗文本"),
            "索引清单数": count_files(data_root / "03索引清单"),
            "检索缓存数": count_files(data_root / "04检索缓存"),
            "问答预演数": count_files(data_root / "06问答预演"),
            "入库前复核数": count_files(data_root / "06入库前复核"),
        },
        "检索增强链路": retrieval_state,
        "R02本地入库预演器": ingest_state,
        "本地问答预演": qa_preview_state,
        "安全边界": {
            "调用模型推理": False,
            "生成向量": False,
            "写正式库": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写旧系统": False,
            "接入税收": False,
        },
    }

    output_json = output_dir / "knowledge-system-status-summary-最新.json"
    output_md = output_dir / "知识库系统状态摘要_最新.md"
    write_json(output_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    print(json.dumps({"状态": summary_state, "输出": str(output_json), "摘要": str(output_md)}, ensure_ascii=False))
    return 0 if summary_state == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
