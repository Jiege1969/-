# -*- coding: utf-8 -*-
"""生成 n8n 离线干跑多场景回归与闸口矩阵包。

只读取本地离线蓝图摘要和本包内置场景；不连接 n8n，不启用 webhook，
不请求网络，不改配置，不重载服务，不真实发送企业微信。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
SCRIPT_DIR = ROOT / "02脚本"
DATA_DIR = ROOT / "03数据" / "78n8n离线干跑多场景回归与闸口矩阵包"
LOG_DIR = ROOT / "04日志" / "n8n离线干跑多场景回归与闸口矩阵包验收"

SOURCE_75_PACKAGE = ROOT / "03数据" / "75n8n离线编排本地干跑执行器包" / "n8n离线编排本地干跑执行器包_最新.json"
SOURCE_75_REPORT = ROOT / "03数据" / "75n8n离线编排本地干跑执行器包" / "n8n离线编排本地干跑报告_最新.json"
SOURCE_72_BLUEPRINT = ROOT / "03数据" / "72n8n离线编排蓝图与禁触发验收包" / "n8n离线编排蓝图_最新.json"

PACKAGE_JSON = DATA_DIR / "n8n离线干跑多场景回归与闸口矩阵包_最新.json"
PACKAGE_MD = DATA_DIR / "n8n离线干跑多场景回归与闸口矩阵包_最新.md"
SCENARIOS_JSON = DATA_DIR / "n8n离线干跑多场景回归场景_最新.json"
GATE_MATRIX_JSON = DATA_DIR / "n8n离线干跑闸口矩阵_最新.json"
GATE_MATRIX_MD = DATA_DIR / "n8n离线干跑闸口矩阵_最新.md"

MODE = "offline/dry_run"

GLOBAL_GUARD = {
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
}


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


def guard_copy(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    data = dict(GLOBAL_GUARD)
    if extra:
        data.update(extra)
    return data


def node(node_id: str, name: str, purpose: str, result: str, status: str = "ready") -> dict[str, Any]:
    return guard_copy(
        {
            "node_id": node_id,
            "node_name": name,
            "purpose": purpose,
            "dry_run_result": result,
            "status": status,
            "error_count": 0,
        }
    )


def scenario(
    scenario_id: str,
    name: str,
    category: str,
    description: str,
    nodes: list[dict[str, Any]],
    final_status: str,
    blocking_gates: list[str],
    expected_candidate: str,
) -> dict[str, Any]:
    return guard_copy(
        {
            "scenario_id": scenario_id,
            "scenario_name": name,
            "category": category,
            "description": description,
            "input_kind": "本包内置离线样本",
            "nodes": nodes,
            "final_status": final_status,
            "blocking_gates": blocking_gates,
            "expected_candidate": expected_candidate,
            "error_count": 0,
        }
    )


def build_source_summary() -> dict[str, Any]:
    package75 = read_json_if_exists(SOURCE_75_PACKAGE)
    report75 = read_json_if_exists(SOURCE_75_REPORT)
    blueprint72 = read_json_if_exists(SOURCE_72_BLUEPRINT)
    package_nodes = package75.get("embedded_blueprint", {}).get("workflow", {}).get("nodes", [])
    report_nodes = report75.get("node_runs", [])
    blueprint_nodes = blueprint72.get("workflow", {}).get("nodes", [])
    guard75 = package75.get("global_guard", {})
    return {
        "source_kind": "本地离线蓝图摘要",
        "package75_exists": SOURCE_75_PACKAGE.exists(),
        "report75_exists": SOURCE_75_REPORT.exists(),
        "blueprint72_exists": SOURCE_72_BLUEPRINT.exists(),
        "package75_status": package75.get("status", ""),
        "report75_status": report75.get("status", ""),
        "package75_node_count": len(package_nodes),
        "report75_node_count": len(report_nodes),
        "blueprint72_node_count": len(blueprint_nodes),
        "observed_guard": {
            "mode": guard75.get("mode", MODE),
            "offline": guard75.get("offline") is True,
            "dry_run": guard75.get("dry_run") is True,
            "real_trigger": guard75.get("real_trigger") is False,
            "webhook_enabled": guard75.get("webhook_enabled") is False,
            "network_request_enabled": guard75.get("network_request_enabled") is False,
            "n8n_connection_enabled": guard75.get("n8n_connection_enabled") is False,
        },
    }


def build_gate_definitions() -> list[dict[str, Any]]:
    gates = [
        ("G01", "n8n连接阻断", "任何连接或触发 n8n 的动作都必须停止"),
        ("G02", "webhook启用阻断", "任何启用或触发 webhook 的动作都必须停止"),
        ("G03", "网络请求阻断", "任何外部网络请求都必须停止"),
        ("G04", "企业微信真实发送阻断", "任何真实发送企业微信的动作都必须停止"),
        ("G05", "税务真实账号阻断", "任何登录税局或财税软件的动作都必须停止"),
        ("G06", "股票交易链路阻断", "任何券商连接、下单、调仓动作都必须停止"),
        ("G07", "视频真实渲染发布阻断", "任何真实渲染、上传、发布视频的动作都必须停止"),
        ("G08", "总管确认闸口", "需要人工确认的候选只停留在待确认状态"),
        ("G09", "配置与服务重载阻断", "任何改配置或重载服务的动作都必须停止"),
        ("G10", "正式规则变更阻断", "任何转正式规则或改总管资产的动作都必须停止"),
    ]
    return [
        guard_copy(
            {
                "gate_id": gate_id,
                "gate_name": name,
                "gate_rule": rule,
                "default_action": "blocked",
                "requires_supervisor": gate_id in {"G08", "G09", "G10"},
            }
        )
        for gate_id, name, rule in gates
    ]


def build_scenarios() -> list[dict[str, Any]]:
    return [
        scenario(
            "S01",
            "税收消息转候选",
            "tax_message_to_candidate",
            "将离线税收消息样本转成待复核候选，不登录税局，不接财税软件。",
            [
                node("S01-N01", "读取离线税收消息", "读取本包内置文本样本", "生成标准化税收消息对象"),
                node("S01-N02", "识别税务意图", "本地规则识别申报、资料、风险关键词", "输出税收候选分类"),
                node("S01-N03", "生成候选草稿", "形成待复核说明", "候选草稿停留在本地"),
                node("S01-N04", "命中总管确认", "税务结论不得自动转正式", "阻断在总管确认闸口", "blocked"),
            ],
            "blocked_waiting_supervisor",
            ["G04", "G05", "G08"],
            "税收候选草稿",
        ),
        scenario(
            "S02",
            "股票展示巡检",
            "stock_display_inspection",
            "只做展示层离线巡检，不连接券商，不下单，不请求业务接口。",
            [
                node("S02-N01", "读取展示快照摘要", "读取本地展示字段样本", "得到展示字段清单"),
                node("S02-N02", "核对展示完整性", "检查价格、风险提示、时间戳占位", "输出展示巡检结论"),
                node("S02-N03", "生成修复候选", "仅生成候选建议", "修复建议停留在本地"),
            ],
            "inspection_ready_blocked_before_trade",
            ["G03", "G06", "G08"],
            "股票展示巡检候选",
        ),
        scenario(
            "S03",
            "视频渲染阻断",
            "video_render_block",
            "识别视频渲染或发布需求并直接阻断，只保留本地预检结果。",
            [
                node("S03-N01", "读取视频任务样本", "读取本地视频需求描述", "得到视频任务候选"),
                node("S03-N02", "识别真实渲染风险", "检测渲染、上传、发布关键词", "命中视频真实渲染发布阻断", "blocked"),
                node("S03-N03", "保留阻断证据", "写入本地 dry_run 结果", "形成阻断说明", "blocked"),
            ],
            "blocked_video_real_render",
            ["G03", "G07", "G08"],
            "视频渲染阻断说明",
        ),
        scenario(
            "S04",
            "总管确认闸口",
            "supervisor_confirmation_gate",
            "验证所有候选在需要人工确认时停留在总管确认闸口。",
            [
                node("S04-N01", "汇总候选摘要", "读取前序候选摘要样本", "形成待确认列表"),
                node("S04-N02", "应用确认规则", "本地判断是否需要总管确认", "命中总管确认闸口", "blocked"),
                node("S04-N03", "输出待确认卡片", "生成只读待确认卡片", "禁止自动放行", "blocked"),
            ],
            "blocked_waiting_supervisor",
            ["G08", "G10"],
            "待总管确认卡片",
        ),
        scenario(
            "S05",
            "异常失败分级",
            "exception_failure_grading",
            "对异常样本做 L0-L5 离线分级，红线类只输出阻断结论。",
            [
                node("S05-N01", "读取异常样本", "读取本地异常描述", "得到异常候选"),
                node("S05-N02", "执行失败分级", "按只读规则模拟 L0-L5 分级", "分级结果为 L4 红线风险"),
                node("S05-N03", "生成处置建议", "仅生成候选处置建议", "停止自动处置并等待确认", "blocked"),
            ],
            "blocked_failure_level_l4",
            ["G01", "G02", "G03", "G08", "G09"],
            "异常失败分级候选",
        ),
    ]


def build_matrix(scenarios: list[dict[str, Any]], gates: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for item in scenarios:
        gate_set = set(item["blocking_gates"])
        for gate in gates:
            applies = gate["gate_id"] in gate_set
            rows.append(
                guard_copy(
                    {
                        "scenario_id": item["scenario_id"],
                        "scenario_name": item["scenario_name"],
                        "gate_id": gate["gate_id"],
                        "gate_name": gate["gate_name"],
                        "applies": applies,
                        "result": "blocked" if applies else "not_hit",
                        "final_status": item["final_status"],
                    }
                )
            )
    return guard_copy(
        {
            "name": "n8n离线干跑闸口矩阵",
            "generated_at": now_text(),
            "gate_count": len(gates),
            "scenario_count": len(scenarios),
            "gates": gates,
            "rows": rows,
            "error_count": 0,
        }
    )


def build_matrix_md(matrix: dict[str, Any]) -> str:
    lines = [
        "# n8n 离线干跑闸口矩阵",
        "",
        f"- 生成时间：{matrix['generated_at']}",
        f"- 场景数：{matrix['scenario_count']}",
        f"- 闸口数：{matrix['gate_count']}",
        "- 模式：offline/dry_run",
        "- 真实触发：false",
        "- webhook_enabled：false",
        "",
        "| 场景 | 命中闸口 | 结果 | 最终状态 |",
        "| --- | --- | --- | --- |",
    ]
    for row in matrix["rows"]:
        if row["applies"]:
            lines.append(
                f"| {row['scenario_id']} {row['scenario_name']} | {row['gate_id']} {row['gate_name']} | {row['result']} | {row['final_status']} |"
            )
    lines.append("")
    return "\n".join(lines)


def build_package_md(package: dict[str, Any]) -> str:
    lines = [
        "# n8n 离线干跑多场景回归与闸口矩阵包",
        "",
        f"- 生成时间：{package['generated_at']}",
        f"- 状态：{package['status']}",
        f"- 模式：{package['mode']}",
        "- 真实触发：false",
        "- webhook_enabled：false",
        "- 网络请求：false",
        "- n8n 连接：false",
        "- 企业微信真实发送：false",
        "",
        "## 场景",
        "",
    ]
    for item in package["scenarios"]:
        lines.extend(
            [
                f"### {item['scenario_id']} {item['scenario_name']}",
                "",
                f"- 最终状态：{item['final_status']}",
                f"- 阻断闸口：{'、'.join(item['blocking_gates'])}",
                f"- dry_run 节点数：{len(item['nodes'])}",
                "",
            ]
        )
    lines.extend(
        [
            "## 验收要求",
            "",
            "- 场景数不少于 5。",
            "- 所有场景必须 offline/dry_run。",
            "- real_trigger=false。",
            "- webhook_enabled=false。",
            "- 不写入真实接入敏感字段。",
            "- error_count=0。",
            "",
        ]
    )
    return "\n".join(lines)


def build_package() -> dict[str, Any]:
    generated_at = now_text()
    scenarios = build_scenarios()
    gates = build_gate_definitions()
    matrix = build_matrix(scenarios, gates)
    return guard_copy(
        {
            "name": "n8n离线干跑多场景回归与闸口矩阵包",
            "version": "offline-multiscenario-gate-matrix-v1",
            "generated_at": generated_at,
            "status": "offline_multiscenario_gate_matrix_ready",
            "source_summary": build_source_summary(),
            "scenario_count": len(scenarios),
            "gate_count": len(gates),
            "scenarios": scenarios,
            "gate_matrix": matrix,
            "acceptance_rules": [
                "场景数不少于5",
                "所有场景保持offline/dry_run",
                "所有真实触发开关为false",
                "所有webhook开关为false",
                "不写入真实接入敏感字段",
                "干跑error_count=0",
            ],
            "artifacts": {
                "package_json": str(PACKAGE_JSON),
                "package_markdown": str(PACKAGE_MD),
                "scenarios_json": str(SCENARIOS_JSON),
                "gate_matrix_json": str(GATE_MATRIX_JSON),
                "gate_matrix_markdown": str(GATE_MATRIX_MD),
                "verify_log": str(LOG_DIR / "n8n-offline-multiscenario-gate-matrix-verify-最新.json"),
            },
            "error_count": 0,
        }
    )


def main() -> int:
    package = build_package()
    scenarios = guard_copy(
        {
            "name": "n8n离线干跑多场景回归场景",
            "generated_at": package["generated_at"],
            "scenario_count": package["scenario_count"],
            "scenarios": package["scenarios"],
            "error_count": 0,
        }
    )
    matrix = package["gate_matrix"]
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, build_package_md(package))
    write_json(SCENARIOS_JSON, scenarios)
    write_json(GATE_MATRIX_JSON, matrix)
    write_text(GATE_MATRIX_MD, build_matrix_md(matrix))
    print(
        json.dumps(
            {
                "status": package["status"],
                "scenario_count": package["scenario_count"],
                "gate_count": package["gate_count"],
                "output": str(PACKAGE_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
