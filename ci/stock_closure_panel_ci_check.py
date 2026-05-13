#!/usr/bin/env python3
"""Read-only stock closure panel for CI and local construction planning.

The panel consumes the consolidation index and groups the next work queue by
owner lane. It turns "many findings" into a lane-by-lane closure board without
renaming, moving, deleting, sending, or calling any external service.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

try:
    from ci import stock_consolidation_index_ci_check as consolidation
except ModuleNotFoundError:  # Running as `python ci/stock_closure_panel_ci_check.py`.
    import stock_consolidation_index_ci_check as consolidation  # type: ignore[no-redef]


OWNER_LANES = [
    "sample_pool",
    "manual_review",
    "pre_push_gate",
    "review_loop",
    "quality_evidence",
    "safe_boundary",
    "stock_system_general",
]


def empty_lane_summary(owner_lane: str) -> dict[str, Any]:
    return {
        "owner_lane": owner_lane,
        "queue_count": 0,
        "duplicate_count": 0,
        "topic_count": 0,
        "precondition_count": 0,
        "targets": [],
        "next_action": "no_current_queue",
    }


def summarize_lanes(index: dict[str, Any]) -> list[dict[str, Any]]:
    lane_map = {owner_lane: empty_lane_summary(owner_lane) for owner_lane in OWNER_LANES}

    for item in index["next_queue"]:
        owner_lane = item.get("owner_lane") or "stock_system_general"
        lane = lane_map.setdefault(owner_lane, empty_lane_summary(owner_lane))
        lane["queue_count"] += 1
        if item["kind"] == "duplicate_number":
            lane["duplicate_count"] += 1
        elif item["kind"] == "semantic_overlap":
            lane["topic_count"] += 1
        lane["targets"].append(f"{item['kind']}:{item['target']}")

    duplicate_preconditions: dict[str, int] = {
        item["number"]: len(item.get("merge_preconditions", []))
        for item in index["duplicate_index"]
    }
    for lane in lane_map.values():
        for target in lane["targets"]:
            kind, value = target.split(":", 1)
            if kind == "duplicate_number":
                lane["precondition_count"] += duplicate_preconditions.get(value, 0)
        if lane["queue_count"]:
            if lane["duplicate_count"] and lane["topic_count"]:
                lane["next_action"] = "build_parent_index_then_review_duplicates"
            elif lane["duplicate_count"]:
                lane["next_action"] = "resolve_duplicate_number_ownership"
            else:
                lane["next_action"] = "build_topic_parent_index"

    return [lane for lane in lane_map.values() if lane["queue_count"] or lane["owner_lane"] in OWNER_LANES[:-1]]


def validate_panel(index: dict[str, Any], lanes: list[dict[str, Any]]) -> list[str]:
    problems: list[str] = list(index.get("blocking_problems", []))
    for item in index["next_queue"]:
        if not item.get("owner_lane"):
            problems.append(f"missing_owner_lane:{item['kind']}:{item['target']}")
    for item in index["duplicate_index"]:
        if not item.get("merge_preconditions"):
            problems.append(f"missing_merge_preconditions:{item['number']}")
    if not lanes:
        problems.append("empty_closure_lanes")
    return problems


def build_closure_panel() -> dict[str, Any]:
    index = consolidation.build_consolidation_index()
    lanes = summarize_lanes(index)
    problems = validate_panel(index, lanes)
    return {
        "name": "stock_closure_panel",
        "ci_gate_status": "fail" if problems else "pass",
        "blocking_problems": problems,
        "maturity_recommendation": index["maturity_recommendation"],
        "lane_count": len(lanes),
        "total_queue_count": len(index["next_queue"]),
        "lanes": lanes,
        "guardrails": [
            "read_only_panel",
            "no_business_file_write",
            "no_external_service_call",
            "no_real_send_or_n8n_or_webhook",
        ],
    }


def render_markdown(panel: dict[str, Any]) -> str:
    lines = [
        "# Stock Closure Panel",
        "",
        f"- CI gate: `{panel['ci_gate_status']}`",
        f"- Total queue: `{panel['total_queue_count']}`",
        f"- Maturity recommendation: `{panel['maturity_recommendation']}`",
        "",
        "## Lane Queue",
    ]
    for lane in panel["lanes"]:
        targets = ", ".join(lane["targets"]) or "-"
        lines.append(
            "- "
            f"`{lane['owner_lane']}`: queue={lane['queue_count']}, "
            f"duplicates={lane['duplicate_count']}, topics={lane['topic_count']}, "
            f"preconditions={lane['precondition_count']}, action={lane['next_action']}, "
            f"targets={targets}"
        )

    lines.extend(["", "## Guardrails"])
    for guardrail in panel["guardrails"]:
        lines.append(f"- `{guardrail}`")

    if panel["blocking_problems"]:
        lines.extend(["", "## Blocking Problems"])
        for problem in panel["blocking_problems"]:
            lines.append(f"- `{problem}`")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    args = parser.parse_args()

    panel = build_closure_panel()
    if args.json:
        print(json.dumps(panel, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(panel))

    if panel["ci_gate_status"] != "pass":
        print("FAIL: stock closure panel found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
