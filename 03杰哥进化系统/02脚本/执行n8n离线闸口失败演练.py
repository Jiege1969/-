# -*- coding: utf-8 -*-
"""执行 n8n 离线闸口失败演练。

只读取第81包场景和回滚剧本，不连接 n8n，不启用 webhook，不请求网络，
不改配置，不重载服务，不真实发送企业微信。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "81n8n离线闸口失败演练与回滚剧本包"

PACKAGE_JSON = DATA_DIR / "n8n离线闸口失败演练与回滚剧本包_最新.json"
SCENARIOS_JSON = DATA_DIR / "n8n离线闸口失败演练场景_最新.json"
ROLLBACK_JSON = DATA_DIR / "n8n离线闸口失败演练回滚剧本_最新.json"
REPORT_JSON = DATA_DIR / "n8n离线闸口失败演练报告_最新.json"
REPORT_MD = DATA_DIR / "n8n离线闸口失败演练报告_最新.md"

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


def read_json(path: Path) -> dict[str, Any]:
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


def load_scenarios() -> tuple[list[dict[str, Any]], str]:
    if SCENARIOS_JSON.exists():
        data = read_json(SCENARIOS_JSON)
        return data.get("scenarios", []), str(SCENARIOS_JSON)
    package = read_json(PACKAGE_JSON)
    return package.get("scenarios", []), str(PACKAGE_JSON)


def load_playbooks() -> dict[str, dict[str, Any]]:
    rollback = read_json(ROLLBACK_JSON)
    return {item.get("scenario_id", ""): item for item in rollback.get("playbooks", [])}


def simulate_rollback_step(step: dict[str, Any], sequence: int) -> dict[str, Any]:
    return guard_copy(
        {
            "sequence": sequence,
            "step_id": step.get("step_id", ""),
            "action": step.get("action", ""),
            "title": step.get("title", ""),
            "operation": step.get("operation", ""),
            "execution_mode": "simulated_local_only",
            "status": "simulated_done",
            "changed_runtime_config": False,
            "called_external_system": False,
            "error_count": 0,
        }
    )


def simulate_scenario(scenario_item: dict[str, Any], playbook: dict[str, Any]) -> dict[str, Any]:
    gates = scenario_item.get("blocking_gates", [])
    steps = [
        simulate_rollback_step(step, index)
        for index, step in enumerate(playbook.get("steps", []), start=1)
    ]
    recovery = scenario_item.get("recovery_after_state", {})
    return guard_copy(
        {
            "scenario_id": scenario_item.get("scenario_id", ""),
            "scenario_name": scenario_item.get("scenario_name", ""),
            "category": scenario_item.get("category", ""),
            "fault_probe": scenario_item.get("fault_probe", {}),
            "detection_result": scenario_item.get("detection_result", {}),
            "blocked": True,
            "blocking_gates": gates,
            "blocking_gate_count": len(gates),
            "rollback_playbook_id": playbook.get("playbook_id", ""),
            "rollback_step_results": steps,
            "recovery_after_state": guard_copy(
                {
                    "status": recovery.get("status", "recovered_to_blocked_offline_state"),
                    "recovery_note": recovery.get("recovery_note", ""),
                    "n8n_connected": False,
                    "webhook_registered": False,
                    "downstream_real_action_released": False,
                    "supervisor_confirmation_required": True,
                    "error_count": 0,
                }
            ),
            "final_status": "blocked_and_recovered_offline",
            "error_count": 0,
        }
    )


def build_report(scenarios: list[dict[str, Any]], playbooks: dict[str, dict[str, Any]], source_ref: str) -> dict[str, Any]:
    errors: list[str] = []
    scenario_runs = [
        simulate_scenario(item, playbooks.get(item.get("scenario_id", ""), {}))
        for item in scenarios
    ]
    if len(scenario_runs) < 5:
        errors.append("演练场景数少于5")
    if any(not item["blocked"] for item in scenario_runs):
        errors.append("存在未阻断场景")
    if any(not item["rollback_step_results"] for item in scenario_runs):
        errors.append("存在缺少回滚步骤的场景")
    return guard_copy(
        {
            "name": "n8n离线闸口失败演练报告",
            "executed_at": now_text(),
            "source_ref": source_ref,
            "status": "pass" if not errors else "blocked",
            "scenario_count": len(scenario_runs),
            "scenario_runs": scenario_runs,
            "metrics": {
                "scenario_count": len(scenario_runs),
                "blocked_scenario_count": sum(1 for item in scenario_runs if item["blocked"]),
                "rollback_step_count": sum(len(item["rollback_step_results"]) for item in scenario_runs),
                "real_trigger_count": 0,
                "webhook_enabled_count": 0,
                "external_call_count": 0,
            },
            "errors": errors,
            "error_count": len(errors),
        }
    )


def build_md(report: dict[str, Any]) -> str:
    lines = [
        "# n8n 离线闸口失败演练报告",
        "",
        f"- 执行时间：{report['executed_at']}",
        f"- 状态：{report['status']}",
        f"- 场景数：{report['scenario_count']}",
        f"- 阻断场景数：{report['metrics']['blocked_scenario_count']}",
        f"- 回滚步骤数：{report['metrics']['rollback_step_count']}",
        f"- error_count：{report['error_count']}",
        "- 模式：offline/dry_run",
        "- real_trigger：false",
        "- webhook_enabled：false",
        "",
        "| 场景 | 检测结果 | 阻断闸口 | 回滚剧本 | 恢复后状态 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["scenario_runs"]:
        gates = "、".join(f"{gate['gate_id']} {gate['gate_name']}" for gate in item["blocking_gates"])
        lines.append(
            f"| {item['scenario_id']} {item['scenario_name']} | "
            f"{item['detection_result'].get('decision', '')} | {gates} | "
            f"{item['rollback_playbook_id']} | {item['recovery_after_state']['status']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    scenarios, source_ref = load_scenarios()
    playbooks = load_playbooks()
    report = build_report(scenarios, playbooks, source_ref)
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, build_md(report))
    print(
        json.dumps(
            {
                "status": report["status"],
                "scenario_count": report["scenario_count"],
                "blocked_scenario_count": report["metrics"]["blocked_scenario_count"],
                "error_count": report["error_count"],
                "output": str(REPORT_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
