# -*- coding: utf-8 -*-
"""生成 n8n 离线编排本地干跑执行器包。

本脚本只读取第三轮离线蓝图摘要并写入本地离线执行器包；不连接 n8n，
不启用 webhook，不请求网络，不改配置，不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
SOURCE_DATA_DIR = ROOT / "03数据" / "72n8n离线编排蓝图与禁触发验收包"
OUTPUT_DIR = ROOT / "03数据" / "75n8n离线编排本地干跑执行器包"

SOURCE_BLUEPRINT_JSON = SOURCE_DATA_DIR / "n8n离线编排蓝图_最新.json"
SOURCE_PACKAGE_JSON = SOURCE_DATA_DIR / "n8n离线编排蓝图与禁触发验收包_最新.json"

EMBEDDED_BLUEPRINT_JSON = OUTPUT_DIR / "n8n离线编排本地干跑内置蓝图_最新.json"
EXECUTOR_PACKAGE_JSON = OUTPUT_DIR / "n8n离线编排本地干跑执行器包_最新.json"
EXECUTOR_README_MD = OUTPUT_DIR / "n8n离线编排本地干跑执行器说明_最新.md"

MODE = "offline/dry_run"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def guarded_node(node_id: str, name: str, purpose: str, inputs: list[str], outputs: list[str], wait_gate: bool = False) -> dict[str, Any]:
    return {
        "id": node_id,
        "name": name,
        "kind": "local_offline_dry_run_node",
        "purpose": purpose,
        "mode": MODE,
        "offline": True,
        "dry_run": True,
        "real_trigger": False,
        "webhook_enabled": False,
        "network_request_enabled": False,
        "n8n_connection_enabled": False,
        "external_send_enabled": False,
        "config_change_enabled": False,
        "service_reload_enabled": False,
        "enterprise_wechat_send_enabled": False,
        "read_only_input": inputs,
        "simulated_output": outputs,
        "ready_rule": "仅使用上一节点的本地模拟输出；无外部触发。",
        "blocked_rule": "命中红线或等待总管确认时阻断。",
        "wait_for_supervisor": wait_gate,
    }


def build_embedded_blueprint(source_summary: dict[str, Any]) -> dict[str, Any]:
    nodes = [
        guarded_node(
            "N01",
            "收到离线消息样本",
            "读取人工转录或第三轮蓝图中的离线消息样本，生成标准化本地对象。",
            ["离线消息文本副本", "本地只读蓝图摘要"],
            ["标准化消息对象候选"],
        ),
        guarded_node(
            "N02",
            "离线分类与红线识别",
            "按业务线、风险等级、是否触碰红线做本地规则分类。",
            ["标准化消息对象候选"],
            ["离线分类结果候选", "红线命中说明候选"],
        ),
        guarded_node(
            "N03",
            "只读脚本核对模拟",
            "模拟只读脚本核对结果，只产生摘要，不调度任何真实脚本或外部服务。",
            ["离线分类结果候选", "本地只读资料路径摘要"],
            ["只读核对摘要候选", "异常阻断说明候选"],
        ),
        guarded_node(
            "N04",
            "候选回传草稿生成",
            "生成等待人工审阅的候选回传草稿，保持离线候选状态。",
            ["只读核对摘要候选"],
            ["候选回传草稿", "禁止自动发送说明"],
        ),
        guarded_node(
            "N05",
            "总管确认闸口",
            "所有候选输出停在总管确认闸口，不自动放行。",
            ["候选回传草稿", "红线命中说明候选"],
            ["待总管确认记录", "人工处理建议"],
            wait_gate=True,
        ),
    ]
    return {
        "name": "n8n离线编排本地干跑内置蓝图",
        "version": "offline-local-dryrun-blueprint-v1",
        "generated_at": now_text(),
        "based_on": source_summary,
        "scope": "只读本地干跑；不接 n8n；不启用 webhook；不请求网络；不真实发送企业微信。",
        "mode": MODE,
        "global_guard": {
            "mode": MODE,
            "offline": True,
            "dry_run": True,
            "real_trigger": False,
            "webhook_enabled": False,
            "network_request_enabled": False,
            "n8n_connection_enabled": False,
            "external_send_enabled": False,
            "config_change_enabled": False,
            "service_reload_enabled": False,
            "enterprise_wechat_send_enabled": False,
        },
        "workflow": {
            "flow": [node["id"] for node in nodes],
            "nodes": nodes,
            "edges": [
                {"from": "N01", "to": "N02", "mode": MODE, "real_trigger": False, "webhook_enabled": False},
                {"from": "N02", "to": "N03", "mode": MODE, "real_trigger": False, "webhook_enabled": False},
                {"from": "N03", "to": "N04", "mode": MODE, "real_trigger": False, "webhook_enabled": False},
                {"from": "N04", "to": "N05", "mode": MODE, "real_trigger": False, "webhook_enabled": False},
            ],
        },
        "red_lines": [
            "不接 n8n",
            "不触发 webhook",
            "不请求网络",
            "不改配置",
            "不重载服务",
            "不真实发送企业微信",
        ],
    }


def summarize_source_blueprint() -> dict[str, Any]:
    source_blueprint = read_json_if_exists(SOURCE_BLUEPRINT_JSON)
    source_package = read_json_if_exists(SOURCE_PACKAGE_JSON)
    source_nodes = source_blueprint.get("workflow", {}).get("nodes", [])
    return {
        "source_blueprint_path": str(SOURCE_BLUEPRINT_JSON),
        "source_package_path": str(SOURCE_PACKAGE_JSON),
        "source_blueprint_exists": SOURCE_BLUEPRINT_JSON.exists(),
        "source_package_exists": SOURCE_PACKAGE_JSON.exists(),
        "source_node_count": len(source_nodes),
        "source_version": source_blueprint.get("version", ""),
        "source_status": source_package.get("status", ""),
        "source_guards_observed": {
            "real_trigger": source_blueprint.get("global_guard", {}).get("real_trigger"),
            "webhook_enabled": source_blueprint.get("global_guard", {}).get("webhook_enabled"),
            "network_request_enabled": source_blueprint.get("global_guard", {}).get("network_call_enabled"),
        },
    }


def build_package(blueprint: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": "n8n离线编排本地干跑执行器包",
        "version": "offline-local-dryrun-executor-v1",
        "generated_at": blueprint["generated_at"],
        "status": "offline_local_dryrun_executor_ready",
        "mode": MODE,
        "executor_kind": "local_offline_dry_run",
        "global_guard": blueprint["global_guard"],
        "embedded_blueprint": blueprint,
        "expected_outputs": {
            "dryrun_json": str(OUTPUT_DIR / "n8n离线编排本地干跑报告_最新.json"),
            "dryrun_markdown": str(OUTPUT_DIR / "n8n离线编排本地干跑报告_最新.md"),
            "verify_log": str(ROOT / "04日志" / "n8n离线编排本地干跑执行器包验收" / "n8n-offline-local-dryrun-executor-verify-最新.json"),
        },
        "acceptance_rules": [
            "节点数不少于 5。",
            "所有节点保持 offline/dry_run。",
            "所有节点 real_trigger=false。",
            "所有节点 webhook_enabled=false。",
            "干跑报告 error_count=0。",
            "所有输出只保留本地模拟结果，停在总管确认闸口。",
        ],
    }


def build_readme(package: dict[str, Any]) -> str:
    blueprint = package["embedded_blueprint"]
    lines = [
        "# n8n 离线编排本地干跑执行器包",
        "",
        f"- 生成时间：{package['generated_at']}",
        f"- 包状态：{package['status']}",
        f"- 执行模式：{package['mode']}",
        "- 真实触发：false",
        "- webhook_enabled：false",
        "- 网络请求：false",
        "- n8n 连接：false",
        "- 企业微信真实发送：false",
        "",
        "## 本地干跑节点",
        "",
    ]
    for node in blueprint["workflow"]["nodes"]:
        lines.extend(
            [
                f"### {node['id']} {node['name']}",
                "",
                f"- mode：{node['mode']}",
                f"- real_trigger：{str(node['real_trigger']).lower()}",
                f"- webhook_enabled：{str(node['webhook_enabled']).lower()}",
                f"- 模拟输入：{'；'.join(node['read_only_input'])}",
                f"- 模拟输出：{'；'.join(node['simulated_output'])}",
                "",
            ]
        )
    lines.extend(["## 红线", "", *[f"- {item}" for item in blueprint["red_lines"]], ""])
    return "\n".join(lines)


def main() -> int:
    source_summary = summarize_source_blueprint()
    blueprint = build_embedded_blueprint(source_summary)
    package = build_package(blueprint)
    write_json(EMBEDDED_BLUEPRINT_JSON, blueprint)
    write_json(EXECUTOR_PACKAGE_JSON, package)
    write_text(EXECUTOR_README_MD, build_readme(package))
    print(
        json.dumps(
            {
                "status": package["status"],
                "nodes": len(blueprint["workflow"]["nodes"]),
                "output": str(EXECUTOR_PACKAGE_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
