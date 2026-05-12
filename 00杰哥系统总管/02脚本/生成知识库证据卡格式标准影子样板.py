# -*- coding: utf-8 -*-
"""
名称：生成知识库证据卡格式标准影子样板.py
作用：基于现有本地问答预演证据生成可追溯证据卡格式标准影子样板。
触发方式：python 生成知识库证据卡格式标准影子样板.py
安全边界：只读现有问答预演报告；只写总管运行状态样板；不启动问答、不调用模型、不生成向量、不入库、不触发n8n、不发送企业微信。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
KB = ROOT / "01杰哥智能系统"
OUT_DIR = MANAGER / "03数据" / "运行状态"
QA_LATEST = KB / "03数据" / "知识库" / "06问答预演" / "knowledge-local-qa-preview-最新.json"
REPORT_JSON = OUT_DIR / "知识库证据卡格式标准影子样板_最新.json"
REPORT_MD = OUT_DIR / "知识库证据卡格式标准影子样板_最新.md"

SCHEMA_FIELDS = [
    "证据卡ID",
    "来源系统",
    "来源文件名",
    "来源路径",
    "分块序号",
    "命中词",
    "内容摘录",
    "内容哈希",
    "关联问题",
    "生成模式",
    "可用于正式答复",
    "需人工复核",
    "禁止动作",
]


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


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def clip(text: str, limit: int = 220) -> str:
    value = " ".join(str(text).replace("\r", "").split())
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + "..."


def make_card(question: str, evidence: dict[str, Any], index: int) -> dict[str, Any]:
    content = str(evidence.get("内容", ""))
    source_path = str(evidence.get("路径", ""))
    source_name = str(evidence.get("文件名", ""))
    chunk_no = evidence.get("分块序号", 0)
    card_seed = f"{source_path}|{source_name}|{chunk_no}|{question}|{index}"
    return {
        "证据卡ID": f"KB-EVID-{text_hash(card_seed)}",
        "来源系统": "01杰哥智能系统/知识库",
        "来源文件名": source_name,
        "来源路径": source_path,
        "分块序号": chunk_no,
        "命中词": evidence.get("命中词", []),
        "内容摘录": clip(content),
        "内容哈希": text_hash(content),
        "关联问题": question,
        "生成模式": "shadow_schema_only",
        "可用于正式答复": False,
        "需人工复核": True,
        "禁止动作": [
            "不作为正式答复直接发送",
            "不写入正式知识库",
            "不写入向量库",
            "不触发n8n",
            "不发送企业微信",
        ],
    }


def main() -> int:
    qa_report = load_json(QA_LATEST, {})
    qa_results = qa_report.get("问答结果", [])
    cards: list[dict[str, Any]] = []
    for qa_index, item in enumerate(qa_results, start=1):
        question = str(item.get("问题", ""))
        for ev_index, evidence in enumerate(item.get("证据", []), start=1):
            cards.append(make_card(question, evidence, qa_index * 100 + ev_index))

    field_missing = [
        {"证据卡ID": card.get("证据卡ID", ""), "缺失字段": [field for field in SCHEMA_FIELDS if field not in card]}
        for card in cards
        if any(field not in card for field in SCHEMA_FIELDS)
    ]
    report = {
        "名称": "知识库证据卡格式标准影子样板",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if cards and not field_missing else "存在缺口",
        "来源报告": str(QA_LATEST),
        "字段标准": SCHEMA_FIELDS,
        "证据卡数量": len(cards),
        "字段缺口": field_missing,
        "证据卡样板": cards,
        "验收清单": [
            "证据卡必须保留来源文件名、来源路径、分块序号、命中词和内容哈希。",
            "证据卡默认不能用于正式答复，必须人工复核。",
            "证据卡生成不启动问答、不调用模型、不生成向量、不写库。",
        ],
        "安全边界": {
            "启动问答": False,
            "调用模型推理": False,
            "生成向量": False,
            "写正式知识库": False,
            "写Qdrant": False,
            "写PostgreSQL": False,
            "触发n8n": False,
            "发送企业微信": False,
            "联网检索": False,
            "读取旧系统": False,
            "接入税收业务": False,
        },
    }
    lines = [
        "# 知识库证据卡格式标准影子样板",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 证据卡数量：{report['证据卡数量']}",
        f"- 来源报告：`{QA_LATEST}`",
        "",
        "## 字段标准",
        "",
    ]
    for field in SCHEMA_FIELDS:
        lines.append(f"- {field}")
    lines.extend(["", "## 样板", ""])
    for card in cards[:5]:
        lines.append(f"### {card['证据卡ID']}")
        lines.append("")
        lines.append(f"- 来源文件名：{card['来源文件名']}")
        lines.append(f"- 来源路径：`{card['来源路径']}`")
        lines.append(f"- 分块序号：{card['分块序号']}")
        lines.append(f"- 命中词：{', '.join(card['命中词'])}")
        lines.append(f"- 内容哈希：{card['内容哈希']}")
        lines.append(f"- 需人工复核：{card['需人工复核']}")
        lines.append("")
    lines.extend([
        "## 安全边界",
        "",
        "本轮只生成证据卡格式影子样板，不启动问答，不调用模型，不生成向量，不写 Qdrant/PostgreSQL，不触发 n8n，不发送企业微信。",
    ])
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "证据卡数量": len(cards), "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if report["结论"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
