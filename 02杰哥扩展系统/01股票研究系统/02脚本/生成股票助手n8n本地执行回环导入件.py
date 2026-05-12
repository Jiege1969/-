# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-n8n-local-execution-loop-artifact.py
Purpose: Generate an inactive n8n Execute Workflow Trigger artifact for local execution-loop testing.
Trigger: python 生成股票助手n8n本地执行回环导入件.py
Dependencies: Python standard library; isolated n8n target.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Writes an inactive local execution-loop workflow artifact only; does not enable webhook, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created local execution-loop artifact generator after webhook registration diagnosis.
Marker: stock-assistant-n8n-local-execution-loop-artifact-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_workflow() -> dict[str, Any]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "name": "股票助手n8n本地执行回环测试",
        "active": False,
        "nodes": [
            {
                "parameters": {},
                "id": "c3022c96-36e8-49d4-9f57-8efaed95dbf1",
                "name": "本地执行触发器",
                "type": "n8n-nodes-base.executeWorkflowTrigger",
                "typeVersion": 1,
                "position": [180, 240],
            },
            {
                "parameters": {
                    "mode": "manual",
                    "duplicateItem": False,
                    "assignments": {
                        "assignments": [
                            {"id": "l1", "name": "mode", "value": "local_execution_loop", "type": "string"},
                            {"id": "l2", "name": "stock", "value": "新易盛", "type": "string"},
                            {"id": "l3", "name": "dry_run", "value": True, "type": "boolean"},
                            {"id": "l4", "name": "real_send", "value": False, "type": "boolean"},
                            {"id": "l5", "name": "trade", "value": False, "type": "boolean"},
                            {"id": "l6", "name": "reply_text", "value": "n8n本地执行回环成功：股票助手链路保持dry_run，不发送企业微信，不交易。", "type": "string"},
                        ]
                    },
                },
                "id": "912f57ec-f924-444a-b5df-6eef4d33826e",
                "name": "生成本地回环响应",
                "type": "n8n-nodes-base.set",
                "typeVersion": 3.4,
                "position": [500, 240],
            },
        ],
        "connections": {
            "本地执行触发器": {"main": [[{"node": "生成本地回环响应", "type": "main", "index": 0}]]}
        },
        "settings": {"executionOrder": "v1", "saveManualExecutions": True},
        "staticData": None,
        "pinData": {},
        "tags": [],
        "meta": {
            "jiege_stock_n8n_local_execution_loop": True,
            "stage": "local_execution_loop_only",
            "must_remain_inactive": True,
            "generated_at": now,
            "real_send": False,
            "broker_api": False,
            "auto_trade": False,
        },
    }


def main() -> int:
    root = module_root()
    workflow = build_workflow()
    output_dir = root / "03数据" / "75n8n本地执行回环导入件"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手n8n本地执行回环导入件_{stamp}.json"
    latest_json = output_dir / "股票助手n8n本地执行回环导入件_最新.json"
    output_md = output_dir / f"股票助手n8n本地执行回环导入件_{stamp}.md"
    latest_md = output_dir / "股票助手n8n本地执行回环导入件_最新.md"
    write_json(output_json, workflow)
    write_json(latest_json, workflow)
    markdown = "\n".join([
        "# 股票助手n8n本地执行回环导入件",
        "",
        f"- 名称：{workflow['name']}",
        f"- active：{workflow['active']}",
        "- 触发器：Execute Workflow Trigger",
        "- 安全边界：只允许 n8n CLI 本地执行，不启用 Webhook，不发送企业微信，不交易。",
        f"- JSON：`{latest_json}`",
        "",
    ])
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"active": workflow["active"], "节点数": len(workflow["nodes"]), "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
