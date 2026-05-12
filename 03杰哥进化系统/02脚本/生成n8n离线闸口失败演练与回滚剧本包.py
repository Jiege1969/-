# -*- coding: utf-8 -*-
"""生成 n8n 离线闸口失败演练与回滚剧本包。

只读取第78包离线矩阵或本包内置样例；不连接 n8n，不启用 webhook，
不请求网络，不改配置，不重载服务，不真实发送企业微信。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "81n8n离线闸口失败演练与回滚剧本包"
SOURCE_78_DIR = ROOT / "03数据" / "78n8n离线干跑多场景回归与闸口矩阵包"
SOURCE_78_PACKAGE = SOURCE_78_DIR / "n8n离线干跑多场景回归与闸口矩阵包_最新.json"
SOURCE_78_MATRIX = SOURCE_78_DIR / "n8n离线干跑闸口矩阵_最新.json"

PACKAGE_JSON = DATA_DIR / "n8n离线闸口失败演练与回滚剧本包_最新.json"
PACKAGE_MD = DATA_DIR / "n8n离线闸口失败演练与回滚剧本包_最新.md"
SCENARIOS_JSON = DATA_DIR / "n8n离线闸口失败演练场景_最新.json"
ROLLBACK_JSON = DATA_DIR / "n8n离线闸口失败演练回滚剧本_最新.json"
ROLLBACK_MD = DATA_DIR / "n8n离线闸口失败演练回滚剧本_最新.md"

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


def build_source_summary() -> dict[str, Any]:
    package78 = read_json_if_exists(SOURCE_78_PACKAGE)
    matrix78 = read_json_if_exists(SOURCE_78_MATRIX)
    return guard_copy(
        {
            "source_kind": "第78包离线矩阵优先，缺失时使用本包内置样例",
            "source_78_package_exists": SOURCE_78_PACKAGE.exists(),
            "source_78_matrix_exists": SOURCE_78_MATRIX.exists(),
            "source_78_status": package78.get("status", ""),
            "source_78_scenario_count": package78.get("scenario_count", 0),
            "source_78_gate_count": matrix78.get("gate_count", 0),
            "source_78_matrix_row_count": len(matrix78.get("rows", [])),
        }
    )


def gate(gate_id: str, gate_name: str, reason: str) -> dict[str, Any]:
    return guard_copy(
        {
            "gate_id": gate_id,
            "gate_name": gate_name,
            "reason": reason,
            "decision": "blocked",
        }
    )


def rollback_steps(scenario_id: str, focus: str) -> list[dict[str, Any]]:
    base_steps = [
        ("freeze", "冻结本地演练证据", "仅保留离线样例、检测结果和阻断原因，不写入任何外部系统"),
        ("force_guard", "强制恢复离线护栏", "确认 mode=offline/dry_run、real_trigger=false、webhook_enabled=false"),
        ("quarantine", "隔离风险候选", f"将 {focus} 标记为 blocked_candidate，只允许人工复核"),
        ("supervisor", "回到总管确认", "恢复为待总管确认状态，禁止自动放行"),
        ("verify", "本地复验", "只读取本包 JSON，复验 error_count=0 且无真实动作开关"),
    ]
    return [
        guard_copy(
            {
                "scenario_id": scenario_id,
                "step_id": f"{scenario_id}-RB{index:02d}",
                "action": action,
                "title": title,
                "operation": operation,
                "execution_mode": "documented_local_recovery_only",
                "expected_result": "offline/dry_run recovered",
                "error_count": 0,
            }
        )
        for index, (action, title, operation) in enumerate(base_steps, start=1)
    ]


def recovery_state(note: str) -> dict[str, Any]:
    return guard_copy(
        {
            "status": "recovered_to_blocked_offline_state",
            "recovery_note": note,
            "n8n_connected": False,
            "webhook_registered": False,
            "downstream_real_action_released": False,
            "supervisor_confirmation_required": True,
            "error_count": 0,
        }
    )


def scenario(
    scenario_id: str,
    name: str,
    category: str,
    injected_fault: str,
    detection: str,
    gates: list[dict[str, Any]],
    rollback_focus: str,
    recovery_note: str,
) -> dict[str, Any]:
    playbook_id = f"RB-{scenario_id}"
    return guard_copy(
        {
            "scenario_id": scenario_id,
            "scenario_name": name,
            "category": category,
            "input_kind": "本包内置离线失败演练样例",
            "fault_probe": {
                "description": injected_fault,
                "simulated_only": True,
                "applied_to_runtime": False,
            },
            "detection_result": guard_copy(
                {
                    "detected": True,
                    "result": detection,
                    "decision": "blocked",
                    "blocked": True,
                    "error_count": 0,
                }
            ),
            "blocking_gates": gates,
            "rollback_playbook": guard_copy(
                {
                    "playbook_id": playbook_id,
                    "scenario_id": scenario_id,
                    "title": f"{name}回滚剧本",
                    "steps": rollback_steps(scenario_id, rollback_focus),
                    "error_count": 0,
                }
            ),
            "recovery_after_state": recovery_state(recovery_note),
            "final_status": "blocked_and_recovered_offline",
            "error_count": 0,
        }
    )


def build_scenarios() -> list[dict[str, Any]]:
    return [
        scenario(
            "FD01",
            "webhook误开",
            "webhook_misopen",
            "离线样例声称 webhook 开关被误开；运行层只记录故障文本，不注册或触发 webhook。",
            "检测到 webhook 开关异常意图，命中 webhook 启用阻断和 n8n 连接阻断。",
            [
                gate("G01", "n8n连接阻断", "任何连接或触发 n8n 的动作都必须停止"),
                gate("G02", "webhook启用阻断", "任何启用或触发 webhook 的动作都必须停止"),
                gate("G08", "总管确认闸口", "失败演练结果必须停留在总管确认前"),
            ],
            "webhook误开候选",
            "webhook 保持未启用，候选停留在 blocked 状态。",
        ),
        scenario(
            "FD02",
            "真实触发标志误开",
            "real_trigger_flag_misopen",
            "离线样例声称真实触发标志被误开；运行层只识别该意图并保持真实触发关闭。",
            "检测到真实触发异常意图，命中真实动作阻断和总管确认闸口。",
            [
                gate("G01", "n8n连接阻断", "真实触发不得进入 n8n 执行链路"),
                gate("G03", "网络请求阻断", "真实触发常伴随外部请求，必须提前阻断"),
                gate("G08", "总管确认闸口", "恢复前必须人工确认"),
            ],
            "真实触发误开候选",
            "真实触发保持 false，恢复为 offline/dry_run。",
        ),
        scenario(
            "FD03",
            "凭据字段出现",
            "credential_field_present",
            "离线样例出现凭据字段占位描述；不包含真实凭据值，不读取或写入凭据。",
            "检测到凭据字段出现，命中敏感字段阻断和配置变更阻断。",
            [
                gate("G03", "网络请求阻断", "凭据字段不得进入任何外部请求"),
                gate("G09", "配置与服务重载阻断", "不得写入配置或重载服务"),
                gate("G10", "正式规则变更阻断", "不得自动固化为正式规则"),
            ],
            "凭据字段风险候选",
            "凭据字段只保留风险说明，恢复为无凭据、无外发的离线状态。",
        ),
        scenario(
            "FD04",
            "总管确认缺失",
            "supervisor_confirmation_missing",
            "离线样例缺少总管确认记录；不自动补确认，不冒充确认。",
            "检测到总管确认缺失，命中总管确认闸口并停止放行。",
            [
                gate("G08", "总管确认闸口", "缺少总管确认时必须阻断"),
                gate("G10", "正式规则变更阻断", "不得跳过确认转正式"),
            ],
            "缺失确认候选",
            "恢复为 waiting_supervisor_confirmation，所有自动放行保持关闭。",
        ),
        scenario(
            "FD05",
            "下游真实动作误放行",
            "downstream_real_action_misrelease",
            "离线样例声称下游真实动作被误放行；运行层不连接任何下游系统。",
            "检测到下游真实动作放行意图，命中外部发送、企业微信发送和网络请求阻断。",
            [
                gate("G03", "网络请求阻断", "下游动作不得发起外部请求"),
                gate("G04", "企业微信真实发送阻断", "不得真实发送企业微信"),
                gate("G08", "总管确认闸口", "下游动作恢复前必须确认"),
            ],
            "下游真实动作候选",
            "下游真实动作恢复为未放行，企业微信发送保持关闭。",
        ),
    ]


def build_rollback_package(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    playbooks = [item["rollback_playbook"] for item in scenarios]
    return guard_copy(
        {
            "name": "n8n离线闸口失败演练回滚剧本",
            "version": "offline-gate-failure-drill-rollback-v1",
            "generated_at": now_text(),
            "playbook_count": len(playbooks),
            "playbooks": playbooks,
            "redline": [
                "不接 n8n",
                "不触发 webhook",
                "不请求网络",
                "不改配置",
                "不重载服务",
                "不真实发送企业微信",
            ],
            "error_count": 0,
        }
    )


def build_package(scenarios: list[dict[str, Any]], rollback_package: dict[str, Any]) -> dict[str, Any]:
    return guard_copy(
        {
            "name": "n8n离线闸口失败演练与回滚剧本包",
            "version": "offline-gate-failure-drill-rollback-v1",
            "generated_at": now_text(),
            "status": "offline_failure_drill_rollback_ready",
            "source_summary": build_source_summary(),
            "scenario_count": len(scenarios),
            "rollback_playbook_count": rollback_package["playbook_count"],
            "scenarios": scenarios,
            "rollback_package": rollback_package,
            "acceptance_requirements": {
                "scenario_count_at_least": 5,
                "all_blocked": True,
                "recovered_mode": MODE,
                "real_trigger": False,
                "webhook_enabled": False,
                "error_count": 0,
            },
            "error_count": 0,
        }
    )


def build_package_md(package: dict[str, Any]) -> str:
    lines = [
        "# n8n 离线闸口失败演练与回滚剧本包",
        "",
        f"- 生成时间：{package['generated_at']}",
        f"- 状态：{package['status']}",
        f"- 场景数：{package['scenario_count']}",
        f"- 回滚剧本数：{package['rollback_playbook_count']}",
        "- 模式：offline/dry_run",
        "- real_trigger：false",
        "- webhook_enabled：false",
        "",
        "| 场景 | 检测结果 | 阻断闸口 | 恢复后状态 |",
        "| --- | --- | --- | --- |",
    ]
    for item in package["scenarios"]:
        gates = "、".join(f"{gate['gate_id']} {gate['gate_name']}" for gate in item["blocking_gates"])
        lines.append(
            f"| {item['scenario_id']} {item['scenario_name']} | "
            f"{item['detection_result']['decision']} | {gates} | "
            f"{item['recovery_after_state']['status']} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_rollback_md(rollback_package: dict[str, Any]) -> str:
    lines = [
        "# n8n 离线闸口失败演练回滚剧本",
        "",
        f"- 生成时间：{rollback_package['generated_at']}",
        f"- 剧本数：{rollback_package['playbook_count']}",
        "- 执行方式：documented_local_recovery_only",
        "- real_trigger：false",
        "- webhook_enabled：false",
        "",
    ]
    for playbook in rollback_package["playbooks"]:
        lines.append(f"## {playbook['playbook_id']} {playbook['title']}")
        for step in playbook["steps"]:
            lines.append(f"- {step['step_id']}：{step['title']}；{step['operation']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    scenarios = build_scenarios()
    rollback_package = build_rollback_package(scenarios)
    package = build_package(scenarios, rollback_package)
    write_json(SCENARIOS_JSON, guard_copy({"scenario_count": len(scenarios), "scenarios": scenarios, "error_count": 0}))
    write_json(ROLLBACK_JSON, rollback_package)
    write_text(ROLLBACK_MD, build_rollback_md(rollback_package))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, build_package_md(package))
    print(
        json.dumps(
            {
                "status": package["status"],
                "scenario_count": package["scenario_count"],
                "rollback_playbook_count": package["rollback_playbook_count"],
                "error_count": package["error_count"],
                "output": str(PACKAGE_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
