# -*- coding: utf-8 -*-
"""
名称：生成股票助手n8n桥接入口导入件.py
作用：生成指向股票企业微信桥接入口19302的n8n未激活Webhook工作流导入件。
触发方式：python 生成股票助手n8n桥接入口导入件.py
依赖：Python标准库；股票企业微信桥接入口.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：仅生成active=false导入件；不导入、不启用、不触发n8n；不发送企业微信；不写旧系统；不交易。
创建修改记录：2026-04-29 创建n8n桥接入口v2导入件生成脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "03数据" / "84n8n桥接入口导入件"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_workflow() -> dict[str, Any]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "name": "股票助手企业微信Webhook桥接入口未激活v2",
        "active": False,
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "jiege-stock-wework-bridge-v2",
                    "responseMode": "responseNode",
                    "options": {},
                },
                "id": "stock-bridge-webhook-v2",
                "name": "股票桥接Webhook入口",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [120, 260],
                "webhookId": "jiege-stock-wework-bridge-v2",
            },
            {
                "parameters": {
                    "method": "POST",
                    "url": "http://host.docker.internal:19302/wecom/stock",
                    "sendBody": True,
                    "contentType": "json",
                    "jsonBody": "={{ JSON.stringify($json.body || $json) }}",
                    "options": {"timeout": 30000},
                },
                "id": "stock-bridge-http-v2",
                "name": "调用股票桥接入口19302",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [460, 260],
            },
            {
                "parameters": {
                    "respondWith": "json",
                    "responseBody": "={{ $json }}",
                    "options": {},
                },
                "id": "stock-bridge-respond-v2",
                "name": "返回桥接结果",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1.4,
                "position": [800, 260],
            },
            {
                "parameters": {
                    "content": f"股票助手企业微信Webhook桥接入口v2\\n生成时间：{now}\\n目标：http://host.docker.internal:19302/wecom/stock\\n安全边界：active=false；不真实发送；不写旧系统；不交易。",
                    "height": 260,
                    "width": 520,
                    "color": 5,
                },
                "id": "stock-bridge-note-v2",
                "name": "安全边界说明",
                "type": "n8n-nodes-base.stickyNote",
                "typeVersion": 1,
                "position": [120, -60],
            },
        ],
        "connections": {
            "股票桥接Webhook入口": {"main": [[{"node": "调用股票桥接入口19302", "type": "main", "index": 0}]]},
            "调用股票桥接入口19302": {"main": [[{"node": "返回桥接结果", "type": "main", "index": 0}]]},
        },
        "settings": {"executionOrder": "v1", "saveManualExecutions": True},
        "staticData": None,
        "pinData": {},
        "tags": [],
        "meta": {
            "jiege_stock_wework_bridge_v2": True,
            "stage": "inactive_bridge_entry",
            "target": "http://host.docker.internal:19302/wecom/stock",
            "generated_at": now,
            "real_send": False,
            "broker_api": False,
            "auto_trade": False,
        },
    }


def main() -> int:
    workflow = build_workflow()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = OUTPUT_DIR / f"股票助手n8n桥接入口导入件_{stamp}.json"
    latest = OUTPUT_DIR / "股票助手n8n桥接入口导入件_最新.json"
    write_json(output, workflow)
    write_json(latest, workflow)
    print(json.dumps({"active": workflow["active"], "输出": str(output), "目标": workflow["meta"]["target"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
