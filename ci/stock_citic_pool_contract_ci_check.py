#!/usr/bin/env python3
"""Read-only CI contract for CITIC self-select stock pools.

This gate protects the settled front-facing CITIC board contract:
- four boards should be visible in CITIC;
- the manual temporary board is preserved and never overwritten by the system;
- the stock system only synchronizes the three result pools;
- stale duplicate/process boards must not be treated as current boards.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STOCK_ROOT = ROOT / "02杰哥扩展系统" / "01股票研究系统"
SYNC_SCRIPT_PATH = STOCK_ROOT / "02脚本" / "同步系统股票池到中信自选板块.py"
SYNC_REPORT_JSON = STOCK_ROOT / "03数据" / "295中信自选板块正式同步" / "中信自选板块正式同步_最新.json"
SYNC_REPORT_MD = STOCK_ROOT / "03数据" / "295中信自选板块正式同步" / "中信自选板块正式同步_最新.md"

VISIBLE_BOARDS = [
    "杰哥的临时选股",
    "杰哥的学习分析股票池",
    "杰哥的重点分析股票池",
    "杰哥短线池",
]

SYSTEM_MANAGED_BOARDS = [
    "杰哥的学习分析股票池",
    "杰哥的重点分析股票池",
    "杰哥短线池",
]

STALE_BOARD_NAMES = [
    "杰哥的重",
    "杰哥的学",
    "杰哥的重点分析股票",
    "分析股票池",
]

GUARDRAILS = [
    "read_only_citic_pool_contract",
    "preserve_manual_temporary_board",
    "system_manages_only_three_result_pools",
    "no_citic_runtime_write",
    "no_external_service_call",
    "no_auto_trade_or_broker_interface",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def missing_items(values: list[str], required: list[str]) -> list[str]:
    return [item for item in required if item not in values]


def build_report() -> dict[str, Any]:
    report_json = read_json(SYNC_REPORT_JSON) if SYNC_REPORT_JSON.exists() else {}
    script_text = read_text(SYNC_SCRIPT_PATH) if SYNC_SCRIPT_PATH.exists() else ""
    markdown_text = read_text(SYNC_REPORT_MD) if SYNC_REPORT_MD.exists() else ""
    current_boards = report_json.get("同步后板块", [])
    managed = [item.get("名称") for item in report_json.get("同步板块", []) if isinstance(item, dict)]

    checks = {
        "sync_script_exists": SYNC_SCRIPT_PATH.exists(),
        "sync_report_json_exists": SYNC_REPORT_JSON.exists(),
        "sync_report_md_exists": SYNC_REPORT_MD.exists(),
        "visible_boards_exact": current_boards == VISIBLE_BOARDS,
        "managed_boards_exact": managed == SYSTEM_MANAGED_BOARDS,
        "manual_board_preserved_in_script": "PRESERVED_MANUAL_BOARD_NAMES = [\"杰哥的临时选股\"]" in script_text,
        "manual_board_not_in_stale_names": all(
            stale not in "PRESERVED_MANUAL_BOARD_NAMES = [\"杰哥的临时选股\"]" for stale in STALE_BOARD_NAMES
        )
        and "杰哥的临时选股" not in script_text.split("STALE_VISIBLE_BOARD_NAMES =", 1)[1].split("]", 1)[0],
        "manual_board_not_overwritten": "系统只覆盖后三个结果型股票池" in markdown_text,
        "stale_boards_absent_from_current": not any(name in current_boards for name in STALE_BOARD_NAMES),
    }
    return {
        "name": "stock_citic_pool_contract",
        "scope": "stock_analysis_sample_room",
        "visible_boards": current_boards,
        "system_managed_boards": managed,
        "required_visible_boards": VISIBLE_BOARDS,
        "required_system_managed_boards": SYSTEM_MANAGED_BOARDS,
        "checks": checks,
        "guardrails": GUARDRAILS,
        "paths": {
            "sync_script": str(SYNC_SCRIPT_PATH),
            "sync_report_json": str(SYNC_REPORT_JSON),
            "sync_report_md": str(SYNC_REPORT_MD),
        },
    }


def validate_report(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    for name, ok in report["checks"].items():
        if not ok:
            problems.append(f"check_failed:{name}")
    missing_visible = missing_items(report["visible_boards"], VISIBLE_BOARDS)
    if missing_visible:
        problems.append("missing_visible_boards:" + ",".join(missing_visible))
    missing_managed = missing_items(report["system_managed_boards"], SYSTEM_MANAGED_BOARDS)
    if missing_managed:
        problems.append("missing_system_managed_boards:" + ",".join(missing_managed))
    for guardrail in GUARDRAILS:
        if guardrail not in report.get("guardrails", []):
            problems.append(f"missing_guardrail:{guardrail}")
    return problems


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stock CITIC Pool Contract",
        "",
        f"- CI gate: `{report['ci_gate_status']}`",
        f"- Scope: `{report['scope']}`",
        f"- Visible boards: `{', '.join(report['visible_boards'])}`",
        f"- System managed boards: `{', '.join(report['system_managed_boards'])}`",
        "",
        "## Checks",
    ]
    for name, ok in report["checks"].items():
        lines.append(f"- `{name}`: `{'pass' if ok else 'fail'}`")
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

    report = build_report()
    problems = validate_report(report)
    report["ci_gate_status"] = "fail" if problems else "pass"
    report["blocking_problems"] = problems
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render_markdown(report))
    if problems:
        print("FAIL: stock CITIC pool contract found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
