# -*- coding: utf-8 -*-
"""
名称：生成研发费用分析准备度门禁.py
作用：汇总研发费用政策链、人工复核清单、事实采集模板和契约影子样例，判断当前分析准备度。
安全边界：只读生成门禁报告；不联网、不下载、不测算金额、不生成正式税务结论。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
POLICY_CHAIN = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案" / "研发费用加计扣除政策链补齐预演_最新.json"
REVIEW_CHECKLIST = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案" / "研发费用加计扣除专项人工复核清单_最新.json"
FACT_TEMPLATE = ROOT / "03数据" / "30研发费用业务事实采集模板" / "研发费用业务事实采集模板_最新.json"
SHADOW_SAMPLE = ROOT / "03数据" / "29涉税业务分析契约影子样例" / "研发费用涉税业务分析契约影子样例_最新.json"
OUT_DIR = ROOT / "03数据" / "31研发费用分析准备度门禁"
OUT_JSON = OUT_DIR / "研发费用分析准备度门禁_最新.json"
OUT_MD = OUT_DIR / "研发费用分析准备度门禁_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_gate() -> dict[str, Any]:
    chain = load_json(POLICY_CHAIN)
    checklist = load_json(REVIEW_CHECKLIST)
    fact_template = load_json(FACT_TEMPLATE)
    shadow_report = load_json(SHADOW_SAMPLE)
    shadow = shadow_report.get("影子样例", {})

    evidence_cards = chain.get("证据卡片", [])
    core_formal_cards = [card for card in evidence_cards if card.get("依据层级") in {"财税文件", "税务规范性文件", "行政法规"}]
    current_formal_cards = [card for card in core_formal_cards if card.get("是否当前适用依据候选") is True]
    fact_fields = fact_template.get("字段", [])
    required_fact_fields = [item for item in fact_fields if item.get("必填") is True]
    filled_required_facts = [item for item in required_fact_fields if item.get("填写值")]
    pending_reviews = [
        row for row in checklist.get("证据复核清单", [])
        if row.get("复核状态") != "已复核"
    ]

    gates = [
        {
            "门禁": "核心正式依据",
            "状态": "未通过" if not current_formal_cards else "待复核",
            "说明": "财税文件、税务规范性文件或行政法规层级中，尚无已确认可作为当前适用依据的核心卡片。",
        },
        {
            "门禁": "业务事实",
            "状态": "未通过" if len(filled_required_facts) < len(required_fact_fields) else "待复核",
            "说明": f"必填事实字段 {len(required_fact_fields)} 项，已填写 {len(filled_required_facts)} 项。",
        },
        {
            "门禁": "人工复核",
            "状态": "未通过" if pending_reviews else "待复核",
            "说明": f"仍有 {len(pending_reviews)} 条证据复核项未完成。",
        },
        {
            "门禁": "分析契约",
            "状态": "未通过" if shadow.get("契约状态") != "pending_review" else "通过",
            "说明": f"当前契约状态为 {shadow.get('契约状态', '缺失')}，只能作为待复核影子样例。",
        },
    ]
    if any(item["状态"] == "未通过" for item in gates):
        readiness = "not_ready"
        allowed_outputs = ["证据链预演", "专项人工复核清单", "业务事实采集模板", "待复核分析契约影子样例"]
    else:
        readiness = "pending_review"
        allowed_outputs = ["待人工复核分析草案"]

    return {
        "名称": "研发费用分析准备度门禁",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "准备度状态": readiness,
        "门禁结论": "当前不得输出研发费用加计扣除适用判断。",
        "允许输出": allowed_outputs,
        "禁止输出": [
            "可以享受研发费用加计扣除",
            "不能享受研发费用加计扣除",
            "可扣除金额或税额影响",
            "正式税务意见",
            "申报、退税、开票或外发动作",
        ],
        "门禁项": gates,
        "来源文件": {
            "政策链预演": str(POLICY_CHAIN),
            "专项人工复核清单": str(REVIEW_CHECKLIST),
            "业务事实采集模板": str(FACT_TEMPLATE),
            "分析契约影子样例": str(SHADOW_SAMPLE),
        },
        "关键缺口": chain.get("政策链缺口", []) + shadow.get("资料缺口", []),
        "安全边界": {
            "是否联网": False,
            "是否下载": False,
            "是否测算金额": False,
            "是否写正式业务规则": False,
            "是否生成正式税务结论": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 研发费用分析准备度门禁",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 准备度状态：{report['准备度状态']}",
        f"- 门禁结论：{report['门禁结论']}",
        "",
        "## 门禁项",
        "",
    ]
    for item in report.get("门禁项", []):
        lines.append(f"- {item['门禁']}：{item['状态']}。{item['说明']}")
    lines.extend(["", "## 允许输出", ""])
    for item in report.get("允许输出", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 禁止输出", ""])
    for item in report.get("禁止输出", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 关键缺口", ""])
    for item in dict.fromkeys(report.get("关键缺口", [])):
        lines.append(f"- {item}")
    lines.extend(["", "## 来源文件", ""])
    for key, value in report.get("来源文件", {}).items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_gate()
    write_json(OUT_JSON, report)
    write_text(OUT_MD, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "准备度状态": report["准备度状态"],
        "门禁结论": report["门禁结论"],
        "输出": str(OUT_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
