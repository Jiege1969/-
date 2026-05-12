# -*- coding: utf-8 -*-
"""生成股票线第九批统一影子验收总表。

只汇总第九批 W1/W2 影子资产，不接券商、不交易、不写正式配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "股票线第九批统一影子验收总表_最新.json"
MD_OUT = DATA_DIR / "股票线第九批统一影子验收总表_最新.md"


CHECKS = [
    {
        "batch_item": "STOCK-AUTO9-001",
        "label": "前台结论型短答压缩回归样例",
        "path": DATA_DIR / "前台结论型短答压缩回归样例验收结果_最新.json",
        "mode": "passed_json",
    },
    {
        "batch_item": "STOCK-AUTO9-002",
        "label": "财报资金真实来源接入前字段候选卡",
        "path": DATA_DIR / "财报资金真实来源接入前字段候选卡_最新.json",
        "mode": "candidate_asset",
    },
    {
        "batch_item": "STOCK-AUTO9-003",
        "label": "行业价格连续观测真实来源候选卡",
        "path": DATA_DIR / "行业价格连续观测真实来源候选卡_最新.json",
        "mode": "candidate_asset",
    },
    {
        "batch_item": "STOCK-AUTO9-004",
        "label": "政策事件真实来源替换准备清单",
        "path": DATA_DIR / "政策事件真实来源替换准备清单_最新.json",
        "mode": "candidate_asset",
    },
    {
        "batch_item": "STOCK-AUTO9-QUEUE",
        "label": "股票线第九批低风险续建队列验收",
        "path": DATA_DIR / "股票线第九批低风险续建队列验收_最新.json",
        "mode": "passed_json",
    },
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_check(item: dict[str, Any]) -> dict[str, Any]:
    path = item["path"]
    if not path.exists():
        return {**item, "path": str(path), "exists": False, "passed": False, "metrics": {"error": "missing"}}
    data = load_json(path)
    if item["mode"] == "passed_json":
        passed = data.get("passed") is True
    else:
        safety = data.get("safety_boundary", {})
        passed = (
            data.get("status", "").startswith("candidate_only")
            or data.get("asset_identity", "").startswith("W2")
        ) and all(
            safety.get(flag) is True
            for flag in ["not_n8n", "not_external_send", "not_formal_config", "not_broker_interface", "not_auto_trade", "not_order"]
        )
    return {
        "batch_item": item["batch_item"],
        "label": item["label"],
        "path": str(path),
        "exists": True,
        "passed": bool(passed),
        "metrics": data.get("summary", data.get("metrics", {})),
    }


def build_markdown(asset: dict[str, Any]) -> str:
    lines = [
        "# 股票线第九批统一影子验收总表",
        "",
        f"- 生成时间：{asset['generated_at']}",
        "- 资产身份：W2 股票线第九批统一影子验收总表",
        "- 真实系统触发：否",
        "- 正式配置写入：否",
        "- 交易能力：否",
        "",
        "## 验收汇总",
        "",
        f"- 检查项：{asset['summary']['check_count']}",
        f"- 通过：{asset['summary']['passed_count']}",
        f"- 失败：{asset['summary']['failed_count']}",
        f"- 队列完成：{asset['summary']['queue_completed_count']}/{asset['summary']['queue_count']}",
        "",
        "| 队列项 | 资产 | 文件存在 | 通过 |",
        "| --- | --- | --- | --- |",
    ]
    for item in asset["checks"]:
        lines.append(f"| {item['batch_item']} | {item['label']} | {item['exists']} | {item['passed']} |")
    lines.extend(["", "## 剩余阻断", ""])
    lines.extend([f"- {item}" for item in asset["remaining_blockers"]])
    return "\n".join(lines)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    checks = [load_check(item) for item in CHECKS]
    queue_path = DATA_DIR / "股票线第九批低风险续建队列_最新.json"
    queue = load_json(queue_path) if queue_path.exists() else {}
    queue_summary = queue.get("summary", {})
    asset = {
        "name": "股票线第九批统一影子验收总表",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W2 股票线第九批统一影子验收总表",
        "status": "shadow_batch_acceptance",
        "purpose": "汇总第九批低风险续建资产，确认真实数据源接入前准备不越权。",
        "not_formal_config": True,
        "not_formal_entry": True,
        "not_external_send": True,
        "not_formal_database_write": True,
        "not_trade": True,
        "checks": checks,
        "queue_summary": queue_summary,
        "remaining_blockers": [
            "真实财报资金接口未接入",
            "真实行业价格连续数据源未接入",
            "政策事件真实来源未替换正式库",
            "企业微信真实外发、券商接口、交易能力继续阻断",
        ],
        "summary": {
            "check_count": len(checks),
            "passed_count": len([item for item in checks if item["passed"]]),
            "failed_count": len([item for item in checks if not item["passed"]]),
            "queue_completed_count": queue_summary.get("completed_count", 0),
            "queue_count": queue_summary.get("queue_count", 0),
            "real_system_triggered": False,
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
    MD_OUT.write_text(build_markdown(asset), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
