# -*- coding: utf-8 -*-
"""生成 n8n 离线编排蓝图与禁触发验收包。

只生成本地蓝图与验收资料，不连接 n8n，不触发 webhook，不调用网络。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
OUTPUT_DIR = ROOT / "03数据" / "72n8n离线编排蓝图与禁触发验收包"

BLUEPRINT_JSON = OUTPUT_DIR / "n8n离线编排蓝图_最新.json"
BLUEPRINT_MD = OUTPUT_DIR / "n8n离线编排蓝图说明_最新.md"
ACCEPTANCE_MD = OUTPUT_DIR / "n8n禁触发验收清单_最新.md"
PACKAGE_JSON = OUTPUT_DIR / "n8n离线编排蓝图与禁触发验收包_最新.json"

COMMON_NODE_GUARD = {
    "mode": "dry_run/offline",
    "real_trigger": False,
    "webhook_enabled": False,
}

FORBIDDEN_ACTIONS = [
    "接 n8n",
    "触发 webhook",
    "调用网络",
    "改企业微信配置",
    "改运行配置",
    "重载服务",
    "真实发送企业微信",
    "接券商",
    "接税局",
    "接财税软件",
    "真实渲染/发布",
    "转正式规则",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def guarded_node(node_id: str, name: str, purpose: str, read_only_input: list[str], output_candidate: list[str]) -> dict[str, Any]:
    node = {
        "id": node_id,
        "name": name,
        "type": "offline_blueprint_node",
        "purpose": purpose,
        "read_only_input": read_only_input,
        "output_candidate": output_candidate,
        "allowed_operation": "只读读取、离线分类、离线候选文本生成、等待总管确认",
        "blocked_operation": FORBIDDEN_ACTIONS,
    }
    node.update(COMMON_NODE_GUARD)
    return node


def build_blueprint() -> dict[str, Any]:
    nodes = [
        guarded_node(
            "N01",
            "收到消息",
            "登记来自企业微信或人工转录的消息样本，但只使用离线文本副本。",
            ["离线消息样本", "人工复制的只读文本"],
            ["标准化消息对象候选"],
        ),
        guarded_node(
            "N02",
            "分类",
            "按业务线、风险等级、是否触碰红线进行离线分类。",
            ["标准化消息对象候选"],
            ["分类结果候选", "红线命中说明候选"],
        ),
        guarded_node(
            "N03",
            "只读脚本",
            "仅指向本地只读核对脚本的执行设计，不实际调度、不连接外部服务。",
            ["分类结果候选", "本地只读资料路径"],
            ["只读核对摘要候选", "异常阻断说明候选"],
        ),
        guarded_node(
            "N04",
            "生成候选回传",
            "生成可供人工审阅的回传草稿，保持候选态。",
            ["只读核对摘要候选"],
            ["候选回传文本", "禁止自动发送说明"],
        ),
        guarded_node(
            "N05",
            "总管确认闸口",
            "所有候选回传必须停在总管确认闸口，不自动放行。",
            ["候选回传文本", "红线命中说明候选"],
            ["待总管确认记录", "人工处理建议"],
        ),
    ]
    return {
        "name": "n8n离线编排蓝图与禁触发验收包",
        "version": "offline-blueprint-v1",
        "generated_at": now_text(),
        "scope": "低风险实际能力前置；仅离线蓝图；不接 n8n。",
        "global_guard": {
            "mode": "dry_run/offline",
            "real_trigger": False,
            "webhook_enabled": False,
            "network_call_enabled": False,
            "n8n_connection_enabled": False,
            "external_delivery_enabled": False,
            "production_rule_enabled": False,
        },
        "workflow": {
            "flow": ["收到消息", "分类", "只读脚本", "生成候选回传", "总管确认闸口"],
            "nodes": nodes,
            "edges": [
                {"from": "N01", "to": "N02", "mode": "dry_run/offline", "real_trigger": False, "webhook_enabled": False},
                {"from": "N02", "to": "N03", "mode": "dry_run/offline", "real_trigger": False, "webhook_enabled": False},
                {"from": "N03", "to": "N04", "mode": "dry_run/offline", "real_trigger": False, "webhook_enabled": False},
                {"from": "N04", "to": "N05", "mode": "dry_run/offline", "real_trigger": False, "webhook_enabled": False},
            ],
        },
        "forbidden_actions": FORBIDDEN_ACTIONS,
        "acceptance_rules": [
            "每个节点必须 mode=dry_run/offline。",
            "每个节点必须 real_trigger=false。",
            "每个节点必须 webhook_enabled=false。",
            "蓝图不得包含 URL、token、credential、active=true、真实发送、真实触发配置。",
            "所有输出保持候选态，必须停在总管确认闸口。",
        ],
    }


def build_blueprint_md(blueprint: dict[str, Any]) -> str:
    lines = [
        "# n8n 离线编排蓝图",
        "",
        f"- 生成时间：{blueprint['generated_at']}",
        f"- 范围：{blueprint['scope']}",
        "- 全局模式：dry_run/offline",
        "- 真实触发：false",
        "- webhook：false",
        "",
        "## 离线流程",
        "",
        "收到消息 -> 分类 -> 只读脚本 -> 生成候选回传 -> 总管确认闸口",
        "",
        "## 节点",
        "",
    ]
    for node in blueprint["workflow"]["nodes"]:
        lines.extend(
            [
                f"### {node['id']} {node['name']}",
                "",
                f"- 目的：{node['purpose']}",
                f"- mode：{node['mode']}",
                f"- real_trigger：{str(node['real_trigger']).lower()}",
                f"- webhook_enabled：{str(node['webhook_enabled']).lower()}",
                f"- 只读输入：{'；'.join(node['read_only_input'])}",
                f"- 候选输出：{'；'.join(node['output_candidate'])}",
                "",
            ]
        )
    return "\n".join(lines)


def build_acceptance_md(blueprint: dict[str, Any]) -> str:
    rows = [
        "| 节点 mode 全部为 dry_run/offline | 待执行脚本核对 |",
        "| 节点 real_trigger 全部为 false | 待执行脚本核对 |",
        "| 节点 webhook_enabled 全部为 false | 待执行脚本核对 |",
        "| 无 URL/token/credential/active=true 等真实接入字段 | 待执行脚本核对 |",
        "| 流程停在总管确认闸口 | 待执行脚本核对 |",
    ]
    return "\n".join(
        [
            "# n8n 禁触发验收清单",
            "",
            f"- 蓝图：{BLUEPRINT_JSON}",
            f"- 生成时间：{blueprint['generated_at']}",
            "",
            "| 验收项 | 状态 |",
            "| --- | --- |",
            *rows,
            "",
            "## 禁止动作",
            "",
            *[f"- {item}" for item in FORBIDDEN_ACTIONS],
            "",
        ]
    )


def main() -> int:
    blueprint = build_blueprint()
    package = {
        "name": "n8n离线编排蓝图与禁触发验收包",
        "generated_at": blueprint["generated_at"],
        "status": "offline_blueprint_ready",
        "blueprint": blueprint,
        "outputs": {
            "blueprint_json": str(BLUEPRINT_JSON),
            "blueprint_markdown": str(BLUEPRINT_MD),
            "acceptance_markdown": str(ACCEPTANCE_MD),
            "package_json": str(PACKAGE_JSON),
        },
    }
    write_json(BLUEPRINT_JSON, blueprint)
    write_text(BLUEPRINT_MD, build_blueprint_md(blueprint))
    write_text(ACCEPTANCE_MD, build_acceptance_md(blueprint))
    write_json(PACKAGE_JSON, package)
    print(json.dumps({"status": package["status"], "nodes": len(blueprint["workflow"]["nodes"]), "output": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
