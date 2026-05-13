#!/usr/bin/env python3
"""Read-only acceptance overview gate for the stock analysis sample room.

This gate aggregates the already-established stock CI signals into one compact
acceptance overview:
- upstream gate status;
- risk counts and readiness score;
- construction advice mode;
- final CI decision for the current commit.

It does not write project files, start services, call external systems, send
messages, or touch real n8n/Webhook/broker paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

try:
    from ci import stock_construction_advice_ci_check as advice
    from ci import stock_risk_matrix_ci_check as risk
except ModuleNotFoundError:  # Running as `python ci/stock_acceptance_overview_ci_check.py`.
    import stock_construction_advice_ci_check as advice  # type: ignore[no-redef]
    import stock_risk_matrix_ci_check as risk  # type: ignore[no-redef]


UPSTREAM_WEIGHTS = {
    "risk_matrix": 30,
    "construction_advice": 25,
    "change_impact": 15,
    "dependency_order": 15,
    "learning_summary": 15,
}

RISK_PENALTY = {
    "low": 0,
    "medium": 2,
    "high": 8,
}

GUARDRAILS = [
    "read_only_acceptance_overview",
    "reuse_risk_matrix_and_construction_advice",
    "no_business_file_write",
    "no_external_service_call",
    "no_real_send_or_n8n_or_webhook",
    "no_auto_trade_or_broker_interface",
]


def upstream_statuses(
    risk_report: dict[str, Any],
    advice_report: dict[str, Any],
) -> dict[str, str]:
    return {
        "risk_matrix": risk_report["ci_gate_status"],
        "construction_advice": advice_report["ci_gate_status"],
        "change_impact": risk_report["upstream"]["change_impact_status"],
        "dependency_order": risk_report["upstream"]["dependency_order_status"],
        "learning_summary": advice_report["upstream"]["learning_gate_status"],
    }


def readiness_score(
    statuses: dict[str, str],
    risk_counts: dict[str, int],
) -> int:
    score = 100
    for name, weight in UPSTREAM_WEIGHTS.items():
        if statuses.get(name) != "pass":
            score -= weight
    for level, count in risk_counts.items():
        score -= RISK_PENALTY.get(level, 4) * count
    return max(0, min(100, score))


def acceptance_state(score: int, risk_counts: dict[str, int], statuses: dict[str, str]) -> str:
    if any(status != "pass" for status in statuses.values()):
        return "blocked"
    if risk_counts.get("high", 0) > 0:
        return "human_review_required"
    if score < 80:
        return "review_before_continue"
    return "continue"


def next_action_for_state(state: str) -> str:
    return {
        "continue": "continue_stock_system_construction_under_current_ci_gates",
        "review_before_continue": "review_medium_risk_items_before_more_construction",
        "human_review_required": "human_review_high_risk_items_before_any_delivery",
        "blocked": "fix_failing_ci_gate_before_new_construction",
    }.get(state, "review_before_continue")


def advice_modes(advice_report: dict[str, Any]) -> list[str]:
    return sorted({card.get("mode", "unknown") for card in advice_report.get("advice_cards", [])})


def validate_report(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if report["score"] < 0 or report["score"] > 100:
        problems.append(f"score_out_of_range:{report['score']}")
    if report["state"] not in {"continue", "review_before_continue", "human_review_required", "blocked"}:
        problems.append(f"unknown_acceptance_state:{report['state']}")
    if report["state"] == "continue" and report["risk_counts"].get("high", 0) > 0:
        problems.append("continue_state_with_high_risk_items")
    if report["state"] == "continue" and any(status != "pass" for status in report["upstream_statuses"].values()):
        problems.append("continue_state_with_failing_upstream")
    if not report.get("next_action"):
        problems.append("missing_next_action")
    if not report.get("advice_modes"):
        problems.append("missing_advice_modes")
    for guardrail in GUARDRAILS:
        if guardrail not in report.get("guardrails", []):
            problems.append(f"missing_guardrail:{guardrail}")
    return problems


def build_acceptance_overview_report() -> dict[str, Any]:
    risk_report = risk.build_risk_matrix_report()
    advice_report = advice.build_construction_advice_report()
    statuses = upstream_statuses(risk_report, advice_report)
    score = readiness_score(statuses, risk_report["risk_counts"])
    state = acceptance_state(score, risk_report["risk_counts"], statuses)
    report = {
        "name": "stock_acceptance_overview",
        "scope": "stock_analysis_sample_room",
        "upstream_statuses": statuses,
        "risk_counts": risk_report["risk_counts"],
        "advice_modes": advice_modes(advice_report),
        "score": score,
        "state": state,
        "next_action": next_action_for_state(state),
        "guardrails": GUARDRAILS,
    }
    problems = validate_report(report)
    report["ci_gate_status"] = "fail" if problems else "pass"
    report["blocking_problems"] = problems
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stock Acceptance Overview",
        "",
        f"- CI gate: `{report['ci_gate_status']}`",
        f"- Scope: `{report['scope']}`",
        f"- Score: `{report['score']}`",
        f"- State: `{report['state']}`",
        f"- Next action: `{report['next_action']}`",
        "",
        "## Upstream Statuses",
    ]
    for name, status in sorted(report["upstream_statuses"].items()):
        lines.append(f"- `{name}`: `{status}`")

    lines.extend(["", "## Risk Counts"])
    for level in risk.RISK_LEVELS:
        lines.append(f"- `{level}`: `{report['risk_counts'].get(level, 0)}`")

    lines.extend(["", "## Advice Modes"])
    for mode in report["advice_modes"]:
        lines.append(f"- `{mode}`")

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

    report = build_acceptance_overview_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))

    if report["ci_gate_status"] != "pass":
        print("FAIL: stock acceptance overview found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
