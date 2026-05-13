#!/usr/bin/env python3
"""Read-only manual-review closure check for the stock system.

This gate narrows the consolidation index to the `manual_review` lane. It
checks that manual verification has visible queue ownership and enough workflow
shape before any construction work tries to consolidate related assets.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

try:
    from ci import stock_closure_panel_ci_check as closure_panel
    from ci import stock_consolidation_index_ci_check as consolidation
except ModuleNotFoundError:  # Running as `python ci/stock_manual_review_ci_check.py`.
    import stock_closure_panel_ci_check as closure_panel  # type: ignore[no-redef]
    import stock_consolidation_index_ci_check as consolidation  # type: ignore[no-redef]


OWNER_LANE = "manual_review"
EXPECTED_TOPIC_TARGETS = {"人工核验"}
MIN_TOPIC_COUNT = 10
EXPECTED_SAMPLE_ROLES = {
    "domain_artifact",
    "parent_or_index_candidate",
    "draft_or_template",
    "execution_artifact",
}
GUARDRAILS = [
    "read_only_manual_review_check",
    "no_business_file_write",
    "no_external_service_call",
    "no_real_send_or_n8n_or_webhook",
]


def manual_lane(panel: dict[str, Any]) -> dict[str, Any] | None:
    for lane in panel.get("lanes", []):
        if lane.get("owner_lane") == OWNER_LANE:
            return lane
    return None


def manual_topic_workstreams(index: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in index.get("topic_index", [])
        if item.get("owner_lane") == OWNER_LANE
    ]


def manual_next_queue(index: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in index.get("next_queue", [])
        if item.get("owner_lane") == OWNER_LANE
    ]


def topic_sample_roles(topic: dict[str, Any]) -> set[str]:
    return {item.get("role", "") for item in topic.get("sample", []) if item.get("role")}


def validate_report(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    problems.extend(report.get("index_blocking_problems", []))
    problems.extend(report.get("panel_blocking_problems", []))

    lane = report.get("lane")
    if not lane:
        problems.append("missing_manual_review_lane")
    elif lane.get("queue_count", 0) < 1:
        problems.append(f"manual_review_queue_too_small:{lane.get('queue_count', 0)}")

    topic_targets = {item.get("term") for item in report.get("topic_workstreams", [])}
    for target in sorted(EXPECTED_TOPIC_TARGETS):
        if target not in topic_targets:
            problems.append(f"missing_manual_topic:{target}")

    for topic in report.get("topic_workstreams", []):
        term = topic.get("term", "-")
        if topic.get("count", 0) < MIN_TOPIC_COUNT:
            problems.append(f"manual_topic_count_too_small:{term}:{topic.get('count', 0)}")
        missing_roles = EXPECTED_SAMPLE_ROLES - topic_sample_roles(topic)
        for role in sorted(missing_roles):
            problems.append(f"missing_manual_sample_role:{term}:{role}")

    next_queue_targets = {item.get("target") for item in report.get("next_queue", [])}
    for target in sorted(EXPECTED_TOPIC_TARGETS):
        if target not in next_queue_targets:
            problems.append(f"missing_manual_next_queue:{target}")

    for guardrail in GUARDRAILS:
        if guardrail not in report.get("guardrails", []):
            problems.append(f"missing_guardrail:{guardrail}")

    return problems


def build_manual_review_report() -> dict[str, Any]:
    index = consolidation.build_consolidation_index()
    panel = closure_panel.build_closure_panel()
    report = {
        "name": "stock_manual_review_closure",
        "owner_lane": OWNER_LANE,
        "lane": manual_lane(panel),
        "next_queue": manual_next_queue(index),
        "topic_workstreams": manual_topic_workstreams(index),
        "expected_topic_targets": sorted(EXPECTED_TOPIC_TARGETS),
        "expected_sample_roles": sorted(EXPECTED_SAMPLE_ROLES),
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
        "# Stock Manual Review Closure",
        "",
        f"- CI gate: `{report['ci_gate_status']}`",
        f"- Owner lane: `{report['owner_lane']}`",
        (
            "- Lane summary: "
            f"queue={lane.get('queue_count', 0)}, "
            f"topics={lane.get('topic_count', 0)}, "
            f"action={lane.get('next_action', '-')}"
        ),
        "",
        "## Topic Workstreams",
    ]
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

    report = build_manual_review_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))

    if report["ci_gate_status"] != "pass":
        print("FAIL: stock manual review closure found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
