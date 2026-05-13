#!/usr/bin/env python3
"""Read-only safe-boundary closure check for the stock system.

This gate keeps delivery acceptance and auto-trade blocking evidence tied
together before stock-system construction continues. It only reads the
consolidation index and closure panel; it does not call external systems,
start services, send messages, or modify business files.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

try:
    from ci import stock_closure_panel_ci_check as closure_panel
    from ci import stock_consolidation_index_ci_check as consolidation
except ModuleNotFoundError:  # Running as `python ci/stock_safe_boundary_ci_check.py`.
    import stock_closure_panel_ci_check as closure_panel  # type: ignore[no-redef]
    import stock_consolidation_index_ci_check as consolidation  # type: ignore[no-redef]


OWNER_LANE = "safe_boundary"
EXPECTED_DUPLICATE_TARGETS = {"243"}
EXPECTED_TOPIC_TARGETS = {"\u9a8c\u6536"}
MIN_TOPIC_COUNT = 10
EXPECTED_DUPLICATE_ROLES = {
    "domain_artifact",
    "parent_or_index_candidate",
}
EXPECTED_TOPIC_ROLES = {"parent_or_index_candidate"}
REQUIRED_MERGE_PRECONDITIONS = [
    "preserve_auto_trade_blocking_evidence",
    "do_not_enable_any_external_action",
]
REQUIRED_POLICY_TERMS = [
    "delivery_status",
    "auto_trade_block",
    "safety_child",
]
GUARDRAILS = [
    "read_only_safe_boundary_check",
    "no_business_file_write",
    "no_external_service_call",
    "no_real_send_or_n8n_or_webhook",
    "no_auto_trade_or_broker_interface",
]


def safe_lane(panel: dict[str, Any]) -> dict[str, Any] | None:
    for lane in panel.get("lanes", []):
        if lane.get("owner_lane") == OWNER_LANE:
            return lane
    return None


def safe_duplicate_workstreams(index: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in index.get("duplicate_index", [])
        if item.get("owner_lane") == OWNER_LANE
    ]


def safe_topic_workstreams(index: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in index.get("topic_index", [])
        if item.get("owner_lane") == OWNER_LANE
    ]


def safe_next_queue(index: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in index.get("next_queue", [])
        if item.get("owner_lane") == OWNER_LANE
    ]


def duplicate_directory_roles(item: dict[str, Any]) -> set[str]:
    return {
        directory.get("role", "")
        for directory in item.get("directories", [])
        if directory.get("role")
    }


def duplicate_directory_names(item: dict[str, Any]) -> list[str]:
    return [
        directory.get("name", "")
        for directory in item.get("directories", [])
        if directory.get("name")
    ]


def topic_sample_roles(topic: dict[str, Any]) -> set[str]:
    return {item.get("role", "") for item in topic.get("sample", []) if item.get("role")}


def validate_report(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    problems.extend(report.get("index_blocking_problems", []))
    problems.extend(report.get("panel_blocking_problems", []))

    lane = report.get("lane")
    if not lane:
        problems.append("missing_safe_boundary_lane")
    elif lane.get("queue_count", 0) < 1:
        problems.append(f"safe_boundary_queue_too_small:{lane.get('queue_count', 0)}")

    duplicate_targets = {item.get("number") for item in report.get("duplicate_workstreams", [])}
    for target in sorted(EXPECTED_DUPLICATE_TARGETS):
        if target not in duplicate_targets:
            problems.append(f"missing_safe_duplicate:{target}")

    for item in report.get("duplicate_workstreams", []):
        number = item.get("number", "-")
        missing_roles = EXPECTED_DUPLICATE_ROLES - duplicate_directory_roles(item)
        for role in sorted(missing_roles):
            problems.append(f"missing_safe_duplicate_role:{number}:{role}")

        preconditions = set(item.get("merge_preconditions", []))
        for precondition in REQUIRED_MERGE_PRECONDITIONS:
            if precondition not in preconditions:
                problems.append(f"missing_safe_precondition:{number}:{precondition}")

        policy = item.get("policy", "")
        for term in REQUIRED_POLICY_TERMS:
            if term not in policy:
                problems.append(f"missing_safe_policy_term:{number}:{term}")

    topic_targets = {item.get("term") for item in report.get("topic_workstreams", [])}
    for target in sorted(EXPECTED_TOPIC_TARGETS):
        if target not in topic_targets:
            problems.append(f"missing_safe_topic:{target}")

    for topic in report.get("topic_workstreams", []):
        term = topic.get("term", "-")
        if topic.get("count", 0) < MIN_TOPIC_COUNT:
            problems.append(f"safe_topic_count_too_small:{term}:{topic.get('count', 0)}")
        missing_roles = EXPECTED_TOPIC_ROLES - topic_sample_roles(topic)
        for role in sorted(missing_roles):
            problems.append(f"missing_safe_topic_role:{term}:{role}")

    next_queue_targets = {item.get("target") for item in report.get("next_queue", [])}
    for target in sorted(EXPECTED_DUPLICATE_TARGETS):
        if target not in next_queue_targets:
            problems.append(f"missing_safe_next_queue:{target}")

    for guardrail in GUARDRAILS:
        if guardrail not in report.get("guardrails", []):
            problems.append(f"missing_guardrail:{guardrail}")

    return problems


def build_safe_boundary_report() -> dict[str, Any]:
    index = consolidation.build_consolidation_index()
    panel = closure_panel.build_closure_panel()
    report = {
        "name": "stock_safe_boundary_closure",
        "owner_lane": OWNER_LANE,
        "lane": safe_lane(panel),
        "next_queue": safe_next_queue(index),
        "duplicate_workstreams": safe_duplicate_workstreams(index),
        "topic_workstreams": safe_topic_workstreams(index),
        "expected_duplicate_targets": sorted(EXPECTED_DUPLICATE_TARGETS),
        "expected_topic_targets": sorted(EXPECTED_TOPIC_TARGETS),
        "expected_duplicate_roles": sorted(EXPECTED_DUPLICATE_ROLES),
        "expected_topic_roles": sorted(EXPECTED_TOPIC_ROLES),
        "required_merge_preconditions": REQUIRED_MERGE_PRECONDITIONS,
        "required_policy_terms": REQUIRED_POLICY_TERMS,
        "index_blocking_problems": index.get("blocking_problems", []),
        "panel_blocking_problems": panel.get("blocking_problems", []),
        "guardrails": GUARDRAILS,
    }
    problems = validate_report(report)
    report["ci_gate_status"] = "fail" if problems else "pass"
    report["blocking_problems"] = problems
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lane = report.get("lane") or {}
    lines = [
        "# Stock Safe Boundary Closure",
        "",
        f"- CI gate: `{report['ci_gate_status']}`",
        f"- Owner lane: `{report['owner_lane']}`",
        (
            "- Lane summary: "
            f"queue={lane.get('queue_count', 0)}, "
            f"duplicates={lane.get('duplicate_count', 0)}, "
            f"preconditions={lane.get('precondition_count', 0)}, "
            f"action={lane.get('next_action', '-')}"
        ),
        "",
        "## Duplicate Workstreams",
    ]
    for item in report["duplicate_workstreams"]:
        roles = ", ".join(sorted(duplicate_directory_roles(item)))
        names = ", ".join(duplicate_directory_names(item))
        preconditions = ", ".join(item.get("merge_preconditions", []))
        lines.append(
            f"- `{item['number']}`: count={item.get('count', 0)}; "
            f"action={item.get('action', '-')}; roles={roles}; "
            f"preconditions={preconditions}; directories={names}"
        )

    lines.extend(["", "## Topic Workstreams"])
    for item in report["topic_workstreams"]:
        roles = ", ".join(sorted(topic_sample_roles(item)))
        lines.append(
            f"- `{item['term']}`: count={item.get('count', 0)}; "
            f"action={item.get('action', '-')}; roles={roles}"
        )

    lines.extend(["", "## Next Queue"])
    for item in report["next_queue"]:
        lines.append(f"- `{item['kind']}` `{item['target']}`: {item.get('action', '-')}")

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

    report = build_safe_boundary_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))

    if report["ci_gate_status"] != "pass":
        print("FAIL: stock safe boundary closure found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
