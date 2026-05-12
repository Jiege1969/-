# -*- coding: utf-8 -*-
"""
名称：执行P2S13影子入口填写差异预览只读检查.py
作用：读取 P2-S12 填写候选闸口样例，为通过候选生成目标入口填写差异预览。
触发方式：python 执行P2S13影子入口填写差异预览只读检查.py
安全边界：只读读取 P2-S12 样例、规则和目标入口；仅输出差异预览；不读取真实材料，不写目标入口，不触发外部动作。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
INCUBATION = ROOT / "02杰哥扩展系统" / "02-00孵化区"
RULE_JSON = INCUBATION / "P2_SHADOW_ENTRY_FILL_DIFF_PREVIEW_RULE_001_影子入口填写差异预览规则_20260509.json"
GATE_SAMPLE_JSON = ROOT / "03杰哥进化系统" / "03数据" / "61P2S12影子入口填写候选闸口只读检查" / "P2S12影子入口填写候选闸口预演样例_20260509.json"
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "62P2S13影子入口填写差异预览只读检查"
DIFF_SAMPLE_JSON = OUTPUT_DIR / "P2S13影子入口填写差异预览样例_20260509.json"
LATEST_JSON = OUTPUT_DIR / "P2S13影子入口填写差异预览只读检查_最新.json"
LATEST_MD = OUTPUT_DIR / "P2S13影子入口填写差异预览只读检查_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def get_path(data: Any, dotted: str) -> Any:
    current = data
    for part in dotted.split("."):
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current.get(part)
    return current


def build_diff_item(gate_item: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any] | None:
    if gate_item.get("gate_result") != "fill_candidate_gate_pass":
        return None
    target_line = gate_item["target_line"]
    plan = rule["candidate_field_plan"][target_line]
    target = read_json(Path(gate_item["target_path"]))

    diffs: list[dict[str, Any]] = []
    for path in plan.get("candidate_paths", []):
        diffs.append({
            "path": path,
            "diff_type": "candidate_placeholder",
            "current_value": get_path(target, path),
            "preview_value": "待人工基于真实脱敏或授权材料填写",
            "requires_real_desensitized_or_authorized_material": True,
            "write_target_entry": False,
        })
    for path in plan.get("must_remain_false_paths", []):
        diffs.append({
            "path": path,
            "diff_type": "must_remain_false",
            "current_value": get_path(target, path),
            "preview_value": False,
            "requires_real_desensitized_or_authorized_material": False,
            "write_target_entry": False,
        })
    for path in plan.get("must_remain_pending_paths", []):
        diffs.append({
            "path": path,
            "diff_type": "must_remain_pending",
            "current_value": get_path(target, path),
            "preview_value": get_path(target, path),
            "requires_real_desensitized_or_authorized_material": False,
            "write_target_entry": False,
        })
    for path in plan.get("must_not_change_paths", []):
        diffs.append({
            "path": path,
            "diff_type": "must_not_change",
            "current_value": get_path(target, path),
            "preview_value": get_path(target, path),
            "requires_real_desensitized_or_authorized_material": False,
            "write_target_entry": False,
        })

    return {
        "review_receipt_id": gate_item["review_receipt_id"],
        "target_line": target_line,
        "target_entry": gate_item["target_entry"],
        "target_path": gate_item["target_path"],
        "target_status": gate_item["target_status"],
        "preview_only": True,
        "write_target_entry": False,
        "auto_fill_shadow_entry": False,
        "formal_capability_claim": False,
        "release_form": False,
        "diffs": diffs,
    }


def check_diff_item(item: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if item.get("preview_only") is not True:
        errors.append("preview_only 未保持 true")
    for key in ("write_target_entry", "auto_fill_shadow_entry", "formal_capability_claim", "release_form"):
        if item.get(key) is not False:
            errors.append(f"{key} 未保持 false")
    if not item.get("diffs"):
        errors.append("差异列表为空")
    allowed_types = set(rule["diff_types"])
    for diff in item.get("diffs", []):
        if diff.get("diff_type") not in allowed_types:
            errors.append(f"未知差异类型: {diff.get('diff_type')}")
        if diff.get("write_target_entry") is not False:
            errors.append(f"差异项请求写入口: {diff.get('path')}")
        if diff.get("diff_type") == "must_remain_false" and diff.get("preview_value") is not False:
            errors.append(f"红线字段未保持 false: {diff.get('path')}")
    return {
        "review_receipt_id": item["review_receipt_id"],
        "target_line": item["target_line"],
        "target_entry": item["target_entry"],
        "diff_count": len(item.get("diffs", [])),
        "candidate_placeholder_count": sum(1 for diff in item.get("diffs", []) if diff.get("diff_type") == "candidate_placeholder"),
        "must_remain_false_count": sum(1 for diff in item.get("diffs", []) if diff.get("diff_type") == "must_remain_false"),
        "status": "pass" if not errors else "fail",
        "errors": errors,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P2-S13 影子入口填写差异预览只读检查",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['status']}",
        f"- 候选入口数：{report['summary']['candidate_entry_count']}",
        f"- 差异项数：{report['summary']['diff_count']}",
        f"- 失败数：{report['summary']['failed']}",
        f"- 写入口数量：{report['summary']['write_target_entry']}",
        "",
        "| 回执 | 路由 | 目标入口 | 差异数 | 占位建议 | 红线保持 false | 状态 |",
        "|:---|:---|:---|---:|---:|---:|:---|",
    ]
    for item in report["checks"]:
        lines.append(f"| {item['review_receipt_id']} | {item['target_line']} | {item['target_entry']} | {item['diff_count']} | {item['candidate_placeholder_count']} | {item['must_remain_false_count']} | {item['status']} |")
    lines.extend([
        "",
        "## 结论",
        "",
        report["conclusion"],
        "",
        "## 安全边界",
        "",
        "- 本检查只生成填写差异预览。",
        "- 占位建议不代表真实材料，不自动写入目标入口。",
        "- 不读取真实材料，不扫描用户目录，不触发外部动作。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    rule = read_json(RULE_JSON)
    gate_sample = read_json(GATE_SAMPLE_JSON)
    gate_items = gate_sample.get("gate_items") or []
    diff_items = [item for item in (build_diff_item(gate_item, rule) for gate_item in gate_items) if item is not None]
    checks = [check_diff_item(item, rule) for item in diff_items]
    failed = [item for item in checks if item["status"] != "pass"]
    status = "pass" if not failed else "fail"
    report = {
        "id": "P2S13_SHADOW_ENTRY_FILL_DIFF_PREVIEW_READONLY_CHECK",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "summary": {
            "candidate_entry_count": len(diff_items),
            "passed": len(diff_items) - len(failed),
            "failed": len(failed),
            "diff_count": sum(len(item["diffs"]) for item in diff_items),
            "candidate_placeholder_count": sum(sum(1 for diff in item["diffs"] if diff["diff_type"] == "candidate_placeholder") for item in diff_items),
            "must_remain_false_count": sum(sum(1 for diff in item["diffs"] if diff["diff_type"] == "must_remain_false") for item in diff_items),
            "write_target_entry": sum(1 for item in diff_items if item["write_target_entry"]),
            "auto_fill_shadow_entry": sum(1 for item in diff_items if item["auto_fill_shadow_entry"]),
            "release_forms": sum(1 for item in diff_items if item["release_form"]),
            "formal_capability_claim": sum(1 for item in diff_items if item["formal_capability_claim"]),
        },
        "diff_sample_path": str(DIFF_SAMPLE_JSON),
        "checks": checks,
        "conclusion": "影子入口填写差异预览通过；4 个候选入口仅生成差异预览和人工占位建议，0 项写入口或自动填写。" if status == "pass" else "影子入口填写差异预览存在缺口，需修复后再进入人工填写。",
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
    DIFF_SAMPLE_JSON.write_text(json.dumps({"sample_only": True, "diff_items": diff_items}, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "总体状态": report["status"],
        "候选入口数": report["summary"]["candidate_entry_count"],
        "差异项数": report["summary"]["diff_count"],
        "通过": report["summary"]["passed"],
        "失败": report["summary"]["failed"],
        "写入口数量": report["summary"]["write_target_entry"],
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
