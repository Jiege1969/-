# -*- coding: utf-8 -*-
"""
名称：执行P2S14影子入口人工填写任务包只读检查.py
作用：读取 P2-S13 差异预览样例，生成并检查人工填写任务包。
触发方式：python 执行P2S14影子入口人工填写任务包只读检查.py
安全边界：只读读取差异预览和任务包规则；仅输出人工填写任务包；不读取真实材料，不写目标入口，不触发外部动作。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
INCUBATION = ROOT / "02杰哥扩展系统" / "02-00孵化区"
RULE_JSON = INCUBATION / "P2_SHADOW_ENTRY_MANUAL_FILL_TASK_PACKET_001_影子入口人工填写任务包规则_20260509.json"
DIFF_SAMPLE_JSON = ROOT / "03杰哥进化系统" / "03数据" / "62P2S13影子入口填写差异预览只读检查" / "P2S13影子入口填写差异预览样例_20260509.json"
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "63P2S14影子入口人工填写任务包只读检查"
TASK_PACKET_SAMPLE_JSON = OUTPUT_DIR / "P2S14影子入口人工填写任务包样例_20260509.json"
LATEST_JSON = OUTPUT_DIR / "P2S14影子入口人工填写任务包只读检查_最新.json"
LATEST_MD = OUTPUT_DIR / "P2S14影子入口人工填写任务包只读检查_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def select_paths(diffs: list[dict[str, Any]], diff_type: str) -> list[dict[str, Any]]:
    return [
        {
            "path": diff["path"],
            "current_value": diff.get("current_value"),
            "instruction": "人工基于真实脱敏或授权材料填写" if diff_type == "candidate_placeholder" else "保持不变",
        }
        for diff in diffs
        if diff.get("diff_type") == diff_type
    ]


def build_task(diff_item: dict[str, Any], idx: int, rule: dict[str, Any]) -> dict[str, Any]:
    diffs = diff_item.get("diffs") or []
    return {
        "task_id": f"P2S14-MANUAL-FILL-TASK-{idx:03d}",
        "source_review_receipt_id": diff_item["review_receipt_id"],
        "target_line": diff_item["target_line"],
        "target_entry": diff_item["target_entry"],
        "target_path": diff_item["target_path"],
        "target_status_before_task": diff_item["target_status"],
        "candidate_fields": select_paths(diffs, "candidate_placeholder"),
        "must_remain_false_fields": select_paths(diffs, "must_remain_false"),
        "must_remain_pending_fields": select_paths(diffs, "must_remain_pending"),
        "must_not_change_fields": select_paths(diffs, "must_not_change"),
        "post_manual_fill_recheck": rule["post_manual_fill_recheck"],
        "preview_only": True,
        "task_packet_is_fill_result": False,
        "write_target_entry": False,
        "auto_fill_shadow_entry": False,
        "release_form": False,
        "formal_capability_claim": False,
        "real_material_read_by_script": False,
    }


def check_task(task: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for field in rule["required_task_fields"]:
        if field not in task:
            errors.append(f"缺少字段: {field}")
    hard = rule["hard_rules"]
    for key, expected in hard.items():
        if task.get(key) != expected:
            errors.append(f"{key} 未保持 {expected}")
    if task.get("task_packet_is_fill_result") is not rule["task_packet_is_fill_result"]:
        errors.append("任务包被误标为填写结果")
    if not task.get("candidate_fields"):
        errors.append("候选填写字段为空")
    if not task.get("must_remain_false_fields"):
        errors.append("必须保持 false 字段为空")
    if len(task.get("post_manual_fill_recheck") or []) < 4:
        errors.append("人工填写后复验步骤不足")
    return {
        "task_id": task["task_id"],
        "target_line": task["target_line"],
        "target_entry": task["target_entry"],
        "candidate_field_count": len(task.get("candidate_fields", [])),
        "must_remain_false_count": len(task.get("must_remain_false_fields", [])),
        "must_not_change_count": len(task.get("must_not_change_fields", [])),
        "status": "pass" if not errors else "fail",
        "errors": errors,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P2-S14 影子入口人工填写任务包只读检查",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['status']}",
        f"- 任务包数：{report['summary']['task_count']}",
        f"- 候选填写字段：{report['summary']['candidate_field_count']}",
        f"- 必须保持 false 字段：{report['summary']['must_remain_false_count']}",
        f"- 失败数：{report['summary']['failed']}",
        "",
        "| 任务 | 路由 | 目标入口 | 候选字段 | false字段 | 状态 |",
        "|:---|:---|:---|---:|---:|:---|",
    ]
    for item in report["checks"]:
        lines.append(f"| {item['task_id']} | {item['target_line']} | {item['target_entry']} | {item['candidate_field_count']} | {item['must_remain_false_count']} | {item['status']} |")
    lines.extend([
        "",
        "## 结论",
        "",
        report["conclusion"],
        "",
        "## 安全边界",
        "",
        "- 本检查只生成人工填写任务包。",
        "- 任务包不是填写结果，不写目标入口。",
        "- 不读取真实材料，不扫描用户目录，不触发外部动作。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    rule = read_json(RULE_JSON)
    diff_sample = read_json(DIFF_SAMPLE_JSON)
    diff_items = diff_sample.get("diff_items") or []
    tasks = [build_task(item, idx, rule) for idx, item in enumerate(diff_items, start=1)]
    checks = [check_task(task, rule) for task in tasks]
    failed = [item for item in checks if item["status"] != "pass"]
    status = "pass" if not failed else "fail"
    report = {
        "id": "P2S14_SHADOW_ENTRY_MANUAL_FILL_TASK_PACKET_READONLY_CHECK",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "summary": {
            "task_count": len(tasks),
            "passed": len(tasks) - len(failed),
            "failed": len(failed),
            "candidate_field_count": sum(len(task["candidate_fields"]) for task in tasks),
            "must_remain_false_count": sum(len(task["must_remain_false_fields"]) for task in tasks),
            "write_target_entry": sum(1 for task in tasks if task["write_target_entry"]),
            "auto_fill_shadow_entry": sum(1 for task in tasks if task["auto_fill_shadow_entry"]),
            "release_forms": sum(1 for task in tasks if task["release_form"]),
            "formal_capability_claim": sum(1 for task in tasks if task["formal_capability_claim"]),
            "real_material_read_by_script": sum(1 for task in tasks if task["real_material_read_by_script"]),
        },
        "task_packet_sample_path": str(TASK_PACKET_SAMPLE_JSON),
        "checks": checks,
        "conclusion": "影子入口人工填写任务包检查通过；4 份任务包仅列出人工填写字段、保持字段和复验步骤，0 项写入口或自动填写。" if status == "pass" else "影子入口人工填写任务包存在缺口，需修复后再交给人工填写。",
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
    TASK_PACKET_SAMPLE_JSON.write_text(json.dumps({"sample_only": True, "manual_fill_tasks": tasks}, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "总体状态": report["status"],
        "任务包数": report["summary"]["task_count"],
        "通过": report["summary"]["passed"],
        "失败": report["summary"]["failed"],
        "候选填写字段": report["summary"]["candidate_field_count"],
        "必须保持false字段": report["summary"]["must_remain_false_count"],
        "写入口数量": report["summary"]["write_target_entry"],
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
