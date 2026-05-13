#!/usr/bin/env python3
"""Read-only construction assistant report for local and CI use.

The assistant is deliberately passive: it reads repository metadata and known
status documents, then prints a report. It does not start services, call
webhooks, invoke n8n, send messages, or write project files.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

KEY_STATUS_PATHS = [
    "杰哥智能化系统全盘架构说明_20260504.md",
    "00杰哥系统总管/07文档/当前施工面板.md",
    "00杰哥系统总管/03数据/开工上下文/一键接续施工包_最新.md",
    "00杰哥系统总管/03数据/开工上下文/开工上下文摘要_最新.json",
    "00杰哥系统总管/03数据/运行状态/全系统只读总检与设计纲领对齐审计_最新.json",
    "00杰哥系统总管/03数据/运行状态/全系统只读总检与设计纲领对齐审计_最新.md",
    "00杰哥系统总管/03数据/状态快照/稳定中台心跳_最新.json",
    "00杰哥系统总管/03数据/运行状态/公网反向隧道守护探测_最新.json",
    "00杰哥系统总管/03数据/运行状态/D盘资源增长监控日报_最新.json",
    "00杰哥系统总管/03数据/运行状态/系统组成与依赖关系图谱_最新.md",
    "00杰哥系统总管/03数据/运行状态/个人智能母系统任务准入_最新.json",
    "00杰哥系统总管/03数据/运行状态/个人智能母系统任务队列调度_最新.json",
    "00杰哥系统总管/03数据/运行状态/个人智能母系统服务缺口清单_最新.json",
]

STOP_TERMS = [
    "真实发送",
    "n8n",
    "Webhook",
    "券商接口",
    "自动交易",
    "写正式库",
    "服务重启",
]

LOCAL_WORKFLOW_MECHANISMS = [
    {
        "circleci_logic": "trigger",
        "local_mechanism": "开工触发和施工面板",
        "path": "00杰哥系统总管/07文档/当前施工面板.md",
        "reuse_rule": "复用现有施工面板，不新增平行入口。",
    },
    {
        "circleci_logic": "standard_steps",
        "local_mechanism": "开工上下文和接续包",
        "path": "00杰哥系统总管/03数据/开工上下文/一键接续施工包_最新.md",
        "reuse_rule": "复用接续包读取顺序，不另造施工流程。",
    },
    {
        "circleci_logic": "readonly_environment",
        "local_mechanism": "全系统只读总检",
        "path": "00杰哥系统总管/03数据/运行状态/全系统只读总检与设计纲领对齐审计_最新.json",
        "reuse_rule": "只读检查优先，禁止把检查变成真实执行。",
    },
    {
        "circleci_logic": "pass_fail_gate",
        "local_mechanism": "模块验收标准",
        "path": "00杰哥系统总管/01配置/machine/acceptance_criteria.json",
        "reuse_rule": "沿用已有验收标准，只补缺失检查项。",
    },
    {
        "circleci_logic": "log_and_feedback",
        "local_mechanism": "施工计划与经验回灌",
        "path": "00杰哥系统总管/07文档/下一阶段施工计划_摸清家底转搭建主线_v1.0.md",
        "reuse_rule": "验收结果回到总管和进化系统，不沉淀孤立规则。",
    },
]

CLOUD_CI_BOUNDARY = "CircleCI only guards repository commits; local construction decisions stay in the D-drive system."

STOCK_GATE_PATHS = [
    {
        "name": "stock_sample_room_gate",
        "role": "sample room local acceptance gate",
        "path": "02杰哥扩展系统/01股票研究系统/02脚本/生成股票样本房本地验收面板.py",
    },
    {
        "name": "stock_mainline_gate",
        "role": "mainline construction acceptance gate",
        "path": "02杰哥扩展系统/01股票研究系统/02脚本/生成股票主线施工闸口面板.py",
    },
    {
        "name": "stock_sample_room_ci_wrapper",
        "role": "CircleCI wrapper for sample room gate",
        "path": "ci/stock_sample_room_ci_check.py",
    },
    {
        "name": "stock_mainline_ci_wrapper",
        "role": "CircleCI wrapper for mainline gate",
        "path": "ci/stock_mainline_ci_check.py",
    },
    {
        "name": "stock_maturity_ci_checker",
        "role": "CircleCI maturity audit for workflow closure and overlap",
        "path": "ci/stock_maturity_ci_check.py",
    },
    {
        "name": "stock_consolidation_index_ci_checker",
        "role": "CircleCI consolidation index for duplicate and overlap review",
        "path": "ci/stock_consolidation_index_ci_check.py",
    },
    {
        "name": "stock_closure_panel_ci_checker",
        "role": "CircleCI closure panel for owner-lane construction queues",
        "path": "ci/stock_closure_panel_ci_check.py",
    },
    {
        "name": "stock_quality_evidence_ci_checker",
        "role": "CircleCI quality-evidence closure check for the largest stock-system queue",
        "path": "ci/stock_quality_evidence_ci_check.py",
    },
    {
        "name": "stock_sample_pool_ci_checker",
        "role": "CircleCI sample-pool closure check for stock pool and sample-room ownership",
        "path": "ci/stock_sample_pool_ci_check.py",
    },
    {
        "name": "stock_manual_review_ci_checker",
        "role": "CircleCI manual-review closure check for stock verification workflow",
        "path": "ci/stock_manual_review_ci_check.py",
    },
    {
        "name": "stock_pre_push_gate_ci_checker",
        "role": "CircleCI pre-push gate closure check for draft and dry-run push workflow",
        "path": "ci/stock_pre_push_gate_ci_check.py",
    },
    {
        "name": "stock_review_loop_ci_checker",
        "role": "CircleCI review-loop closure check for feedback and learning workflow",
        "path": "ci/stock_review_loop_ci_check.py",
    },
]


@dataclass(frozen=True)
class GitChange:
    status: str
    path: str

    @property
    def category(self) -> str:
        normalized = self.path.replace("\\", "/")
        if (
            normalized.startswith("ci/")
            or normalized.startswith(".circleci/")
            or normalized == "杰哥智能化系统全盘架构说明_20260504.md"
        ):
            return "construction_support"
        if "运行状态" in normalized or "04日志" in normalized:
            return "runtime_status"
        return "project"


def run_git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def parse_status_short(text: str) -> list[GitChange]:
    changes: list[GitChange] = []
    for line in text.splitlines():
        if not line:
            continue
        status = line[:2].strip() or line[:2]
        path = line[3:] if len(line) > 3 else ""
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        changes.append(GitChange(status=status, path=path.strip('"')))
    return changes


def tracked_file_count() -> int:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    return len([name for name in raw.split(b"\0") if name])


def gitlinks() -> list[str]:
    paths: list[str] = []
    for line in run_git("ls-files", "-s").splitlines():
        parts = line.split(None, 3)
        if len(parts) == 4 and parts[0] == "160000":
            paths.append(parts[3].strip('"'))
    return paths


def path_info(relative_path: str) -> dict[str, Any]:
    path = ROOT / relative_path
    return {
        "path": relative_path,
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def local_workflow_mechanism_status() -> list[dict[str, Any]]:
    mechanisms: list[dict[str, Any]] = []
    for mechanism in LOCAL_WORKFLOW_MECHANISMS:
        item = dict(mechanism)
        item["exists"] = (ROOT / item["path"]).exists()
        item["action"] = "reuse_existing" if item["exists"] else "gap_to_fill"
        mechanisms.append(item)
    return mechanisms


def stock_gate_status() -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []
    for gate in STOCK_GATE_PATHS:
        item = dict(gate)
        item["exists"] = (ROOT / item["path"]).exists()
        item["action"] = "ci_guarded" if item["exists"] else "gap_to_fill"
        gates.append(item)
    return gates


def build_report() -> dict[str, Any]:
    changes = parse_status_short(run_git("status", "--short"))
    categories: dict[str, int] = {}
    for change in changes:
        categories[change.category] = categories.get(change.category, 0) + 1

    return {
        "tracked_files": tracked_file_count(),
        "branch": run_git("branch", "--show-current").strip(),
        "head": run_git("rev-parse", "HEAD").strip(),
        "dirty_files": len(changes),
        "dirty_categories": categories,
        "dirty_runtime_status_files": [
            change.path for change in changes if change.category == "runtime_status"
        ],
        "gitlinks": gitlinks(),
        "key_status_files": [path_info(path) for path in KEY_STATUS_PATHS],
        "redline_stop_terms": STOP_TERMS,
        "cloud_ci_boundary": CLOUD_CI_BOUNDARY,
        "integration_principle": "reuse existing local mechanisms before adding new ones",
        "local_workflow_mechanisms": local_workflow_mechanism_status(),
        "stock_gate_status": stock_gate_status(),
        "recommendation": recommend_next_step(changes),
    }


def recommend_next_step(changes: list[GitChange]) -> str:
    runtime_changes = [change for change in changes if change.category == "runtime_status"]
    project_changes = [change for change in changes if change.category == "project"]
    if project_changes:
        return "review_project_changes_before_new_construction"
    if runtime_changes:
        return "continue_low_risk_construction_without_touching_runtime_status"
    return "continue_low_risk_construction"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Construction Assistant Report",
        "",
        f"- Branch: `{report['branch']}`",
        f"- HEAD: `{report['head']}`",
        f"- Tracked files: `{report['tracked_files']}`",
        f"- Dirty files: `{report['dirty_files']}`",
        f"- Recommendation: `{report['recommendation']}`",
        "",
        "## Dirty Categories",
    ]
    if report["dirty_categories"]:
        for name, count in sorted(report["dirty_categories"].items()):
            lines.append(f"- `{name}`: `{count}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Gitlinks"])
    if report["gitlinks"]:
        for path in report["gitlinks"]:
            lines.append(f"- `{path}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Key Status Files"])
    for item in report["key_status_files"]:
        state = "present" if item["exists"] else "missing"
        size = item["bytes"] if item["bytes"] is not None else "-"
        lines.append(f"- `{item['path']}`: {state}, bytes={size}")

    lines.extend(["", "## Local Workflow Absorption"])
    lines.append(f"- Boundary: {report['cloud_ci_boundary']}")
    lines.append(f"- Principle: {report['integration_principle']}")
    for item in report["local_workflow_mechanisms"]:
        lines.append(
            "- "
            f"`{item['circleci_logic']}` -> `{item['local_mechanism']}`: "
            f"{item['action']}; `{item['path']}`; {item['reuse_rule']}"
        )

    lines.extend(["", "## Stock Gate Status"])
    stock_gate_items = report.get("stock_gate_status", [])
    if stock_gate_items:
        for item in stock_gate_items:
            state = "present" if item["exists"] else "missing"
            lines.append(
                "- "
                f"`{item['name']}`: {state}; {item['action']}; "
                f"`{item['path']}`; {item['role']}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Redline Stop Terms"])
    for term in report["redline_stop_terms"]:
        lines.append(f"- `{term}`")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
