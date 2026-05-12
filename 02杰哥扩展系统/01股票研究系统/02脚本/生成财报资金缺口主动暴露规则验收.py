# -*- coding: utf-8 -*-
"""
生成财报资金缺口主动暴露规则验收。

作用：把财报、资金、机构、解禁等证据缺失状态，转成前台固定缺口话术
和后台阻断字段，避免缺证据仍输出强结论。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
RECEIPT_PATH = DATA_DIR / "财报资金证据人工填写回执模板_最新.json"
VALIDATION_PATH = DATA_DIR / "财报资金证据人工填写回执模板验收_最新.json"
JSON_OUT = DATA_DIR / "财报资金缺口主动暴露规则验收_最新.json"
MD_OUT = DATA_DIR / "财报资金缺口主动暴露规则验收_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def group_receipts_by_stock(receipts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in receipts:
        stock = item.get("stock", {})
        code = stock.get("code")
        if not code:
            continue
        grouped.setdefault(code, {"stock": stock, "groups": []})
        grouped[code]["groups"].append(item)
    return grouped


def stock_gap_rule(stock_record: dict[str, Any]) -> dict[str, Any]:
    stock = stock_record["stock"]
    groups = stock_record["groups"]
    missing_groups = []
    score_allowed = 0
    for group in groups:
        fields = group.get("field_receipts", {})
        if any(field.get("can_enter_score") is True for field in fields.values()):
            score_allowed += 1
        if group.get("ready_review", {}).get("ready") is not True:
            missing_groups.append(group.get("display_name") or group.get("field_group"))
    return {
        "stock": stock,
        "missing_groups": missing_groups,
        "score_allowed_group_count": score_allowed,
        "front_gap_wording": "财报/资金/机构/解禁证据尚未补齐，基本面和资金项只能作为缺口提示，不能强化结论。",
        "backend_blocking_fields": {
            "financial_capital_score_allowed": False,
            "fundamental_confirmation_allowed": False,
            "capital_flow_confirmation_allowed": False,
            "institutional_confirmation_allowed": False,
            "unlock_risk_confirmation_allowed": False,
            "max_confidence_if_other_evidence_ready": "medium",
        },
        "missing_to_evidence_ready_condition": [
            "来源名称、来源URL、口径日期齐全。",
            "核心字段由missing/candidate变为evidence_ready。",
            "人工复核通过。",
            "can_enter_score显式为true。",
        ],
    }


def build_asset() -> dict[str, Any]:
    receipt = load_json(RECEIPT_PATH)
    validation = load_json(VALIDATION_PATH)
    grouped = group_receipts_by_stock(receipt.get("receipts", []))
    rules = [stock_gap_rule(grouped[key]) for key in sorted(grouped)]
    return {
        "name": "财报资金缺口主动暴露规则验收",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1财报资金缺口主动暴露规则",
        "status": "shadow_acceptance",
        "source_assets": {
            "receipt_template": str(RECEIPT_PATH),
            "receipt_template_exists": RECEIPT_PATH.exists(),
            "receipt_validation": str(VALIDATION_PATH),
            "receipt_validation_passed": validation.get("passed") is True,
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "not_real_data_fetch": True,
        "stock_gap_rules": rules,
        "global_front_rules": [
            "前台必须主动写财报/资金缺口，不等用户追问。",
            "缺财报资金证据时，不能写基本面确认。",
            "缺资金流证据时，不能写资金确认。",
            "缺机构持仓证据时，不能写机构认可。",
            "缺解禁减持证据时，不能写风险已排除。",
        ],
        "global_backend_rules": [
            "financial_capital_score_allowed默认为false。",
            "所有missing字段不得进入L3加分。",
            "空白回执不得作为证据。",
            "人工填报后仍需复核，复核前保持pending_review。",
        ],
        "summary": {
            "stock_count": len(rules),
            "receipt_count": len(receipt.get("receipts", [])),
            "ready_count": validation.get("metrics", {}).get("ready_count", 0),
            "score_allowed_count": validation.get("metrics", {}).get("score_allowed_count", 0),
            "front_gap_required_count": len(rules),
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
        "# 财报资金缺口主动暴露规则验收",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：影子规则验收，不抓取真实数据，不写评分。",
        "",
        "## 样本缺口规则",
        "",
    ]
    for item in asset["stock_gap_rules"]:
        stock = item["stock"]
        lines.append(f"- {stock.get('name')}（{stock.get('code')}）：缺口组={len(item['missing_groups'])}，score_allowed={item['score_allowed_group_count']}")
    lines.extend(["", "## 前台规则", ""])
    lines.extend([f"- {rule}" for rule in asset["global_front_rules"]])
    lines.extend(["", "## 后台规则", ""])
    lines.extend([f"- {rule}" for rule in asset["global_backend_rules"]])
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
