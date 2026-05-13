#!/usr/bin/env python3
"""Read-only consolidation index for stock-system maturity findings.

This script consumes the stock maturity audit and turns noisy overlap findings
into a construction queue. It does not rename, move, delete, or write project
assets. It only prints an index that helps decide what should become a parent
index, what should stay as an execution artifact, and what needs review.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

try:
    from ci import stock_maturity_ci_check as maturity
except ModuleNotFoundError:  # Running as `python ci/stock_consolidation_index_ci_check.py`.
    import stock_maturity_ci_check as maturity  # type: ignore[no-redef]


INDEX_TERMS = ["索引", "总览", "面板", "清单", "状态", "验收"]
EXECUTION_TERMS = ["执行", "导入", "写入", "放行", "确认", "复测"]
DRAFT_TERMS = ["草案", "模板", "影子", "占位", "预案", "样例"]
HISTORY_TERMS = ["历史", "记录", "日志", "复盘"]

TOPIC_OWNER_LANES = {
    "人工核验": "manual_review",
    "推送": "pre_push_gate",
    "复盘": "review_loop",
    "质量": "quality_evidence",
    "风险": "quality_evidence",
    "证据": "quality_evidence",
    "候选": "sample_pool",
    "样本": "sample_pool",
    "验收": "safe_boundary",
    "报告": "quality_evidence",
}


def classify_directory_name(name: str) -> str:
    if any(term in name for term in INDEX_TERMS):
        return "parent_or_index_candidate"
    if any(term in name for term in EXECUTION_TERMS):
        return "execution_artifact"
    if any(term in name for term in DRAFT_TERMS):
        return "draft_or_template"
    if any(term in name for term in HISTORY_TERMS):
        return "history_or_feedback"
    return "domain_artifact"


def directory_roles(names: list[str]) -> list[dict[str, str]]:
    return [{"name": name, "role": classify_directory_name(name)} for name in names]


def choose_duplicate_action(roles: list[dict[str, str]]) -> str:
    role_names = {item["role"] for item in roles}
    if "parent_or_index_candidate" in role_names:
        return "keep_parent_index_and_link_related_artifacts"
    if "execution_artifact" in role_names and "draft_or_template" in role_names:
        return "separate_template_from_execution_before_any_merge"
    if "history_or_feedback" in role_names:
        return "keep_history_separate_and_add_parent_index"
    return "assign_owner_lane_before_renaming_or_merging"


def build_duplicate_index(maturity_report: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for candidate in maturity_report["duplicate_number_candidates"]:
        roles = directory_roles(candidate["directories"])
        items.append(
            {
                "number": candidate["number"],
                "count": candidate["count"],
                "directories": roles,
                "action": choose_duplicate_action(roles),
            }
        )
    return items


def build_topic_index(maturity_report: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for candidate in maturity_report["semantic_overlap_candidates"]:
        term = candidate["term"]
        items.append(
            {
                "term": term,
                "count": candidate["count"],
                "owner_lane": TOPIC_OWNER_LANES.get(term, "stock_system_general"),
                "sample": directory_roles(candidate["sample"]),
                "action": "build_topic_parent_index_before_merging",
            }
        )
    return items


def build_consolidation_index() -> dict[str, Any]:
    maturity_report = maturity.build_report()
    duplicate_index = build_duplicate_index(maturity_report)
    topic_index = build_topic_index(maturity_report)
    blocking_problems = list(maturity_report["blocking_problems"])

    return {
        "name": "stock_consolidation_index",
        "ci_gate_status": "fail" if blocking_problems else "pass",
        "blocking_problems": blocking_problems,
        "maturity_recommendation": maturity_report["recommendation"],
        "duplicate_index": duplicate_index,
        "topic_index": topic_index,
        "next_queue": next_queue(duplicate_index, topic_index),
    }


def next_queue(duplicate_index: list[dict[str, Any]], topic_index: list[dict[str, Any]]) -> list[dict[str, str]]:
    queue: list[dict[str, str]] = []
    for item in duplicate_index[:5]:
        queue.append(
            {
                "kind": "duplicate_number",
                "target": item["number"],
                "action": item["action"],
            }
        )
    for item in topic_index[:5]:
        queue.append(
            {
                "kind": "semantic_overlap",
                "target": item["term"],
                "action": item["action"],
            }
        )
    return queue


def render_markdown(index: dict[str, Any]) -> str:
    lines = [
        "# Stock Consolidation Index",
        "",
        f"- CI gate: `{index['ci_gate_status']}`",
        f"- Maturity recommendation: `{index['maturity_recommendation']}`",
        "",
        "## Next Queue",
    ]
    if index["next_queue"]:
        for item in index["next_queue"]:
            lines.append(f"- `{item['kind']}` `{item['target']}`: {item['action']}")
    else:
        lines.append("- none")

    lines.extend(["", "## Duplicate Number Index"])
    if index["duplicate_index"]:
        for item in index["duplicate_index"][:20]:
            roles = "; ".join(f"{role['name']} [{role['role']}]" for role in item["directories"])
            lines.append(f"- `{item['number']}` count={item['count']}: {item['action']}; {roles}")
    else:
        lines.append("- none")

    lines.extend(["", "## Topic Index"])
    if index["topic_index"]:
        for item in index["topic_index"]:
            sample = "; ".join(f"{role['name']} [{role['role']}]" for role in item["sample"])
            lines.append(
                f"- `{item['term']}` -> `{item['owner_lane']}` count={item['count']}: "
                f"{item['action']}; {sample}"
            )
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    args = parser.parse_args()

    index = build_consolidation_index()
    if args.json:
        print(json.dumps(index, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(index))

    if index["ci_gate_status"] != "pass":
        print("FAIL: stock consolidation index found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
