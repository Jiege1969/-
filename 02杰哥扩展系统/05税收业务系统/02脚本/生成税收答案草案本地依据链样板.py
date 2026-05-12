# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
FORMAL_INDEX = ROOT / "03数据" / "13智能政策下载管道" / "正式依据库" / "正式依据索引_最新.json"
RELATION_PREVIEW = ROOT / "03数据" / "14证据关系机制" / "税收证据关系边预览_最新.json"
DOWNLOAD_REPORT = ROOT / "03数据" / "15关联附件下载预演" / "运行报告" / "税收附件与关联链接受控下载预演_最新.json"
OUT_DIR = ROOT / "03数据" / "16答案草案依据链样板"
OUT_JSON = OUT_DIR / "税收答案草案本地依据链样板_最新.json"
OUT_MD = OUT_DIR / "税收答案草案本地依据链样板_最新.md"


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


QUESTIONS = [
    {
        "问题ID": "tax-draft-001",
        "问题": "企业所得税预缴申报表现在按什么依据使用？",
        "关键词": ["企业所得税", "预缴", "申报表", "2025年第17号"],
        "场景": "正式依据充足样板",
    },
    {
        "问题ID": "tax-draft-002",
        "问题": "研发费用加计扣除项目怎样判断能不能享受？",
        "关键词": ["研发费用", "加计扣除", "财税〔2015〕119号", "项目鉴定"],
        "场景": "依据不足降级样板",
    },
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def compact_text(value: str, limit: int = 120) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    return value[:limit]


def text_blob(item: dict) -> str:
    return " ".join(str(item.get(key, "")) for key in [
        "标题",
        "文号",
        "税费政策分类",
        "二级税费政策分类",
        "标签",
        "摘要",
        "原目标标题",
        "文件时效",
    ])


def score_item(item: dict, keywords: list[str]) -> int:
    blob = text_blob(item)
    score = 0
    for keyword in keywords:
        if keyword and keyword in blob:
            score += 2 if len(keyword) >= 4 else 1
    if item.get("是否可作当前适用依据") is True:
        score += 1
    return score


def formal_evidence_card(item: dict) -> dict:
    paths = item.get("保存路径", {}) if isinstance(item.get("保存路径"), dict) else {}
    return {
        "标题": item.get("标题", ""),
        "文号": item.get("文号", ""),
        "发文机关": item.get("发文机关") or item.get("来源名称", ""),
        "发布日期": item.get("发布日期", ""),
        "施行日期": item.get("施行日期", ""),
        "文件时效": item.get("文件时效", ""),
        "来源链接": item.get("最终链接") or item.get("来源链接", ""),
        "本地原文路径": paths.get("原始文件", ""),
        "本地解析文本路径": paths.get("解析文本", ""),
        "是否可作当前适用依据": item.get("可作为当前适用依据") is True and item.get("文件时效") == "全文有效",
        "阻断原因": item.get("阻断原因", []),
    }


def downloaded_card(item: dict) -> dict:
    return {
        "标题": item.get("标题") or item.get("原目标标题", ""),
        "文号": item.get("文号", ""),
        "资料类别": item.get("资料类别", ""),
        "文件类型": item.get("文件类型", ""),
        "文件时效": item.get("文件时效", ""),
        "来源链接": item.get("最终链接") or item.get("来源链接", ""),
        "本地原文路径": item.get("本地原文路径", ""),
        "本地解析文本路径": item.get("本地解析文本路径", ""),
        "是否可作当前适用依据": item.get("是否可作当前适用依据") is True,
        "阻断原因": item.get("阻断原因", []),
    }


def relation_summary(relation_preview: dict, selected_titles: list[str]) -> list[dict]:
    result = []
    for edge in relation_preview.get("关系边", []):
        target_title = edge.get("目标标题", "")
        if any(title and (title in target_title or target_title in title) for title in selected_titles):
            result.append({
                "关系类型": edge.get("关系类型"),
                "目标标题": target_title,
                "目标链接或本地路径": edge.get("目标链接或本地路径", ""),
                "是否可支撑当前结论": edge.get("是否可支撑当前结论", False),
            })
    return result[:10]


def build_answer(question: dict, formal_items: list[dict], downloaded_items: list[dict], relation_preview: dict) -> dict:
    keywords = question["关键词"]
    formal_ranked = sorted(
        [(score_item(item, keywords), item) for item in formal_items],
        key=lambda pair: pair[0],
        reverse=True,
    )
    downloaded_ranked = sorted(
        [(score_item(item, keywords), item) for item in downloaded_items],
        key=lambda pair: pair[0],
        reverse=True,
    )

    formal_selected = [formal_evidence_card(item) for score, item in formal_ranked if score > 0][:3]
    downloaded_selected = [downloaded_card(item) for score, item in downloaded_ranked if score > 0][:6]
    auxiliary = [item for item in downloaded_selected if not item["是否可作当前适用依据"]]
    formal_candidates = [item for item in downloaded_selected if item["是否可作当前适用依据"]]
    usable_formal = [item for item in formal_selected if item["是否可作当前适用依据"]] + formal_candidates
    titles = [item["标题"] for item in formal_selected + downloaded_selected]
    relations = relation_summary(relation_preview, titles)

    enough = bool(usable_formal)
    if "研发费用" in " ".join(keywords):
        enough = any("研发" in item.get("标题", "") and item.get("是否可作当前适用依据") for item in usable_formal)

    if enough and "预缴" in " ".join(keywords):
        conclusion = "答案草案：企业所得税预缴申报表可优先依据国家税务总局公告2025年第17号进行判断；该公告为全文有效，本地已保存原文和附件链接。具体填报仍需结合企业征收方式、分支机构情况和适用优惠事项人工复核。"
        confidence = "中高"
        risk = [
            "本草案只说明本地依据链，不替代税务机关或专业税务判断。",
            "附件申报表已下载或已识别，但附件正文解析仍需后续补齐。",
        ]
    elif enough:
        conclusion = "答案草案：本地找到了可用正式依据候选，但仍需按具体事实、适用期间和政策口径人工复核后才能形成正式判断。"
        confidence = "中"
        risk = ["当前仅为本地依据链样板，不能作为正式税务结论。"]
    else:
        conclusion = "答案草案：本地已找到相关解读、案例或关联资料，但缺少可直接支撑当前结论的全文有效正式依据；因此只能给出学习参考和待核验方向，不能判断当前是否可以享受。"
        confidence = "低"
        risk = [
            "解释材料和案例不能替代正式政策正文。",
            "时效缺失或已修改资料不得作为当前适用依据。",
            "需要继续补齐正式依据、文号、时效和适用条件。",
        ]

    display_formal_count = len(usable_formal) if enough else 0
    wechat_preview = [
        f"【税收答案草案】{question['问题']}",
        f"结论：{conclusion}",
        f"依据：找到可支撑本问题的正式依据 {display_formal_count} 条；辅助材料 {len(auxiliary)} 条。",
        f"可信度：{confidence}。",
        f"风险：{risk[0] if risk else '需人工复核。'}",
        "详情：本地依据链样板，暂未接入企业微信正式入口。",
    ]

    return {
        "问题ID": question["问题ID"],
        "问题": question["问题"],
        "场景": question["场景"],
        "关键词": keywords,
        "结论草案": conclusion,
        "结论可信度": confidence,
        "是否可形成当前适用判断": enough,
        "正式依据": formal_selected,
        "正式依据候选": formal_candidates,
        "辅助材料": auxiliary,
        "关系链摘要": relations,
        "风险提示": risk,
        "待核验项": [
            "核验政策适用期间与纳税人具体事实是否一致。",
            "核验附件正文解析是否完成。",
            "核验是否存在地方口径或后续修订。"
        ],
        "微信短答预览": wechat_preview,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formal = load_json(FORMAL_INDEX)
    relation_preview = load_json(RELATION_PREVIEW)
    download_report = load_json(DOWNLOAD_REPORT)

    answers = [
        build_answer(question, formal.get("资料", []), download_report.get("下载结果", []), relation_preview)
        for question in QUESTIONS
    ]

    package = {
        "名称": "税收答案草案本地依据链样板",
        "生成时间": now,
        "模式": "preview_only_no_runtime_change_rule_based_no_model",
        "问题数量": len(answers),
        "答案草案": answers,
        "安全边界": NO_RUNTIME_CHANGE,
        "下一步建议": [
            "将问题关键词检索扩展为可配置规则。",
            "补充附件正文解析结果。",
            "在人工确认后再做小样本RAG灰度。",
            "企业微信税收入口仍需另行停下确认。"
        ],
    }
    OUT_JSON.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收答案草案本地依据链样板",
        "",
        f"- 生成时间：{now}",
        "- 模式：preview_only_no_runtime_change_rule_based_no_model",
        f"- 问题数量：{len(answers)}",
        "",
    ]
    for answer in answers:
        lines.extend([
            f"## {answer['问题']}",
            "",
            f"- 场景：{answer['场景']}",
            f"- 结论可信度：{answer['结论可信度']}",
            f"- 是否可形成当前适用判断：{answer['是否可形成当前适用判断']}",
            "",
            "### 结论草案",
            "",
            answer["结论草案"],
            "",
            "### 正式依据",
            "",
        ])
        for item in answer["正式依据"]:
            lines.append(f"- {item['标题']}；{item['文号']}；{item['文件时效']}；{item['来源链接']}")
        if not answer["正式依据"]:
            lines.append("- 未找到可用正式依据。")
        lines.extend(["", "### 辅助材料", ""])
        for item in answer["辅助材料"]:
            lines.append(f"- {item['标题']}；{item['资料类别']}；{item['文件时效']}；阻断：{'；'.join(item['阻断原因'])}")
        if not answer["辅助材料"]:
            lines.append("- 无。")
        lines.extend(["", "### 微信短答预览", ""])
        for line in answer["微信短答预览"]:
            lines.append(f"- {line}")
        lines.append("")
    lines.extend(["## 安全边界", ""])
    for key, value in NO_RUNTIME_CHANGE.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": "完成", "问题数量": len(answers), "报告": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
