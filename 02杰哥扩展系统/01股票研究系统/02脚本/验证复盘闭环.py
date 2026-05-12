# -*- coding: utf-8 -*-
"""
名称：验证复盘闭环.py
作用：验收股票系统复盘闭环是否具备本地可运行证据，并明确自动调权是否启用，防止复盘框架被误写成自动修正规则引擎。
触发方式：python 验证复盘闭环.py
安全边界：只读本地复盘日志和脚本；只写L3验收报告；不发送企业微信；不触发n8n；不调用券商接口；不自动交易；不自动修改规则权重。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


PATTERNS = {
    "runtime_ledger_verify": "stock-review-ledger-runtime-verify-*.json",
    "minimal_review_verify": "stock-minimal-review-loop-verify-*.json",
    "minimal_review_run": "stock-minimal-review-loop-run-*.json",
    "l5_review_verify": "stock-l5-review-loop-verify-*.json",
    "l5_review_run": "stock-l5-review-loop-run-*.json",
    "weight_back_calibration_placeholder": "trial-pool-300-review-weight-back-calibration-placeholder-verify-*.json",
    "review_due_checklist": "*review-due-manual-checklist-verify-*.json",
}


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def log_dir(root: Path) -> Path:
    return root / "04日志"


def out_dir(root: Path) -> Path:
    return root / "03数据" / "245L3评分基础资产"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return ""


def load_json(path: Path) -> Any:
    text = read_text(path)
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        return {"raw_text": text[:4000]}


def latest_files(root: Path, pattern: str) -> list[Path]:
    base = log_dir(root)
    if not base.exists():
        return []
    files = [p for p in base.rglob(pattern) if p.is_file()]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def file_record(root: Path, key: str, pattern: str) -> dict[str, Any]:
    files = latest_files(root, pattern)
    latest = files[0] if files else None
    obj = load_json(latest) if latest else {}
    text = read_text(latest) if latest else ""
    return {
        "key": key,
        "pattern": pattern,
        "exists": latest is not None,
        "count": len(files),
        "latest_path": str(latest) if latest else "",
        "latest_mtime": datetime.fromtimestamp(latest.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if latest else "",
        "json_keys": list(obj.keys())[:20] if isinstance(obj, dict) else [],
        "contains_auto_trade_true": "自动交易\": true" in text or "not_auto_trade\": false" in text,
        "contains_external_send_true": "真实发送企业微信\": true" in text or "not_external_send\": false" in text,
        "contains_n8n_true": "触发n8n\": true" in text or "not_n8n\": false" in text,
    }


def scan_formal_weight_scripts(root: Path) -> list[str]:
    scripts = root / "02脚本"
    if not scripts.exists():
        return []
    hits: list[str] = []
    for path in scripts.glob("*.py"):
        name = path.name
        if "调权" in name or "权重" in name or "weight" in name.lower():
            text = read_text(path)
            if "placeholder" not in name.lower() and "占位" not in text and "候选" not in text:
                hits.append(str(path))
    return hits


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['key']} | {item['exists']} | {item['count']} | {item['latest_mtime']} | `{item['latest_path']}` |"
        for item in report["evidence_files"]
    ]
    lines = [
        "# 复盘闭环验收",
        "",
        f"生成时间：{report['generated_at']}",
        f"总体状态：{report['status']}",
        f"自动调权状态：{report['auto_weight_adjustment_status']}",
        "",
        "## 证据文件",
        "",
        "| 类型 | 存在 | 数量 | 最新时间 | 最新文件 |",
        "|---|---:|---:|---|---|",
        *rows,
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in report["blocking"]] or ["- 无"])
    lines.extend(["", "## 提醒项", ""])
    lines.extend([f"- {item}" for item in report["warnings"]] or ["- 无"])
    lines.extend([
        "",
        "## 结论口径",
        "",
        "- 复盘闭环有本地运行证据时，只能说具备复盘账本和人工复核沉淀能力。",
        "- 若没有正式调权脚本或配置，不得写成规则权重会自动调整。",
        "- 人工修正只能进入复盘/经验候选，不自动改正式评分规则。",
        "",
        "## 边界",
        "",
        "- 不真实发送企业微信",
        "- 不触发 n8n",
        "- 不调用券商接口",
        "- 不自动交易",
        "- 不自动修改规则权重",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    evidence = [file_record(root, key, pattern) for key, pattern in PATTERNS.items()]
    blocking: list[str] = []
    warnings: list[str] = []

    by_key = {item["key"]: item for item in evidence}
    if not by_key["runtime_ledger_verify"]["exists"]:
        blocking.append("缺少复盘账本运行验收文件：stock-review-ledger-runtime-verify")
    if not (by_key["minimal_review_verify"]["exists"] or by_key["l5_review_verify"]["exists"]):
        warnings.append("未发现最小复盘或L5复盘最新验收文件；当前只能确认复盘账本层，不确认完整结果回放层。")
    if not by_key["weight_back_calibration_placeholder"]["exists"]:
        warnings.append("未发现调权占位验收文件；需要继续明确自动调权未启用。")

    for item in evidence:
        if item["contains_auto_trade_true"]:
            blocking.append(f"{item['key']} 出现自动交易开启迹象")
        if item["contains_external_send_true"]:
            blocking.append(f"{item['key']} 出现真实外发开启迹象")
        if item["contains_n8n_true"]:
            blocking.append(f"{item['key']} 出现n8n触发开启迹象")

    formal_weight_scripts = scan_formal_weight_scripts(root)
    auto_weight_status = "not_enabled_manual_review_only"
    if formal_weight_scripts:
        auto_weight_status = "needs_manual_review_possible_formal_weight_script_found"
        blocking.append("发现疑似正式调权脚本，需要人工复核后才能允许进入统一验收")

    status = "passed" if not blocking else "failed"
    report = {
        "名称": "复盘闭环验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "自动验收报告",
        "status": status,
        "auto_weight_adjustment_status": auto_weight_status,
        "summary": {
            "evidence_file_types": len(evidence),
            "existing_evidence_types": sum(1 for item in evidence if item["exists"]),
            "blocking_count": len(blocking),
            "warning_count": len(warnings),
        },
        "evidence_files": evidence,
        "formal_weight_script_candidates": formal_weight_scripts,
        "blocking": blocking,
        "warnings": warnings,
        "front_output_rule": {
            "can_say": "复盘闭环具备本地账本和人工复核沉淀能力",
            "cannot_say": "规则权重会自动调整或系统会自动修正式评分规则",
            "human_feedback_rule": "人工修正只进入复盘/经验候选，不能自动改正式规则",
        },
        "safety_boundary": {
            "not_external_send": True,
            "not_n8n": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
            "not_auto_weight_change": True,
        },
    }
    json_path = out_dir(root) / "复盘闭环验收_最新.json"
    md_path = out_dir(root) / "复盘闭环验收_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({"status": status, "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
