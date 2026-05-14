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
from pathlib import Path
from typing import Any

try:
    from ci import stock_construction_advice_ci_check as advice
    from ci import stock_risk_matrix_ci_check as risk
    from ci import stock_runtime_artifact_governance_ci_check as runtime_artifacts
except ModuleNotFoundError:  # Running as `python ci/stock_acceptance_overview_ci_check.py`.
    import stock_construction_advice_ci_check as advice  # type: ignore[no-redef]
    import stock_risk_matrix_ci_check as risk  # type: ignore[no-redef]
    import stock_runtime_artifact_governance_ci_check as runtime_artifacts  # type: ignore[no-redef]


UPSTREAM_WEIGHTS = {
    "risk_matrix": 25,
    "construction_advice": 20,
    "change_impact": 15,
    "dependency_order": 15,
    "learning_summary": 15,
    "runtime_artifact_governance": 10,
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

ROOT = Path(__file__).resolve().parents[1]
STOCK_ROOT = ROOT / "02杰哥扩展系统" / "01股票研究系统"
FINAL_DELIVERY_MD = STOCK_ROOT / "03数据" / "158完全交付最终验收" / "股票系统完全交付最终验收_最新.md"
WECOM_EXPERIENCE_MD = STOCK_ROOT / "03数据" / "289企业微信体验入口状态" / "股票企业微信体验入口状态_最新.md"


def upstream_statuses(
    risk_report: dict[str, Any],
    advice_report: dict[str, Any],
    runtime_report: dict[str, Any],
) -> dict[str, str]:
    return {
        "risk_matrix": risk_report["ci_gate_status"],
        "construction_advice": advice_report["ci_gate_status"],
        "change_impact": risk_report["upstream"]["change_impact_status"],
        "dependency_order": risk_report["upstream"]["dependency_order_status"],
        "learning_summary": advice_report["upstream"]["learning_gate_status"],
        "runtime_artifact_governance": runtime_report["ci_gate_status"],
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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def delivery_truthfulness_status(
    final_text: str | None = None,
    wecom_text: str | None = None,
) -> dict[str, Any]:
    final = final_text if final_text is not None else read_text(FINAL_DELIVERY_MD)
    wecom = wecom_text if wecom_text is not None else read_text(WECOM_EXPERIENCE_MD)
    claims_complete = "结论：完全交付通过" in final or "完全交付通过：股票分析系统已可完整使用" in final
    active_push_blocked = (
        "最新受控发送被可信IP拦截" in final
        or "主动推送受可信IP限制" in wecom
        or "主动推送可信IP受限" in wecom
    )
    status = "fail" if claims_complete and active_push_blocked else "pass"
    return {
        "status": status,
        "claims_complete": claims_complete,
        "active_push_blocked": active_push_blocked,
        "final_report": str(FINAL_DELIVERY_MD),
        "wecom_experience_report": str(WECOM_EXPERIENCE_MD),
    }


def wecom_status_command_status(wecom_text: str | None = None) -> dict[str, Any]:
    wecom = wecom_text if wecom_text is not None else read_text(WECOM_EXPERIENCE_MD)
    required_terms = [
        "状态帮助短答可用",
        "问答入口：可用",
        "需放行IP",
    ]
    missing = [term for term in required_terms if term not in wecom]
    return {
        "status": "fail" if missing else "pass",
        "missing_terms": missing,
        "wecom_experience_report": str(WECOM_EXPERIENCE_MD),
    }


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
    if report.get("delivery_truthfulness", {}).get("status") != "pass":
        problems.append("final_delivery_claim_conflicts_with_wecom_ip_gate")
    if report.get("wecom_status_command", {}).get("status") != "pass":
        problems.append("wecom_status_command_not_covered_by_experience_acceptance")
    return problems


def build_acceptance_overview_report() -> dict[str, Any]:
    risk_report = risk.build_risk_matrix_report()
    advice_report = advice.build_construction_advice_report()
    runtime_report = runtime_artifacts.build_runtime_artifact_report()
    statuses = upstream_statuses(risk_report, advice_report, runtime_report)
    score = readiness_score(statuses, risk_report["risk_counts"])
    state = acceptance_state(score, risk_report["risk_counts"], statuses)
    report = {
        "name": "stock_acceptance_overview",
        "scope": "stock_analysis_sample_room",
        "upstream_statuses": statuses,
        "runtime_artifact_governance": {
            "live_runtime_status_count": len(runtime_report.get("live_runtime_status_files", [])),
            "category_counts": runtime_report.get("category_counts", {}),
            "blocking_problems": runtime_report.get("blocking_problems", []),
        },
        "risk_counts": risk_report["risk_counts"],
        "advice_modes": advice_modes(advice_report),
        "score": score,
        "state": state,
        "next_action": next_action_for_state(state),
        "delivery_truthfulness": delivery_truthfulness_status(),
        "wecom_status_command": wecom_status_command_status(),
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

    lines.extend(["", "## Delivery Truthfulness"])
    truth = report["delivery_truthfulness"]
    lines.append(f"- `status`: `{truth['status']}`")
    lines.append(f"- `claims_complete`: `{str(truth['claims_complete']).lower()}`")
    lines.append(f"- `active_push_blocked`: `{str(truth['active_push_blocked']).lower()}`")

    lines.extend(["", "## WeCom Status Command"])
    status_command = report["wecom_status_command"]
    lines.append(f"- `status`: `{status_command['status']}`")
    lines.append(f"- `missing_terms`: `{len(status_command['missing_terms'])}`")

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
