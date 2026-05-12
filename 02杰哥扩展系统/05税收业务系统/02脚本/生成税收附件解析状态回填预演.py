# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
ATTACH_PARSE = ROOT / "03数据" / "18附件正文解析预演" / "税收附件正文解析预演_最新.json"
QUESTION_PACK = ROOT / "03数据" / "17问题包与人工复核清单" / "税收答案草案问题包与人工复核清单_最新.json"
RELATION_PREVIEW = ROOT / "03数据" / "14证据关系机制" / "税收证据关系边预览_最新.json"
OUT_DIR = ROOT / "03数据" / "19附件解析状态回填预演"
OUT_JSON = OUT_DIR / "税收附件解析状态回填预演_最新.json"
OUT_MD = OUT_DIR / "税收附件解析状态回填预演_最新.md"


NO_RUNTIME_CHANGE = {
    "是否触发n8n": False,
    "是否企业微信真实发送": False,
    "是否写向量库": False,
    "是否调用模型推理": False,
    "是否生成正式税务结论": False,
    "是否新增端口": False,
    "是否重启服务": False,
    "是否影响股票系统": False,
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value or "")


def attachment_key(title: str) -> str:
    title = compact(title)
    title = title.replace(".doc", "").replace(".wps", "").replace(".docx", "")
    return title[:40]


def match_attachment(title: str, attachments: list[dict]) -> dict | None:
    key = attachment_key(title)
    for item in attachments:
        if key and (key in attachment_key(item.get("标题", "")) or attachment_key(item.get("标题", "")) in key):
            return item
    return None


def question_needs_attachment(question: dict) -> bool:
    text = "".join(question.get("关键词", [])) + question.get("问题", "")
    return any(word in text for word in ["申报表", "预缴", "年度纳税申报表", "A类", "附件"])


def related_attachment_count(question: dict, attachments: list[dict]) -> int:
    text = "".join(question.get("关键词", [])) + question.get("问题", "")
    count = 0
    for item in attachments:
        title = item.get("标题", "")
        if ("预缴" in text and "预缴" in title) or ("年度" in text and "年度" in title) or ("申报表" in text and "申报表" in title):
            count += 1
    return count


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    attach_pack = load_json(ATTACH_PARSE)
    question_pack = load_json(QUESTION_PACK)
    relation_pack = load_json(RELATION_PREVIEW)

    attachments = attach_pack.get("解析结果", [])
    enriched_questions = deepcopy(question_pack.get("问题包复核清单", []))
    enriched_nodes = deepcopy(relation_pack.get("节点", []))
    enriched_edges = deepcopy(relation_pack.get("关系边", []))

    for question in enriched_questions:
        needs_attachment = question_needs_attachment(question)
        count = related_attachment_count(question, attachments)
        review = question.setdefault("人工复核清单", {})
        if needs_attachment and count > 0:
            review["附件是否已解析"] = f"已部分解析 {count} 个附件，待正式文档解析器复核"
            question.setdefault("当前阻断原因", [])
            if "附件为轻量解析，需正式文档解析器复核。" not in question["当前阻断原因"]:
                question["当前阻断原因"].append("附件为轻量解析，需正式文档解析器复核。")
            question["附件解析状态"] = "部分解析"
            question["匹配附件数量"] = count
        elif needs_attachment:
            review["附件是否已解析"] = "未匹配到附件解析结果"
            question["附件解析状态"] = "未匹配"
            question["匹配附件数量"] = 0
            question.setdefault("当前阻断原因", []).append("问题依赖附件但未匹配到附件解析结果。")
        else:
            review["附件是否已解析"] = "本问题暂不依赖附件解析"
            question["附件解析状态"] = "不适用"
            question["匹配附件数量"] = 0

    backfilled_node_count = 0
    for node in enriched_nodes:
        matched = match_attachment(node.get("标题", ""), attachments)
        if not matched:
            continue
        node["附件解析状态"] = matched.get("解析状态")
        node["附件解析方法"] = matched.get("解析方法")
        node["附件解析字符数"] = matched.get("解析字符数")
        node["附件解析文本路径"] = matched.get("解析文本路径")
        node["附件解析元数据路径"] = matched.get("本地解析元数据路径")
        node["是否可作当前适用依据"] = False
        blockers = node.setdefault("阻断原因", [])
        for reason in matched.get("阻断原因", []):
            if reason not in blockers:
                blockers.append(reason)
        backfilled_node_count += 1

    backfilled_edge_count = 0
    for edge in enriched_edges:
        if edge.get("关系类型") != "附件":
            continue
        matched = match_attachment(edge.get("目标标题", ""), attachments)
        if not matched:
            continue
        edge["附件解析状态"] = matched.get("解析状态")
        edge["附件解析文本路径"] = matched.get("解析文本路径")
        edge["是否可支撑当前结论"] = False
        blockers = edge.setdefault("阻断原因", [])
        for reason in matched.get("阻断原因", []):
            if reason not in blockers:
                blockers.append(reason)
        backfilled_edge_count += 1

    output = {
        "名称": "税收附件解析状态回填预演",
        "生成时间": now,
        "模式": "preview_only_no_runtime_change_backfill",
        "来源": {
            "附件解析预演": str(ATTACH_PARSE),
            "问题包复核清单": str(QUESTION_PACK),
            "证据关系边预览": str(RELATION_PREVIEW),
        },
        "附件解析数量": len(attachments),
        "问题数量": len(enriched_questions),
        "回填问题数量": sum(1 for item in enriched_questions if item.get("附件解析状态") == "部分解析"),
        "回填节点数量": backfilled_node_count,
        "回填关系边数量": backfilled_edge_count,
        "增强问题包复核清单": enriched_questions,
        "增强证据节点": enriched_nodes,
        "增强关系边": enriched_edges,
        "安全边界": NO_RUNTIME_CHANGE,
        "下一步建议": [
            "引入正式文档解析器复核部分解析附件。",
            "将正式解析结果替换轻量解析状态。",
            "再生成小样本RAG灰度方案，但仍不直接接企业微信正式入口。",
        ],
    }
    OUT_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收附件解析状态回填预演",
        "",
        f"- 生成时间：{now}",
        "- 模式：preview_only_no_runtime_change_backfill",
        f"- 附件解析数量：{output['附件解析数量']}",
        f"- 问题数量：{output['问题数量']}",
        f"- 回填问题数量：{output['回填问题数量']}",
        f"- 回填节点数量：{output['回填节点数量']}",
        f"- 回填关系边数量：{output['回填关系边数量']}",
        "",
        "## 问题包回填摘要",
        "",
    ]
    for item in enriched_questions:
        lines.extend([
            f"### {item['问题']}",
            f"- 附件解析状态：{item.get('附件解析状态')}",
            f"- 匹配附件数量：{item.get('匹配附件数量')}",
            f"- 附件是否已解析：{item.get('人工复核清单', {}).get('附件是否已解析')}",
            f"- 当前阻断原因：{'；'.join(item.get('当前阻断原因', [])) if item.get('当前阻断原因') else '无'}",
            "",
        ])
    lines.extend(["## 安全边界", ""])
    for key, value in NO_RUNTIME_CHANGE.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": "完成", "回填问题数量": output["回填问题数量"], "回填节点数量": backfilled_node_count, "报告": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
