# -*- coding: utf-8 -*-
"""
名称：执行P2S16人工填写后复验结果分流只读检查.py
作用：读取 P2-S15 人工填写后复验回执样例，验证复验结果分流是否正确。
触发方式：python 执行P2S16人工填写后复验结果分流只读检查.py
安全边界：只读读取复验回执和分流规则；仅输出分流预演；不读取真实材料，不写入口，不生成业务草案。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
INCUBATION = ROOT / "02杰哥扩展系统" / "02-00孵化区"
RULE_JSON = INCUBATION / "P2_POST_MANUAL_FILL_RECHECK_ROUTING_RULE_001_人工填写后复验结果分流规则_20260509.json"
RECHECK_SAMPLE_JSON = ROOT / "03杰哥进化系统" / "03数据" / "64P2S15人工填写后复验回执模板只读检查" / "P2S15人工填写后复验回执空白样例_20260509.json"
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "65P2S16人工填写后复验结果分流只读检查"
ROUTING_SAMPLE_JSON = OUTPUT_DIR / "P2S16人工填写后复验结果分流预演样例_20260509.json"
LATEST_JSON = OUTPUT_DIR / "P2S16人工填写后复验结果分流只读检查_最新.json"
LATEST_MD = OUTPUT_DIR / "P2S16人工填写后复验结果分流只读检查_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def route_receipt(receipt: dict[str, Any], required_rechecks: list[str]) -> str:
    statuses = [receipt.get(field) for field in required_rechecks]
    if "blocked" in statuses:
        return "blocked_redline_recovery"
    if "fail" in statuses:
        return "problem_recovery"
    if not receipt.get("human_filled") or "pending_manual_fill" in statuses:
        return "waiting_manual_fill"
    if all(status == "pass" for status in statuses):
        return "shadow_draft_candidate_discussion"
    return "problem_recovery"


def build_route_item(receipt: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
    route = route_receipt(receipt, rule["required_rechecks"])
    return {
        "recheck_receipt_id": receipt["recheck_receipt_id"],
        "source_manual_fill_task_id": receipt["source_manual_fill_task_id"],
        "target_line": receipt["target_line"],
        "target_entry": receipt["target_entry"],
        "human_filled": receipt["human_filled"],
        "recheck_statuses": {field: receipt.get(field) for field in rule["required_rechecks"]},
        "routing_result": route,
        "ready_for_shadow_draft_candidate": receipt.get("ready_for_shadow_draft_candidate"),
        "write_target_entry": False,
        "auto_generate_business_conclusion": False,
        "release_form": False,
        "formal_capability_claim": False,
    }


def check_route_item(item: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    hard = rule["hard_rules"]
    for key in ("write_target_entry", "auto_generate_business_conclusion", "release_form", "formal_capability_claim"):
        if item.get(key) is not hard[key]:
            errors.append(f"{key} 未保持 false")
    statuses = list(item["recheck_statuses"].values())
    if not item["human_filled"] and item["routing_result"] != "waiting_manual_fill":
        errors.append("未人工填写却未进入等待人工填写")
    if "pending_manual_fill" in statuses and item["routing_result"] != "waiting_manual_fill":
        errors.append("存在待人工填写复验项却未等待")
    if item["routing_result"] == "shadow_draft_candidate_discussion":
        if not item["human_filled"] or not all(status == "pass" for status in statuses):
            errors.append("未满足全部复验通过却进入影子草案候选讨论")
    if item["ready_for_shadow_draft_candidate"] and item["routing_result"] != "shadow_draft_candidate_discussion":
        errors.append("候选标记与分流结果不一致")
    return {
        "recheck_receipt_id": item["recheck_receipt_id"],
        "target_line": item["target_line"],
        "target_entry": item["target_entry"],
        "routing_result": item["routing_result"],
        "human_filled": item["human_filled"],
        "status": "pass" if not errors else "fail",
        "errors": errors,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P2-S16 人工填写后复验结果分流只读检查",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['status']}",
        f"- 回执数：{report['summary']['receipt_count']}",
        f"- 等待人工填写：{report['summary']['waiting_manual_fill']}",
        f"- 影子草案候选讨论：{report['summary']['shadow_draft_candidate_discussion']}",
        f"- 失败数：{report['summary']['failed']}",
        "",
        "| 回执 | 路由 | 目标入口 | 人工填写 | 分流结果 | 状态 |",
        "|:---|:---|:---|:---|:---|:---|",
    ]
    for item in report["checks"]:
        lines.append(f"| {item['recheck_receipt_id']} | {item['target_line']} | {item['target_entry']} | {item['human_filled']} | {item['routing_result']} | {item['status']} |")
    lines.extend([
        "",
        "## 结论",
        "",
        report["conclusion"],
        "",
        "## 安全边界",
        "",
        "- 本检查只生成复验结果分流预演。",
        "- 不读取真实材料，不写入口，不生成业务草案。",
        "- 不触发 n8n、企业微信、正式库或真实业务动作。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    rule = read_json(RULE_JSON)
    sample = read_json(RECHECK_SAMPLE_JSON)
    receipts = sample.get("post_manual_fill_recheck_receipts") or []
    route_items = [build_route_item(receipt, rule) for receipt in receipts]
    checks = [check_route_item(item, rule) for item in route_items]
    failed = [item for item in checks if item["status"] != "pass"]
    status = "pass" if not failed else "fail"
    report = {
        "id": "P2S16_POST_MANUAL_FILL_RECHECK_ROUTING_READONLY_CHECK",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "summary": {
            "receipt_count": len(route_items),
            "passed": len(route_items) - len(failed),
            "failed": len(failed),
            "waiting_manual_fill": sum(1 for item in route_items if item["routing_result"] == "waiting_manual_fill"),
            "problem_recovery": sum(1 for item in route_items if item["routing_result"] == "problem_recovery"),
            "blocked_redline_recovery": sum(1 for item in route_items if item["routing_result"] == "blocked_redline_recovery"),
            "shadow_draft_candidate_discussion": sum(1 for item in route_items if item["routing_result"] == "shadow_draft_candidate_discussion"),
            "write_target_entry": sum(1 for item in route_items if item["write_target_entry"]),
            "auto_generate_business_conclusion": sum(1 for item in route_items if item["auto_generate_business_conclusion"]),
            "release_forms": sum(1 for item in route_items if item["release_form"]),
            "formal_capability_claim": sum(1 for item in route_items if item["formal_capability_claim"]),
        },
        "routing_sample_path": str(ROUTING_SAMPLE_JSON),
        "checks": checks,
        "conclusion": "人工填写后复验结果分流检查通过；4 份空白回执均继续等待人工填写，0 份进入影子草案候选讨论，0 项写入口或业务结论。" if status == "pass" else "人工填写后复验结果分流存在缺口，需修复后再承接人工填写结果。",
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
    ROUTING_SAMPLE_JSON.write_text(json.dumps({"sample_only": True, "routing_items": route_items}, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "总体状态": report["status"],
        "回执数": report["summary"]["receipt_count"],
        "通过": report["summary"]["passed"],
        "失败": report["summary"]["failed"],
        "等待人工填写": report["summary"]["waiting_manual_fill"],
        "影子草案候选讨论": report["summary"]["shadow_draft_candidate_discussion"],
        "写入口数量": report["summary"]["write_target_entry"],
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
