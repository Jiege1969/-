#!/usr/bin/env python3
"""Read-only maturity audit for the stock analysis system.

The audit turns the growing stock system into a CI-readable checklist:
- duplicate and overlap candidates;
- missing or thin construction areas;
- possible consolidation targets;
- workflow closure across input, analysis, output, human review, and feedback.

It never starts services, calls external endpoints, sends messages, or writes
project files. CI fails only on structural absence or explicit redline flags.
Optimization findings are reported as review items.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STOCK_ROOT = ROOT / "02杰哥扩展系统" / "01股票研究系统"
DATA_ROOT = STOCK_ROOT / "03数据"

ESSENTIAL_ROOTS = [
    "01配置",
    "02脚本",
    "03数据",
    "05入口工具",
    "07文档",
]

MATURITY_LANES = [
    {
        "name": "sample_pool",
        "label": "样本池和候选池",
        "purpose": "把股票池、样本池、候选池、深度研究池收成可持续样本房。",
        "required_terms": ["股票池", "样本池", "候选池", "观察池", "研究池"],
        "closure_terms": {
            "input": ["股票池", "样本池"],
            "analysis": ["候选池", "过滤池", "技术指标"],
            "output": ["分层日报", "报告"],
            "human_gate": ["人工", "核验"],
            "feedback": ["复盘", "学习"],
        },
    },
    {
        "name": "manual_review",
        "label": "人工核验",
        "purpose": "保证公告、财务、行业事件、证据链进入人工核验和受控导入。",
        "required_terms": ["人工核验", "批量填报", "导入", "证据核验"],
        "closure_terms": {
            "input": ["任务", "模板"],
            "analysis": ["预演", "完整性"],
            "output": ["结果", "报告"],
            "human_gate": ["人工核验", "填写"],
            "feedback": ["回填", "导入"],
        },
    },
    {
        "name": "pre_push_gate",
        "label": "推送前闸口",
        "purpose": "把候选包、草案、放行包和人工闸口串起来，但不触发真实发送。",
        "required_terms": ["推送前", "推送草案", "放行包", "交付"],
        "closure_terms": {
            "input": ["候选包", "草案"],
            "analysis": ["检查", "质量"],
            "output": ["放行包", "交付"],
            "human_gate": ["人工", "闸口"],
            "feedback": ["复盘", "回执"],
        },
    },
    {
        "name": "review_loop",
        "label": "复盘学习闭环",
        "purpose": "把T+1/T+3/T+5复盘、权重建议和学习面板收口。",
        "required_terms": ["复盘", "权重", "学习闭环", "到期提醒"],
        "closure_terms": {
            "input": ["提醒", "任务包"],
            "analysis": ["权重", "诊断"],
            "output": ["结果", "报告"],
            "human_gate": ["人工", "填写"],
            "feedback": ["学习", "闭环"],
        },
    },
    {
        "name": "quality_evidence",
        "label": "质量和证据链",
        "purpose": "让质量诊断、证据源、风险失效条件和报告可信度可追踪。",
        "required_terms": ["质量", "证据", "风险", "可信度", "金融专项复核"],
        "closure_terms": {
            "input": ["证据", "数据源"],
            "analysis": ["质量", "风险", "复核"],
            "output": ["面板", "报告"],
            "human_gate": ["人工核验", "专项复核"],
            "feedback": ["历史", "闭环"],
        },
    },
    {
        "name": "safe_boundary",
        "label": "安全边界",
        "purpose": "确认外部动作、企微、n8n、券商和自动交易继续处在只读或阻断状态。",
        "required_terms": ["安全边界", "真实发送", "只读", "自动交易", "n8n"],
        "closure_terms": {
            "input": ["入口", "清点"],
            "analysis": ["检查", "监测"],
            "output": ["状态", "验收"],
            "human_gate": ["人工", "最终验收"],
            "feedback": ["日志", "复测"],
        },
    },
]

REDLINE_TRUE_PATTERNS = [
    re.compile(r"真实发送[\"']?\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"触发n8n[\"']?\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"触发Webhook[\"']?\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"调用券商接口[\"']?\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"自动交易[\"']?\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\breal_send\s*=\s*True\b"),
    re.compile(r"\bREAL_SEND\s*=\s*True\b"),
]

SCAN_SUFFIXES = {".py", ".json", ".yaml", ".yml", ".toml", ".ps1", ".md", ".txt"}
MAX_SCAN_BYTES = 1_000_000


def immediate_data_dirs() -> list[Path]:
    if not DATA_ROOT.exists():
        return []
    return sorted([path for path in DATA_ROOT.iterdir() if path.is_dir()], key=lambda path: path.name)


def stock_files(limit: int | None = None) -> list[Path]:
    if not STOCK_ROOT.exists():
        return []
    files: list[Path] = []
    for path in STOCK_ROOT.rglob("*"):
        if path.is_file():
            files.append(path)
            if limit is not None and len(files) >= limit:
                break
    return files


def leading_code(name: str) -> str | None:
    match = re.match(r"^(\d+[A-Za-z]?)", name)
    return match.group(1) if match else None


def duplicate_number_candidates(directories: list[Path]) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for directory in directories:
        code = leading_code(directory.name)
        if code is None:
            continue
        groups.setdefault(code, []).append(directory.name)
    return [
        {"number": code, "directories": names, "count": len(names)}
        for code, names in sorted(groups.items())
        if len(names) > 1
    ]


def semantic_overlap_candidates(directories: list[Path]) -> list[dict[str, Any]]:
    terms = ["人工核验", "推送", "复盘", "质量", "风险", "证据", "候选", "样本", "验收", "报告"]
    candidates: list[dict[str, Any]] = []
    for term in terms:
        matches = [directory.name for directory in directories if term in directory.name]
        if len(matches) >= 4:
            candidates.append(
                {
                    "term": term,
                    "count": len(matches),
                    "sample": matches[:10],
                    "action": "review_for_possible_merge_or_indexing",
                }
            )
    return candidates


def term_hits(paths: list[Path], terms: list[str]) -> dict[str, int]:
    hits: dict[str, int] = {}
    names = [path.name for path in paths]
    for term in terms:
        hits[term] = sum(1 for name in names if term in name)
    return hits


def lane_status(lane: dict[str, Any], directories: list[Path]) -> dict[str, Any]:
    required_hits = term_hits(directories, lane["required_terms"])
    closure: dict[str, dict[str, Any]] = {}
    for stage, terms in lane["closure_terms"].items():
        hits = term_hits(directories, terms)
        closure[stage] = {
            "ok": any(count > 0 for count in hits.values()),
            "hits": hits,
        }

    missing_required_terms = [term for term, count in required_hits.items() if count == 0]
    missing_closure_stages = [stage for stage, info in closure.items() if not info["ok"]]

    if len(missing_closure_stages) >= 3:
        status = "thin"
    elif missing_required_terms or missing_closure_stages:
        status = "review"
    else:
        status = "closed"

    return {
        "name": lane["name"],
        "label": lane["label"],
        "purpose": lane["purpose"],
        "status": status,
        "required_hits": required_hits,
        "missing_required_terms": missing_required_terms,
        "closure": closure,
        "missing_closure_stages": missing_closure_stages,
    }


def read_text_safely(path: Path) -> str | None:
    if path.suffix not in SCAN_SUFFIXES:
        return None
    try:
        if path.stat().st_size > MAX_SCAN_BYTES:
            return None
    except OSError:
        return None
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except OSError:
            return None
    return path.read_text(encoding="utf-8", errors="replace")


def redline_true_hits() -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    scan_roots = [STOCK_ROOT / "01配置", STOCK_ROOT / "02脚本", STOCK_ROOT / "05入口工具"]
    for root in scan_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            text = read_text_safely(path)
            if text is None:
                continue
            for pattern in REDLINE_TRUE_PATTERNS:
                if pattern.search(text):
                    hits.append(
                        {
                            "path": path.relative_to(ROOT).as_posix(),
                            "pattern": pattern.pattern,
                        }
                    )
                    break
    return hits


def build_report() -> dict[str, Any]:
    directories = immediate_data_dirs()
    essential_status = [
        {
            "path": f"02杰哥扩展系统/01股票研究系统/{name}",
            "exists": (STOCK_ROOT / name).exists(),
        }
        for name in ESSENTIAL_ROOTS
    ]
    lanes = [lane_status(lane, directories) for lane in MATURITY_LANES]
    duplicate_candidates = duplicate_number_candidates(directories)
    overlap_candidates = semantic_overlap_candidates(directories)
    redline_hits = redline_true_hits()
    thin_lanes = [lane for lane in lanes if lane["status"] == "thin"]
    review_lanes = [lane for lane in lanes if lane["status"] == "review"]

    blocking_problems: list[str] = []
    if not STOCK_ROOT.exists():
        blocking_problems.append("stock_root_missing")
    missing_essentials = [item["path"] for item in essential_status if not item["exists"]]
    if missing_essentials:
        blocking_problems.append("essential_stock_roots_missing")

    return {
        "name": "stock_maturity_audit",
        "stock_root": STOCK_ROOT.relative_to(ROOT).as_posix(),
        "ci_gate_status": "fail" if blocking_problems else "pass",
        "blocking_problems": blocking_problems,
        "essential_roots": essential_status,
        "data_dir_count": len(directories),
        "tracked_stock_file_sample_count": len(stock_files(limit=2000)),
        "lanes": lanes,
        "thin_lanes": [lane["name"] for lane in thin_lanes],
        "review_lanes": [lane["name"] for lane in review_lanes],
        "duplicate_number_candidates": duplicate_candidates,
        "semantic_overlap_candidates": overlap_candidates,
        "redline_true_hits": redline_hits,
        "redline_review_mode": "inventory_only_existing_stock_assets_are_not_executed_by_ci",
        "recommendation": recommend_next_step(lanes, duplicate_candidates, overlap_candidates),
    }


def recommend_next_step(
    lanes: list[dict[str, Any]],
    duplicate_candidates: list[dict[str, Any]],
    overlap_candidates: list[dict[str, Any]],
) -> str:
    thin_lanes = [lane["name"] for lane in lanes if lane["status"] == "thin"]
    review_lanes = [lane["name"] for lane in lanes if lane["status"] == "review"]
    if thin_lanes:
        return "fill_thin_lanes_before_new_features"
    if duplicate_candidates or overlap_candidates:
        return "build_consolidation_index_before_renaming_or_merging"
    if review_lanes:
        return "close_review_lanes_with_existing_assets"
    return "continue_feature_work_under_ci_guard"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stock Maturity Audit",
        "",
        f"- CI gate: `{report['ci_gate_status']}`",
        f"- Data directories: `{report['data_dir_count']}`",
        f"- Recommendation: `{report['recommendation']}`",
        "",
        "## Essential Roots",
    ]
    for item in report["essential_roots"]:
        lines.append(f"- `{item['path']}`: {'present' if item['exists'] else 'missing'}")

    lines.extend(["", "## Workflow Closure"])
    for lane in report["lanes"]:
        missing = ", ".join(lane["missing_closure_stages"]) or "none"
        missing_terms = ", ".join(lane["missing_required_terms"]) or "none"
        lines.append(
            "- "
            f"`{lane['name']}` ({lane['label']}): {lane['status']}; "
            f"missing stages={missing}; missing terms={missing_terms}"
        )

    lines.extend(["", "## Duplicate Number Candidates"])
    if report["duplicate_number_candidates"]:
        for item in report["duplicate_number_candidates"][:20]:
            joined = "; ".join(item["directories"])
            lines.append(f"- `{item['number']}` count={item['count']}: {joined}")
    else:
        lines.append("- none")

    lines.extend(["", "## Semantic Overlap Candidates"])
    if report["semantic_overlap_candidates"]:
        for item in report["semantic_overlap_candidates"]:
            joined = "; ".join(item["sample"])
            lines.append(f"- `{item['term']}` count={item['count']}: {joined}")
    else:
        lines.append("- none")

    lines.extend(["", "## Redline True Hits"])
    lines.append(f"- mode: `{report.get('redline_review_mode', 'blocking')}`")
    if report["redline_true_hits"]:
        for item in report["redline_true_hits"]:
            lines.append(f"- `{item['path']}` matched `{item['pattern']}`")
    else:
        lines.append("- none")

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

    if report["ci_gate_status"] != "pass":
        print("FAIL: stock maturity audit found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
