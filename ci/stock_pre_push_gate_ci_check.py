#!/usr/bin/env python3
"""Read-only pre-push gate closure check for the stock system.

This gate narrows the consolidation index to the `pre_push_gate` lane. It keeps
push drafts, manual confirmations, whitelist/frequency controls, and dry-run
samples visible as review assets only. It never sends messages or calls any
external workflow.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

try:
    from ci import stock_closure_panel_ci_check as closure_panel
    from ci import stock_consolidation_index_ci_check as consolidation
except ModuleNotFoundError:  # Running as `python ci/stock_pre_push_gate_ci_check.py`.
    import stock_closure_panel_ci_check as closure_panel  # type: ignore[no-redef]
    import stock_consolidation_index_ci_check as consolidation  # type: ignore[no-redef]


OWNER_LANE = "pre_push_gate"
EXPECTED_TOPIC_TARGETS = {"推送"}
MIN_TOPIC_COUNT = 15
EXPECTED_SAMPLE_ROLES = {
    "domain_artifact",
    "draft_or_template",
    "execution_artifact",
}
REQUIRED_SAMPLE_TERMS = ["dry-run", "白名单", "确认"]
GUARDRAILS = [
    "read_only_pre_push_gate_check",
    "no_business_file_write",
    "no_external_service_call",
    "no_real_send_or_n8n_or_webhook",
]


def pre_push_lane(panel: dict[str, Any]) -> dict[str, Any] | None:
    for lane in panel.get("lanes", []):
        if lane.get("owner_lane") == OWNER_LANE:
            return lane
    return None


def pre_push_topic_workstreams(index: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in index.get("topic_index", [])
        if item.get("owner_lane") == OWNER_LANE
    ]


def pre_push_next_queue(index: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in index.get("next_queue", [])
        if item.get("owner_lane") == OWNER_LANE
    ]


def topic_sample_roles(topic: dict[str, Any]) -> set[str]:
    return {item.get("role", "") for item in topic.get("sample", []) if item.get("role")}


def topic_sample_names(topic: dict[str, Any]) -> list[str]:
    return [item.get("name", "") for item in topic.get("sample", []) if item.get("name")]


def validate_report(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    problems.extend(report.get("index_blocking_problems", []))
    problems.extend(report.get("panel_blocking_problems", []))

    lane = report.get("lane")
    if not lane:
        problems.append("missing_pre_push_gate_lane")
    elif lane.get("queue_count", 0) < 1:
        problems.append(f"pre_push_gate_queue_too_small:{lane.get('queue_count', 0)}")

    topic_targets = {item.get("term") for item in report.get("topic_workstreams", [])}
    for target in sorted(EXPECTED_TOPIC_TARGETS):
        if target not in topic_targets:
            problems.append(f"missing_pre_push_topic:{target}")

    for topic in report.get("topic_workstreams", []):
        term = topic.get("term", "-")
        if topic.get("count", 0) < MIN_TOPIC_COUNT:
            problems.append(f"pre_push_topic_count_too_small:{term}:{topic.get('count', 0)}")
        missing_roles = EXPECTED_SAMPLE_ROLES - topic_sample_roles(topic)
        for role in sorted(missing_roles):
            problems.append(f"missing_pre_push_sample_role:{term}:{role}")
        names = topic_sample_names(topic)
        for required in REQUIRED_SAMPLE_TERMS:
            if not any(required in name for name in names):
                problems.append(f"missing_pre_push_sample_term:{term}:{required}")

    next_queue_targets = {item.get("target") for item in report.get("next_queue", [])}
    for target in sorted(EXPECTED_TOPIC_TARGETS):
        if target not in next_queue_targets:
            problems.append(f"missing_pre_push_next_queue:{target}")

    for guardrail in GUARDRAILS:
        if guardrail not in report.get("guardrails", []):
            problems.append(f"missing_guardrail:{guardrail}")

    return problems


def build_pre_push_gate_report() -> dict[str, Any]:
    index = consolidation.build_consolidation_index()
    panel = closure_panel.build_closure_panel()
    report = {
        "name": "stock_pre_push_gate_closure",
        "owner_lane": OWNER_LANE,
        "lane": pre_push_lane(panel),
        "next_queue": pre_push_next_queue(index),
        "topic_workstreams": pre_push_topic_workstreams(index),
        "expected_topic_targets": sorted(EXPECTED_TOPIC_TARGETS),
        "expected_sample_roles": sorted(EXPECTED_SAMPLE_ROLES),
        "required_sample_terms": REQUIRED_SAMPLE_TERMS,
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
        "# Stock Pre-Push Gate Closure",
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
        required_terms = ", ".join(report["required_sample_terms"])
        lines.append(
            f"- `{item['term']}`: count={item.get('count', 0)}; "
            f"action={item.get('action', '-')}; roles={roles}; required_terms={required_terms}"
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

    report = build_pre_push_gate_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))

    if report["ci_gate_status"] != "pass":
        print("FAIL: stock pre-push gate closure found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
