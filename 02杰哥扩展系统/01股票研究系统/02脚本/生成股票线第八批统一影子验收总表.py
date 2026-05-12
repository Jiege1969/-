# -*- coding: utf-8 -*-
"""生成股票线第八批统一影子验收总表。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "股票线第八批统一影子验收总表_最新.json"
MD_OUT = DATA_DIR / "股票线第八批统一影子验收总表_最新.md"


CHECKS = [
    {
        "key": "policy_events_fields",
        "label": "政策事件库字段化补齐样例",
        "path": DATA_DIR / "政策事件库字段化补齐样例验收结果_最新.json",
        "batch_item": "STOCK-AUTO8-001",
    },
    {
        "key": "market_style_fields",
        "label": "市场风格日表字段化补齐样例",
        "path": DATA_DIR / "市场风格日表字段化补齐样例验收结果_最新.json",
        "batch_item": "STOCK-AUTO8-002",
    },
    {
        "key": "replay_rule_gate",
        "label": "复盘结果到规则候选二次门禁样例",
        "path": DATA_DIR / "复盘结果到规则候选二次门禁样例验收结果_最新.json",
        "batch_item": "STOCK-AUTO8-003",
    },
    {
        "key": "l3_missing_refresh",
        "label": "L3证据缺口统一刷新验收样例",
        "path": DATA_DIR / "L3证据缺口统一刷新验收样例验收结果_最新.json",
        "batch_item": "STOCK-AUTO8-004",
    },
    {
        "key": "queue_acceptance",
        "label": "股票线第八批低风险续建队列验收",
        "path": DATA_DIR / "股票线第八批低风险续建队列验收_最新.json",
        "batch_item": "STOCK-AUTO8-005",
    },
]


def load_check(item: dict[str, object]) -> dict[str, object]:
    path = item["path"]
    assert isinstance(path, Path)
    if not path.exists():
        return {
            "key": item["key"],
            "label": item["label"],
            "batch_item": item["batch_item"],
            "exists": False,
            "passed": False,
            "path": str(path),
            "metrics": {},
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {
            "key": item["key"],
            "label": item["label"],
            "batch_item": item["batch_item"],
            "exists": True,
            "passed": False,
            "path": str(path),
            "metrics": {"json_error": str(exc)},
        }
    return {
        "key": item["key"],
        "label": item["label"],
        "batch_item": item["batch_item"],
        "exists": True,
        "passed": data.get("passed") is True,
        "path": str(path),
        "metrics": data.get("metrics", {}),
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    checks = [load_check(item) for item in CHECKS]
    queue_path = DATA_DIR / "股票线第八批低风险续建队列_最新.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8-sig")) if queue_path.exists() else {}
    queue_summary = queue.get("summary", {})
    asset = {
        "name": "股票线第八批统一影子验收总表",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W2 股票线第八批统一影子验收总表",
        "status": "shadow_batch_acceptance",
        "purpose": "汇总第八批低风险续建资产的验收状态，确认本批只增强研究分析证据闭环，不触发真实系统。",
        "not_formal_config": True,
        "not_formal_entry": True,
        "not_external_send": True,
        "not_formal_database_write": True,
        "not_rule_update": True,
        "not_trade": True,
        "checks": checks,
        "queue_summary": queue_summary,
        "blocked_register": queue.get("blocked_queue", []),
        "batch_effect": {
            "frontend_effect": "前台更容易输出使用者需要的结论型短答，并把证据缺口压缩为必要原因。",
            "backend_effect": "后台保留政策事件、市场风格、财报资金、行业价格、复盘候选和缺口刷新记录。",
            "remaining_debt": [
                "真实财报资金自动来源仍未正式接入",
                "真实行业价格连续数据仍未正式接入",
                "真实交易日市场风格日表仍未正式接入",
                "真实企业微信外发和生产入口仍为红线阻断",
            ],
        },
        "summary": {
            "check_count": len(checks),
            "passed_count": len([item for item in checks if item["passed"]]),
            "failed_count": len([item for item in checks if not item["passed"]]),
            "queue_completed_count": queue_summary.get("completed_count", 0),
            "queue_count": queue_summary.get("queue_count", 0),
            "blocked_count": queue_summary.get("blocked_count", 0),
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
    lines = [
        "# 股票线第八批统一影子验收总表",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：W2 股票线第八批统一影子验收总表",
        "- 真实系统触发：否",
        "- 正式规则更新：否",
        "- 交易能力：否",
        "",
        "## 验收汇总",
        "",
        f"- 检查项：{asset['summary']['check_count']}",
        f"- 通过：{asset['summary']['passed_count']}",
        f"- 失败：{asset['summary']['failed_count']}",
        f"- 队列完成：{asset['summary']['queue_completed_count']}/{asset['summary']['queue_count']}",
        f"- 阻断登记：{asset['summary']['blocked_count']}",
        "",
        "## 检查项",
        "",
        "| 项目 | 文件存在 | 验收通过 | 队列项 |",
        "| --- | --- | --- | --- |",
    ]
    for item in checks:
        lines.append(f"| {item['label']} | {item['exists']} | {item['passed']} | {item['batch_item']} |")
    lines.extend(["", "## 剩余旧债", ""])
    lines.extend([f"- {item}" for item in asset["batch_effect"]["remaining_debt"]])
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
