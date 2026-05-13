#!/usr/bin/env python3
"""Read-only CI learning summary for the stock analysis sample room.

This gate turns existing CI signals into a compact learning report:
- what the current commit touched;
- which stock-system contract lanes stayed green;
- what the next construction focus should be.

It deliberately reuses existing gates instead of inventing a new source of
truth. It does not write project files or call external services.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

try:
    from ci import stock_change_impact_ci_check as impact
    from ci import stock_system_contract_ci_check as contract
except ModuleNotFoundError:  # Running as `python ci/stock_ci_learning_summary.py`.
    import stock_change_impact_ci_check as impact  # type: ignore[no-redef]
    import stock_system_contract_ci_check as contract  # type: ignore[no-redef]


GUARDRAILS = [
    "read_only_ci_learning_summary",
    "reuse_contract_and_impact_gates",
    "no_business_file_write",
    "no_external_service_call",
    "no_real_send_or_n8n_or_webhook",
]


def impacted_stage_counts(changes: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for change in changes:
        for stage in change.get("impacted_stages", []):
            counts[stage] = counts.get(stage, 0) + 1
    return counts


def contract_learning_items(contract_report: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    focused = contract_report.get("focused_gate_statuses", {})
    maturity = contract_report.get("maturity_lane_statuses", {})
    for stage in contract_report.get("stages", []):
        name = stage["name"]
        items.append(
            {
                "stage": name,
                "position": stage.get("position"),
                "doc_count": stage.get("doc_count", 0),
                "maturity_status": maturity.get(name, "missing"),
                "focused_gate_status": focused.get(name, "missing"),
                "learning": "contract_lane_understood",
            }
        )
    return items


def next_focus_items(
    contract_report: dict[str, Any],
    impact_report: dict[str, Any],
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    if contract_report.get("blocking_problems"):
        items.append(
            {
                "priority": "P0",
                "focus": "contract_blocking_problems",
                "action": "fix_stock_system_contract_before_new_construction",
            }
        )
    if impact_report.get("blocking_problems"):
        items.append(
            {
                "priority": "P0",
                "focus": "change_impact_blocking_problems",
                "action": "resolve_high_risk_or_impacted_gate_failure",
            }
        )
    if impact_report.get("review_items"):
        items.append(
            {
                "priority": "P1",
                "focus": "unmapped_stock_changes",
                "action": "map_unknown_stock_paths_to_a_contract_lane_when_the_pattern_repeats",
            }
        )

    counts = impacted_stage_counts(impact_report.get("changes", []))
    stock_stages = [
        stage["name"]
        for stage in contract.CONTRACT_STAGES
        if counts.get(stage["name"], 0) > 0
    ]
    if stock_stages:
        items.append(
            {
                "priority": "P1",
                "focus": "impacted_stock_lanes",
                "action": "review_impacted_lanes:" + ",".join(stock_stages),
            }
        )
    elif counts.get("ci_contract", 0) > 0:
        items.append(
            {
                "priority": "P1",
                "focus": "ci_contract_layer",
                "action": "keep_contract_tests_aligned_with_stock_system_reality",
            }
        )
    else:
        items.append(
            {
                "priority": "P2",
                "focus": "no_stock_lane_change",
                "action": "continue_mainline_construction_under_existing_contract",
            }
        )
    return items


def validate_report(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if report["contract"]["ci_gate_status"] != "pass":
        problems.append("contract_gate_not_pass")
    if report["impact"]["ci_gate_status"] != "pass":
        problems.append("change_impact_gate_not_pass")
    if len(report.get("contract_learning_items", [])) < len(contract.CONTRACT_STAGES):
        problems.append("contract_learning_items_do_not_cover_all_stages")
    if not report.get("next_focus"):
        problems.append("missing_next_focus")
    for guardrail in GUARDRAILS:
        if guardrail not in report.get("guardrails", []):
            problems.append(f"missing_guardrail:{guardrail}")
    return problems


def build_learning_summary_report() -> dict[str, Any]:
    contract_report = contract.build_system_contract_report()
    impact_report = impact.build_change_impact_report()
    report = {
        "name": "stock_ci_learning_summary",
        "scope": "stock_analysis_sample_room",
        "contract": {
            "ci_gate_status": contract_report["ci_gate_status"],
            "stage_count": len(contract_report.get("stages", [])),
            "dependency_edge_count": len(contract_report.get("dependency_edges", [])),
            "focused_gate_statuses": contract_report.get("focused_gate_statuses", {}),
            "blocking_problems": contract_report.get("blocking_problems", []),
        },
        "impact": {
            "ci_gate_status": impact_report["ci_gate_status"],
            "changed_file_count": len(impact_report.get("changes", [])),
            "impacted_stage_counts": impacted_stage_counts(impact_report.get("changes", [])),
            "review_items": impact_report.get("review_items", []),
            "blocking_problems": impact_report.get("blocking_problems", []),
        },
        "contract_learning_items": contract_learning_items(contract_report),
        "next_focus": next_focus_items(contract_report, impact_report),
        "guardrails": GUARDRAILS,
    }
    problems = validate_report(report)
    report["ci_gate_status"] = "fail" if problems else "pass"
    report["blocking_problems"] = problems
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stock CI Learning Summary",
        "",
        f"- CI gate: `{report['ci_gate_status']}`",
        f"- Scope: `{report['scope']}`",
        f"- Contract stages: `{report['contract']['stage_count']}`",
        f"- Dependency edges: `{report['contract']['dependency_edge_count']}`",
        f"- Changed files: `{report['impact']['changed_file_count']}`",
        "",
        "## Learned Contract Lanes",
    ]
    for item in report["contract_learning_items"]:
        lines.append(
            "- "
            f"`{item['stage']}`: position={item['position']}; "
            f"docs={item['doc_count']}; "
            f"maturity={item['maturity_status']}; "
            f"gate={item['focused_gate_status']}"
        )

    lines.extend(["", "## Impact Counts"])
    if report["impact"]["impacted_stage_counts"]:
        for stage, count in sorted(report["impact"]["impacted_stage_counts"].items()):
            lines.append(f"- `{stage}`: `{count}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Next Focus"])
    for item in report["next_focus"]:
        lines.append(f"- `{item['priority']}` `{item['focus']}`: {item['action']}")

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

    report = build_learning_summary_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))

    if report["ci_gate_status"] != "pass":
        print("FAIL: stock CI learning summary found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
