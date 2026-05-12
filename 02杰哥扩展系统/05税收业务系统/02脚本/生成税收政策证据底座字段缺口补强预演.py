# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "28政策证据底座字段补齐预演"
PREVIEW_JSON = OUT_DIR / "税收政策证据底座字段补齐预演_最新.json"
REVIEW_JSON = OUT_DIR / "税收政策证据底座字段补齐预演复核_最新.json"
OUT_JSON = OUT_DIR / "税收政策证据底座字段缺口补强预演_最新.json"
OUT_MD = OUT_DIR / "税收政策证据底座字段缺口补强预演_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def row_key(row: dict[str, Any]) -> str:
    return str(row.get("标题") or row.get("资料ID") or "")


def text_from(value: Any) -> str:
    if isinstance(value, list):
        return "；".join(str(item) for item in value if item is not None)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return "" if value is None else str(value)


def build_suggestion(gap: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    field = gap.get("字段")
    title = gap.get("资料标题")
    suggestion = "保持为空，进入人工复核补强"
    basis = []
    confidence = "低"
    status = "pending_review"

    if field == "施行日期":
        applicable_period = text_from(row.get("适用期间"))
        release_date = text_from(row.get("发布日期"))
        basis.extend([
            f"发布日期：{release_date}" if release_date else "",
            f"适用期间：{applicable_period}" if applicable_period else "",
        ])
        suggestion = "不自动推定施行日期；以正文生效条款或人工核验为准。可先记录适用期间草案。"
        confidence = "中" if applicable_period else "低"
    elif field in {"适用主体", "适用事项", "适用期间", "关键条件", "排除条件", "所需资料"}:
        basis.extend([
            f"适用主体：{text_from(row.get('适用主体'))}",
            f"适用事项：{text_from(row.get('适用事项'))}",
            f"适用期间：{text_from(row.get('适用期间'))}",
            f"附件资料：{text_from(row.get('所需资料'))}",
        ])
        suggestion = "根据现有结构化字段生成待复核补强草案，不回写为正式事实。"
        confidence = "中"

    basis = [item for item in basis if item]
    return {
        "资料标题": title,
        "资料ID": row.get("资料ID"),
        "缺口字段": field,
        "建议补强值草案": suggestion,
        "证据摘录": basis,
        "置信度": confidence,
        "处理状态": status,
        "是否回写正式字段": False,
        "是否生成正式税务结论": False,
        "人工复核要求": "人工确认字段含义、正文依据和适用期间后，才能进入更高可信度依据候选层。",
    }


def write_md(report: dict[str, Any]) -> None:
    lines = [
        "# 税收政策证据底座字段缺口补强预演",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 缺口数量：{report['缺口数量']}",
        f"- 补强草案数量：{report['补强草案数量']}",
        "",
        "## 补强草案",
        "",
    ]
    for item in report["补强草案"]:
        lines.extend([
            f"### {item['资料标题']}",
            f"- 缺口字段：{item['缺口字段']}",
            f"- 建议补强值草案：{item['建议补强值草案']}",
            f"- 置信度：{item['置信度']}",
            f"- 是否回写正式字段：{item['是否回写正式字段']}",
            f"- 人工复核要求：{item['人工复核要求']}",
            "",
        ])
    if not report["补强草案"]:
        lines.append("- 无")

    lines.extend(["", "## 下一步自动队列", ""])
    for item in report["下一步自动队列"]:
        lines.append(f"- {item['优先级']} {item['事项']}：{item['边界']}")

    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    preview = load_json(PREVIEW_JSON)
    review = load_json(REVIEW_JSON)
    rows = preview.get("资料", [])
    rows_by_title = {row_key(row): row for row in rows}

    gaps = review.get("字段缺口", [])
    suggestions = []
    unmatched = []
    for gap in gaps:
        row = rows_by_title.get(str(gap.get("资料标题", "")))
        if not row:
            unmatched.append(gap)
            continue
        suggestions.append(build_suggestion(gap, row))

    next_queue = [
        {
            "优先级": "L2",
            "事项": "税收研发费用加计扣除核心正式依据时效补齐",
            "原因": "政策证据底座字段缺口已形成待复核补强草案，下一步继续补齐研发费用专题核心依据时效链。",
            "是否可自动推进": True,
            "边界": "只处理已有官方来源候选和本地证据卡；不联网、不下载、不写正式业务规则、不生成正式税务结论。",
        },
        {
            "优先级": "L2",
            "事项": "税收研发费用加计扣除后续比例延续政策本地证据卡补齐准备",
            "原因": "后续比例、延续和行业范围政策仍缺少本地证据卡闭环。",
            "是否可自动推进": True,
            "边界": "只生成准备包、字段清单和待复核项；不联网、不下载、不生成正式税务结论。",
        },
    ]

    report = {
        "名称": "税收政策证据底座字段缺口补强预演",
        "生成时间": now,
        "资产身份": "政策证据底座字段缺口待复核补强草案，不是税务结论库。",
        "来源文件": {
            "字段补齐预演": str(PREVIEW_JSON),
            "字段补齐预演复核": str(REVIEW_JSON),
        },
        "结论": "完成，补强草案进入待人工复核" if not unmatched else "完成，存在未匹配缺口待人工核对",
        "缺口数量": len(gaps),
        "补强草案数量": len(suggestions),
        "未匹配缺口数量": len(unmatched),
        "补强草案": suggestions,
        "未匹配缺口": unmatched,
        "下一步自动队列": next_queue,
        "安全边界": {
            "是否联网": False,
            "是否下载": False,
            "是否覆盖原始资料": False,
            "是否回写正式字段": False,
            "是否写正式业务规则": False,
            "是否生成正式税务结论": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(report)
    print(json.dumps({"状态": "完成", "缺口数量": len(gaps), "补强草案数量": len(suggestions), "输出": str(OUT_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
