# -*- coding: utf-8 -*-
"""生成财报资金证据字段化补齐样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "财报资金证据字段化补齐样例_最新.json"
MD_OUT = DATA_DIR / "财报资金证据字段化补齐样例_最新.md"


FIELD_SCHEMA = [
    {"field": "financial_report", "label": "财报核心指标", "priority": "P0", "frontend_effect": "缺失时结论最高可纳入观察"},
    {"field": "valuation_position", "label": "估值位置", "priority": "P0", "frontend_effect": "缺失时不得输出估值便宜/昂贵判断"},
    {"field": "institutional_holding", "label": "机构持仓", "priority": "P1", "frontend_effect": "缺失时不得用机构态度强化结论"},
    {"field": "capital_flow", "label": "资金流向", "priority": "P1", "frontend_effect": "缺失时不得声称资金承接强"},
    {"field": "announcement_quality", "label": "近期公告质量", "priority": "P1", "frontend_effect": "缺失时公告因素不进入主因"},
]


SAMPLES = [
    {
        "stock_name": "云南锗业",
        "stock_code": "002428",
        "evidence_fields": {
            "financial_report": {"status": "missing", "priority": "P0", "missing_reason": "最新财报核心指标未进入结构化样例"},
            "valuation_position": {"status": "missing", "priority": "P0", "missing_reason": "估值分位未完成结构化"},
            "institutional_holding": {"status": "missing", "priority": "P1", "missing_reason": "机构持仓变化未接入"},
            "capital_flow": {"status": "missing", "priority": "P1", "missing_reason": "主力/北向资金字段未接入"},
            "announcement_quality": {"status": "partial", "priority": "P1", "missing_reason": "公告只可作为线索，尚未结构化评分"},
        },
        "frontend_constraint": {"conclusion_cap": "可纳入观察", "confidence_cap": "medium", "must_expose_missing": True},
    },
    {
        "stock_name": "三花智控",
        "stock_code": "002050",
        "evidence_fields": {
            "financial_report": {"status": "partial", "priority": "P0", "missing_reason": "财报摘要可补，但盈利质量字段待校验"},
            "valuation_position": {"status": "missing", "priority": "P0", "missing_reason": "估值分位待补"},
            "institutional_holding": {"status": "missing", "priority": "P1", "missing_reason": "机构持仓变化待补"},
            "capital_flow": {"status": "missing", "priority": "P1", "missing_reason": "资金变化待补"},
            "announcement_quality": {"status": "partial", "priority": "P1", "missing_reason": "公告质量字段待复核"},
        },
        "frontend_constraint": {"conclusion_cap": "可纳入观察", "confidence_cap": "medium", "must_expose_missing": True},
    },
    {
        "stock_name": "上纬新材",
        "stock_code": "688585",
        "evidence_fields": {
            "financial_report": {"status": "missing", "priority": "P0", "missing_reason": "财报与盈利质量证据缺失"},
            "valuation_position": {"status": "missing", "priority": "P0", "missing_reason": "估值证据缺失"},
            "institutional_holding": {"status": "missing", "priority": "P1", "missing_reason": "机构证据缺失"},
            "capital_flow": {"status": "missing", "priority": "P1", "missing_reason": "资金证据缺失"},
            "announcement_quality": {"status": "missing", "priority": "P1", "missing_reason": "公告质量未结构化"},
        },
        "frontend_constraint": {"conclusion_cap": "暂不建议关注", "confidence_cap": "low", "must_expose_missing": True},
    },
    {
        "stock_name": "浙商中拓",
        "stock_code": "000906",
        "evidence_fields": {
            "financial_report": {"status": "missing", "priority": "P0", "missing_reason": "贸易业务收入、毛利和周转指标未结构化"},
            "valuation_position": {"status": "missing", "priority": "P0", "missing_reason": "估值与同业比较未补"},
            "institutional_holding": {"status": "missing", "priority": "P1", "missing_reason": "机构变化待补"},
            "capital_flow": {"status": "missing", "priority": "P1", "missing_reason": "资金流向待补"},
            "announcement_quality": {"status": "partial", "priority": "P1", "missing_reason": "公告线索待复核"},
        },
        "frontend_constraint": {"conclusion_cap": "可纳入观察", "confidence_cap": "low", "must_expose_missing": True},
    },
    {
        "stock_name": "正丹股份",
        "stock_code": "300641",
        "evidence_fields": {
            "financial_report": {"status": "missing", "priority": "P0", "missing_reason": "盈利弹性和持续性待结构化"},
            "valuation_position": {"status": "missing", "priority": "P0", "missing_reason": "估值位置待补"},
            "institutional_holding": {"status": "missing", "priority": "P1", "missing_reason": "机构持仓变化待补"},
            "capital_flow": {"status": "missing", "priority": "P1", "missing_reason": "资金承接待补"},
            "announcement_quality": {"status": "partial", "priority": "P1", "missing_reason": "公告线索待复核"},
        },
        "frontend_constraint": {"conclusion_cap": "可纳入观察", "confidence_cap": "medium", "must_expose_missing": True},
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "财报资金证据字段化补齐样例",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W1财报资金证据字段化样例",
        "status": "shadow_field_sample",
        "purpose": "把财报、估值、机构、资金和公告证据拆成结构化字段，并明确缺口如何限制前台结论。",
        "not_real_market_report": True,
        "not_external_send": True,
        "not_formal_entry": True,
        "not_trade_advice": True,
        "field_schema": FIELD_SCHEMA,
        "samples": SAMPLES,
        "summary": {
            "field_count": len(FIELD_SCHEMA),
            "sample_count": len(SAMPLES),
            "all_samples_have_frontend_constraint": all(bool(item["frontend_constraint"]) for item in SAMPLES),
            "all_samples_have_p0_field": all(
                any(field.get("priority") == "P0" for field in item["evidence_fields"].values()) for item in SAMPLES
            ),
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
    }
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 财报资金证据字段化补齐样例",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：W1财报资金证据字段化样例",
        "- 真实外发：否",
        "- 交易建议：否",
        "",
        "## 字段定义",
        "",
        "| 字段 | 名称 | 优先级 | 前台影响 |",
        "| --- | --- | --- | --- |",
    ]
    for item in FIELD_SCHEMA:
        lines.append(f"| {item['field']} | {item['label']} | {item['priority']} | {item['frontend_effect']} |")
    lines.extend(["", "## 样本", ""])
    for sample in SAMPLES:
        lines.extend(
            [
                f"### {sample['stock_name']}（{sample['stock_code']}）",
                "",
                f"- 前台结论上限：{sample['frontend_constraint']['conclusion_cap']}",
                f"- 置信度上限：{sample['frontend_constraint']['confidence_cap']}",
                "",
                "| 字段 | 状态 | 优先级 | 缺口原因 |",
                "| --- | --- | --- | --- |",
            ]
        )
        for field, value in sample["evidence_fields"].items():
            lines.append(f"| {field} | {value['status']} | {value['priority']} | {value['missing_reason']} |")
        lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
