#!/usr/bin/env python3
"""Read-only governance check for stock runtime artifacts.

This gate keeps the stock sample-room repository from mixing up three different
kinds of files:
- business evidence that should be committed;
- dated evidence snapshots that preserve history;
- live machine status snapshots that may refresh every minute locally.

It never starts services, calls external systems, sends messages, or writes
project files.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

STOCK_ROOT_PARTS = (
    "02\u6770\u54e5\u6269\u5c55\u7cfb\u7edf",
    "01\u80a1\u7968\u7814\u7a76\u7cfb\u7edf",
)
STOCK_DATA_PART = "03\u6570\u636e"
MANAGER_STATUS_PREFIX = "00\u6770\u54e5\u7cfb\u7edf\u603b\u7ba1/03\u6570\u636e/\u8fd0\u884c\u72b6\u6001/"

LIVE_RUNTIME_STATUS_FILES = [
    MANAGER_STATUS_PREFIX + "\u516c\u7f51\u53cd\u5411\u96a7\u9053\u5b88\u62a4_\u6700\u65b0.json",
    MANAGER_STATUS_PREFIX + "\u516c\u7f51\u53cd\u5411\u96a7\u9053\u5b88\u62a4\u63a2\u6d4b_\u6700\u65b0.json",
    MANAGER_STATUS_PREFIX + "\u8840\u8109\u5206\u949f\u7ea7\u63a2\u9488_\u6700\u65b0.json",
    MANAGER_STATUS_PREFIX + "\u8840\u8109\u5206\u949f\u7ea7\u63a2\u9488_\u6700\u65b0.md",
]

DATED_SNAPSHOT_RE = re.compile(r"(?:_20\d{6}(?:_\d{6})?|-\d{8,})")
LATEST_MARKER = "_\u6700\u65b0"
TEXT_EVIDENCE_SUFFIXES = {".json", ".md", ".csv", ".txt", ".svg"}
GUARDRAILS = [
    "read_only_git_inventory",
    "commit_business_evidence",
    "keep_dated_snapshots_as_history",
    "treat_live_machine_status_as_local_runtime",
    "no_external_service_call",
    "no_real_send_or_runtime_trigger",
]


def rel(path: Path, root: Path = ROOT) -> str:
    return path.relative_to(root).as_posix()


def run_git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-c", "core.quotePath=false", *args], cwd=root)


def tracked_paths(root: Path = ROOT) -> list[str]:
    raw = run_git(root, "ls-files", "-z")
    return [name for name in raw.decode("utf-8", errors="replace").split("\0") if name]


def local_skip_worktree_paths(root: Path = ROOT) -> set[str]:
    try:
        raw = run_git(root, "ls-files", "-v")
    except subprocess.CalledProcessError:
        return set()
    paths: set[str] = set()
    for line in raw.decode("utf-8", errors="replace").splitlines():
        if line.startswith("S "):
            paths.add(line[2:])
    return paths


def is_stock_data_path(path: str) -> bool:
    prefix = "/".join(STOCK_ROOT_PARTS + (STOCK_DATA_PART,))
    return path.startswith(prefix + "/")


def is_evidence_file(path: str) -> bool:
    return Path(path).suffix.lower() in TEXT_EVIDENCE_SUFFIXES


def classify_path(path: str) -> str:
    if path in LIVE_RUNTIME_STATUS_FILES:
        return "live_runtime_status"
    if is_stock_data_path(path) and DATED_SNAPSHOT_RE.search(Path(path).stem) and is_evidence_file(path):
        return "dated_stock_evidence"
    if is_stock_data_path(path) and LATEST_MARKER in Path(path).stem and is_evidence_file(path):
        return "latest_stock_evidence"
    if path.startswith(MANAGER_STATUS_PREFIX) and LATEST_MARKER in Path(path).stem:
        return "manager_runtime_status"
    return "other"


def build_runtime_artifact_report(
    root: Path = ROOT,
    paths: list[str] | None = None,
    skip_paths: set[str] | None = None,
) -> dict[str, Any]:
    paths = paths if paths is not None else tracked_paths(root)
    skip_paths = skip_paths if skip_paths is not None else local_skip_worktree_paths(root)
    category_counts: dict[str, int] = {}
    for path in paths:
        category = classify_path(path)
        category_counts[category] = category_counts.get(category, 0) + 1

    live_status = []
    path_set = set(paths)
    for path in LIVE_RUNTIME_STATUS_FILES:
        live_status.append(
            {
                "path": path,
                "tracked": path in path_set,
                "local_skip_worktree": path in skip_paths,
                "policy": "commit_a_known_snapshot_then_ignore_local_heartbeat_noise",
            }
        )

    report = {
        "name": "stock_runtime_artifact_governance",
        "scope": "stock_analysis_sample_room",
        "category_counts": category_counts,
        "live_runtime_status_files": live_status,
        "recommendations": [
            "commit_stock_business_evidence_when_it_changes",
            "keep_dated_snapshots_when_they_are_acceptance_or_history_evidence",
            "do_not_treat_minute_heartbeat_changes_as_new_construction_debt",
            "use_local_skip_worktree_only_for_machine-local_live_status_snapshots",
        ],
        "guardrails": GUARDRAILS,
    }
    problems = validate_report(report)
    report["ci_gate_status"] = "fail" if problems else "pass"
    report["blocking_problems"] = problems
    return report


def validate_report(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    counts = report.get("category_counts", {})
    if counts.get("dated_stock_evidence", 0) <= 0:
        problems.append("missing_dated_stock_evidence")
    if counts.get("latest_stock_evidence", 0) <= 0:
        problems.append("missing_latest_stock_evidence")
    for item in report.get("live_runtime_status_files", []):
        if not item.get("tracked"):
            problems.append(f"live_runtime_status_not_tracked:{item.get('path')}")
        if not str(item.get("path", "")).startswith(MANAGER_STATUS_PREFIX):
            problems.append(f"live_runtime_status_outside_manager_status:{item.get('path')}")
    for guardrail in GUARDRAILS:
        if guardrail not in report.get("guardrails", []):
            problems.append(f"missing_guardrail:{guardrail}")
    return problems


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stock Runtime Artifact Governance",
        "",
        f"- CI gate: `{report['ci_gate_status']}`",
        f"- Scope: `{report['scope']}`",
        "",
        "## Category Counts",
    ]
    for name, count in sorted(report["category_counts"].items()):
        lines.append(f"- `{name}`: `{count}`")
    lines.extend(["", "## Live Runtime Status Files"])
    for item in report["live_runtime_status_files"]:
        lines.append(
            "- "
            f"`{item['path']}`: tracked={str(item['tracked']).lower()}; "
            f"local_skip_worktree={str(item['local_skip_worktree']).lower()}; "
            f"policy={item['policy']}"
        )
    lines.extend(["", "## Recommendations"])
    for item in report["recommendations"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Guardrails"])
    for item in report["guardrails"]:
        lines.append(f"- `{item}`")
    if report["blocking_problems"]:
        lines.extend(["", "## Blocking Problems"])
        for problem in report["blocking_problems"]:
            lines.append(f"- `{problem}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    args = parser.parse_args()

    report = build_runtime_artifact_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))
    if report["ci_gate_status"] != "pass":
        print("FAIL: stock runtime artifact governance found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
