# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信查询n8n禁用态工作流草案.py
作用：生成股票研究系统企业微信查询链路的n8n禁用态工作流草案，供后续人工确认后导入评审。
触发方式：python 生成股票企业微信查询n8n禁用态工作流草案.py
依赖：Python标准库；企业微信股票查询灰度启用许可令_最新.json；股票助手入口.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成本地工作流草案JSON；不调用n8n API；不导入n8n；不启用Webhook；不触发工作流；不真实发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信查询n8n禁用态工作流草案生成脚本。
标识：stock-wework-query-n8n-disabled-draft-generate
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return module_root().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def node_id() -> str:
    return str(uuid.uuid4())


def build_workflow() -> dict[str, Any]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    webhook_id = node_id()
    normalize_id = node_id()
    stock_id = node_id()
    response_id = node_id()
    note_id = node_id()
    return {
        "name": "股票企业微信查询禁用态草案",
        "active": False,
        "nodes": [
            {
                "parameters": {
                    "path": "jiege-stock-query-disabled-draft",
                    "responseMode": "responseNode",
                    "options": {
                        "allowedOrigins": "",
                        "rawBody": False,
                    },
                },
                "id": webhook_id,
                "name": "OpenClaw消息入口禁用态",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [220, 260],
            },
            {
                "parameters": {
                    "mode": "manual",
                    "duplicateItem": False,
                    "assignments": {
                        "assignments": [
                            {
                                "id": node_id(),
                                "name": "mode",
                                "value": "disabled_draft_only",
                                "type": "string",
                            },
                            {
                                "id": node_id(),
                                "name": "message",
                                "value": "={{ $json.body.message || $json.body.text || '' }}",
                                "type": "string",
                            },
                            {
                                "id": node_id(),
                                "name": "source",
                                "value": "openclaw_wework_gateway",
                                "type": "string",
                            },
                            {
                                "id": node_id(),
                                "name": "must_review_before_enable",
                                "value": True,
                                "type": "boolean",
                            },
                        ]
                    },
                },
                "id": normalize_id,
                "name": "标准化查询消息",
                "type": "n8n-nodes-base.set",
                "typeVersion": 3.4,
                "position": [500, 260],
            },
            {
                "parameters": {
                    "method": "POST",
                    "url": "http://127.0.0.1:19300/analyze",
                    "sendBody": True,
                    "contentType": "json",
                    "jsonBody": "={{ { \"message\": $json.message, \"source\": $json.source, \"dry_run\": true } }}",
                    "options": {
                        "timeout": 30000,
                    },
                },
                "id": stock_id,
                "name": "请求本地股票助手草稿",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [780, 260],
            },
            {
                "parameters": {
                    "respondWith": "json",
                    "responseBody": "={{ { \"mode\": \"disabled_draft_only\", \"reply\": $json.reply || $json.report || $json, \"real_send\": false, \"trade\": false } }}",
                    "options": {},
                },
                "id": response_id,
                "name": "返回回复草稿不外发",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1.1,
                "position": [1060, 260],
            },
            {
                "parameters": {
                    "content": f"股票企业微信查询禁用态草案\\n生成时间：{now}\\n安全边界：active=false；不导入、不启用、不触发、不发送企业微信、不写旧系统、不调用交易接口。OpenClaw只转发消息，n8n负责逻辑编排。",
                    "height": 260,
                    "width": 420,
                    "color": 5,
                },
                "id": note_id,
                "name": "安全边界说明",
                "type": "n8n-nodes-base.stickyNote",
                "typeVersion": 1,
                "position": [220, -40],
            },
        ],
        "connections": {
            "OpenClaw消息入口禁用态": {
                "main": [[{"node": "标准化查询消息", "type": "main", "index": 0}]]
            },
            "标准化查询消息": {
                "main": [[{"node": "请求本地股票助手草稿", "type": "main", "index": 0}]]
            },
            "请求本地股票助手草稿": {
                "main": [[{"node": "返回回复草稿不外发", "type": "main", "index": 0}]]
            },
        },
        "settings": {
            "executionOrder": "v1",
            "saveManualExecutions": True,
        },
        "staticData": None,
        "pinData": {},
        "tags": [],
        "meta": {
            "jiege_stock_wework_query": True,
            "stage": "disabled_draft_only",
            "must_remain_inactive": True,
            "generated_at": now,
            "requires_manual_confirm_before_import": True,
            "requires_manual_confirm_before_enable": True,
        },
    }


def main() -> int:
    root = module_root()
    v3_root = system_root()
    permit = load_json(root / "03数据" / "19企业微信灰度启用" / "企业微信股票查询灰度启用许可令_最新.json")
    workflow = build_workflow()
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "股票企业微信查询n8n禁用态工作流草案",
        "许可令来源": str(root / "03数据" / "19企业微信灰度启用" / "企业微信股票查询灰度启用许可令_最新.json"),
        "许可令结论": permit.get("结论", "未找到许可令"),
        "工作流工件": workflow,
        "安全检查": {
            "active": workflow.get("active"),
            "包含Webhook节点": any("webhook" in node.get("type", "").lower() for node in workflow.get("nodes", [])),
            "包含凭据": any("credentials" in node for node in workflow.get("nodes", [])),
            "是否调用n8nAPI": False,
            "是否执行导入": False,
            "是否启用Webhook": False,
            "是否触发真实工作流": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
        "后续人工确认点": [
            "是否允许导入n8n但保持active=false",
            "是否允许启动或重启本地股票助手服务",
            "是否允许OpenClaw把企业微信消息转发到n8n",
            "是否允许统一消息出口真实发送企业微信回复",
        ],
    }
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    stock_output_dir = root / "03数据" / "20n8n禁用态工作流草案"
    manager_output_dir = v3_root / "01杰哥智能系统" / "03数据" / "工作流导入工件"
    stock_workflow = stock_output_dir / "股票企业微信查询_n8n禁用态工作流草案_最新.json"
    stock_latest_workflow = stock_output_dir / "股票企业微信查询_n8n禁用态工作流草案_最新.json"
    stock_package = stock_output_dir / "股票企业微信查询_n8n禁用态工作流草案包_最新.json"
    stock_latest_package = stock_output_dir / "股票企业微信查询_n8n禁用态工作流草案包_最新.json"
    manager_latest = manager_output_dir / "股票企业微信查询_n8n禁用态工作流草案_最新.json"
    log_path = root / "04日志" / "n8n禁用态工作流草案" / "stock-wework-query-n8n-disabled-draft-generate-最新.json"
    write_json(stock_workflow, workflow)
    write_json(stock_latest_workflow, workflow)
    write_json(stock_package, package)
    write_json(stock_latest_package, package)
    write_json(manager_latest, workflow)
    write_json(log_path, package)
    print(json.dumps({"active": workflow["active"], "输出": str(stock_latest_package)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
