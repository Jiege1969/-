# -*- coding: utf-8 -*-
"""
名称：执行P2S15人工填写后复验回执模板只读检查.py
作用：读取 P2-S14 人工填写任务包样例，生成并检查人工填写后复验回执空白样例。
触发方式：python 执行P2S15人工填写后复验回执模板只读检查.py
安全边界：只读读取任务包和回执模板；仅输出空白复验回执样例；不读取真实材料，不写目标入口，不触发外部动作。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
INCUBATION = ROOT / "02杰哥扩展系统" / "02-00孵化区"
TEMPLATE_JSON = INCUBATION / "P2_POST_MANUAL_FILL_RECHECK_RECEIPT_TEMPLATE_001_人工填写后复验回执模板_20260509.json"
TASK_SAMPLE_JSON = ROOT / "03杰哥进化系统" / "03数据" / "63P2S14影子入口人工填写任务包只读检查" / "P2S14影子入口人工填写任务包样例_20260509.json"
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "64P2S15人工填写后复验回执模板只读检查"
RECHECK_SAMPLE_JSON = OUTPUT_DIR / "P2S15人工填写后复验回执空白样例_20260509.json"
LATEST_JSON = OUTPUT_DIR / "P2S15人工填写后复验回执模板只读检查_最新.json"
LATEST_MD = OUTPUT_DIR / "P2S15人工填写后复验回执模板只读检查_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_receipt(task: dict[str, Any], idx: int) -> dict[str, Any]:
    return {
        "recheck_receipt_id": f"P2S15-POST-MANUAL-FILL-RECHECK-{idx:03d}",
        "source_manual_fill_task_id": task["task_id"],
        "target_line": task["target_line"],
        "target_entry": task["target_entry"],
        "target_path": task["target_path"],
        "human_filled": False,
        "json_parse_check": "pending_manual_fill",
        "redline_false_check": "pending_manual_fill",
        "target_entry_status_check": "pending_manual_fill",
        "readonly_shadow_regression": "pending_manual_fill",
        "ready_for_shadow_draft_candidate": False,
        "write_target_entry": False,
        "auto_generate_business_conclusion": False,
        "release_form": False,
        "formal_capability_claim": False,
        "sample_only": True,
    }


def check_receipt(receipt: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for field in template["required_fields"]:
        if field not in receipt:
            errors.append(f"缺少字段: {field}")
    allowed = set(template["allowed_recheck_status"])
    for field in template["required_rechecks"]:
        if receipt.get(field) not in allowed:
            errors.append(f"{field} 状态不允许")
    hard = template["hard_rules"]
    if receipt.get("release_form") is not hard["receipt_is_release_form"]:
        errors.append("release_form 未保持 false")
    for key in ("write_target_entry", "auto_generate_business_conclusion", "formal_capability_claim"):
        if receipt.get(key) is not hard[key]:
            errors.append(f"{key} 未保持 false")
    if receipt.get("ready_for_shadow_draft_candidate") and not receipt.get("human_filled"):
        errors.append("未人工填写却进入影子草案候选")
    return {
        "recheck_receipt_id": receipt["recheck_receipt_id"],
        "source_manual_fill_task_id": receipt["source_manual_fill_task_id"],
        "target_line": receipt["target_line"],
        "target_entry": receipt["target_entry"],
        "human_filled": receipt["human_filled"],
        "ready_for_shadow_draft_candidate": receipt["ready_for_shadow_draft_candidate"],
        "status": "pass" if not errors else "fail",
        "errors": errors,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P2-S15 人工填写后复验回执模板只读检查",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['status']}",
        f"- 回执数：{report['summary']['receipt_count']}",
        f"- 通过数：{report['summary']['passed']}",
        f"- 失败数：{report['summary']['failed']}",
        f"- 影子草案候选：{report['summary']['ready_for_shadow_draft_candidate']}",
        "",
        "| 回执 | 来源任务 | 路由 | 目标入口 | 人工填写 | 影子草案候选 | 状态 |",
        "|:---|:---|:---|:---|:---|:---|:---|",
    ]
    for item in report["checks"]:
        lines.append(f"| {item['recheck_receipt_id']} | {item['source_manual_fill_task_id']} | {item['target_line']} | {item['target_entry']} | {item['human_filled']} | {item['ready_for_shadow_draft_candidate']} | {item['status']} |")
    lines.extend([
        "",
        "## 结论",
        "",
        report["conclusion"],
        "",
        "## 安全边界",
        "",
        "- 本检查只生成空白复验回执样例。",
        "- 回执通过不代表人工已经填写，也不代表正式业务放行。",
        "- 不读取真实材料，不扫描用户目录，不写影子入口。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    template = read_json(TEMPLATE_JSON)
    sample = read_json(TASK_SAMPLE_JSON)
    tasks = sample.get("manual_fill_tasks") or []
    receipts = [build_receipt(task, idx) for idx, task in enumerate(tasks, start=1)]
    checks = [check_receipt(receipt, template) for receipt in receipts]
    failed = [item for item in checks if item["status"] != "pass"]
    status = "pass" if not failed else "fail"
    report = {
        "id": "P2S15_POST_MANUAL_FILL_RECHECK_RECEIPT_TEMPLATE_READONLY_CHECK",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "summary": {
            "receipt_count": len(receipts),
            "passed": len(receipts) - len(failed),
            "failed": len(failed),
            "human_filled": sum(1 for item in receipts if item["human_filled"]),
            "ready_for_shadow_draft_candidate": sum(1 for item in receipts if item["ready_for_shadow_draft_candidate"]),
            "write_target_entry": sum(1 for item in receipts if item["write_target_entry"]),
            "auto_generate_business_conclusion": sum(1 for item in receipts if item["auto_generate_business_conclusion"]),
            "release_forms": sum(1 for item in receipts if item["release_form"]),
            "formal_capability_claim": sum(1 for item in receipts if item["formal_capability_claim"]),
        },
        "recheck_sample_path": str(RECHECK_SAMPLE_JSON),
        "checks": checks,
        "conclusion": "人工填写后复验回执模板检查通过；4 份空白复验回执均保持待人工填写状态，0 项写入口、0 项业务结论、0 项正式放行。" if status == "pass" else "人工填写后复验回执模板存在缺口，需修复后再用于人工填写后复验。",
        "forbidden_actions": {
            "read_real_material": False,
            "scan_user_directory": False,
            "write_target_entry": False,
            "trigger_n8n": False,
            "send_wecom": False,
            "write_formal_database": False,
            "restart_service": False,
            "trade": False,
            "tax_filing": False,
            "render_or_publish_video": False,
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RECHECK_SAMPLE_JSON.write_text(json.dumps({"sample_only": True, "post_manual_fill_recheck_receipts": receipts}, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "总体状态": report["status"],
        "回执数": report["summary"]["receipt_count"],
        "通过": report["summary"]["passed"],
        "失败": report["summary"]["failed"],
        "人工填写": report["summary"]["human_filled"],
        "影子草案候选": report["summary"]["ready_for_shadow_draft_candidate"],
        "写入口数量": report["summary"]["write_target_entry"],
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
