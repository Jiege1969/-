#!/usr/bin/env python3
"""Read-only quality-evidence closure check for the stock system.

This gate narrows the closure panel to its largest current lane:
`quality_evidence`. It verifies that duplicate numbers and topic overlaps are
owned by the same lane before any human construction work tries to merge,
rename, or optimize the underlying business materials.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

try:
    from ci import stock_closure_panel_ci_check as closure_panel
    from ci import stock_consolidation_index_ci_check as consolidation
except ModuleNotFoundError:  # Running as `python ci/stock_quality_evidence_ci_check.py`.
    import stock_closure_panel_ci_check as closure_panel  # type: ignore[no-redef]
    import stock_consolidation_index_ci_check as consolidation  # type: ignore[no-redef]


OWNER_LANE = "quality_evidence"
EXPECTED_DUPLICATE_TARGETS = {"149", "186", "195"}
MIN_NEXT_QUEUE_COUNT = 5
GUARDRAILS = [
    "read_only_quality_evidence_check",
    "no_business_file_write",
    "no_external_service_call",
    "no_real_send_or_n8n_or_webhook",
]


def expected_topic_targets() -> set[str]:
    return {
        term
        for term, owner_lane in consolidation.TOPIC_OWNER_LANES.items()
        if owner_lane == OWNER_LANE
    }


def quality_lane(panel: dict[str, Any]) -> dict[str, Any] | None:
    for lane in panel.get("lanes", []):
        if lane.get("owner_lane") == OWNER_LANE:
            return lane
    return None


def quality_duplicate_workstreams(index: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in index.get("duplicate_index", [])
        if item.get("owner_lane") == OWNER_LANE
    ]


def quality_topic_workstreams(index: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in index.get("topic_index", [])
        if item.get("owner_lane") == OWNER_LANE
    ]


def quality_next_queue(index: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in index.get("next_queue", [])
        if item.get("owner_lane") == OWNER_LANE
    ]


def validate_report(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    problems.extend(report.get("index_blocking_problems", []))
    problems.extend(report.get("panel_blocking_problems", []))

    lane = report.get("lane")
    if not lane:
        problems.append("missing_quality_evidence_lane")
    elif lane.get("queue_count", 0) < MIN_NEXT_QUEUE_COUNT:
        problems.append(f"quality_evidence_queue_too_small:{lane.get('queue_count', 0)}")

    duplicate_targets = {item.get("number") for item in report.get("duplicate_workstreams", [])}
    for target in sorted(EXPECTED_DUPLICATE_TARGETS):
        if target not in duplicate_targets:
            problems.append(f"missing_quality_duplicate:{target}")

    for item in report.get("duplicate_workstreams", []):
        number = item.get("number", "-")
        if not item.get("policy"):
            problems.append(f"missing_quality_duplicate_policy:{number}")
        if not item.get("merge_preconditions"):
            problems.append(f"missing_quality_duplicate_preconditions:{number}")

    topic_targets = {item.get("term") for item in report.get("topic_workstreams", [])}
    for target in sorted(expected_topic_targets()):
        if target not in topic_targets:
            problems.append(f"missing_quality_topic:{target}")

    next_queue = report.get("next_queue", [])
    if not next_queue:
        problems.append("missing_quality_next_queue")

    for guardrail in GUARDRAILS:
        if guardrail not in report.get("guardrails", []):
            problems.append(f"missing_guardrail:{guardrail}")

    return problems


def build_quality_evidence_report() -> dict[str, Any]:
    index = consolidation.build_consolidation_index()
    panel = closure_panel.build_closure_panel()
    report = {
        "name": "stock_quality_evidence_closure",
        "owner_lane": OWNER_LANE,
        "lane": quality_lane(panel),
        "next_queue": quality_next_queue(index),
        "duplicate_workstreams": quality_duplicate_workstreams(index),
        "topic_workstreams": quality_topic_workstreams(index),
        "expected_duplicate_targets": sorted(EXPECTED_DUPLICATE_TARGETS),
        "expected_topic_targets": sorted(expected_topic_targets()),
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
        "# Stock Quality Evidence Closure",
        "",
        f"- CI gate: `{report['ci_gate_status']}`",
        f"- Owner lane: `{report['owner_lane']}`",
        (
            "- Lane summary: "
            f"queue={lane.get('queue_count', 0)}, "
            f"duplicates={lane.get('duplicate_count', 0)}, "
            f"topics={lane.get('topic_count', 0)}, "
            f"preconditions={lane.get('precondition_count', 0)}, "
            f"action={lane.get('next_action', '-')}"
        ),
        "",
        "## Duplicate Workstreams",
    ]
    for item in report["duplicate_workstreams"]:
        preconditions = ", ".join(item.get("merge_preconditions", []))
        lines.append(
            f"- `{item['number']}`: policy={item.get('policy', '-')}; "
            f"action={item.get('action', '-')}; preconditions={preconditions}"
        )

    lines.extend(["", "## Topic Workstreams"])
    for item in report["topic_workstreams"]:
        lines.append(
            f"- `{item['term']}`: count={item.get('count', 0)}; "
            f"action={item.get('action', '-')}"
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

    report = build_quality_evidence_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))

    if report["ci_gate_status"] != "pass":
        print("FAIL: stock quality evidence closure found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
