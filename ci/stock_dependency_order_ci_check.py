#!/usr/bin/env python3
"""Read-only dependency-order gate for the stock analysis sample room.

This gate checks whether the stock-system contract still preserves the intended
construction order:
- source pool before manual review;
- manual review before quality evidence;
- quality evidence before pre-output;
- pre-output before review loop;
- safe boundary guarding every construction lane.

It also checks the meta-CI order for the newer contract, impact, learning,
advice, traceability, and dependency gates. It does not write project files or
call external services.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from typing import Any

try:
    from ci import stock_ci_traceability_ci_check as traceability
    from ci import stock_system_contract_ci_check as contract
except ModuleNotFoundError:  # Running as `python ci/stock_dependency_order_ci_check.py`.
    import stock_ci_traceability_ci_check as traceability  # type: ignore[no-redef]
    import stock_system_contract_ci_check as contract  # type: ignore[no-redef]


CONSTRUCTION_STAGE_SEQUENCE = [
    "sample_pool",
    "manual_review",
    "quality_evidence",
    "pre_push_gate",
    "review_loop",
]

SAFE_STAGE = "safe_boundary"

META_CI_ORDER = [
    "ci/stock_system_contract_ci_check.py",
    "ci/stock_change_impact_ci_check.py",
    "ci/stock_ci_learning_summary.py",
    "ci/stock_construction_advice_ci_check.py",
    "ci/stock_ci_traceability_ci_check.py",
    "ci/stock_dependency_order_ci_check.py",
]

GUARDRAILS = [
    "read_only_dependency_order",
    "reuse_system_contract_edges",
    "reuse_ci_traceability_order",
    "no_business_file_write",
    "no_external_service_call",
    "no_real_send_or_n8n_or_webhook",
]


def edge_key(edge: tuple[str, str, str] | list[str]) -> tuple[str, str]:
    return edge[0], edge[1]


def required_chain_edges() -> list[tuple[str, str]]:
    return list(zip(CONSTRUCTION_STAGE_SEQUENCE, CONSTRUCTION_STAGE_SEQUENCE[1:]))


def required_safe_edges() -> list[tuple[str, str]]:
    return [(SAFE_STAGE, stage) for stage in CONSTRUCTION_STAGE_SEQUENCE]


def build_graph(edges: list[tuple[str, str, str] | list[str]]) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = defaultdict(list)
    for source, target, _label in edges:
        graph[source].append(target)
        graph.setdefault(target, [])
    return {node: sorted(targets) for node, targets in graph.items()}


def topological_order(graph: dict[str, list[str]]) -> list[str]:
    indegree = {node: 0 for node in graph}
    for targets in graph.values():
        for target in targets:
            indegree[target] = indegree.get(target, 0) + 1

    ready = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while ready:
        node = ready.popleft()
        order.append(node)
        for target in graph.get(node, []):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
        ready = deque(sorted(ready))
    return order


def has_cycle(graph: dict[str, list[str]]) -> bool:
    return len(topological_order(graph)) != len(graph)


def stage_position_map(stages: list[dict[str, Any]]) -> dict[str, str]:
    return {stage["name"]: stage.get("position", "") for stage in stages}


def ci_position_map() -> dict[str, int]:
    commands = traceability.stock_circleci_commands()
    paths = [traceability.command_to_path(command) for command in commands]
    return {path: index for index, path in enumerate(paths)}


def validate_report(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    edges = {tuple(edge) for edge in report["edge_pairs"]}
    stage_names = set(report["stage_positions"])

    for stage in [*CONSTRUCTION_STAGE_SEQUENCE, SAFE_STAGE]:
        if stage not in stage_names:
            problems.append(f"missing_contract_stage:{stage}")

    for source, target in required_chain_edges():
        if (source, target) not in edges:
            problems.append(f"missing_required_chain_edge:{source}->{target}")

    for source, target in required_safe_edges():
        if (source, target) not in edges:
            problems.append(f"missing_safe_boundary_edge:{source}->{target}")

    if report["graph_has_cycle"]:
        problems.append("dependency_graph_has_cycle")

    topo_positions = {stage: index for index, stage in enumerate(report["topological_order"])}
    for source, target in required_chain_edges() + required_safe_edges():
        if source in topo_positions and target in topo_positions and topo_positions[source] >= topo_positions[target]:
            problems.append(f"topological_order_violation:{source}->{target}")

    ci_positions = report["ci_positions"]
    for before, after in zip(META_CI_ORDER, META_CI_ORDER[1:]):
        if before not in ci_positions:
            problems.append(f"missing_meta_ci_command:{before}")
            continue
        if after not in ci_positions:
            problems.append(f"missing_meta_ci_command:{after}")
            continue
        if ci_positions[before] >= ci_positions[after]:
            problems.append(f"meta_ci_order_violation:{before}->{after}")

    if report["system_contract_status"] != "pass":
        problems.append("system_contract_not_pass")
    if report["traceability_status"] != "pass":
        problems.append("traceability_not_pass")

    for guardrail in GUARDRAILS:
        if guardrail not in report.get("guardrails", []):
            problems.append(f"missing_guardrail:{guardrail}")
    return problems


def build_dependency_order_report() -> dict[str, Any]:
    contract_report = contract.build_system_contract_report()
    traceability_report = traceability.build_traceability_report()
    graph = build_graph(contract_report["dependency_edges"])
    report = {
        "name": "stock_dependency_order",
        "scope": "stock_analysis_sample_room",
        "system_contract_status": contract_report["ci_gate_status"],
        "traceability_status": traceability_report["ci_gate_status"],
        "stage_positions": stage_position_map(contract_report["stages"]),
        "edge_pairs": [list(edge_key(edge)) for edge in contract_report["dependency_edges"]],
        "required_chain_edges": [list(edge) for edge in required_chain_edges()],
        "required_safe_edges": [list(edge) for edge in required_safe_edges()],
        "graph": graph,
        "graph_has_cycle": has_cycle(graph),
        "topological_order": topological_order(graph),
        "meta_ci_order": META_CI_ORDER,
        "ci_positions": ci_position_map(),
        "guardrails": GUARDRAILS,
    }
    problems = validate_report(report)
    report["ci_gate_status"] = "fail" if problems else "pass"
    report["blocking_problems"] = problems
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stock Dependency Order",
        "",
        f"- CI gate: `{report['ci_gate_status']}`",
        f"- Scope: `{report['scope']}`",
        f"- System contract: `{report['system_contract_status']}`",
        f"- Traceability: `{report['traceability_status']}`",
        f"- Graph has cycle: `{str(report['graph_has_cycle']).lower()}`",
        f"- Topological order: `{','.join(report['topological_order'])}`",
        "",
        "## Required Chain Edges",
    ]
    for source, target in report["required_chain_edges"]:
        lines.append(f"- `{source}` before `{target}`")

    lines.extend(["", "## Safe Boundary Edges"])
    for source, target in report["required_safe_edges"]:
        lines.append(f"- `{source}` guards `{target}`")

    lines.extend(["", "## Meta CI Order"])
    for before, after in zip(report["meta_ci_order"], report["meta_ci_order"][1:]):
        lines.append(f"- `{before}` before `{after}`")

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

    report = build_dependency_order_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))

    if report["ci_gate_status"] != "pass":
        print("FAIL: stock dependency order found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
