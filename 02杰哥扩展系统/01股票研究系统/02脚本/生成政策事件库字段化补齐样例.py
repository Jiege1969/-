# -*- coding: utf-8 -*-
"""生成政策事件库字段化补齐样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "政策事件库字段化补齐样例_最新.json"
MD_OUT = DATA_DIR / "政策事件库字段化补齐样例_最新.md"


FIELD_SCHEMA = [
    {"field": "event_id", "required": True},
    {"field": "source_name", "required": True},
    {"field": "source_url_status", "required": True},
    {"field": "publish_date", "required": True},
    {"field": "impact_direction", "required": True},
    {"field": "impact_strength", "required": True},
    {"field": "stock_exposure", "required": True},
    {"field": "decay_status", "required": True},
    {"field": "confidence", "required": True},
    {"field": "frontend_effect", "required": True},
    {"field": "missing_reason", "required": True},
]


SAMPLES = [
    {
        "stock_name": "云南锗业",
        "stock_code": "002428",
        "policy_event": {
            "event_id": "POL-GE-EXPORT-CONTROL-SHADOW-001",
            "title": "锗相关物项出口管制政策事件候选",
            "source_name": "商务部/海关总署候选来源",
            "source_url_status": "pending_real_url_review",
            "publish_date": "shadow_sample",
            "impact_direction": "positive",
            "impact_strength": 0.85,
            "stock_exposure": 0.95,
            "decay_status": "pending_valid_until_review",
            "confidence": "medium",
            "frontend_effect": "可作为政策主因候选，但来源链接和有效期未复核前不得单独支撑重点关注。",
            "missing_reason": "真实来源链接、有效期、衰减窗口和政策原文摘要待复核。",
        },
    },
    {
        "stock_name": "正丹股份",
        "stock_code": "300641",
        "policy_event": {
            "event_id": "POL-CHEM-SUPPLY-SHADOW-001",
            "title": "化工品供需与安全监管政策候选",
            "source_name": "行业监管/产业政策候选来源",
            "source_url_status": "missing",
            "publish_date": "shadow_sample",
            "impact_direction": "neutral_watch",
            "impact_strength": 0.35,
            "stock_exposure": 0.55,
            "decay_status": "not_started",
            "confidence": "low",
            "frontend_effect": "只能作为行业背景线索，不进入强政策加分。",
            "missing_reason": "缺少可复核政策原文、影响方向和公司暴露度证据。",
        },
    },
    {
        "stock_name": "三花智控",
        "stock_code": "002050",
        "policy_event": {
            "event_id": "POL-ADV-MFG-SHADOW-001",
            "title": "先进制造/节能设备政策背景候选",
            "source_name": "产业政策候选来源",
            "source_url_status": "partial",
            "publish_date": "shadow_sample",
            "impact_direction": "positive_watch",
            "impact_strength": 0.45,
            "stock_exposure": 0.6,
            "decay_status": "pending_event_match",
            "confidence": "medium",
            "frontend_effect": "只作为产业背景辅助，不替代财报、订单和资金证据。",
            "missing_reason": "政策事件与具体业务暴露度匹配待复核。",
        },
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "政策事件库字段化补齐样例",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W1政策事件字段化样例",
        "status": "shadow_field_sample",
        "purpose": "把政策事件库中的来源、方向、强度、暴露度、时效、置信度和前台影响拆成可验收字段。",
        "not_real_policy_database": True,
        "not_external_send": True,
        "not_formal_entry": True,
        "not_score_write": True,
        "field_schema": FIELD_SCHEMA,
        "samples": SAMPLES,
        "summary": {
            "field_count": len(FIELD_SCHEMA),
            "sample_count": len(SAMPLES),
            "all_have_frontend_effect": all(bool(item["policy_event"]["frontend_effect"]) for item in SAMPLES),
            "all_have_missing_reason": all(bool(item["policy_event"]["missing_reason"]) for item in SAMPLES),
            "ready_source_count": len([item for item in SAMPLES if item["policy_event"]["source_url_status"] == "ready"]),
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
        "# 政策事件库字段化补齐样例",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：W1政策事件字段化样例",
        "- 正式政策库写入：否",
        "- 交易建议：否",
        "",
        "## 字段定义",
        "",
        "| 字段 | 必填 |",
        "| --- | --- |",
    ]
    for item in FIELD_SCHEMA:
        lines.append(f"| {item['field']} | {'是' if item['required'] else '否'} |")
    lines.extend(["", "## 样本", ""])
    for sample in SAMPLES:
        event = sample["policy_event"]
        lines.extend(
            [
                f"### {sample['stock_name']}（{sample['stock_code']}）",
                "",
                f"- 事件：{event['title']}",
                f"- 来源状态：{event['source_url_status']}",
                f"- 影响方向：{event['impact_direction']}",
                f"- 影响强度：{event['impact_strength']}",
                f"- 股票暴露度：{event['stock_exposure']}",
                f"- 时效状态：{event['decay_status']}",
                f"- 置信度：{event['confidence']}",
                f"- 前台影响：{event['frontend_effect']}",
                f"- 缺口原因：{event['missing_reason']}",
                "",
            ]
        )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
