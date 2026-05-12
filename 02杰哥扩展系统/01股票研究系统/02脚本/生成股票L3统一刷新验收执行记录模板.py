# -*- coding: utf-8 -*-
"""
生成股票 L3 统一刷新验收执行记录模板。

只生成 W1 记录模板，不执行真实刷新、不抓取数据、不外发、不写正式库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
CHECKLIST_PATH = DATA_DIR / "股票L3五样本统一刷新验收清单_最新.json"
JSON_OUT = DATA_DIR / "股票L3统一刷新验收执行记录模板_最新.json"
MD_OUT = DATA_DIR / "股票L3统一刷新验收执行记录模板_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_asset_check_template(asset_check: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_key": asset_check.get("asset_key"),
        "display_name": asset_check.get("display_name"),
        "path": asset_check.get("path"),
        "expected_exists": True,
        "actual_exists": None,
        "check_result": "pending",
        "blocking_issue": None,
        "missing_action": "如缺失，则禁止生成声称 L3 完整的前台报告，并登记缺口。",
        "review_note": None,
    }


def build_asset() -> dict[str, Any]:
    checklist = load_json(CHECKLIST_PATH)
    source_checks = checklist.get("asset_checks", [])
    execution_items = [build_asset_check_template(item) for item in source_checks]
    return {
        "name": "股票L3统一刷新验收执行记录模板",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1执行记录模板",
        "status": "blank_template",
        "source_assets": {
            "refresh_checklist": str(CHECKLIST_PATH),
            "refresh_checklist_exists": bool(checklist),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "not_real_refresh": True,
        "execution_header": {
            "execution_id": None,
            "execution_time": None,
            "operator": None,
            "trigger_source": "manual_or_shadow",
            "scope": "五样本L3统一刷新验收",
            "real_refresh_performed": False,
            "external_send_performed": False,
            "formal_database_write_performed": False,
        },
        "asset_check_records": execution_items,
        "decision_section": {
            "all_required_assets_ready": None,
            "allow_front_answer_generation": None,
            "allow_l3_complete_claim": None,
            "blocked_reasons": [],
            "missing_summary": None,
            "next_action": None,
        },
        "front_answer_gate": {
            "object_first_line_required": True,
            "conclusion_from_contract_required": True,
            "missing_must_be_explicit": True,
            "no_trade_wording": True,
            "no_formal_recommendation": True,
        },
        "prohibited_actions": [
            "真实发送企业微信",
            "触发 n8n",
            "重启服务或修改 19310",
            "写正式库",
            "接入真实账号",
            "新增买入、卖出、下单、仓位调整、券商接口或自动交易",
        ],
        "summary": {
            "asset_record_count": len(execution_items),
            "required_blank_decision_fields": 6,
            "default_real_refresh_performed": False,
            "default_external_send_performed": False,
            "default_formal_database_write_performed": False,
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
            "not_real_refresh": True,
        },
    }


def write_markdown(asset: dict[str, Any]) -> None:
    lines = [
        "# 股票L3统一刷新验收执行记录模板",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：W1 执行记录模板，不真实刷新，不抓取数据，不外发，不写正式库。",
        "",
        "## 执行头",
        "",
    ]
    for key, value in asset["execution_header"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 资产检查记录", ""])
    for item in asset["asset_check_records"]:
        lines.extend(
            [
                f"### {item['display_name']}",
                "",
                f"- asset_key：{item['asset_key']}",
                f"- expected_exists：{item['expected_exists']}",
                f"- actual_exists：{item['actual_exists']}",
                f"- check_result：{item['check_result']}",
                f"- missing_action：{item['missing_action']}",
                "",
            ]
        )
    lines.extend(["## 决策区", ""])
    for key, value in asset["decision_section"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 禁止动作", ""])
    lines.extend([f"- {item}" for item in asset["prohibited_actions"]])
    lines.extend(["", "## 下一步自动推进", ""])
    lines.append("- 继续生成“统一刷新验收执行记录样例”，用当前资产状态填一份影子执行记录；仍不真实刷新。")
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
