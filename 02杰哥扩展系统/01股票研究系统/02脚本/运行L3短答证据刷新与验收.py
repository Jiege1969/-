# -*- coding: utf-8 -*-
"""
名称：运行L3短答证据刷新与验收.py
作用：顺序运行L3短答相关的低风险证据刷新和自动验收。
触发方式：python 运行L3短答证据刷新与验收.py
安全边界：只读公开行情/本地账本；只写股票系统L3证据资产和验收报告；不真实发送企业微信；不触发n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def decode_output(data: bytes) -> str:
    for encoding in ("utf-8", "gbk", "cp936"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def run_script(root: Path, name: str, timeout: int = 180) -> dict[str, Any]:
    script = root / "02脚本" / name
    if not script.exists():
        return {
            "script": name,
            "status": "missing",
            "returncode": None,
            "stdout": "",
            "stderr": f"脚本不存在：{script}",
        }
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(root),
        capture_output=True,
        timeout=timeout,
    )
    return {
        "script": name,
        "status": "passed" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "stdout": decode_output(result.stdout).strip(),
        "stderr": decode_output(result.stderr).strip(),
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def markdown(report: dict[str, Any]) -> str:
    rows = []
    for item in report["steps"]:
        rows.append(f"| {item['script']} | {item['status']} | {item['returncode']} |")
    return "\n".join([
        "# L3短答证据刷新与验收",
        "",
        f"生成时间：{report['generated_at']}",
        f"总体状态：{report['status']}",
        "",
        "| 脚本 | 状态 | 返回码 |",
        "|---|---:|---:|",
        *rows,
        "",
        "## 边界",
        "",
        "- 不真实发送企业微信",
        "- 不触发 n8n",
        "- 不调用券商接口",
        "- 不自动交易",
        "",
    ])


def summary_report(report: dict[str, Any]) -> dict[str, Any]:
    failed = [item for item in report["steps"] if item.get("status") != "passed"]
    step_ids = [
        "market_style_update",
        "industry_price_card_update",
        "industry_price_ledger_validation",
        "policy_event_validation",
        "l3_scoring_contract_validation",
        "review_loop_validation",
        "l3_sample_coverage_validation",
        "l3_wecom_short_answer_validation",
        "l3_front_evidence_wording_validation",
        "l3_wecom_bridge_dry_run",
    ]
    return {
        "name": "l3_unified_validation_summary",
        "generated_at": report["generated_at"],
        "status": report["status"],
        "step_count": len(report["steps"]),
        "passed_count": len(report["steps"]) - len(failed),
        "failed_count": len(failed),
        "steps": [
            {
                "step_id": step_ids[index] if index < len(step_ids) else f"step_{index + 1}",
                "status": item.get("status"),
                "returncode": item.get("returncode"),
            }
            for index, item in enumerate(report["steps"])
        ],
        "failed_steps": [
            {
                "step_id": step_ids[report["steps"].index(item)] if item in report["steps"] and report["steps"].index(item) < len(step_ids) else "unknown",
                "status": item.get("status"),
                "returncode": item.get("returncode"),
                "stderr_preview": str(item.get("stderr") or "")[:500],
            }
            for item in failed
        ],
        "safety_boundary": report["safety_boundary"],
    }


def summary_markdown(summary: dict[str, Any]) -> str:
    rows = [
        f"| {item['step_id']} | {item['status']} | {item['returncode']} |"
        for item in summary["steps"]
    ]
    return "\n".join([
        "# L3 Unified Validation Summary",
        "",
        f"generated_at: {summary['generated_at']}",
        f"status: {summary['status']}",
        f"passed: {summary['passed_count']}/{summary['step_count']}",
        "",
        "| step_id | status | returncode |",
        "|---|---:|---:|",
        *rows,
        "",
        "## Safety",
        "",
        f"- not_external_send: {summary['safety_boundary']['not_external_send']}",
        f"- not_n8n: {summary['safety_boundary']['not_n8n']}",
        f"- not_broker_interface: {summary['safety_boundary']['not_broker_interface']}",
        f"- not_auto_trade: {summary['safety_boundary']['not_auto_trade']}",
        "",
    ])


def main() -> int:
    root = module_root()
    steps = [
        run_script(root, "更新L3市场风格日表_东方财富只读.py", timeout=240),
        run_script(root, "更新行业价格趋势证据卡_本地观测.py", timeout=120),
        run_script(root, "验证行业价格观测账本.py", timeout=120),
        run_script(root, "验证政策事件库.py", timeout=120),
        run_script(root, "验证L3评分契约执行.py", timeout=120),
        run_script(root, "验证复盘闭环.py", timeout=120),
        run_script(root, "验证L3样本覆盖.py", timeout=120),
        run_script(root, "验证L3企业微信短答适配器.py", timeout=180),
        run_script(root, "验证L3前台证据状态话术.py", timeout=120),
        run_script(root, "验证L3企业微信短答桥接dry_run.py", timeout=180),
    ]
    ok = all(item["status"] == "passed" for item in steps)
    report = {
        "名称": "L3短答证据刷新与验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "passed" if ok else "failed",
        "steps": steps,
        "safety_boundary": {
            "not_external_send": True,
            "not_n8n": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }
    out_dir = root / "03数据" / "245L3评分基础资产"
    json_path = out_dir / "L3短答证据刷新与验收_最新.json"
    md_path = out_dir / "L3短答证据刷新与验收_最新.md"
    summary = summary_report(report)
    summary_json_path = out_dir / "l3_unified_validation_summary_latest.json"
    summary_md_path = out_dir / "l3_unified_validation_summary_latest.md"
    write_json(json_path, report)
    write_text(md_path, markdown(report))
    write_json(summary_json_path, summary)
    write_text(summary_md_path, summary_markdown(summary))
    print(json.dumps({
        "status": report["status"],
        "json": str(json_path),
        "md": str(md_path),
        "summary_json": str(summary_json_path),
        "summary_md": str(summary_md_path),
    }, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

