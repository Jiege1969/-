#!/usr/bin/env python3
"""Read-only risk-matrix gate for stock-system construction changes.

This gate turns the existing change-impact and dependency-order signals into a
simple risk matrix. It answers:
- what risk level each touched file has;
- which stock lanes must stay green for that risk;
- whether safety boundary coverage is present for risky work.

It does not write project files, start services, call external systems, send
messages, or touch real n8n/Webhook/broker paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

try:
    from ci import stock_change_impact_ci_check as impact
    from ci import stock_dependency_order_ci_check as dependency
except ModuleNotFoundError:  # Running as `python ci/stock_risk_matrix_ci_check.py`.
    import stock_change_impact_ci_check as impact  # type: ignore[no-redef]
    import stock_dependency_order_ci_check as dependency  # type: ignore[no-redef]


RISK_LEVELS = ["low", "medium", "high"]

REQUIRED_GATES_BY_LEVEL = {
    "low": ["system_contract"],
    "medium": ["system_contract", "change_impact", "dependency_order"],
    "high": ["system_contract", "change_impact", "dependency_order", "safe_boundary"],
}

STOCK_CATEGORY_RISK = {
    "ci_support": "medium",
    "stock_config": "medium",
    "stock_script": "medium",
    "stock_data": "medium",
    "stock_runtime_status": "high",
    "stock_doc": "low",
    "stock_other": "medium",
    "non_stock": "low",
}

GUARDRAILS = [
    "read_only_risk_matrix",
    "reuse_change_impact_and_dependency_order",
    "no_business_file_write",
    "no_external_service_call",
    "no_real_send_or_n8n_or_webhook",
    "no_auto_trade_or_broker_interface",
]


def higher_risk(left: str, right: str) -> str:
    return left if RISK_LEVELS.index(left) >= RISK_LEVELS.index(right) else right


def risk_level_for_change(change: dict[str, Any]) -> str:
    level = STOCK_CATEGORY_RISK.get(change.get("category", "non_stock"), "medium")
    stages = set(change.get("impacted_stages", []))
    if change.get("high_risk_marker"):
        level = "high"
    if "unmapped_stock" in stages:
        level = higher_risk(level, "medium")
    return level


def required_gates_for_change(change: dict[str, Any]) -> list[str]:
    level = risk_level_for_change(change)
    gates = list(REQUIRED_GATES_BY_LEVEL[level])
    for stage in change.get("impacted_stages", []):
        if stage in dependency.CONSTRUCTION_STAGE_SEQUENCE or stage == dependency.SAFE_STAGE:
            gates.append(stage)
    return sorted(set(gates), key=gates.index)


def gate_statuses(
    impact_report: dict[str, Any],
    dependency_report: dict[str, Any],
) -> dict[str, str]:
    statuses = {
        "system_contract": impact_report["system_contract"]["ci_gate_status"],
        "change_impact": impact_report["ci_gate_status"],
        "dependency_order": dependency_report["ci_gate_status"],
    }
    statuses.update(impact_report["system_contract"].get("focused_gate_statuses", {}))
    return statuses


def risk_rows(
    impact_report: dict[str, Any],
    dependency_report: dict[str, Any],
) -> list[dict[str, Any]]:
    statuses = gate_statuses(impact_report, dependency_report)
    rows: list[dict[str, Any]] = []
    for change in impact_report.get("changes", []):
        gates = required_gates_for_change(change)
        missing_or_failed = [
            gate
            for gate in gates
            if statuses.get(gate) != "pass"
        ]
        rows.append(
            {
                "path": change["path"],
                "category": change["category"],
                "impacted_stages": change["impacted_stages"],
                "high_risk_marker": change["high_risk_marker"],
                "risk_level": risk_level_for_change(change),
                "required_gates": gates,
                "missing_or_failed_gates": missing_or_failed,
                "safe_boundary_required": risk_level_for_change(change) == "high",
                "safe_boundary_present": "safe_boundary" in change["impacted_stages"]
                or statuses.get("safe_boundary") == "pass",
            }
        )
    return rows


def validate_report(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if report["upstream"]["change_impact_status"] != "pass":
        problems.append("change_impact_not_pass")
    if report["upstream"]["dependency_order_status"] != "pass":
        problems.append("dependency_order_not_pass")

    for row in report["rows"]:
        if row["risk_level"] not in RISK_LEVELS:
            problems.append(f"unknown_risk_level:{row['path']}:{row['risk_level']}")
        if row["missing_or_failed_gates"]:
            problems.append(
                "risk_required_gate_not_pass:"
                f"{row['path']}:{','.join(row['missing_or_failed_gates'])}"
            )
        if row["safe_boundary_required"] and not row["safe_boundary_present"]:
            problems.append(f"high_risk_without_safe_boundary:{row['path']}")
        if row["high_risk_marker"] and row["risk_level"] != "high":
            problems.append(f"high_risk_marker_not_classified_high:{row['path']}")

    for guardrail in GUARDRAILS:
        if guardrail not in report.get("guardrails", []):
            problems.append(f"missing_guardrail:{guardrail}")
    return problems


def build_risk_matrix_report() -> dict[str, Any]:
    impact_report = impact.build_change_impact_report()
    dependency_report = dependency.build_dependency_order_report()
    rows = risk_rows(impact_report, dependency_report)
    counts = {level: 0 for level in RISK_LEVELS}
    for row in rows:
        counts[row["risk_level"]] += 1
    report = {
        "name": "stock_risk_matrix",
        "scope": "stock_analysis_sample_room",
        "upstream": {
            "change_impact_status": impact_report["ci_gate_status"],
            "dependency_order_status": dependency_report["ci_gate_status"],
        },
        "risk_counts": counts,
        "rows": rows,
        "guardrails": GUARDRAILS,
    }
    problems = validate_report(report)
    report["ci_gate_status"] = "fail" if problems else "pass"
    report["blocking_problems"] = problems
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stock Risk Matrix",
        "",
        f"- CI gate: `{report['ci_gate_status']}`",
        f"- Scope: `{report['scope']}`",
        f"- Change impact: `{report['upstream']['change_impact_status']}`",
        f"- Dependency order: `{report['upstream']['dependency_order_status']}`",
        "",
        "## Risk Counts",
    ]
    for level in RISK_LEVELS:
        lines.append(f"- `{level}`: `{report['risk_counts'].get(level, 0)}`")

    lines.extend(["", "## Rows"])
    if not report["rows"]:
        lines.append("- none")
    for row in report["rows"]:
        lines.append(
            "- "
            f"`{row['risk_level']}` `{row['path']}`: "
            f"category={row['category']}; "
            f"stages={','.join(row['impacted_stages']) or 'none'}; "
            f"gates={','.join(row['required_gates'])}"
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

    report = build_risk_matrix_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))

    if report["ci_gate_status"] != "pass":
        print("FAIL: stock risk matrix found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
