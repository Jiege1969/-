# -*- coding: utf-8 -*-
"""
生成五样本前台结论型短答修订样例。

只生成样本资产，用于对齐“企业微信里用户看到的是结论型回答”的目标；
不接企业微信真实入口，不改正式适配器，不外发。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
CHECKLIST_PATH = DATA_DIR / "五样本前台结论型短答验收清单_最新.json"
JSON_OUT = DATA_DIR / "五样本前台结论型短答修订样例_最新.json"
MD_OUT = DATA_DIR / "五样本前台结论型短答修订样例_最新.md"


REVISED_SAMPLES = [
    {
        "stock": {"name": "云南锗业", "code": "sz002428"},
        "front_answer": [
            "云南锗业（sz002428）",
            "结论：可纳入观察，但还不能上调为重点关注。",
            "主要原因：锗出口管制政策事件已结构化匹配，是目前最清楚的积极证据；但资金/机构/解禁证据仍待采集，不能强化结论。",
            "关键缺口：价格/景气尚未入账，不能写趋势确认；财报和资金证据还需要补齐。",
            "置信度：medium。下一次复核重点看锗价连续观测、资金证据和财报摘要是否补上。",
        ],
    },
    {
        "stock": {"name": "天齐锂业", "code": "sz002466"},
        "front_answer": [
            "天齐锂业（sz002466）",
            "结论：可观察，但暂不强化结论。",
            "主要原因：锂行业价格只有少量观测点，只能弱参考；未匹配直接结构化政策，政策项不能加分。",
            "关键缺口：资金/机构/解禁证据仍待采集，不能强化结论；碳酸锂价格/景气观测点不足，不能写趋势确认。",
            "置信度：low to medium。下一次复核重点看锂价连续观测和资金证据。",
        ],
    },
    {
        "stock": {"name": "华虹公司", "code": "sh688347"},
        "front_answer": [
            "华虹公司（sh688347）",
            "结论：可纳入观察，但需要等政策和景气证据落到单股。",
            "主要原因：半导体政策背景存在，但尚未结构化到单股事件，政策证据待补；行业景气尚不能写趋势确认。",
            "关键缺口：资金/机构/解禁证据仍待采集，不能强化结论；晶圆代工景气观测点不足，不能写趋势确认。",
            "置信度：medium。下一次复核重点看政策事件是否能结构化到公司，以及行业景气是否形成连续证据。",
        ],
    },
    {
        "stock": {"name": "浙商中拓", "code": "sz000906"},
        "front_answer": [
            "浙商中拓（sz000906）",
            "结论：暂不建议强化关注，先补证据。",
            "主要原因：当前没有匹配到直接结构化政策，供应链景气也尚未形成连续观测。",
            "关键缺口：资金/机构/解禁证据仍待采集，不能强化结论；价格/景气尚未入账，不能写趋势确认。",
            "置信度：low。下一次复核重点看财报质量、资金证据和供应链景气观测。",
        ],
    },
    {
        "stock": {"name": "正丹股份", "code": "sz300641"},
        "front_answer": [
            "正丹股份（sz300641）",
            "结论：可观察，但不能用题材热度替代结构化证据。",
            "主要原因：未匹配直接结构化政策，政策项不能加分；TMA 价格/景气观测点不足，不能写趋势确认。",
            "关键缺口：资金/机构/解禁证据仍待采集，不能强化结论；财报摘要和行业价格连续观测需要补齐。",
            "置信度：low to medium。下一次复核重点看TMA价格连续观测、资金证据和业绩兑现情况。",
        ],
    },
]


def build_asset() -> dict:
    checklist_exists = CHECKLIST_PATH.exists()
    return {
        "name": "五样本前台结论型短答修订样例",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1样本修订草案",
        "status": "draft",
        "source_assets": {
            "checklist": str(CHECKLIST_PATH),
            "checklist_exists": checklist_exists,
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "front_answer_contract": {
            "format": [
                "第一行：股票名称（代码）",
                "第二行：结论词",
                "第三行：主要原因",
                "第四行：关键缺口",
                "第五行：置信度和下一次复核重点",
            ],
            "principles": [
                "前台回答先给结论，后台分析不原样堆给用户。",
                "依据只写关键原因，缺证据必须明说。",
                "政策、市场风格、行业价格、财报、资金证据不足时，不得强行补分。",
                "不出现交易执行、下单、仓位或券商接口话术。",
            ],
        },
        "samples": REVISED_SAMPLES,
        "summary": {
            "sample_count": len(REVISED_SAMPLES),
            "all_first_line_object_clear": True,
            "all_include_conclusion": True,
            "all_include_missing_or_gap": True,
            "all_include_confidence": True,
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_adapter_write": True,
            "not_score_write": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }


def write_markdown(asset: dict) -> None:
    lines = [
        "# 五样本前台结论型短答修订样例",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：样本修订草案，不写企业微信入口，不真实外发，不改正式适配器。",
        "",
        "## 前台回答格式",
        "",
    ]
    lines.extend([f"- {item}" for item in asset["front_answer_contract"]["format"]])
    lines.extend(["", "## 样本短答", ""])
    for sample in asset["samples"]:
        stock = sample["stock"]
        lines.append(f"### {stock['name']}（{stock['code']}）")
        lines.append("")
        lines.extend(sample["front_answer"])
        lines.append("")
    lines.extend(
        [
            "## 下一步建议",
            "",
            "- 可继续生成“前台短答样例验收器”，用机器规则检查上述样例是否符合对象、结论、缺口、置信度和禁用词要求。",
            "- 写入企业微信适配器或正式入口属于 W3，本轮不实施。",
            "",
        ]
    )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    asset = build_asset()
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({"status": "ok", "json": str(JSON_OUT), "md": str(MD_OUT), "sample_count": len(REVISED_SAMPLES)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
