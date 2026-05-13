#!/usr/bin/env python3
"""Read-only construction advice gate for the stock analysis sample room.

This gate converts existing CI understanding into a practical, safe work list:
- contract lanes become lane work orders;
- learning-summary next-focus items become construction advice;
- upstream blockers stay blockers instead of being hidden in a report.

It does not write project files, start services, call external systems, send
messages, or touch real n8n/Webhook/broker paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

try:
    from ci import stock_ci_learning_summary as learning
except ModuleNotFoundError:  # Running as `python ci/stock_construction_advice_ci_check.py`.
    import stock_ci_learning_summary as learning  # type: ignore[no-redef]


GUARDRAILS = [
    "read_only_construction_advice",
    "reuse_learning_summary_signals",
    "no_business_file_write",
    "no_external_service_call",
    "no_real_send_or_n8n_or_webhook",
    "no_auto_trade_or_broker_interface",
]

FORBIDDEN_ADVICE_TERMS = [
    "real_send=true",
    "--real-send",
    "trigger_webhook",
    "call_webhook",
    "run_n8n",
    "broker_order",
    "auto_trade",
]

PRIORITY_TO_MODE = {
    "P0": "stop_and_fix",
    "P1": "review_then_continue",
    "P2": "continue_under_contract",
}


def lane_work_orders(learning_report: dict[str, Any]) -> list[dict[str, str]]:
    orders: list[dict[str, str]] = []
    for item in learning_report.get("contract_learning_items", []):
        maturity = item.get("maturity_status", "missing")
        gate = item.get("focused_gate_status", "missing")
        if maturity == "closed" and gate == "pass":
            decision = "continue_under_contract"
        else:
            decision = "repair_lane_before_new_work"
        orders.append(
            {
                "lane": item["stage"],
                "position": str(item.get("position", "")),
                "decision": decision,
                "evidence": f"docs={item.get('doc_count', 0)};maturity={maturity};gate={gate}",
                "next_check": f"python ci/stock_{item['stage']}_ci_check.py",
            }
        )
    return orders


def advice_cards(learning_report: dict[str, Any]) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    for item in learning_report.get("next_focus", []):
        priority = item.get("priority", "P2")
        cards.append(
            {
                "priority": priority,
                "mode": PRIORITY_TO_MODE.get(priority, "review_then_continue"),
                "focus": item.get("focus", "unknown_focus"),
                "action": item.get("action", "continue_under_existing_contract"),
                "allowed_scope": "code_tests_docs_ci_only",
                "safety": "offline_read_only_until_human_delivery_approval",
            }
        )
    return cards


def validate_report(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    upstream = report["upstream"]
    if upstream["learning_gate_status"] != "pass":
        problems.append("learning_summary_not_pass")
    if upstream["contract_gate_status"] != "pass":
        problems.append("contract_gate_not_pass")
    if upstream["impact_gate_status"] != "pass":
        problems.append("change_impact_gate_not_pass")

    if len(report.get("lane_work_orders", [])) < report.get("contract_stage_count", 0):
        problems.append("lane_work_orders_do_not_cover_contract")
    if not report.get("advice_cards"):
        problems.append("missing_advice_cards")

    if upstream.get("has_blockers") and not any(
        card.get("priority") == "P0" for card in report.get("advice_cards", [])
    ):
        problems.append("blockers_without_p0_advice")

    for card in report.get("advice_cards", []):
        for key in ("priority", "mode", "focus", "action", "allowed_scope", "safety"):
            if not card.get(key):
                problems.append(f"advice_card_missing:{key}")
        action_text = " ".join(str(value).lower() for value in card.values())
        for term in FORBIDDEN_ADVICE_TERMS:
            if term.lower() in action_text:
                problems.append(f"forbidden_advice_term:{term}:{card.get('focus')}")

    for order in report.get("lane_work_orders", []):
        for key in ("lane", "decision", "evidence", "next_check"):
            if not order.get(key):
                problems.append(f"lane_work_order_missing:{key}")

    for guardrail in GUARDRAILS:
        if guardrail not in report.get("guardrails", []):
            problems.append(f"missing_guardrail:{guardrail}")
    return problems


def build_construction_advice_report() -> dict[str, Any]:
    learning_report = learning.build_learning_summary_report()
    contract_status = learning_report["contract"]["ci_gate_status"]
    impact_status = learning_report["impact"]["ci_gate_status"]
    report = {
        "name": "stock_construction_advice",
        "scope": "stock_analysis_sample_room",
        "upstream": {
            "learning_gate_status": learning_report["ci_gate_status"],
            "contract_gate_status": contract_status,
            "impact_gate_status": impact_status,
            "has_blockers": bool(learning_report.get("blocking_problems")),
        },
        "contract_stage_count": learning_report["contract"]["stage_count"],
        "lane_work_orders": lane_work_orders(learning_report),
        "advice_cards": advice_cards(learning_report),
        "guardrails": GUARDRAILS,
    }
    problems = validate_report(report)
    report["ci_gate_status"] = "fail" if problems else "pass"
    report["blocking_problems"] = problems
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stock Construction Advice",
        "",
        f"- CI gate: `{report['ci_gate_status']}`",
        f"- Scope: `{report['scope']}`",
        f"- Learning gate: `{report['upstream']['learning_gate_status']}`",
        f"- Contract gate: `{report['upstream']['contract_gate_status']}`",
        f"- Impact gate: `{report['upstream']['impact_gate_status']}`",
        "",
        "## Lane Work Orders",
    ]
    for order in report["lane_work_orders"]:
        lines.append(
            "- "
            f"`{order['lane']}`: decision={order['decision']}; "
            f"evidence={order['evidence']}; next_check=`{order['next_check']}`"
        )

    lines.extend(["", "## Advice Cards"])
    for card in report["advice_cards"]:
        lines.append(
            "- "
            f"`{card['priority']}` `{card['mode']}` `{card['focus']}`: "
            f"{card['action']}; scope={card['allowed_scope']}; safety={card['safety']}"
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

    report = build_construction_advice_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))

    if report["ci_gate_status"] != "pass":
        print("FAIL: stock construction advice found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
