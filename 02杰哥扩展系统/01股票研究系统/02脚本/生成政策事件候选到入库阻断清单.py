# -*- coding: utf-8 -*-
"""
生成政策事件候选到入库阻断清单。

作用：候选政策在官方来源、方向、强度、股票暴露度、时效衰减、反证风险
未完成复核前，不得入库、不得入分。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
CANDIDATE_PATH = DATA_DIR / "政策事件候选草案_20260507.json"
REVIEW_PATH = DATA_DIR / "政策事件单股暴露度人工复核回执模板验收_最新.json"
JSON_OUT = DATA_DIR / "政策事件候选到入库阻断清单_最新.json"
MD_OUT = DATA_DIR / "政策事件候选到入库阻断清单_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def candidate_record(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": event.get("candidate_id"),
        "suggested_event_id": event.get("suggested_event_id"),
        "title": event.get("title"),
        "candidate_status": event.get("candidate_status", "draft"),
        "not_for_scoring": True,
        "entry_gates": {
            "official_source_verified": False,
            "source_url_reachable_or_archived": False,
            "impact_direction_confirmed": False,
            "impact_strength_confirmed": False,
            "valid_until_or_decay_confirmed": False,
            "risk_counterpoint_confirmed": False,
            "stock_exposure_split_ready": False,
            "duplicate_policy_check_passed": False,
            "human_review_passed": False,
        },
        "entry_decision": {
            "can_write_policy_events": False,
            "can_write_stock_exposures": False,
            "can_enter_l3_policy_score": False,
            "blocking_reason": "政策候选尚未完成入库前复核，只能作为线索，不得入库或入分。",
        },
        "candidate_exposure_count": len(event.get("candidate_stock_exposures", [])),
        "missing_before_formal_use": event.get("missing_before_formal_use", []),
    }


def build_asset() -> dict[str, Any]:
    candidate = load_json(CANDIDATE_PATH)
    review = load_json(REVIEW_PATH)
    events = candidate.get("candidate_events", [])
    records = [candidate_record(event) for event in events]
    return {
        "name": "政策事件候选到入库阻断清单",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1政策候选入库阻断清单",
        "status": "shadow_blocking_checklist",
        "source_assets": {
            "candidate_draft": str(CANDIDATE_PATH),
            "candidate_draft_exists": CANDIDATE_PATH.exists(),
            "exposure_review_validation": str(REVIEW_PATH),
            "exposure_review_validation_passed": review.get("passed") is True,
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_policy_event_write": True,
        "not_score_write": True,
        "not_formal_database_write": True,
        "candidate_blocking_records": records,
        "global_blocking_rules": [
            "候选政策不得参与L3政策分。",
            "候选政策不得直接写入policy_events正式表。",
            "候选股票暴露度不得直接写入stock_policy_exposures正式表。",
            "官方来源、影响方向、影响强度、股票暴露度、时效衰减、反证风险、重复政策检查均未完成前，只能作为线索。",
            "新闻热词、行业口号、宏观背景不得替代结构化政策事件。",
        ],
        "summary": {
            "candidate_count": len(records),
            "entry_allowed_count": 0,
            "score_allowed_count": 0,
            "blocked_count": len(records),
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


def write_markdown(asset: dict[str, Any]) -> None:
    lines = [
        "# 政策事件候选到入库阻断清单",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：影子阻断清单，不写政策库，不写评分。",
        "",
        "## 候选阻断",
        "",
    ]
    for item in asset["candidate_blocking_records"]:
        lines.append(f"- {item.get('candidate_id')}｜entry={item['entry_decision']['can_write_policy_events']}｜score={item['entry_decision']['can_enter_l3_policy_score']}")
    lines.extend(["", "## 全局阻断规则", ""])
    lines.extend([f"- {rule}" for rule in asset["global_blocking_rules"]])
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    asset = build_asset()
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({"status": "ok", "json": str(JSON_OUT), "md": str(MD_OUT), "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
