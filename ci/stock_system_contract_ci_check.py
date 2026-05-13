#!/usr/bin/env python3
"""Read-only system contract check for the stock analysis sample room.

This gate is the first CI layer that treats the stock system as a system:
it connects source documents, mainline construction lanes, closure lanes,
focused lane gates, dependency order, and safety boundaries into one contract.

It does not create reports, start services, call external systems, send
messages, or modify business data.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

try:
    from ci import stock_closure_panel_ci_check as closure_panel
    from ci import stock_manual_review_ci_check as manual_review
    from ci import stock_maturity_ci_check as maturity
    from ci import stock_pre_push_gate_ci_check as pre_push_gate
    from ci import stock_quality_evidence_ci_check as quality_evidence
    from ci import stock_review_loop_ci_check as review_loop
    from ci import stock_safe_boundary_ci_check as safe_boundary
    from ci import stock_sample_pool_ci_check as sample_pool
except ModuleNotFoundError:  # Running as `python ci/stock_system_contract_ci_check.py`.
    import stock_closure_panel_ci_check as closure_panel  # type: ignore[no-redef]
    import stock_manual_review_ci_check as manual_review  # type: ignore[no-redef]
    import stock_maturity_ci_check as maturity  # type: ignore[no-redef]
    import stock_pre_push_gate_ci_check as pre_push_gate  # type: ignore[no-redef]
    import stock_quality_evidence_ci_check as quality_evidence  # type: ignore[no-redef]
    import stock_review_loop_ci_check as review_loop  # type: ignore[no-redef]
    import stock_safe_boundary_ci_check as safe_boundary  # type: ignore[no-redef]
    import stock_sample_pool_ci_check as sample_pool  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
STOCK_ROOT = maturity.STOCK_ROOT
STOCK_DOC_ROOT = STOCK_ROOT / "07文档"
MAINLINE_SCRIPT_NAME = "生成股票主线施工闸口面板.py"

CONTRACT_STAGES = [
    {
        "name": "sample_pool",
        "position": "source",
        "owner_lane": "sample_pool",
        "doc_markers": ["家底盘点", "2000只标准", "分层池"],
    },
    {
        "name": "manual_review",
        "position": "human_gate",
        "owner_lane": "manual_review",
        "doc_markers": ["施工原则", "数据字段", "人工"],
    },
    {
        "name": "quality_evidence",
        "position": "evidence",
        "owner_lane": "quality_evidence",
        "doc_markers": ["报告v2", "证据", "金融"],
    },
    {
        "name": "pre_push_gate",
        "position": "pre_output",
        "owner_lane": "pre_push_gate",
        "doc_markers": ["日常研究链路", "前后台", "推送"],
    },
    {
        "name": "review_loop",
        "position": "feedback",
        "owner_lane": "review_loop",
        "doc_markers": ["复盘闭环", "轻量学习", "推荐方法工作流"],
    },
    {
        "name": "safe_boundary",
        "position": "crosscutting_guard",
        "owner_lane": "safe_boundary",
        "doc_markers": ["安全", "施工原则", "交付"],
    },
]

DEPENDENCY_EDGES = [
    ("sample_pool", "manual_review", "candidate_source_before_manual_evidence"),
    ("manual_review", "quality_evidence", "verified_material_before_quality_evidence"),
    ("quality_evidence", "pre_push_gate", "evidence_before_output_draft"),
    ("pre_push_gate", "review_loop", "output_record_before_feedback"),
    ("safe_boundary", "sample_pool", "guard_all_stock_construction"),
    ("safe_boundary", "manual_review", "guard_all_stock_construction"),
    ("safe_boundary", "quality_evidence", "guard_all_stock_construction"),
    ("safe_boundary", "pre_push_gate", "guard_all_stock_construction"),
    ("safe_boundary", "review_loop", "guard_all_stock_construction"),
]

FOCUSED_GATE_BUILDERS = {
    "sample_pool": sample_pool.build_sample_pool_report,
    "manual_review": manual_review.build_manual_review_report,
    "quality_evidence": quality_evidence.build_quality_evidence_report,
    "pre_push_gate": pre_push_gate.build_pre_push_gate_report,
    "review_loop": review_loop.build_review_loop_report,
    "safe_boundary": safe_boundary.build_safe_boundary_report,
}

SAFETY_FALSE_KEYS = [
    "真实发送企业微信",
    "触发n8n",
    "触发Webhook",
    "调用券商接口",
    "自动交易",
    "写正式库",
    "重启服务",
]

GUARDRAILS = [
    "read_only_system_contract_check",
    "reuse_existing_stock_gates",
    "no_business_file_write",
    "no_external_service_call",
    "no_real_send_or_n8n_or_webhook",
    "no_auto_trade_or_broker_interface",
]


def find_stock_docs(markers: list[str]) -> list[str]:
    if not STOCK_DOC_ROOT.exists():
        return []
    matches: list[str] = []
    for path in sorted(STOCK_DOC_ROOT.glob("*")):
        if not path.is_file():
            continue
        name = path.name
        if any(marker in name for marker in markers):
            matches.append(path.relative_to(ROOT).as_posix())
    return matches


def find_mainline_script() -> Path:
    matches = sorted((STOCK_ROOT / "02脚本").glob(MAINLINE_SCRIPT_NAME))
    if matches:
        return matches[0]
    raise FileNotFoundError(MAINLINE_SCRIPT_NAME)


def load_mainline_module():
    path = find_mainline_script()
    spec = importlib.util.spec_from_file_location("stock_mainline_contract_gate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load mainline gate: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stage_contracts() -> list[dict[str, Any]]:
    stages: list[dict[str, Any]] = []
    for stage in CONTRACT_STAGES:
        item = dict(stage)
        item["source_docs"] = find_stock_docs(stage["doc_markers"])
        item["doc_count"] = len(item["source_docs"])
        stages.append(item)
    return stages


def maturity_lane_statuses() -> dict[str, str]:
    report = maturity.build_report()
    return {lane["name"]: lane["status"] for lane in report.get("lanes", [])}


def closure_lane_names() -> set[str]:
    panel = closure_panel.build_closure_panel()
    return {lane["owner_lane"] for lane in panel.get("lanes", [])}


def focused_gate_statuses() -> dict[str, str]:
    statuses: dict[str, str] = {}
    for name, builder in FOCUSED_GATE_BUILDERS.items():
        statuses[name] = builder().get("ci_gate_status", "missing")
    return statuses


def mainline_contract() -> dict[str, Any]:
    module = load_mainline_module()
    report = module.build_report()
    queue = report.get("construction_queue", [])
    safety = report.get("安全边界", {})
    return {
        "ci_gate_status": report.get("CI闸口状态"),
        "lane_count": report.get("泳道数"),
        "construction_queue_count": len(queue),
        "construction_queue": queue,
        "safety_boundary": safety,
        "safety_false_keys": {
            key: safety.get(key) is False
            for key in SAFETY_FALSE_KEYS
        },
    }


def validate_report(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    stage_names = {stage["name"] for stage in report["stages"]}

    for stage in report["stages"]:
        if stage["doc_count"] < 1:
            problems.append(f"missing_stage_source_doc:{stage['name']}")

    for stage in report["stages"]:
        name = stage["name"]
        if report["maturity_lane_statuses"].get(name) != "closed":
            problems.append(f"maturity_lane_not_closed:{name}")
        if name not in report["closure_lanes"]:
            problems.append(f"missing_closure_lane:{name}")
        if report["focused_gate_statuses"].get(name) != "pass":
            problems.append(f"focused_gate_not_pass:{name}")

    for source, target, label in report["dependency_edges"]:
        if source not in stage_names or target not in stage_names:
            problems.append(f"dependency_edge_unknown_endpoint:{label}:{source}->{target}")

    mainline = report["mainline_contract"]
    if mainline["ci_gate_status"] != "pass":
        problems.append(f"mainline_gate_not_pass:{mainline['ci_gate_status']}")
    if mainline["construction_queue_count"] < mainline.get("lane_count", 0):
        problems.append(
            "construction_queue_does_not_cover_mainline_lanes:"
            f"{mainline['construction_queue_count']}<{mainline.get('lane_count', 0)}"
        )
    for key, ok in mainline["safety_false_keys"].items():
        if not ok:
            problems.append(f"mainline_safety_not_false:{key}")

    for guardrail in GUARDRAILS:
        if guardrail not in report["guardrails"]:
            problems.append(f"missing_guardrail:{guardrail}")

    return problems


def build_system_contract_report() -> dict[str, Any]:
    report = {
        "name": "stock_system_contract",
        "scope": "stock_analysis_sample_room",
        "stages": stage_contracts(),
        "dependency_edges": DEPENDENCY_EDGES,
        "maturity_lane_statuses": maturity_lane_statuses(),
        "closure_lanes": sorted(closure_lane_names()),
        "focused_gate_statuses": focused_gate_statuses(),
        "mainline_contract": mainline_contract(),
        "guardrails": GUARDRAILS,
    }
    problems = validate_report(report)
    report["ci_gate_status"] = "fail" if problems else "pass"
    report["blocking_problems"] = problems
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stock System Contract",
        "",
        f"- CI gate: `{report['ci_gate_status']}`",
        f"- Scope: `{report['scope']}`",
        f"- Stage count: `{len(report['stages'])}`",
        f"- Dependency edges: `{len(report['dependency_edges'])}`",
        "",
        "## Stages",
    ]
    for stage in report["stages"]:
        lines.append(
            "- "
            f"`{stage['name']}`: position={stage['position']}; "
            f"owner_lane={stage['owner_lane']}; docs={stage['doc_count']}"
        )

    lines.extend(["", "## Dependency Edges"])
    for source, target, label in report["dependency_edges"]:
        lines.append(f"- `{source}` -> `{target}`: {label}")

    lines.extend(["", "## Focused Gates"])
    for name, status in sorted(report["focused_gate_statuses"].items()):
        lines.append(f"- `{name}`: `{status}`")

    mainline = report["mainline_contract"]
    lines.extend(
        [
            "",
            "## Mainline Contract",
            f"- CI gate: `{mainline['ci_gate_status']}`",
            f"- Construction queue: `{mainline['construction_queue_count']}`",
        ]
    )
    for key, ok in mainline["safety_false_keys"].items():
        lines.append(f"- `{key}` false: `{str(ok).lower()}`")

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

    report = build_system_contract_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))

    if report["ci_gate_status"] != "pass":
        print("FAIL: stock system contract found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
