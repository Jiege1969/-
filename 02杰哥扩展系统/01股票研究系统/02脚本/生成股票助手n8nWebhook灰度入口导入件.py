# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-n8n-webhook-gray-entry-artifact.py
Purpose: Generate an inactive n8n webhook workflow artifact for stock assistant gray connectivity.
Trigger: python 生成股票助手n8nWebhook灰度入口导入件.py
Dependencies: Python standard library; isolated n8n target.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Writes an inactive webhook workflow artifact only; does not import, enable, trigger, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created inactive webhook gray entry artifact generator.
Marker: stock-assistant-n8n-webhook-gray-entry-artifact-generate
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
        "name": "股票助手企业微信Webhook灰度入口未激活",
        "active": False,
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "jiege-stock-wework-gray",
                    "responseMode": "responseNode",
                    "options": {}
                },
                "id": "0ee3ce6b-5c16-4ec7-8b9c-d9470a4cd8b2",
                "name": "股票助手Webhook入口",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [180, 240],
                "webhookId": "jiege-stock-wework-gray"
            },
            {
                "parameters": {
                    "mode": "manual",
                    "duplicateItem": False,
                    "assignments": {
                        "assignments": [
                            {"id": "a1", "name": "mode", "value": "inactive_webhook_gray_entry", "type": "string"},
                            {"id": "a2", "name": "dry_run", "value": True, "type": "boolean"},
                            {"id": "a3", "name": "real_send", "value": False, "type": "boolean"},
                            {"id": "a4", "name": "trade", "value": False, "type": "boolean"},
                            {"id": "a5", "name": "reply_text", "value": "股票助手Webhook灰度入口已接收请求；当前未启用真实发送、未调用券商接口、未自动交易。", "type": "string"}
                        ]
                    }
                },
                "id": "5527b95a-1b39-43cd-ae40-a9d904003d9f",
                "name": "生成安全灰度响应",
                "type": "n8n-nodes-base.set",
                "typeVersion": 3.4,
                "position": [500, 240]
            },
            {
                "parameters": {
                    "respondWith": "json",
                    "responseBody": "={{ $json }}",
                    "options": {}
                },
                "id": "a56c2300-3882-4cc1-9712-f5082a0e3501",
                "name": "返回灰度响应",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1.4,
                "position": [820, 240]
            },
            {
                "parameters": {
                    "content": f"股票助手企业微信Webhook灰度入口\\n生成时间：{now}\\n安全边界：active=false；不真实发送；不写正式库；不调用券商接口；不自动交易。",
                    "height": 260,
                    "width": 480,
                    "color": 5
                },
                "id": "75a4527a-05d7-4cfd-a607-33a2cad1be75",
                "name": "安全边界说明",
                "type": "n8n-nodes-base.stickyNote",
                "typeVersion": 1,
                "position": [180, -80]
            }
        ],
        "connections": {
            "股票助手Webhook入口": {"main": [[{"node": "生成安全灰度响应", "type": "main", "index": 0}]]},
            "生成安全灰度响应": {"main": [[{"node": "返回灰度响应", "type": "main", "index": 0}]]}
        },
        "settings": {"executionOrder": "v1", "saveManualExecutions": True},
        "staticData": None,
        "pinData": {},
        "tags": [],
        "meta": {
            "jiege_stock_wework_webhook_gray_entry": True,
            "stage": "inactive_webhook_gray_entry",
            "must_remain_inactive": True,
            "generated_at": now,
            "real_send": False,
            "broker_api": False,
            "auto_trade": False
        }
    }


def main() -> int:
    root = module_root()
    workflow = build_workflow()
    output_dir = root / "03数据" / "74n8nWebhook灰度入口导入件"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手n8nWebhook灰度入口导入件_{stamp}.json"
    latest_json = output_dir / "股票助手n8nWebhook灰度入口导入件_最新.json"
    output_md = output_dir / f"股票助手n8nWebhook灰度入口导入件_{stamp}.md"
    latest_md = output_dir / "股票助手n8nWebhook灰度入口导入件_最新.md"
    write_json(output_json, workflow)
    write_json(latest_json, workflow)
    markdown = "\n".join([
        "# 股票助手n8nWebhook灰度入口导入件",
        "",
        f"- 名称：{workflow['name']}",
        f"- active：{workflow['active']}",
        "- Webhook路径：`/webhook/jiege-stock-wework-gray`",
        "- 安全边界：不启用、不触发、不真实发送、不写正式库、不调用券商接口、不自动交易。",
        f"- JSON：`{latest_json}`",
        "",
    ])
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"active": workflow["active"], "节点数": len(workflow["nodes"]), "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
