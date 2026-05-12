# -*- coding: utf-8 -*-
"""执行 n8n 离线干跑多场景回归。

只读取第78包内置场景，不连接 n8n，不启用 webhook，不请求网络，
不改配置，不重载服务，不真实发送企业微信。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "78n8n离线干跑多场景回归与闸口矩阵包"

PACKAGE_JSON = DATA_DIR / "n8n离线干跑多场景回归与闸口矩阵包_最新.json"
SCENARIOS_JSON = DATA_DIR / "n8n离线干跑多场景回归场景_最新.json"
GATE_MATRIX_JSON = DATA_DIR / "n8n离线干跑闸口矩阵_最新.json"
DRYRUN_JSON = DATA_DIR / "n8n离线干跑多场景回归报告_最新.json"
DRYRUN_MD = DATA_DIR / "n8n离线干跑多场景回归报告_最新.md"

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


def simulate_node(scenario_item: dict[str, Any], node_item: dict[str, Any], sequence: int) -> dict[str, Any]:
    status = node_item.get("status", "ready")
    blocked = status == "blocked"
    return guard_copy(
        {
            "scenario_id": scenario_item.get("scenario_id", ""),
            "scenario_name": scenario_item.get("scenario_name", ""),
            "sequence": sequence,
            "node_id": node_item.get("node_id", ""),
            "node_name": node_item.get("node_name", ""),
            "status": status,
            "ready": not blocked,
            "blocked": blocked,
            "dry_run_result": node_item.get("dry_run_result", ""),
            "simulated_input": {
                "input_kind": scenario_item.get("input_kind", "本包内置离线样本"),
                "previous_step_only": True,
            },
            "simulated_output": {
                "candidate": node_item.get("dry_run_result", ""),
                "kept_local": True,
                "requires_supervisor": blocked or "G08" in scenario_item.get("blocking_gates", []),
            },
            "blocked_reason": "命中离线闸口，停止在本地 dry_run 结果" if blocked else "",
            "error_count": 0,
        }
    )


def simulate_scenario(scenario_item: dict[str, Any]) -> dict[str, Any]:
    node_results = [
        simulate_node(scenario_item, node_item, index)
        for index, node_item in enumerate(scenario_item.get("nodes", []), start=1)
    ]
    blocked = bool(scenario_item.get("blocking_gates"))
    return guard_copy(
        {
            "scenario_id": scenario_item.get("scenario_id", ""),
            "scenario_name": scenario_item.get("scenario_name", ""),
            "category": scenario_item.get("category", ""),
            "status": "pass",
            "final_status": scenario_item.get("final_status", "ready"),
            "blocked": blocked,
            "blocking_gates": scenario_item.get("blocking_gates", []),
            "dry_run_node_results": node_results,
            "node_count": len(node_results),
            "expected_candidate": scenario_item.get("expected_candidate", ""),
            "error_count": 0,
        }
    )


def build_report(scenarios: list[dict[str, Any]], source_ref: str) -> dict[str, Any]:
    errors: list[str] = []
    scenario_runs = [simulate_scenario(item) for item in scenarios]
    if len(scenario_runs) < 5:
        errors.append("场景数少于5")
    if any(not item.get("dry_run_node_results") for item in scenario_runs):
        errors.append("存在空节点结果场景")
    return guard_copy(
        {
            "name": "n8n离线干跑多场景回归报告",
            "executed_at": now_text(),
            "source_ref": source_ref,
            "status": "pass" if not errors else "blocked",
            "scenario_count": len(scenario_runs),
            "scenario_runs": scenario_runs,
            "final_status_summary": {
                item["scenario_id"]: item["final_status"] for item in scenario_runs
            },
            "blocking_gate_summary": {
                item["scenario_id"]: item["blocking_gates"] for item in scenario_runs
            },
            "metrics": {
                "scenario_count": len(scenario_runs),
                "node_result_count": sum(item["node_count"] for item in scenario_runs),
                "blocked_scenario_count": sum(1 for item in scenario_runs if item["blocked"]),
                "real_trigger_count": 0,
                "webhook_enabled_count": 0,
            },
            "errors": errors,
            "error_count": len(errors),
        }
    )


def build_md(report: dict[str, Any]) -> str:
    lines = [
        "# n8n 离线干跑多场景回归报告",
        "",
        f"- 执行时间：{report['executed_at']}",
        f"- 状态：{report['status']}",
        f"- 场景数：{report['scenario_count']}",
        f"- 节点结果数：{report['metrics']['node_result_count']}",
        f"- error_count：{report['error_count']}",
        "- 模式：offline/dry_run",
        "- 真实触发：false",
        "- webhook_enabled：false",
        "",
        "| 场景 | 最终状态 | 阻断闸口 | dry_run 节点结果 |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["scenario_runs"]:
        nodes = "；".join(
            f"{node['node_id']}={node['status']}:{node['dry_run_result']}"
            for node in item["dry_run_node_results"]
        )
        gates = "、".join(item["blocking_gates"])
        lines.append(f"| {item['scenario_id']} {item['scenario_name']} | {item['final_status']} | {gates} | {nodes} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    scenarios, source_ref = load_scenarios()
    report = build_report(scenarios, source_ref)
    write_json(DRYRUN_JSON, report)
    write_text(DRYRUN_MD, build_md(report))
    print(
        json.dumps(
            {
                "status": report["status"],
                "scenario_count": report["scenario_count"],
                "error_count": report["error_count"],
                "output": str(DRYRUN_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
