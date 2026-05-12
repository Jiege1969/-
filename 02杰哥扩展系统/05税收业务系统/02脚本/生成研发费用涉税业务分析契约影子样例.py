# -*- coding: utf-8 -*-
"""
名称：生成研发费用涉税业务分析契约影子样例.py
作用：基于研发费用政策链预演和专项人工复核清单，生成涉税业务分析契约影子样例。
安全边界：只生成待复核分析草案样例；不联网、不下载、不生成正式税务结论。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONTRACT = ROOT / "01配置" / "涉税业务分析契约.json"
POLICY_CHAIN = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案" / "研发费用加计扣除政策链补齐预演_最新.json"
REVIEW_CHECKLIST = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案" / "研发费用加计扣除专项人工复核清单_最新.json"
READINESS_GATE = ROOT / "03数据" / "31研发费用分析准备度门禁" / "研发费用分析准备度门禁_最新.json"
OUT_DIR = ROOT / "03数据" / "29涉税业务分析契约影子样例"
OUT_JSON = OUT_DIR / "研发费用涉税业务分析契约影子样例_最新.json"
OUT_MD = OUT_DIR / "研发费用涉税业务分析契约影子样例_最新.md"


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


def policy_refs(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs = []
    for card in cards:
        refs.append({
            "标题": card.get("标题", ""),
            "文号": card.get("文号", ""),
            "依据层级": card.get("依据层级", ""),
            "资料角色": card.get("资料角色", ""),
            "文件时效": card.get("文件时效", ""),
            "来源链接": card.get("来源链接", ""),
            "本地解析文本路径": card.get("本地解析文本路径", ""),
            "是否当前适用依据候选": card.get("是否当前适用依据候选", False),
            "阻断原因": card.get("阻断原因", []),
        })
    return refs


def condition_rows(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for card in cards:
        if card.get("依据层级") not in {"财税文件", "法律", "行政法规", "税务规范性文件"}:
            continue
        rows.append({
            "依据标题": card.get("标题", ""),
            "适用主体": ["居民企业", "查账征收企业", "待人工结合业务事实确认"],
            "适用事项": ["研发费用税前加计扣除政策证据核验"],
            "适用期间": card.get("施行日期") or "待人工确认",
            "关键条件": card.get("关键条款摘录", []),
            "排除条件": ["不适用活动、限制行业、费用划分不清等需人工核验。"],
            "所需资料": ["研发项目资料", "研发费用辅助账", "费用归集明细", "留存备查资料", "必要时项目鉴定材料"],
        })
    return rows


def build_shadow(contract: dict[str, Any], chain: dict[str, Any], checklist: dict[str, Any], gate: dict[str, Any]) -> dict[str, Any]:
    cards = chain.get("证据卡片", [])
    facts = checklist.get("业务事实补充清单", [])
    return {
        "问题ID": "tax-rd-analysis-shadow-001",
        "契约版本": contract.get("版本", ""),
        "契约状态": "pending_review",
        "准备度门禁状态": gate.get("准备度状态", "not_ready"),
        "准备度门禁结论": gate.get("门禁结论", "当前不得输出研发费用加计扣除适用判断。"),
        "业务问题": "企业研发项目是否具备研发费用加计扣除政策分析条件？",
        "业务事实": {
            "纳税人类型": "待人工补充",
            "税种": "企业所得税",
            "事项": "研发费用加计扣除适用条件分析草案",
            "所属期间": "待人工补充",
            "地区": "待人工补充",
            "金额口径": "不测算金额",
            "事实补充字段": facts,
        },
        "政策依据": policy_refs(cards),
        "依据层级": sorted({card.get("依据层级", "待判定") for card in cards}),
        "适用条件": condition_rows(cards),
        "资料缺口": [
            "财税〔2015〕119号文件时效和联合发文来源仍需人工核验。",
            "企业所得税法实施条例等行政法规层级资料尚未闭环。",
            "后续比例、延续、行业范围政策链尚未闭环。",
            "企业主体、所属期间、项目创新性、费用归集、辅助账和留存备查资料尚未补齐。",
        ],
        "风险点": [
            "案例和政策指引只能用于事实识别或解释辅助，不能替代正式依据。",
            "政策全文有效不等于具体企业项目一定适用，仍需匹配业务事实。",
            "系统不得自行认定项目创新性、技术不确定性或费用归集准确性。",
            "当前样例不得输出可以享受或不能享受研发费用加计扣除的结论。",
        ],
        "置信度": "low",
        "人工复核项": checklist.get("放行闸口", []) + checklist.get("政策链缺口", []),
        "门禁限制": gate.get("禁止输出", []),
        "输出边界": "政策顾问式分析草案；不申报、不退税、不开票、不外发正式税务意见；不输出能否享受的正式税务结论。",
        "是否生成正式税务结论": False,
        "是否接正式入口": False,
    }


def build_markdown(report: dict[str, Any]) -> str:
    item = report["影子样例"]
    lines = [
        "# 研发费用涉税业务分析契约影子样例",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 契约状态：{item['契约状态']}",
        f"- 准备度门禁状态：{item.get('准备度门禁状态')}",
        f"- 准备度门禁结论：{item.get('准备度门禁结论')}",
        f"- 业务问题：{item['业务问题']}",
        f"- 置信度：{item['置信度']}",
        f"- 输出边界：{item['输出边界']}",
        "",
        "## 政策依据",
        "",
    ]
    for evidence in item.get("政策依据", []):
        lines.append(f"- {evidence.get('标题')} | {evidence.get('依据层级')} | {evidence.get('文号') or '文号待核验'} | {evidence.get('文件时效')}")
    lines.extend(["", "## 资料缺口", ""])
    for gap in item.get("资料缺口", []):
        lines.append(f"- {gap}")
    lines.extend(["", "## 风险点", ""])
    for risk in item.get("风险点", []):
        lines.append(f"- {risk}")
    lines.extend(["", "## 人工复核项", ""])
    for review in item.get("人工复核项", []):
        lines.append(f"- {review}")
    return "\n".join(lines) + "\n"


def main() -> int:
    contract = load_json(CONTRACT)
    chain = load_json(POLICY_CHAIN)
    checklist = load_json(REVIEW_CHECKLIST)
    gate = load_json(READINESS_GATE)
    shadow = build_shadow(contract, chain, checklist, gate)
    report = {
        "名称": "研发费用涉税业务分析契约影子样例",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "契约来源": str(CONTRACT),
        "政策链来源": str(POLICY_CHAIN),
        "复核清单来源": str(REVIEW_CHECKLIST),
        "准备度门禁来源": str(READINESS_GATE),
        "影子样例": shadow,
        "安全边界": {
            "是否联网": False,
            "是否下载": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否生成正式税务结论": False,
            "是否接正式入口": False,
        },
    }
    write_json(OUT_JSON, report)
    write_text(OUT_MD, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "契约状态": shadow["契约状态"],
        "政策依据数量": len(shadow["政策依据"]),
        "输出": str(OUT_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
