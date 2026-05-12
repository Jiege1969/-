# -*- coding: utf-8 -*-
"""
名称：生成股票主动研究n8n未激活导入工件.py
作用：生成可导入n8n的股票主动研究闭环未激活工作流工件。
触发方式：python 生成股票主动研究n8n未激活导入工件.py
依赖：运行股票主动研究闭环_本地.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成本地导入工件；不调用n8n API；不导入n8n；不启用工作流；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-active-research-n8n-inactive-import-artifact
"""

from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


WORKFLOW_NAME = "股票主动研究闭环_文件桥接未激活"
BRIDGE_BIND_HOST = "0.0.0.0"
BRIDGE_URL_HOST = "172.22.0.1"
BRIDGE_PORT = 19310


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def bridge_config(root: Path) -> dict[str, Any]:
    path = root / "01配置" / "n8n本地桥接配置.json"
    config = load_json(path, {})
    if not config.get("token"):
        config = {
            "名称": "股票主动研究n8n本地桥接配置",
            "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "bind_host": BRIDGE_BIND_HOST,
            "url_host": BRIDGE_URL_HOST,
            "port": BRIDGE_PORT,
            "token": secrets.token_urlsafe(24),
            "说明": "仅用于n8n容器调用宿主机本地桥接服务。不得用于公网。",
        }
        write_json(path, config)
    return config


def node_id() -> str:
    return str(uuid.uuid4())


def assignment(name: str, value: Any, value_type: str) -> dict[str, Any]:
    return {"id": node_id(), "name": name, "value": value, "type": value_type}


def build_workflow(root: Path, generated_at: str) -> dict[str, Any]:
    report = root / "03数据" / "135分层日报" / "AI分析报告_最新.md"
    push_draft = root / "03数据" / "136推送草案" / "股票企微推送草案_最新.md"
    intraday_strategy = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "股票n8n日内报告闭环与晨报推送策略包_最新.json"
    trigger_path = "/home/node/.n8n/jiege_bridge/stock_active_research_trigger.json"
    command = (
        "mkdir -p /home/node/.n8n/jiege_bridge && "
        "printf '{\"task\":\"stock_active_research\",\"mode\":\"inactive_intraday_loop\",\"stage\":\"manual_test_or_schedule\",\"created_at\":\"%s\"}\\n' \"$(date -Iseconds)\" "
        f"> {trigger_path} && cat {trigger_path}"
    )
    return {
        "name": WORKFLOW_NAME,
        "active": False,
        "nodes": [
            {
                "parameters": {},
                "id": node_id(),
                "name": "手动触发",
                "type": "n8n-nodes-base.manualTrigger",
                "typeVersion": 1,
                "position": [240, 260],
            },
            {
                "parameters": {
                    "command": command
                },
                "id": node_id(),
                "name": "写入宿主机股票研究触发文件",
                "type": "n8n-nodes-base.executeCommand",
                "typeVersion": 1,
                "position": [520, 260],
                "notes": "向n8n共享目录写入触发文件；宿主机受控脚本读取后运行股票闭环。"
            },
            {
                "parameters": {
                    "mode": "manual",
                    "duplicateItem": False,
                    "assignments": {
                        "assignments": [
                            assignment("状态", "inactive_import_only", "string"),
                            assignment("工作流名", WORKFLOW_NAME, "string"),
                            assignment("桥接方式", "n8n共享目录触发文件", "string"),
                            assignment("触发文件", trigger_path, "string"),
                            assignment("AI分析报告", str(report), "string"),
                            assignment("企微推送草案", str(push_draft), "string"),
                            assignment("日内报告闭环策略", str(intraday_strategy), "string"),
                            assignment("收市后每日观察", "15:40-18:30；生成分层日报、候选池和第二天候选推荐草案。", "string"),
                            assignment("半夜宏观规律分析", "00:30-05:30；复盘前日推送、行业轮动、更优候选和风险纠偏。", "string"),
                            assignment("开市前晨报推送", "08:20-08:40；仅本人单条晨报灰度闸口，不群发。", "string"),
                            assignment("学习沉淀", "推送、纠偏、用户反馈和晚间复盘均进入学习沉淀账与进化候选。", "string"),
                            assignment("是否需要人工复核", True, "boolean"),
                            assignment("安全声明", "未激活导入；无Webhook；无真实发送节点；无券商接口；无自动交易。", "string"),
                        ]
                    },
                },
                "id": node_id(),
                "name": "输出本地结果路径",
                "type": "n8n-nodes-base.set",
                "typeVersion": 3.4,
                "position": [820, 260],
            },
            {
                "parameters": {
                    "content": (
                        "股票主动研究闭环文件桥接未激活导入工件\\n"
                        f"生成时间：{generated_at}\\n"
                        "日内节奏：全天轻量随问随答；15:40-18:30收市观察；00:30-05:30半夜规律复盘；08:20-08:40开市前晨报。\\n"
                        "安全边界：active=false；无Webhook；无n8n凭据；无企业微信真实发送节点；无券商接口；无自动交易。\\n"
                        "用途：n8n写触发文件，宿主机受控脚本消费触发并运行股票主动研究闭环。"
                    ),
                    "height": 260,
                    "width": 420,
                    "color": 4,
                },
                "id": node_id(),
                "name": "安全边界说明",
                "type": "n8n-nodes-base.stickyNote",
                "typeVersion": 1,
                "position": [240, -40],
            },
        ],
        "connections": {
            "手动触发": {
                "main": [[{"node": "写入宿主机股票研究触发文件", "type": "main", "index": 0}]]
            },
            "写入宿主机股票研究触发文件": {
                "main": [[{"node": "输出本地结果路径", "type": "main", "index": 0}]]
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
            "jiege_stock_active_research": True,
            "target": "jiege_v3_n8n",
            "requires_manual_confirm_before_import": True,
            "requires_manual_confirm_before_enable": True,
            "must_remain_inactive": True,
            "generated_at": generated_at,
            "intraday_report_loop": True,
            "strategy_package": str(intraday_strategy),
            "schedule_plan": [
                {"name": "收市后每日观察", "time": "15:40-18:30", "real_send": False},
                {"name": "半夜宏观规律分析", "time": "00:30-05:30", "real_send": False},
                {"name": "开市前晨报推送", "time": "08:20-08:40", "real_send": "single-user-gate-only"},
            ],
        },
    }


def validate_workflow(workflow: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if workflow.get("active") is not False:
        errors.append("active必须为false")
    for node in workflow.get("nodes", []):
        node_type = str(node.get("type", "")).lower()
        if "webhook" in node_type:
            errors.append(f"禁止Webhook节点：{node.get('name')}")
        if "credentials" in node:
            errors.append(f"禁止凭据字段：{node.get('name')}")
        name_text = str(node.get("name", ""))
        if "企业微信发送" in name_text or "券商" in name_text or "交易" in name_text:
            errors.append(f"节点名称含高风险动作：{name_text}")
    return errors


def main() -> int:
    root = module_root()
    now = datetime.now()
    generated_at = now.strftime("%Y-%m-%d %H:%M:%S")
    stamp = now.strftime("%Y%m%d_%H%M%S")
    workflow = build_workflow(root, generated_at)
    errors = validate_workflow(workflow)
    output_dir = root / "03数据" / "142n8n未激活导入工件"
    artifact = output_dir / f"股票主动研究闭环_n8n未激活导入_{stamp}.json"
    artifact_latest = output_dir / "股票主动研究闭环_n8n未激活导入_最新.json"
    package = output_dir / f"股票主动研究闭环_n8n未激活导入包_{stamp}.json"
    package_latest = output_dir / "股票主动研究闭环_n8n未激活导入包_最新.json"
    markdown = output_dir / f"股票主动研究闭环_n8n未激活导入说明_{stamp}.md"
    markdown_latest = output_dir / "股票主动研究闭环_n8n未激活导入说明_最新.md"
    report = {
        "名称": "股票主动研究闭环n8n未激活导入包",
        "版本": "2026-05-01",
        "生成时间": generated_at,
        "生成工具": "生成股票主动研究n8n未激活导入工件.py",
        "目标容器": "jiege_v3_n8n",
        "目标工作流": WORKFLOW_NAME,
        "桥接方式": "n8n共享目录触发文件",
        "日内报告闭环策略包": str(root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "股票n8n日内报告闭环与晨报推送策略包_最新.json"),
        "日内节奏": {
            "轻量随问随答": "全天；不走n8n即时主链路。",
            "收市后每日观察": "15:40-18:30；分析第二天候选。",
            "半夜宏观规律分析": "00:30-05:30；复盘推送、行业轮动、替代候选。",
            "开市前晨报推送": "08:20-08:40；本人单条晨报灰度闸口。",
            "学习沉淀": "推送、纠偏、反馈和复盘进入学习沉淀账与进化候选。",
        },
        "宿主机触发文件": r"D:\杰哥智能化系统\01杰哥智能系统\03数据\n8n\jiege_bridge\stock_active_research_trigger.json",
        "工件预检错误": errors,
        "是否可导入": not errors,
        "是否已导入n8n": False,
        "是否已启用n8n": False,
        "工作流工件": str(artifact),
        "安全边界": {
            "是否调用n8n API": False,
            "是否导入n8n": False,
            "是否启用n8n": False,
            "是否包含Webhook": False,
            "是否包含凭据": False,
            "是否包含企业微信真实发送节点": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
        "实际动作": {
            "生成本地工件": True,
            "写入03数据": True,
            "调用n8n API": False,
            "导入n8n": False,
            "启用n8n": False,
        },
    }
    md_text = "\n".join([
        "# 股票主动研究闭环n8n未激活导入说明",
        "",
        f"- 目标工作流：{WORKFLOW_NAME}",
        f"- 桥接方式：{report['桥接方式']}",
        f"- 宿主机触发文件：`{report['宿主机触发文件']}`",
        "- active=false。",
        "- 导入前需要人工确认，启用前需要再次人工确认。",
        "- 导入后仍保持 active=false。",
        "- 不执行手动触发，不接 OpenClaw，不接企业微信真实发送。",
        "- 已并入260日内报告闭环：随问随答、收市观察、半夜规律、开市前晨报、学习沉淀。",
        "- 不包含Webhook。",
        "- 不包含凭据。",
        "- 不包含企业微信真实发送节点。",
        "- 不包含券商接口或自动交易。",
        "",
        f"工件：`{artifact}`",
    ])
    write_json(artifact, workflow)
    write_json(artifact_latest, workflow)
    write_json(package, report)
    write_json(package_latest, report)
    write_text(markdown, md_text)
    write_text(markdown_latest, md_text)
    print(json.dumps({
        "状态": "完成",
        "是否可导入": not errors,
        "工件": str(artifact),
        "导入包": str(package),
    }, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
