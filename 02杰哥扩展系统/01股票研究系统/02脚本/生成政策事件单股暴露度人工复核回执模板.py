# -*- coding: utf-8 -*-
"""
生成政策事件单股暴露度人工复核回执模板。

政策事件库和暴露度表只是结构化证据来源；进入L3政策分前，还需要
复核官方来源、影响强度、股票暴露度、时效衰减、反证风险和重复计分。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
QUEUE_PATH = DATA_DIR / "五样本政策事件缺口队列_最新.json"
EVENTS_PATH = DATA_DIR / "policy_events_v1.0.json"
EXPOSURES_PATH = DATA_DIR / "stock_policy_exposures_v1.0.json"
JSON_OUT = DATA_DIR / "政策事件单股暴露度人工复核回执模板_最新.json"
MD_OUT = DATA_DIR / "政策事件单股暴露度人工复核回执模板_最新.md"

FALLBACK_TASKS = [
    {"stock": {"name": "云南锗业", "code": "sz002428"}, "classification": "structured_policy_ready", "matched_policy_events": [{"event_id": "POL-2023-001"}]},
    {"stock": {"name": "天齐锂业", "code": "sz002466"}, "classification": "no_direct_structured_policy", "matched_policy_events": []},
    {"stock": {"name": "华虹公司", "code": "sh688347"}, "classification": "candidate_policy_needed", "matched_policy_events": []},
    {"stock": {"name": "浙商中拓", "code": "sz000906"}, "classification": "no_direct_structured_policy", "matched_policy_events": []},
    {"stock": {"name": "正丹股份", "code": "sz300641"}, "classification": "candidate_policy_needed", "matched_policy_events": []},
]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return default


def load_tasks() -> list[dict[str, Any]]:
    queue = load_json(QUEUE_PATH, {})
    tasks = queue.get("tasks") if isinstance(queue, dict) else None
    return tasks if isinstance(tasks, list) and tasks else FALLBACK_TASKS


def review_fields(has_event: bool) -> dict[str, dict[str, Any]]:
    base_status = "pending_review"
    return {
        "official_source_valid": {
            "value": None,
            "required_for_score": True,
            "evidence_status": "missing",
            "review_status": base_status,
        },
        "impact_direction_confirmed": {
            "value": None,
            "required_for_score": True,
            "evidence_status": "missing",
            "review_status": base_status,
        },
        "impact_strength_review": {
            "value": None,
            "range": [0, 1],
            "required_for_score": True,
            "evidence_status": "missing" if has_event else "not_applicable",
            "review_status": base_status,
        },
        "stock_exposure_review": {
            "value": None,
            "range": [0, 1],
            "required_for_score": True,
            "evidence_status": "missing" if has_event else "not_applicable",
            "review_status": base_status,
        },
        "decay_factor_review": {
            "value": None,
            "range": [0, 1],
            "required_for_score": True,
            "evidence_status": "missing" if has_event else "not_applicable",
            "review_status": base_status,
        },
        "risk_counterpoint_review": {
            "value": None,
            "required_for_score": True,
            "evidence_status": "missing" if has_event else "not_applicable",
            "review_status": base_status,
        },
        "duplicate_score_check": {
            "value": None,
            "required_for_score": True,
            "evidence_status": "missing" if has_event else "not_applicable",
            "review_status": base_status,
        },
        "policy_score_candidate": {
            "value": None,
            "range": [0, 20],
            "required_for_score": True,
            "evidence_status": "missing",
            "review_status": base_status,
        },
    }


def build_receipt(task: dict[str, Any]) -> dict[str, Any]:
    matched = task.get("matched_policy_events", []) or []
    has_event = bool(matched)
    return {
        "stock": task.get("stock", {}),
        "classification": task.get("classification"),
        "matched_event_count": len(matched),
        "matched_policy_events": matched,
        "source_assets": {
            "policy_events": str(EVENTS_PATH),
            "stock_policy_exposures": str(EXPOSURES_PATH),
            "gap_queue": str(QUEUE_PATH),
        },
        "receipt_status": "blank",
        "review_fields": review_fields(has_event),
        "ready_review": {
            "policy_score_ready": False,
            "score_ready": False,
            "ready_condition": "官方来源、影响方向、影响强度、股票暴露度、时效衰减、反证风险和重复计分检查全部通过后，才可进入政策分。",
            "blocking_reason": "政策证据尚未完成入分前复核，不能凭政策背景或新闻热词给单股政策分。",
        },
        "front_output_rule": {
            "when_missing": "未完成政策事件入分复核时，前台只写政策证据缺口或背景参考，不写政策强驱动。",
            "when_ready": "输出一句结论型政策影响判断，并在后台保留事件ID、来源、暴露度、时效衰减和反证风险。",
        },
    }


def build_asset() -> dict[str, Any]:
    events = load_json(EVENTS_PATH, [])
    exposures = load_json(EXPOSURES_PATH, [])
    receipts = [build_receipt(task) for task in load_tasks()]
    return {
        "name": "政策事件单股暴露度人工复核回执模板",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1政策事件单股暴露度复核模板",
        "status": "blank_template",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_policy_event_write": True,
        "not_score_write": True,
        "not_formal_database_write": True,
        "source_summary": {
            "policy_event_count": len(events) if isinstance(events, list) else 0,
            "stock_exposure_count": len(exposures) if isinstance(exposures, list) else 0,
            "queue_exists": QUEUE_PATH.exists(),
        },
        "receipts": receipts,
        "review_rules": [
            "未入库政策不得参与L3政策分。",
            "无股票暴露度映射不得给单股政策分。",
            "宏观背景、行业口号、新闻热词不得替代结构化政策事件。",
            "政策强度、股票暴露度、时效衰减和反证风险不得凭空补。",
            "已有结构化事件也必须复核重复计分和时效衰减后再入分。",
            "不得生成买卖、下单、仓位或交易建议。",
        ],
        "summary": {
            "receipt_count": len(receipts),
            "stock_count": len({item.get("stock", {}).get("code") for item in receipts}),
            "matched_event_stock_count": len([item for item in receipts if item.get("matched_event_count", 0) > 0]),
            "policy_score_ready_count": 0,
            "score_allowed_count": 0,
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_policy_event_write": True,
            "not_score_write": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }


def write_markdown(asset: dict[str, Any]) -> None:
    lines = [
        "# 政策事件单股暴露度人工复核回执模板",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：W1复核模板，不写政策库，不改评分，不触发外发。",
        "",
        "## 来源概况",
        "",
        f"- 政策事件数：{asset['source_summary']['policy_event_count']}",
        f"- 暴露度映射数：{asset['source_summary']['stock_exposure_count']}",
        f"- 缺口队列存在：{asset['source_summary']['queue_exists']}",
        "",
        "## 回执清单",
        "",
    ]
    for item in asset["receipts"]:
        stock = item.get("stock", {})
        lines.append(
            f"- {stock.get('name')}（{stock.get('code')}）："
            f"匹配事件{item.get('matched_event_count')}个，policy_score_ready={item['ready_review']['policy_score_ready']}"
        )
    lines.extend(["", "## 复核规则", ""])
    lines.extend([f"- {rule}" for rule in asset["review_rules"]])
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
