#!/usr/bin/env python3
"""Read-only traceability gate for the stock CI chain.

This gate checks the CI chain itself: each stock-system CI script should be
visible in the construction report index, allowed by the safety whitelist,
called by CircleCI, and backed by a test file or explicit test evidence.

It is a meta-gate for preventing drift as the stock sample room grows. It does
not inspect live services, write business data, or call external systems.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from ci import construction_assistant_report as construction
    from ci import safe_ci_check as safe
except ModuleNotFoundError:  # Running as `python ci/stock_ci_traceability_ci_check.py`.
    import construction_assistant_report as construction  # type: ignore[no-redef]
    import safe_ci_check as safe  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]

GUARDRAILS = [
    "read_only_ci_traceability",
    "reuse_circleci_config_and_safe_whitelist",
    "no_business_file_write",
    "no_external_service_call",
    "no_real_send_or_n8n_or_webhook",
]

TEST_EVIDENCE_OVERRIDES = {
    "ci/stock_sample_room_ci_check.py": ["ci/tests/test_safe_ci_check.py"],
    "ci/stock_mainline_ci_check.py": [
        "ci/tests/test_stock_mainline_gate.py",
        "ci/tests/test_safe_ci_check.py",
    ],
}


def circleci_commands() -> list[str]:
    config = ROOT / ".circleci" / "config.yml"
    return safe.circleci_executable_lines(config.read_text(encoding="utf-8"))


def stock_circleci_commands(commands: list[str] | None = None) -> list[str]:
    source = commands if commands is not None else circleci_commands()
    return [
        command
        for command in source
        if command.startswith("python ci/stock_") and command.endswith(".py")
    ]


def command_to_path(command: str) -> str:
    prefix = "python "
    if command.startswith(prefix):
        return command[len(prefix) :]
    return command


def indexed_stock_ci_paths() -> list[str]:
    return [
        item["path"]
        for item in construction.STOCK_GATE_PATHS
        if item["path"].startswith("ci/stock") and item["path"].endswith(".py")
    ]


def filesystem_stock_ci_paths() -> list[str]:
    paths = sorted((ROOT / "ci").glob("stock*.py"))
    return [path.relative_to(ROOT).as_posix() for path in paths]


def expected_test_paths(path: str) -> list[str]:
    if path in TEST_EVIDENCE_OVERRIDES:
        return TEST_EVIDENCE_OVERRIDES[path]
    stem = Path(path).stem
    return [f"ci/tests/test_{stem}.py"]


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def traceability_rows() -> list[dict[str, Any]]:
    commands = stock_circleci_commands()
    command_paths = [command_to_path(command) for command in commands]
    indexed_paths = indexed_stock_ci_paths()
    filesystem_paths = filesystem_stock_ci_paths()
    safe_commands = safe.ALLOWED_CIRCLECI_COMMANDS

    all_paths = sorted(set(command_paths) | set(indexed_paths) | set(filesystem_paths))
    rows: list[dict[str, Any]] = []
    for path in all_paths:
        tests = expected_test_paths(path)
        rows.append(
            {
                "path": path,
                "exists": (ROOT / path).exists(),
                "in_circleci": path in command_paths,
                "circleci_position": command_paths.index(path) if path in command_paths else None,
                "in_safe_whitelist": f"python {path}" in safe_commands,
                "in_construction_index": path in indexed_paths,
                "test_paths": tests,
                "has_test_evidence": any((ROOT / test_path).exists() for test_path in tests),
            }
        )
    return rows


def order_pairs(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    indexed_paths = indexed_stock_ci_paths()
    position = {row["path"]: row["circleci_position"] for row in rows}
    pairs: list[dict[str, str]] = []
    for previous, current in zip(indexed_paths, indexed_paths[1:]):
        if position.get(previous) is None or position.get(current) is None:
            continue
        pairs.append({"before": previous, "after": current})
    return pairs


def validate_report(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    commands = stock_circleci_commands()
    command_paths = [command_to_path(command) for command in commands]
    indexed_paths = indexed_stock_ci_paths()

    for duplicate in duplicate_values(command_paths):
        problems.append(f"duplicate_circleci_stock_command:{duplicate}")
    for duplicate in duplicate_values(indexed_paths):
        problems.append(f"duplicate_construction_index_path:{duplicate}")

    for row in report["rows"]:
        path = row["path"]
        if not row["exists"]:
            problems.append(f"missing_stock_ci_file:{path}")
        if not row["in_circleci"]:
            problems.append(f"stock_ci_file_not_in_circleci:{path}")
        if not row["in_safe_whitelist"]:
            problems.append(f"stock_ci_file_not_whitelisted:{path}")
        if not row["in_construction_index"]:
            problems.append(f"stock_ci_file_not_indexed:{path}")
        if not row["has_test_evidence"]:
            problems.append(f"stock_ci_file_without_test_evidence:{path}")

    command_positions = {
        row["path"]: row["circleci_position"]
        for row in report["rows"]
        if row["circleci_position"] is not None
    }
    for previous, current in zip(indexed_paths, indexed_paths[1:]):
        previous_position = command_positions.get(previous)
        current_position = command_positions.get(current)
        if previous_position is None or current_position is None:
            continue
        if previous_position >= current_position:
            problems.append(f"stock_ci_order_drift:{previous}->{current}")

    for guardrail in GUARDRAILS:
        if guardrail not in report.get("guardrails", []):
            problems.append(f"missing_guardrail:{guardrail}")
    return problems


def build_traceability_report() -> dict[str, Any]:
    rows = traceability_rows()
    report = {
        "name": "stock_ci_traceability",
        "scope": "stock_analysis_sample_room_ci_chain",
        "stock_ci_file_count": len(rows),
        "rows": rows,
        "order_pairs": order_pairs(rows),
        "guardrails": GUARDRAILS,
    }
    problems = validate_report(report)
    report["ci_gate_status"] = "fail" if problems else "pass"
    report["blocking_problems"] = problems
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stock CI Traceability",
        "",
        f"- CI gate: `{report['ci_gate_status']}`",
        f"- Scope: `{report['scope']}`",
        f"- Stock CI files: `{report['stock_ci_file_count']}`",
        "",
        "## Rows",
    ]
    for row in report["rows"]:
        lines.append(
            "- "
            f"`{row['path']}`: exists={str(row['exists']).lower()}; "
            f"circleci={str(row['in_circleci']).lower()}; "
            f"whitelist={str(row['in_safe_whitelist']).lower()}; "
            f"index={str(row['in_construction_index']).lower()}; "
            f"tests={str(row['has_test_evidence']).lower()}"
        )

    lines.extend(["", "## Order"])
    for pair in report["order_pairs"]:
        lines.append(f"- `{pair['before']}` before `{pair['after']}`")

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

    report = build_traceability_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))

    if report["ci_gate_status"] != "pass":
        print("FAIL: stock CI traceability found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
