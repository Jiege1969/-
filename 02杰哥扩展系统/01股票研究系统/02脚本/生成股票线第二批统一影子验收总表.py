# -*- coding: utf-8 -*-
"""
生成股票线第二批统一影子验收总表。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
QUEUE_PATH = DATA_DIR / "股票线第二批低风险续建队列_最新.json"
JSON_OUT = DATA_DIR / "股票线第二批统一影子验收总表_最新.json"
MD_OUT = DATA_DIR / "股票线第二批统一影子验收总表_最新.md"

CHECKS = [
    ("l3_report_gate_matrix", "L3报告生成前置闸口矩阵验收_最新.json"),
    ("front_backend_layering", "五样本前后台分层输出验收矩阵验收_最新.json"),
    ("financial_capital_gap", "财报资金缺口主动暴露规则验收结果_最新.json"),
    ("industry_price_entry_check", "行业价格连续观测入账前检查清单验收_最新.json"),
    ("policy_candidate_blocking", "政策事件候选到入库阻断清单验收_最新.json"),
    ("second_queue", "股票线第二批低风险续建队列验收_最新.json"),
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def check_record(key: str, filename: str) -> dict[str, Any]:
    path = DATA_DIR / filename
    data = load_json(path)
    return {
        "key": key,
        "path": str(path),
        "exists": path.exists(),
        "passed": data.get("passed") is True,
        "errors": data.get("errors", []),
        "warnings": data.get("warnings", []),
        "metrics": data.get("metrics", {}),
    }


def build_asset() -> dict[str, Any]:
    queue = load_json(QUEUE_PATH)
    checks = [check_record(*item) for item in CHECKS]
    all_passed = all(item["exists"] and item["passed"] for item in checks)
    return {
        "name": "股票线第二批统一影子验收总表",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W2第二批统一影子验收总表",
        "status": "passed" if all_passed else "needs_fix",
        "source_assets": {
            "second_queue": str(QUEUE_PATH),
            "second_queue_completed_count": queue.get("summary", {}).get("completed_count"),
            "second_queue_queued_count": queue.get("summary", {}).get("queued_count"),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_real_refresh": True,
        "not_score_write": True,
        "checks": checks,
        "summary": {
            "check_count": len(checks),
            "exists_count": len([item for item in checks if item["exists"]]),
            "passed_count": len([item for item in checks if item["passed"]]),
            "failed_count": len([item for item in checks if not item["passed"]]),
            "allow_shadow_acceptance_claim": all_passed,
            "allow_real_wecom_send": False,
            "allow_formal_entry": False,
            "allow_formal_score_update": False,
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
    s = asset["summary"]
    lines = [
        "# 股票线第二批统一影子验收总表",
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
        f"- 允许影子验收口径：{s['allow_shadow_acceptance_claim']}",
        f"- 允许真实企微发送：{s['allow_real_wecom_send']}",
        "",
        "## 检查项",
        "",
    ]
    for item in asset["checks"]:
        lines.append(f"- {item['key']}｜exists={item['exists']}｜passed={item['passed']}")
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
