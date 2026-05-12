# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-n8n-inactive-import-artifact.py
Purpose: Generate a valid active=false n8n workflow artifact for the stock assistant isolated n8n import.
Trigger: python 生成股票助手n8n未激活导入件.py
Dependencies: Python standard library; isolated n8n target.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Writes an inactive workflow artifact only under the new stock module data directory; does not import, enable, trigger, send, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created sanitized inactive n8n import artifact generator.
Marker: stock-assistant-n8n-inactive-import-artifact-generate
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
        "name": "股票助手企业微信查询适配器未激活导入件",
        "active": False,
        "nodes": [
            {
                "parameters": {},
                "id": "733f45cb-8009-4bd6-b053-aa6be149d670",
                "name": "手动触发禁用态",
                "type": "n8n-nodes-base.manualTrigger",
                "typeVersion": 1,
                "position": [220, 260],
            },
            {
                "parameters": {
                    "mode": "manual",
                    "duplicateItem": False,
                    "assignments": {
                        "assignments": [
                            {"id": "72a5f8c2-9062-4d58-981c-077721e1d83a", "name": "trace_id", "value": "stock-disabled-import-demo", "type": "string"},
                            {"id": "1b93a7d7-8f4f-4e47-991e-2d10a1be9ab9", "name": "message_type", "value": "text", "type": "string"},
                            {"id": "05d943a1-5ddb-4665-904a-5fc135e85851", "name": "text", "value": "分析新易盛", "type": "string"},
                            {"id": "126a3b75-59d0-4e97-a412-4cca19366bec", "name": "voice_text", "value": "", "type": "string"},
                            {"id": "45b05e52-8f6d-4426-bdca-60d815a022a7", "name": "dry_run", "value": True, "type": "boolean"},
                        ]
                    },
                },
                "id": "2af5b79b-c886-4898-93d7-ad86e591530c",
                "name": "构造契约输入",
                "type": "n8n-nodes-base.set",
                "typeVersion": 3.4,
                "position": [500, 260],
            },
            {
                "parameters": {
                    "jsCode": "return [{ json: { mode: 'inactive_import_only', message: $json.text, dry_run: true, real_send: false, trade: false, note: 'This workflow is imported inactive. It does not call local scripts, WeWork, databases, broker APIs, or trading interfaces.' } }];"
                },
                "id": "881cfd31-6046-47e4-b571-b303b721525b",
                "name": "安全占位输出",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [780, 260],
            },
            {
                "parameters": {
                    "content": f"股票助手企业微信查询适配器未激活导入件\\n生成时间：{now}\\n安全边界：active=false；不启用；不触发；不发送企业微信；不写正式库；不调用券商接口；不自动交易。",
                    "height": 260,
                    "width": 460,
                    "color": 5,
                },
                "id": "e19d6db6-a238-4cf1-b2b3-16858a43408b",
                "name": "安全边界说明",
                "type": "n8n-nodes-base.stickyNote",
                "typeVersion": 1,
                "position": [220, -60],
            },
        ],
        "connections": {
            "手动触发禁用态": {"main": [[{"node": "构造契约输入", "type": "main", "index": 0}]]},
            "构造契约输入": {"main": [[{"node": "安全占位输出", "type": "main", "index": 0}]]},
        },
        "settings": {"executionOrder": "v1", "saveManualExecutions": True},
        "staticData": None,
        "pinData": {},
        "tags": [],
        "meta": {
            "jiege_stock_wework_n8n_adapter": True,
            "stage": "inactive_import_only",
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
    output_dir = root / "03数据" / "69n8n未激活导入件"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手n8n未激活导入件_{stamp}.json"
    latest_json = output_dir / "股票助手n8n未激活导入件_最新.json"
    output_md = output_dir / f"股票助手n8n未激活导入件_{stamp}.md"
    latest_md = output_dir / "股票助手n8n未激活导入件_最新.md"
    write_json(output_json, workflow)
    write_json(latest_json, workflow)
    markdown = "\n".join([
        "# 股票助手n8n未激活导入件",
        "",
        f"- 名称：{workflow['name']}",
        f"- active：{workflow['active']}",
        "- 安全边界：不启用、不触发、不发送企业微信、不写正式库、不调用券商接口、不自动交易。",
        f"- JSON：`{latest_json}`",
        "",
    ])
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"active": workflow["active"], "节点数": len(workflow["nodes"]), "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
