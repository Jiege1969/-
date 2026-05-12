# -*- coding: utf-8 -*-
"""
名称：生成涉税业务分析契约影子样例.py
作用：基于涉税业务分析契约和政策证据底座字段补齐预演，生成待复核分析草案样例。
触发方式：python 生成涉税业务分析契约影子样例.py
安全边界：只生成影子样例；不联网、不下载、不接电子税务局或财税软件、不触发n8n、不企业微信发送、不生成正式税务结论。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONTRACT = ROOT / "01配置" / "涉税业务分析契约.json"
EVIDENCE_PREVIEW = ROOT / "03数据" / "28政策证据底座字段补齐预演" / "税收政策证据底座字段补齐预演_最新.json"
OUT_DIR = ROOT / "03数据" / "29涉税业务分析契约影子样例"


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


def select_evidence(rows: list[dict[str, Any]], keyword: str) -> list[dict[str, Any]]:
    selected = []
    for item in rows:
        hay = json.dumps(item, ensure_ascii=False)
        if keyword in hay and item.get("是否当前适用依据候选") is True:
            selected.append(item)
    return selected[:3]


def build_shadow_case(contract: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    evidences = select_evidence(rows, "企业所得税")
    policy_refs = [
        {
            "标题": item.get("标题", ""),
            "文号": item.get("文号", ""),
            "发文机关": item.get("发文机关", ""),
            "文件时效": item.get("文件时效", ""),
            "来源链接": item.get("最终链接") or item.get("来源链接", ""),
            "本地解析文本路径": item.get("保存路径", {}).get("解析文本", ""),
            "是否当前适用依据候选": item.get("是否当前适用依据候选", False),
        }
        for item in evidences
    ]
    condition_items = []
    for item in evidences:
        condition_items.append({
            "依据标题": item.get("标题", ""),
            "适用主体": item.get("适用主体", []),
            "适用事项": item.get("适用事项", []),
            "适用期间": item.get("适用期间", ""),
            "关键条件": item.get("关键条件", []),
            "排除条件": item.get("排除条件", []),
            "所需资料": item.get("所需资料", []),
        })

    return {
        "问题ID": "tax-analysis-shadow-001",
        "契约版本": contract.get("版本", ""),
        "契约状态": "pending_review",
        "业务问题": "企业进行企业所得税预缴申报时，当前应参考哪些申报表政策依据？",
        "业务事实": {
            "纳税人类型": "待人工确认",
            "税种": "企业所得税",
            "事项": "预缴申报表适用依据分析",
            "所属期间": "待人工确认",
            "地区": "待人工确认",
            "金额口径": "不测算金额",
        },
        "政策依据": policy_refs,
        "依据层级": sorted({item.get("依据层级", "待判定") for item in evidences}),
        "适用条件": condition_items,
        "资料缺口": [
            "纳税人征收方式、所属期间、是否跨地区经营、是否涉及出口或优惠事项仍需人工补充。",
            "附件表单和填报说明需要确认正式解析结果。",
            "如涉及地方执行口径，需要补充适用地区和上位文件关系。",
        ],
        "风险点": [
            "本样例只展示分析契约字段，不形成正式税务意见。",
            "政策全文有效不等于具体业务一定适用，仍需匹配业务事实。",
            "附件未完成正式解析前，不得把表单栏次作为确定处理依据。",
        ],
        "置信度": "medium" if policy_refs else "low",
        "人工复核项": [
            "确认业务主体、期间、地区和申报场景。",
            "确认政策时效、附件解析和是否存在后续修订。",
            "确认是否需要地方税务机关口径或专业税务复核。",
        ],
        "输出边界": "政策顾问式分析草案；不申报、不退税、不开票、不外发正式税务意见。",
        "是否生成正式税务结论": False,
        "是否接正式入口": False,
    }


def build_markdown(report: dict[str, Any]) -> str:
    item = report["影子样例"]
    lines = [
        "# 涉税业务分析契约影子样例",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 契约状态：{item['契约状态']}",
        f"- 业务问题：{item['业务问题']}",
        f"- 置信度：{item['置信度']}",
        f"- 输出边界：{item['输出边界']}",
        "",
        "## 政策依据",
        "",
    ]
    for evidence in item.get("政策依据", []):
        lines.append(f"- {evidence.get('标题')} | {evidence.get('文号') or '文号待补'} | {evidence.get('文件时效')}")
    lines.extend(["", "## 资料缺口", ""])
    for gap in item.get("资料缺口", []):
        lines.append(f"- {gap}")
    lines.extend(["", "## 人工复核项", ""])
    for review in item.get("人工复核项", []):
        lines.append(f"- {review}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    contract = load_json(CONTRACT)
    evidence = load_json(EVIDENCE_PREVIEW, {"资料": []})
    shadow = build_shadow_case(contract, evidence.get("资料", []))
    report = {
        "名称": "涉税业务分析契约影子样例",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "契约来源": str(CONTRACT),
        "证据来源": str(EVIDENCE_PREVIEW),
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
    write_json(OUT_DIR / "涉税业务分析契约影子样例_最新.json", report)
    write_text(OUT_DIR / "涉税业务分析契约影子样例_最新.md", build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "契约状态": shadow["契约状态"],
        "政策依据数量": len(shadow["政策依据"]),
        "输出": str(OUT_DIR / "涉税业务分析契约影子样例_最新.json"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
