# -*- coding: utf-8 -*-
"""
生成股票L3统一刷新影子验收总表。

汇总前台短答、财报资金、行业价格、政策事件、市场风格、复盘候选、
连续施工队列等低风险影子验收资产；不触发真实刷新或外发。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "股票L3统一刷新影子验收总表_最新.json"
MD_OUT = DATA_DIR / "股票L3统一刷新影子验收总表_最新.md"

CHECKS = [
    ("front_short_answer", "前台结论型短答统一验收记录验收_最新.json", "W1"),
    ("financial_capital_receipt", "财报资金证据人工填写回执模板验收_最新.json", "W1"),
    ("industry_price_receipt", "行业价格观测人工填报回执模板验收_最新.json", "W1"),
    ("policy_event_exposure_receipt", "政策事件单股暴露度人工复核回执模板验收_最新.json", "W1"),
    ("market_style_fit_receipt", "市场风格单股适配人工复核回执模板验收_最新.json", "W1"),
    ("review_candidate_template", "复盘人工修正规则候选模板验收_最新.json", "W1"),
    ("review_loop_acceptance", "复盘闭环验收_最新.json", "W1"),
    ("auto_continue_queue", "股票线连续施工自动续建队列验收_最新.json", "W1"),
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def check_record(key: str, filename: str, risk_level: str) -> dict[str, Any]:
    path = DATA_DIR / filename
    data = load_json(path)
    passed = data.get("passed")
    if passed is None:
        passed = data.get("status") == "passed"
    return {
        "key": key,
        "risk_level": risk_level,
        "path": str(path),
        "exists": path.exists(),
        "passed": passed is True,
        "status": data.get("status"),
        "generated_at": data.get("generated_at"),
        "errors": data.get("errors", []),
        "warnings": data.get("warnings", []),
        "metrics": data.get("metrics") or data.get("summary") or {},
    }


def build_asset() -> dict[str, Any]:
    checks = [check_record(*item) for item in CHECKS]
    all_passed = all(item["exists"] and item["passed"] for item in checks)
    return {
        "name": "股票L3统一刷新影子验收总表",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1统一刷新影子验收总表",
        "status": "passed" if all_passed else "needs_fix",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_real_refresh": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "checks": checks,
        "summary": {
            "check_count": len(checks),
            "exists_count": len([item for item in checks if item["exists"]]),
            "passed_count": len([item for item in checks if item["passed"]]),
            "failed_count": len([item for item in checks if not item["passed"]]),
            "allow_shadow_refresh_claim": all_passed,
            "allow_real_wecom_send": False,
            "allow_formal_entry": False,
            "allow_formal_score_update": False,
        },
        "front_output_rule": {
            "can_say": "影子验收链路已通过，可用于后台继续验证前台短答和证据缺口。",
            "cannot_say": "已正式上线、已真实外发、已接入正式入口或评分规则会自动更新。",
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
            "not_formal_config": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }


def write_markdown(asset: dict[str, Any]) -> None:
    s = asset["summary"]
    lines = [
        "# 股票L3统一刷新影子验收总表",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：影子验收总表，不真实刷新、不外发、不改正式入口。",
        "",
        "## 汇总",
        "",
        f"- 检查项：{s['check_count']}",
        f"- 存在：{s['exists_count']}",
        f"- 通过：{s['passed_count']}",
        f"- 失败：{s['failed_count']}",
        f"- 允许影子刷新口径：{s['allow_shadow_refresh_claim']}",
        f"- 允许真实企微发送：{s['allow_real_wecom_send']}",
        "",
        "## 检查项",
        "",
    ]
    for item in asset["checks"]:
        lines.append(f"- {item['key']}｜{item['risk_level']}｜exists={item['exists']}｜passed={item['passed']}")
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    asset = build_asset()
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({"status": asset["status"], "json": str(JSON_OUT), "md": str(MD_OUT), "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
