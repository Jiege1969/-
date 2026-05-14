#!/usr/bin/env python3
"""Read-only change-impact check for the stock analysis system.

This gate answers a narrow CI question: what part of the stock system did the
current commit touch, and are the relevant guardrails still green?

It inspects only the committed diff for HEAD. Local dirty business files are
ignored so this remains useful in a busy workspace.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from ci import stock_system_contract_ci_check as contract
except ModuleNotFoundError:  # Running as `python ci/stock_change_impact_ci_check.py`.
    import stock_system_contract_ci_check as contract  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
STOCK_PREFIXES = [
    contract.STOCK_ROOT.relative_to(ROOT).as_posix() + "/",
    "02\u6770\u54e5\u6269\u5c55\u7cfb\u7edf/01\u80a1\u7968\u7814\u7a76\u7cfb\u7edf/",
]

STAGE_MARKERS = {
    "sample_pool": [
        "01",
        "270",
        "286",
        "L8",
        "L7",
        "L6",
        "L5",
        "\u80a1\u7968\u6c60",
        "\u6837\u672c",
        "\u5019\u9009",
    ],
    "manual_review": [
        "103",
        "116",
        "117",
        "119",
        "120",
        "121",
        "122",
        "\u4eba\u5de5",
        "\u6838\u9a8c",
        "\u5bfc\u5165",
    ],
    "quality_evidence": [
        "146",
        "149",
        "180",
        "186",
        "195",
        "219",
        "\u8d28\u91cf",
        "\u8bc1\u636e",
        "\u98ce\u9669",
        "\u62a5\u544a",
        "\u91d1\u878d",
    ],
    "pre_push_gate": [
        "96",
        "99",
        "136",
        "138",
        "247",
        "248",
        "249",
        "250",
        "\u63a8\u9001",
        "\u8349\u6848",
        "\u653e\u884c",
    ],
    "review_loop": [
        "107",
        "113",
        "114",
        "115",
        "137",
        "187",
        "\u590d\u76d8",
        "\u5b66\u4e60",
        "\u6743\u91cd",
        "\u63d0\u9192",
    ],
    "safe_boundary": [
        "150",
        "243",
        "252",
        "257",
        "\u5b89\u5168",
        "\u53ea\u8bfb",
        "\u9a8c\u6536",
        "\u771f\u5b9e",
        "n8n",
        "Webhook",
        "\u5238\u5546",
        "\u81ea\u52a8\u4ea4\u6613",
    ],
}

EXPLICIT_STAGE_RULES = [
    (("股票企业微信桥接入口.py",), ["pre_push_gate", "safe_boundary"]),
    (("验证股票企业微信体验入口状态.py",), ["pre_push_gate", "safe_boundary"]),
    (("验证股票推荐点击详情与手机排版.py",), ["quality_evidence", "pre_push_gate"]),
    (("03数据/289企业微信体验入口状态/",), ["pre_push_gate", "safe_boundary"]),
    (("03数据/196推荐点击详情与手机排版验收/",), ["quality_evidence", "pre_push_gate"]),
    (("同步系统股票池到中信自选板块.py",), ["sample_pool", "review_loop", "safe_boundary"]),
    (("03数据/295中信自选板块正式同步/",), ["sample_pool", "review_loop", "safe_boundary"]),
]

HIGH_RISK_MARKERS = [
    "\u771f\u5b9e",
    "n8n",
    "Webhook",
    "\u5238\u5546",
    "\u81ea\u52a8\u4ea4\u6613",
    "\u53d1\u9001",
    "\u7070\u5ea6",
]

CI_CONTRACT_MARKERS = [
    "stock_system_contract_ci_check.py",
    "stock_change_impact_ci_check.py",
    "stock_mainline_gate.py",
    "stock_",
]

GUARDRAILS = [
    "read_only_change_impact_check",
    "inspect_head_commit_only",
    "no_business_file_write",
    "no_external_service_call",
    "no_real_send_or_n8n_or_webhook",
]


def run_git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def changed_files_for_head() -> list[dict[str, str]]:
    raw = run_git("diff-tree", "--no-commit-id", "--name-status", "-r", "HEAD")
    changes: list[dict[str, str]] = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            changes.append({"status": parts[0], "path": parts[-1].replace("\\", "/")})
    if changes:
        return changes

    raw_root = run_git("diff-tree", "--root", "--no-commit-id", "--name-status", "-r", "HEAD")
    for line in raw_root.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            changes.append({"status": parts[0], "path": parts[-1].replace("\\", "/")})
    return changes


def stock_relative_path(path: str) -> str | None:
    normalized = path.replace("\\", "/")
    for prefix in STOCK_PREFIXES:
        if normalized.startswith(prefix):
            return normalized.removeprefix(prefix)
    return None


def path_category(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith(".circleci/") or normalized.startswith("ci/"):
        return "ci_support"
    relative = stock_relative_path(normalized)
    if relative is None:
        return "non_stock"
    if relative.startswith(("01配置/", "01閰嶇疆/")):
        return "stock_config"
    if relative.startswith(("02脚本/", "02鑴氭湰/")):
        return "stock_script"
    if relative.startswith(("03数据/", "03鏁版嵁/")):
        return "stock_data"
    if relative.startswith(("04日志/", "04鏃ュ織/")):
        return "stock_runtime_status"
    if relative.startswith(("07文档/", "07鏂囨。/")):
        return "stock_doc"
    return "stock_other"


def impacted_stages(path: str) -> list[str]:
    normalized = path.replace("\\", "/")
    category = path_category(normalized)
    if category == "ci_support":
        if any(marker in normalized for marker in CI_CONTRACT_MARKERS):
            return ["ci_contract"]
        return ["ci_support"]
    if not category.startswith("stock_"):
        return []

    relative = stock_relative_path(normalized) or normalized
    if normalized.endswith(contract.MAINLINE_SCRIPT_NAME) or normalized.endswith(
        "\u751f\u6210\u80a1\u7968\u4e3b\u7ebf\u65bd\u5de5\u95f8\u53e3\u9762\u677f.py"
    ):
        return [stage["name"] for stage in contract.CONTRACT_STAGES]
    if normalized.endswith("\u751f\u6210\u80a1\u7968\u6837\u672c\u623f\u672c\u5730\u9a8c\u6536\u9762\u677f.py"):
        return ["sample_pool", "quality_evidence", "safe_boundary"]

    for markers, stages in EXPLICIT_STAGE_RULES:
        if any(marker in relative for marker in markers):
            return stages

    stages = [
        stage
        for stage, markers in STAGE_MARKERS.items()
        if any(marker in relative for marker in markers)
    ]
    return stages or ["unmapped_stock"]


def has_high_risk_marker(path: str) -> bool:
    return any(marker.lower() in path.lower() for marker in HIGH_RISK_MARKERS)


def summarize_changes(changes: list[dict[str, str]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for change in changes:
        path = change["path"]
        stages = impacted_stages(path)
        summary.append(
            {
                "status": change["status"],
                "path": path,
                "category": path_category(path),
                "impacted_stages": stages,
                "high_risk_marker": has_high_risk_marker(path),
            }
        )
    return summary


def validate_report(report: dict[str, Any]) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    review_items: list[str] = []
    focused_statuses = report["system_contract"]["focused_gate_statuses"]

    for change in report["changes"]:
        stages = change["impacted_stages"]
        if change["category"].startswith("stock_") and "unmapped_stock" in stages:
            review_items.append(f"unmapped_stock_change:{change['path']}")
        if change["high_risk_marker"] and "safe_boundary" not in stages:
            problems.append(f"high_risk_change_without_safe_boundary:{change['path']}")
        for stage in stages:
            if stage in focused_statuses and focused_statuses[stage] != "pass":
                problems.append(f"impacted_stage_gate_not_pass:{stage}:{change['path']}")

    if report["system_contract"].get("ci_gate_status") != "pass":
        problems.append("stock_system_contract_not_pass")

    for guardrail in GUARDRAILS:
        if guardrail not in report["guardrails"]:
            problems.append(f"missing_guardrail:{guardrail}")

    return problems, review_items


def build_change_impact_report(changes: list[dict[str, str]] | None = None) -> dict[str, Any]:
    raw_changes = changes if changes is not None else changed_files_for_head()
    system_contract = contract.build_system_contract_report()
    report = {
        "name": "stock_change_impact",
        "scope": "head_commit_only",
        "head": run_git("rev-parse", "HEAD").strip(),
        "changes": summarize_changes(raw_changes),
        "system_contract": {
            "ci_gate_status": system_contract["ci_gate_status"],
            "focused_gate_statuses": system_contract["focused_gate_statuses"],
        },
        "guardrails": GUARDRAILS,
    }
    problems, review_items = validate_report(report)
    report["ci_gate_status"] = "fail" if problems else "pass"
    report["blocking_problems"] = problems
    report["review_items"] = review_items
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stock Change Impact",
        "",
        f"- CI gate: `{report['ci_gate_status']}`",
        f"- Scope: `{report['scope']}`",
        f"- HEAD: `{report['head'][:8]}`",
        f"- Changed files: `{len(report['changes'])}`",
        "",
        "## Changes",
    ]
    if not report["changes"]:
        lines.append("- none")
    for change in report["changes"]:
        stages = ", ".join(change["impacted_stages"]) or "none"
        lines.append(
            "- "
            f"`{change['status']}` `{change['path']}`: "
            f"category={change['category']}; stages={stages}; "
            f"high_risk={str(change['high_risk_marker']).lower()}"
        )

    lines.extend(["", "## Guardrails"])
    for guardrail in report["guardrails"]:
        lines.append(f"- `{guardrail}`")

    if report["review_items"]:
        lines.extend(["", "## Review Items"])
        for item in report["review_items"]:
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

    report = build_change_impact_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))

    if report["ci_gate_status"] != "pass":
        print("FAIL: stock change impact found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
