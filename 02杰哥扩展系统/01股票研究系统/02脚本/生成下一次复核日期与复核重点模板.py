# -*- coding: utf-8 -*-
"""生成下一次复核日期与复核重点模板。

本脚本只生成股票线W1影子模板，帮助前后台报告闭环，不触发任何真实提醒或外发。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "下一次复核日期与复核重点模板_最新.json"
MD_OUT = DATA_DIR / "下一次复核日期与复核重点模板_最新.md"


REVIEW_RULES = [
    {
        "rule_id": "REVIEW-001",
        "condition": "high_confidence_and_core_evidence_ready",
        "default_interval": "T+1至T+3",
        "review_trigger": "价格、成交、公告或政策证据发生明显变化",
        "front_requirement": "短答可给明确结论，但必须给下一次复核日期。",
    },
    {
        "rule_id": "REVIEW-002",
        "condition": "medium_confidence_with_one_key_missing",
        "default_interval": "T+3至T+5",
        "review_trigger": "关键缺口补齐或市场风格明显切换",
        "front_requirement": "短答以观察结论为主，复核重点必须指向缺口。",
    },
    {
        "rule_id": "REVIEW-003",
        "condition": "low_confidence_or_two_plus_key_missing",
        "default_interval": "T+5至T+10",
        "review_trigger": "财报、政策、行业价格、资金证据至少补齐两项",
        "front_requirement": "短答不输出强判断，主要给缺口和补证方向。",
    },
    {
        "rule_id": "REVIEW-004",
        "condition": "object_unresolved",
        "default_interval": "none",
        "review_trigger": "用户补充明确股票名称或代码",
        "front_requirement": "先澄清对象，不生成复核日期。",
    },
]


SAMPLES = [
    {
        "stock": {"name": "云南锗业", "code": "002428"},
        "confidence": "medium",
        "next_review_date": "2026-05-13",
        "review_focus": ["锗价连续观测", "政策事件暴露度复核", "资金承接变化"],
    },
    {
        "stock": {"name": "天齐锂业", "code": "002466"},
        "confidence": "medium",
        "next_review_date": "2026-05-13",
        "review_focus": ["锂价趋势", "财报盈利修复", "板块热度"],
    },
    {
        "stock": {"name": "华虹公司", "code": "688347"},
        "confidence": "medium",
        "next_review_date": "2026-05-13",
        "review_focus": ["半导体景气", "毛利率趋势", "政策证据匹配"],
    },
    {
        "stock": {"name": "浙商中拓", "code": "000906"},
        "confidence": "low",
        "next_review_date": "2026-05-15",
        "review_focus": ["经营现金流", "商品周期", "公告风险"],
    },
    {
        "stock": {"name": "正丹股份", "code": "300641"},
        "confidence": "medium",
        "next_review_date": "2026-05-13",
        "review_focus": ["核心产品价格", "订单景气", "资金承接"],
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "下一次复核日期与复核重点模板",
        "version": "v1.0",
        "generated_at": generated_at,
        "asset_identity": "W1下一次复核日期与复核重点影子模板",
        "status": "shadow_review_template",
        "not_formal_config": True,
        "not_scheduler": True,
        "not_external_send": True,
        "rules": REVIEW_RULES,
        "samples": SAMPLES,
        "required_output_fields": [
            "next_review_date",
            "review_focus",
            "review_trigger",
            "missing_to_check",
            "confidence_recheck_condition",
        ],
        "summary": {
            "rule_count": len(REVIEW_RULES),
            "sample_count": len(SAMPLES),
            "real_reminder_allowed": False,
            "external_send_allowed": False,
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
        },
    }
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 下一次复核日期与复核重点模板",
        "",
        f"- 生成时间：{generated_at}",
        "- 资产身份：W1下一次复核日期与复核重点影子模板",
        "- 状态：shadow_review_template",
        "- 边界：只生成报告字段模板，不触发真实提醒或外发。",
        "",
        "## 样本",
        "",
    ]
    for item in SAMPLES:
        lines.append(f"- {item['stock']['name']}（{item['stock']['code']}）：{item['next_review_date']}；重点：{'、'.join(item['review_focus'])}")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
