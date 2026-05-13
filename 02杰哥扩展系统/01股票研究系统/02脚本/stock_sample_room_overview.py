#!/usr/bin/env python3
"""Read-only stock sample-room construction overview.

This script summarizes the stock system's current local materials into a small
construction overview. It is intentionally passive by default: it scans local
files, prints JSON or Markdown, and writes only when --write is explicitly used.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


LANES = [
    {
        "name": "sample_pool",
        "position": "source",
        "keywords": ["\u6837\u672c", "\u80a1\u7968\u6c60", "\u5019\u9009", "L8", "L7", "L6", "L5"],
        "next_action": "keep_sample_pool_and_layered_candidates_current",
    },
    {
        "name": "manual_review",
        "position": "human_gate",
        "keywords": ["\u4eba\u5de5", "\u6838\u9a8c", "\u56de\u6267", "\u586b\u5199", "\u590d\u6838"],
        "next_action": "keep_manual_review_templates_and_receipts_aligned",
    },
    {
        "name": "quality_evidence",
        "position": "evidence",
        "keywords": ["\u8bc1\u636e", "\u8d28\u91cf", "\u98ce\u9669", "\u62a5\u544a", "\u8d22\u62a5"],
        "next_action": "keep_evidence_sources_visible_before_frontend_conclusions",
    },
    {
        "name": "pre_push_gate",
        "position": "pre_output",
        "keywords": ["\u63a8\u9001", "\u53d1\u9001", "\u8349\u6848", "\u95f8\u53e3", "dry"],
        "next_action": "keep_outputs_in_dry_run_until_manual_release",
    },
    {
        "name": "review_loop",
        "position": "feedback",
        "keywords": ["\u590d\u76d8", "\u5b66\u4e60", "\u53cd\u9988", "\u95ed\u73af", "\u6743\u91cd"],
        "next_action": "feed_review_results_back_into_lightweight_learning",
    },
    {
        "name": "safe_boundary",
        "position": "crosscutting_guard",
        "keywords": ["\u5b89\u5168", "\u53ea\u8bfb", "\u9a8c\u6536", "n8n", "Webhook", "\u5238\u5546", "\u81ea\u52a8\u4ea4\u6613"],
        "next_action": "keep_real_send_n8n_webhook_broker_and_auto_trade_disabled",
    },
]

SAFETY_FLAGS = {
    "real_send": False,
    "n8n": False,
    "webhook": False,
    "broker_interface": False,
    "auto_trade": False,
    "service_restart": False,
}

OUTPUT_DIR_PARTS = ("03", "286")


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def child_by_prefix(root: Path, prefix: str) -> Path:
    for child in sorted(root.iterdir()):
        if child.name.startswith(prefix):
            return child
    return root / prefix


def stock_dirs(root: Path) -> dict[str, Path]:
    return {
        "config": child_by_prefix(root, "01"),
        "scripts": child_by_prefix(root, "02"),
        "data": child_by_prefix(root, "03"),
        "logs": child_by_prefix(root, "04"),
        "docs": child_by_prefix(root, "07"),
    }


def iter_local_files(path: Path, suffixes: tuple[str, ...]) -> list[Path]:
    if not path.exists():
        return []
    return sorted(
        item
        for item in path.rglob("*")
        if item.is_file() and item.suffix.lower() in suffixes and "__pycache__" not in item.parts
    )


def relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def keyword_hit(path: Path, keywords: list[str]) -> bool:
    name = path.name.lower()
    return any(keyword.lower() in name for keyword in keywords)


def lane_evidence(root: Path, lane: dict[str, Any], files_by_area: dict[str, list[Path]]) -> dict[str, Any]:
    matches: dict[str, list[str]] = {}
    for area, files in files_by_area.items():
        hits = [relative(path, root) for path in files if keyword_hit(path, lane["keywords"])]
        matches[area] = hits[:8]

    script_count = len(matches.get("scripts", []))
    data_count = len(matches.get("data", []))
    doc_count = len(matches.get("docs", []))
    evidence_count = script_count + data_count + doc_count
    status = "closed" if evidence_count >= 3 and script_count >= 1 else "review"
    if lane["name"] == "safe_boundary" and not all(value is False for value in SAFETY_FLAGS.values()):
        status = "blocked"

    return {
        "name": lane["name"],
        "position": lane["position"],
        "status": status,
        "evidence_count": evidence_count,
        "script_count": script_count,
        "data_count": data_count,
        "doc_count": doc_count,
        "evidence": matches,
        "next_action": lane["next_action"],
    }


def build_overview(root: Path | None = None) -> dict[str, Any]:
    root = root or module_root()
    dirs = stock_dirs(root)
    files_by_area = {
        "scripts": iter_local_files(dirs["scripts"], (".py", ".ps1")),
        "data": iter_local_files(dirs["data"], (".json", ".md", ".csv")),
        "docs": iter_local_files(dirs["docs"], (".md", ".txt")),
    }
    lanes = [lane_evidence(root, lane, files_by_area) for lane in LANES]
    status_counts: dict[str, int] = {}
    for lane in lanes:
        status_counts[lane["status"]] = status_counts.get(lane["status"], 0) + 1
    overview_state = "continue" if status_counts.get("blocked", 0) == 0 else "blocked"
    if status_counts.get("review", 0) > 0 and overview_state == "continue":
        overview_state = "review_before_continue"
    return {
        "name": "stock_sample_room_overview",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root),
        "overview_state": overview_state,
        "status_counts": status_counts,
        "lane_count": len(lanes),
        "lanes": lanes,
        "safety_flags": SAFETY_FLAGS,
        "guardrails": [
            "read_only_by_default",
            "no_external_service_call",
            "no_real_send",
            "no_n8n_or_webhook",
            "no_broker_or_auto_trade",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stock Sample Room Overview",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- State: `{report['overview_state']}`",
        f"- Lanes: `{report['lane_count']}`",
        "",
        "## Lanes",
    ]
    for lane in report["lanes"]:
        lines.append(
            "- "
            f"`{lane['name']}`: status={lane['status']}; "
            f"scripts={lane['script_count']}; data={lane['data_count']}; docs={lane['doc_count']}; "
            f"next={lane['next_action']}"
        )
    lines.extend(["", "## Safety Flags"])
    for name, enabled in report["safety_flags"].items():
        lines.append(f"- `{name}`: `{str(enabled).lower()}`")
    lines.extend(["", "## Guardrails"])
    for item in report["guardrails"]:
        lines.append(f"- `{item}`")
    return "\n".join(lines) + "\n"


def default_output_dir(root: Path) -> Path:
    data_dir = child_by_prefix(root, OUTPUT_DIR_PARTS[0])
    matches = [item for item in sorted(data_dir.iterdir()) if item.name.startswith(OUTPUT_DIR_PARTS[1])] if data_dir.exists() else []
    if matches:
        return matches[0]
    return data_dir / f"{OUTPUT_DIR_PARTS[1]}stock_sample_room_overview"


def write_outputs(report: dict[str, Any], root: Path | None = None) -> dict[str, str]:
    root = root or module_root()
    output_dir = default_output_dir(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "stock_sample_room_overview_latest.json"
    md_path = output_dir / "stock_sample_room_overview_latest.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--markdown", action="store_true", help="print Markdown instead of JSON")
    parser.add_argument("--write", action="store_true", help="write latest overview files")
    args = parser.parse_args()

    report = build_overview()
    if args.write:
        report["outputs"] = write_outputs(report)
    if args.markdown:
        print(render_markdown(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["overview_state"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
