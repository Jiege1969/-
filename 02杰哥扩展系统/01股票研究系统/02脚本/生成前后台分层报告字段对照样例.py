# -*- coding: utf-8 -*-
"""生成前后台分层报告字段对照样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "前后台分层报告字段对照样例_最新.json"
MD_OUT = DATA_DIR / "前后台分层报告字段对照样例_最新.md"


FIELD_MAPPING = [
    {
        "backend_field": "stock_identity",
        "frontend_field": "第一行对象",
        "rule": "前台第一行必须输出股票名称和代码，格式为“股票名称（代码）：结论词”。",
        "frontend_visible": True,
    },
    {
        "backend_field": "total_score + conclusion_threshold",
        "frontend_field": "结论词",
        "rule": "前台只展示结论词，不展开完整计分过程；分数留在后台。",
        "frontend_visible": True,
    },
    {
        "backend_field": "item_scores.evidence",
        "frontend_field": "主要依据",
        "rule": "从后台证据中选择最多3条最能解释结论的依据，禁止平铺全部指标。",
        "frontend_visible": True,
    },
    {
        "backend_field": "item_scores.missing",
        "frontend_field": "关键缺口",
        "rule": "只展示P0/P1缺口，并说明它如何限制结论强度和置信度。",
        "frontend_visible": True,
    },
    {
        "backend_field": "confidence",
        "frontend_field": "置信度表达",
        "rule": "前台用高/中/低和一句原因表达，不展示模型内部推理。",
        "frontend_visible": True,
    },
    {
        "backend_field": "next_review_date + review_focus",
        "frontend_field": "复核提醒",
        "rule": "前台只说明下一次复核看什么，不给买卖、下单、仓位动作。",
        "frontend_visible": True,
    },
    {
        "backend_field": "raw_indicators",
        "frontend_field": "不直接展示",
        "rule": "K线、MACD、RSI、量比等原始指标只作为后台证据，不在前台堆叠。",
        "frontend_visible": False,
    },
    {
        "backend_field": "calculation_trace",
        "frontend_field": "不直接展示",
        "rule": "评分计算过程留在后台验收，不进入企业微信短答。",
        "frontend_visible": False,
    },
]


SAMPLES = [
    {
        "stock_name": "云南锗业",
        "stock_code": "002428",
        "backend_snapshot": {
            "total_score": 68,
            "item_scores": {
                "technical_structure": 27,
                "fundamentals_capital": 8,
                "policy_events": 16,
                "market_style_fit": 17,
            },
            "evidence": ["锗相关政策事件候选有支撑", "资源品主题与市场风格适配", "技术结构仅作辅助确认"],
            "missing": ["P0：财报和盈利质量未结构化", "P0：锗价连续观测待补", "P1：资金和机构变化待补"],
            "confidence": "medium",
        },
        "frontend_output": {
            "first_line": "云南锗业（002428）：可纳入观察。",
            "one_sentence": "政策和资源属性有支撑，但财报、锗价和资金证据还没补齐，暂不输出强结论。",
            "main_reasons": ["锗相关政策事件候选有支撑", "资源品主题与市场风格存在适配", "技术结构只作为辅助确认"],
            "key_missing": ["P0：财报和盈利质量未结构化", "P0：锗价连续观测待补"],
            "confidence_text": "置信度中等，主要受财报和价格连续数据缺口限制。",
            "review_hint": "下一次优先复核财报、锗价和资金证据。",
        },
    },
    {
        "stock_name": "正丹股份",
        "stock_code": "300641",
        "backend_snapshot": {
            "total_score": 66,
            "item_scores": {
                "technical_structure": 24,
                "fundamentals_capital": 9,
                "policy_events": 11,
                "market_style_fit": 18,
            },
            "evidence": ["化工品价格弹性线索", "新增样本已纳入验收", "市场风格存在阶段适配"],
            "missing": ["P0：核心产品价格连续数据待补", "P0：最新财报盈利弹性待复核", "P1：资金承接待补"],
            "confidence": "medium",
        },
        "frontend_output": {
            "first_line": "正丹股份（300641）：可纳入观察。",
            "one_sentence": "若产品价格和盈利弹性能连续验证，结论才有上修空间；当前先观察。",
            "main_reasons": ["化工品价格弹性线索值得跟踪", "新增样本已纳入验收", "市场风格阶段适配"],
            "key_missing": ["P0：核心产品价格连续数据待补", "P0：最新财报盈利弹性待复核"],
            "confidence_text": "置信度中等，关键取决于价格和财报能否连续验证。",
            "review_hint": "下一次优先复核核心产品价格、财报和资金承接。",
        },
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "前后台分层报告字段对照样例",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W2前后台字段映射样例",
        "status": "shadow_mapping_sample",
        "purpose": "明确后台负责证据链和评分，前台负责结论型表达，防止企业微信回答堆指标或展示过多分析过程。",
        "not_real_market_report": True,
        "not_external_send": True,
        "not_formal_entry": True,
        "not_trade_advice": True,
        "field_mapping": FIELD_MAPPING,
        "samples": SAMPLES,
        "frontend_constraints": {
            "max_main_reasons": 3,
            "must_include_stock_identity_first": True,
            "must_include_missing_when_present": True,
            "must_hide_raw_indicators": True,
            "must_hide_calculation_trace": True,
            "must_not_include_trade_action": True,
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_formal_config": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
            "not_order": True,
            "not_position_adjustment": True,
        },
        "summary": {
            "mapping_count": len(FIELD_MAPPING),
            "sample_count": len(SAMPLES),
            "frontend_visible_count": len([item for item in FIELD_MAPPING if item["frontend_visible"]]),
            "backend_only_count": len([item for item in FIELD_MAPPING if not item["frontend_visible"]]),
        },
    }
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 前后台分层报告字段对照样例",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：W2前后台字段映射样例",
        "- 真实外发：否",
        "- 交易建议：否",
        "",
        "## 字段映射",
        "",
        "| 后台字段 | 前台字段 | 是否前台展示 | 规则 |",
        "| --- | --- | --- | --- |",
    ]
    for item in FIELD_MAPPING:
        lines.append(f"| {item['backend_field']} | {item['frontend_field']} | {'是' if item['frontend_visible'] else '否'} | {item['rule']} |")
    lines.extend(["", "## 样本", ""])
    for sample in SAMPLES:
        front = sample["frontend_output"]
        lines.extend(
            [
                f"### {sample['stock_name']}（{sample['stock_code']}）",
                "",
                front["first_line"],
                "",
                front["one_sentence"],
                "",
                "主要依据：" + "；".join(front["main_reasons"]) + "。",
                "",
                "关键缺口：" + "；".join(front["key_missing"]) + "。",
                "",
                front["confidence_text"],
                "",
                "复核提醒：" + front["review_hint"],
                "",
            ]
        )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
