#!/usr/bin/env python3
"""Read-only task queue for the stock sample-room construction flow.

The overview script tells us what exists. This script turns that understanding
into a safe, ordered work queue:
- every lane keeps its existing contract;
- dependencies are explicit;
- each task points back to an existing CI gate;
- no services, webhooks, brokers, or real send paths are touched.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


QUEUE_ORDER = [
    "safe_boundary",
    "sample_pool",
    "quality_evidence",
    "manual_review",
    "pre_push_gate",
    "review_loop",
]

LANE_DEPENDENCIES = {
    "safe_boundary": [],
    "sample_pool": [],
    "quality_evidence": ["sample_pool", "safe_boundary"],
    "manual_review": ["sample_pool", "quality_evidence", "safe_boundary"],
    "pre_push_gate": ["sample_pool", "quality_evidence", "manual_review", "safe_boundary"],
    "review_loop": ["quality_evidence", "pre_push_gate", "safe_boundary"],
}

LANE_CHECKS = {
    "safe_boundary": "python ci/stock_safe_boundary_ci_check.py",
    "sample_pool": "python ci/stock_sample_pool_ci_check.py",
    "quality_evidence": "python ci/stock_quality_evidence_ci_check.py",
    "manual_review": "python ci/stock_manual_review_ci_check.py",
    "pre_push_gate": "python ci/stock_pre_push_gate_ci_check.py",
    "review_loop": "python ci/stock_review_loop_ci_check.py",
}

ALLOWED_SCOPE = "local_code_tests_docs_ci_only"
PROHIBITED_ACTIONS = [
    "real_send",
    "n8n",
    "webhook",
    "broker_interface",
    "auto_trade",
    "service_restart",
]


def load_overview_module():
    path = Path(__file__).with_name("stock_sample_room_overview.py")
    spec = importlib.util.spec_from_file_location("stock_sample_room_overview", path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"cannot load overview module: {path}")
    spec.loader.exec_module(module)
    return module


def priority_for_status(status: str) -> str:
    if status == "blocked":
        return "P0"
    if status == "review":
        return "P1"
    return "P2"


def mode_for_priority(priority: str) -> str:
    return {
        "P0": "stop_and_fix_before_any_new_work",
        "P1": "review_then_continue",
        "P2": "continue_under_contract",
    }[priority]


def dependency_state(lane_by_name: dict[str, dict[str, Any]], dependencies: list[str]) -> str:
    missing = [name for name in dependencies if name not in lane_by_name]
    if missing:
        return "missing_dependency"
    blocked = [name for name in dependencies if lane_by_name[name]["status"] == "blocked"]
    if blocked:
        return "blocked_dependency"
    review = [name for name in dependencies if lane_by_name[name]["status"] == "review"]
    if review:
        return "review_dependency"
    return "ready"


def build_task(lane: dict[str, Any], lane_by_name: dict[str, dict[str, Any]]) -> dict[str, Any]:
    name = lane["name"]
    dependencies = LANE_DEPENDENCIES.get(name, [])
    dep_state = dependency_state(lane_by_name, dependencies)
    priority = priority_for_status(lane["status"])
    return {
        "lane": name,
        "position": lane["position"],
        "status": lane["status"],
        "priority": priority,
        "mode": mode_for_priority(priority),
        "ready_state": dep_state,
        "ready": lane["status"] != "blocked" and dep_state in {"ready", "review_dependency"},
        "dependencies": dependencies,
        "evidence_summary": {
            "scripts": lane["script_count"],
            "data": lane["data_count"],
            "docs": lane["doc_count"],
            "total": lane["evidence_count"],
        },
        "next_action": lane["next_action"],
        "acceptance_check": LANE_CHECKS.get(name, "python ci/stock_acceptance_overview_ci_check.py"),
        "allowed_scope": ALLOWED_SCOPE,
        "prohibited_actions": PROHIBITED_ACTIONS,
    }


def validate_queue(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    lanes = [task["lane"] for task in report.get("tasks", [])]
    if lanes != QUEUE_ORDER:
        problems.append("queue_order_changed")
    if len(lanes) != len(set(lanes)):
        problems.append("duplicate_lane_task")
    for required in QUEUE_ORDER:
        if required not in lanes:
            problems.append(f"missing_lane_task:{required}")
    for task in report.get("tasks", []):
        for key in ("lane", "priority", "mode", "ready_state", "acceptance_check", "allowed_scope"):
            if not task.get(key):
                problems.append(f"task_missing:{task.get('lane', 'unknown')}:{key}")
        if task["allowed_scope"] != ALLOWED_SCOPE:
            problems.append(f"unsafe_scope:{task['lane']}")
        for action in PROHIBITED_ACTIONS:
            if action not in task.get("prohibited_actions", []):
                problems.append(f"missing_prohibited_action:{task['lane']}:{action}")
        for dependency in task.get("dependencies", []):
            if dependency not in lanes:
                problems.append(f"unknown_dependency:{task['lane']}:{dependency}")
    if not all(value is False for value in report.get("safety_flags", {}).values()):
        problems.append("safety_flag_enabled")
    return problems


def build_task_queue(root: Path | None = None, overview_report: dict[str, Any] | None = None) -> dict[str, Any]:
    overview = load_overview_module()
    overview_report = overview_report or overview.build_overview(root)
    lane_by_name = {lane["name"]: lane for lane in overview_report["lanes"]}
    tasks = [build_task(lane_by_name[name], lane_by_name) for name in QUEUE_ORDER if name in lane_by_name]
    report = {
        "name": "stock_sample_room_task_queue",
        "source_overview": overview_report["name"],
        "overview_state": overview_report["overview_state"],
        "task_count": len(tasks),
        "tasks": tasks,
        "safety_flags": overview_report["safety_flags"],
        "guardrails": [
            "read_only_by_default",
            "reuse_sample_room_overview",
            "explicit_dependencies",
            "existing_ci_acceptance_checks",
            "no_external_service_call",
            "no_real_send_n8n_webhook_broker_or_auto_trade",
        ],
    }
    problems = validate_queue(report)
    report["queue_state"] = "blocked" if problems else "ready"
    report["blocking_problems"] = problems
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stock Sample Room Task Queue",
        "",
        f"- Queue state: `{report['queue_state']}`",
        f"- Overview state: `{report['overview_state']}`",
        f"- Task count: `{report['task_count']}`",
        "",
        "## Tasks",
    ]
    for task in report["tasks"]:
        evidence = task["evidence_summary"]
        lines.append(
            "- "
            f"`{task['priority']}` `{task['lane']}`: status={task['status']}; "
            f"ready={str(task['ready']).lower()}; deps={','.join(task['dependencies']) or 'none'}; "
            f"evidence=scripts:{evidence['scripts']}/data:{evidence['data']}/docs:{evidence['docs']}; "
            f"check=`{task['acceptance_check']}`; next={task['next_action']}"
        )
    lines.extend(["", "## Guardrails"])
    for guardrail in report["guardrails"]:
        lines.append(f"- `{guardrail}`")
    if report["blocking_problems"]:
        lines.extend(["", "## Blocking Problems"])
        for problem in report["blocking_problems"]:
            lines.append(f"- `{problem}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    args = parser.parse_args()

    report = build_task_queue()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["queue_state"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
