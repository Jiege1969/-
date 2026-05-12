# -*- coding: utf-8 -*-
"""
名称：生成股票n8n企业微信终端灰度工作流.py
作用：复用260策略包，生成可导入n8n的股票企业微信终端灰度调度工作流。
触发方式：python 生成股票n8n企业微信终端灰度工作流.py
依赖：01配置/n8n本地桥接配置.json；股票n8n企业微信终端桥接服务.py。
安全边界：只生成本地工作流工件；不导入、不触发、不真实发送企业微信、不接券商、不交易。
标识：stock-n8n-wecom-terminal-gray-workflow-generate
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


WORKFLOW_NAME = "股票主动研究闭环_企业微信终端灰度启用"
ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "01配置" / "n8n本地桥接配置.json"
OUT_DIR = ROOT / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def node_id() -> str:
    return str(uuid.uuid4())


def bridge_config() -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})
    if int(config.get("port") or 0) in {0, 19310, 19302, 19300}:
        config["port"] = 19312
    if not config.get("bind_host"):
        config["bind_host"] = "0.0.0.0"
    if not config.get("url_host"):
        config["url_host"] = str(config.get("host") or "172.22.0.1")
    if not config.get("token"):
        raise RuntimeError(f"n8n桥接配置缺少token：{CONFIG_PATH}")
    write_json(CONFIG_PATH, config)
    return config


def schedule_node(name: str, stage: str, hour: int, minute: int, x: int, y: int) -> dict[str, Any]:
    return {
        "parameters": {
            "rule": {
                "interval": [
                    {
                        "field": "weeks",
                        "weeksInterval": 1,
                        "triggerAtDay": [1, 2, 3, 4, 5],
                        "triggerAtHour": hour,
                        "triggerAtMinute": minute,
                    }
                ]
            }
        },
        "id": node_id(),
        "name": name,
        "type": "n8n-nodes-base.scheduleTrigger",
        "typeVersion": 1.3,
        "position": [x, y],
        "notes": f"工作日定时触发股票{stage}；不含企业微信真实发送节点。",
    }


def execute_node(config: dict[str, Any], stage: str, x: int, y: int) -> dict[str, Any]:
    trigger_path = "/home/node/.n8n/jiege_bridge/stock_active_research_trigger.json"
    command = (
        "mkdir -p /home/node/.n8n/jiege_bridge && "
        "printf '{\"task\":\"stock_active_research\",\"source\":\"n8n_schedule\",\"stage\":\""
        + stage
        + "\",\"created_at\":\"%s\"}\\n' \"$(date -Iseconds)\" > "
        + trigger_path
        + " && cat "
        + trigger_path
    )
    return {
        "parameters": {"command": command},
        "id": node_id(),
        "name": f"调用股票桥接生成{stage}",
        "type": "n8n-nodes-base.executeCommand",
        "typeVersion": 1,
        "position": [x, y],
    }


def manual_node() -> dict[str, Any]:
    return {
        "parameters": {},
        "id": node_id(),
        "name": "手动触发即时验证",
        "type": "n8n-nodes-base.manualTrigger",
        "typeVersion": 1,
        "position": [180, 520],
    }


def set_node(x: int, y: int) -> dict[str, Any]:
    return {
        "parameters": {
            "mode": "manual",
            "duplicateItem": False,
            "assignments": {
                "assignments": [
                    {"id": node_id(), "name": "工作流状态", "value": "active_gray_scheduled", "type": "string"},
                    {"id": node_id(), "name": "企业微信定位", "value": "输入输出终端，不是判断核心", "type": "string"},
                    {"id": node_id(), "name": "报告定位", "value": "大模型/股票系统加工成使用者可读报告，不输出技术过程堆砌", "type": "string"},
                    {"id": node_id(), "name": "真实发送企业微信", "value": False, "type": "boolean"},
                    {"id": node_id(), "name": "券商交易", "value": False, "type": "boolean"},
                ]
            },
        },
        "id": node_id(),
        "name": "输出灰度状态",
        "type": "n8n-nodes-base.set",
        "typeVersion": 3.4,
        "position": [760, 260],
    }


def sticky_node() -> dict[str, Any]:
    return {
        "parameters": {
            "content": "股票企业微信终端灰度调度\\n企业微信是使用者与系统的输入输出窗口。\\nn8n只做定时调度，股票系统和模型路由负责生成可读报告。\\n当前不含企业微信真实发送节点，不群发，不接券商，不交易。",
            "height": 260,
            "width": 420,
            "color": 4,
        },
        "id": node_id(),
        "name": "安全边界说明",
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [180, -120],
    }


def build_workflow(config: dict[str, Any]) -> dict[str, Any]:
    schedules = [
        ("收市后每日观察 18:30", "after_close_report", 18, 30, 180, 80),
        ("半夜长期观察 00:30", "night_observation", 0, 30, 180, 260),
        ("开市前晨报准备 08:20", "morning_brief", 8, 20, 180, 440),
    ]
    nodes: list[dict[str, Any]] = [sticky_node()]
    connections: dict[str, Any] = {}
    for name, stage, hour, minute, x, y in schedules:
        trigger = schedule_node(name, stage, hour, minute, x, y)
        execute = execute_node(config, stage, 500, y)
        nodes.extend([trigger, execute])
        connections[trigger["name"]] = {"main": [[{"node": execute["name"], "type": "main", "index": 0}]]}
        connections[execute["name"]] = {"main": [[{"node": "输出灰度状态", "type": "main", "index": 0}]]}
    manual = manual_node()
    manual_execute = execute_node(config, "manual", 500, 620)
    status = set_node(820, 260)
    nodes.extend([manual, manual_execute, status])
    connections[manual["name"]] = {"main": [[{"node": manual_execute["name"], "type": "main", "index": 0}]]}
    connections[manual_execute["name"]] = {"main": [[{"node": "输出灰度状态", "type": "main", "index": 0}]]}
    return {
        "name": WORKFLOW_NAME,
        "active": True,
        "nodes": nodes,
        "connections": connections,
        "settings": {
            "executionOrder": "v1",
            "saveManualExecutions": True,
            "timezone": "Asia/Shanghai",
        },
        "staticData": None,
        "pinData": {},
        "tags": [],
        "meta": {
            "jiege_stock_n8n_wecom_terminal_gray": True,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "strategy_package": str(OUT_DIR / "股票n8n日内报告闭环与晨报推送策略包_最新.json"),
            "real_wecom_send": False,
            "broker_api": False,
            "trade": False,
            "formal_rule_auto_apply": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    return "\n".join([
        "# 股票n8n企业微信终端灰度工作流",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 工作流名称：{report['工作流名称']}",
        f"- active：{report['工作流']['active']}",
        f"- 桥接地址：{report['桥接地址']}",
        "- 调度：18:30收市观察；00:30夜间长期观察；08:20开市前晨报准备。",
        "- 企业微信定位：输入输出终端，报告由股票系统和模型路由加工。",
        "- 安全边界：不真实发送企业微信、不群发、不接券商、不交易、不自动转正式规则。",
        "",
    ])


def main() -> int:
    config = bridge_config()
    workflow = build_workflow(config)
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    artifact = OUT_DIR / f"股票n8n企业微信终端灰度工作流_{stamp}.json"
    latest = OUT_DIR / "股票n8n企业微信终端灰度工作流_最新.json"
    report = {
        "名称": "股票n8n企业微信终端灰度工作流生成记录",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "工作流名称": WORKFLOW_NAME,
        "桥接地址": f"file://n8n-shared/jiege_bridge/stock_active_research_trigger.json",
        "工作流": workflow,
        "安全边界": {
            "导入n8n": False,
            "触发n8n": False,
            "真实发送企业微信": False,
            "群发": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    report_json = OUT_DIR / f"股票n8n企业微信终端灰度工作流生成记录_{stamp}.json"
    report_latest = OUT_DIR / "股票n8n企业微信终端灰度工作流生成记录_最新.json"
    report_md = OUT_DIR / f"股票n8n企业微信终端灰度工作流生成记录_{stamp}.md"
    report_md_latest = OUT_DIR / "股票n8n企业微信终端灰度工作流生成记录_最新.md"
    write_json(artifact, workflow)
    write_json(latest, workflow)
    write_json(report_json, report)
    write_json(report_latest, report)
    markdown = build_markdown(report)
    write_text(report_md, markdown)
    write_text(report_md_latest, markdown)
    print(json.dumps({"状态": "完成", "工作流": str(latest), "报告": str(report_latest)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
