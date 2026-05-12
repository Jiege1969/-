# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信n8n适配器工作流草案.py
作用：生成股票企业微信n8n适配器的未激活工作流草案工件，供后续人工确认后导入评审。
触发方式：python 生成股票企业微信n8n适配器工作流草案.py
依赖：Python标准库；股票企业微信n8n路由契约_最新.json；执行股票企业微信n8n适配器禁用态.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成本地n8n工作流草案JSON；不调用n8n API；不导入n8n；不启用Webhook；不触发工作流；不调用OpenClaw；不真实发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信n8n适配器工作流草案生成脚本。
标识：stock-wework-n8n-adapter-workflow-draft-generate
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


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def node_id() -> str:
    return str(uuid.uuid4())


def build_workflow(root: Path) -> dict[str, Any]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    manual_id = node_id()
    payload_id = node_id()
    adapter_id = node_id()
    note_id = node_id()
    adapter_script = root / "02脚本" / "执行股票企业微信n8n适配器禁用态.py"
    return {
        "name": "股票企业微信n8n适配器禁用态草案",
        "active": False,
        "nodes": [
            {
                "parameters": {},
                "id": manual_id,
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
                            {"id": node_id(), "name": "trace_id", "value": "n8n-draft-demo", "type": "string"},
                            {"id": node_id(), "name": "message_type", "value": "text", "type": "string"},
                            {"id": node_id(), "name": "text", "value": "分析新易盛", "type": "string"},
                            {"id": node_id(), "name": "voice_text", "value": "", "type": "string"},
                            {"id": node_id(), "name": "dry_run", "value": True, "type": "boolean"},
                        ]
                    },
                },
                "id": payload_id,
                "name": "构造契约输入",
                "type": "n8n-nodes-base.set",
                "typeVersion": 3.4,
                "position": [500, 260],
            },
            {
                "parameters": {
                    "jsCode": (
                        "return [{ json: { mode: 'disabled_draft_only', "
                        "adapter_script: '" + str(adapter_script).replace("\\", "\\\\") + "', "
                        "expected_cli: 'python 执行股票企业微信n8n适配器禁用态.py --message-type text --text \"分析新易盛\"', "
                        "real_send: false, trade: false, note: '草案不在n8n内执行本地命令；导入前需人工确认执行节点方案。' } }];"
                    )
                },
                "id": adapter_id,
                "name": "适配器调用占位",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [780, 260],
            },
            {
                "parameters": {
                    "content": f"股票企业微信n8n适配器工作流草案\\n生成时间：{now}\\n安全边界：active=false；不导入、不启用、不触发、不发送企业微信、不调用交易接口。真正执行本地适配器前必须人工确认。",
                    "height": 260,
                    "width": 460,
                    "color": 5,
                },
                "id": note_id,
                "name": "安全边界说明",
                "type": "n8n-nodes-base.stickyNote",
                "typeVersion": 1,
                "position": [220, -60],
            },
        ],
        "connections": {
            "手动触发禁用态": {"main": [[{"node": "构造契约输入", "type": "main", "index": 0}]]},
            "构造契约输入": {"main": [[{"node": "适配器调用占位", "type": "main", "index": 0}]]},
        },
        "settings": {"executionOrder": "v1", "saveManualExecutions": True},
        "staticData": None,
        "pinData": {},
        "tags": [],
        "meta": {
            "jiege_stock_wework_n8n_adapter": True,
            "stage": "disabled_workflow_draft_only",
            "must_remain_inactive": True,
            "generated_at": now,
            "requires_manual_confirm_before_import": True,
            "requires_manual_confirm_before_enable": True,
        },
    }


def main() -> int:
    root = module_root()
    v3_root = system_root()
    contract = load_json(root / "03数据" / "26n8n路由契约" / "股票企业微信n8n路由契约_最新.json", {})
    workflow = build_workflow(root)
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "股票企业微信n8n适配器未激活工作流草案",
        "契约来源": str(root / "03数据" / "26n8n路由契约" / "股票企业微信n8n路由契约_最新.json"),
        "契约模式": contract.get("模式", ""),
        "工作流工件": workflow,
        "安全检查": {
            "active": workflow.get("active"),
            "是否调用n8nAPI": False,
            "是否执行导入": False,
            "是否启用Webhook": False,
            "是否触发真实工作流": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = root / "03数据" / "28n8n适配器工作流草案"
    manager_output_dir = v3_root / "01杰哥智能系统" / "03数据" / "工作流导入工件"
    workflow_path = output_dir / "股票企业微信n8n适配器工作流草案_最新.json"
    latest_workflow = output_dir / "股票企业微信n8n适配器工作流草案_最新.json"
    package_path = output_dir / "股票企业微信n8n适配器工作流草案包_最新.json"
    latest_package = output_dir / "股票企业微信n8n适配器工作流草案包_最新.json"
    manager_latest = manager_output_dir / "股票企业微信n8n适配器工作流草案_最新.json"
    log_path = root / "04日志" / "n8n适配器工作流草案" / "stock-wework-n8n-adapter-workflow-draft-generate-最新.json"
    write_json(workflow_path, workflow)
    write_json(latest_workflow, workflow)
    write_json(package_path, package)
    write_json(latest_package, package)
    write_json(manager_latest, workflow)
    write_json(log_path, package)
    print(json.dumps({"active": workflow["active"], "输出": str(latest_package)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
