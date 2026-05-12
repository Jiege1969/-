# -*- coding: utf-8 -*-
"""
名称：执行P2S6真实材料接入分流回执模板只读检查.py
作用：检查 P2-S6 真实材料接入分流回执模板是否覆盖分流门字段、路由、暂停和红线要求。
触发方式：python 执行P2S6真实材料接入分流回执模板只读检查.py
安全边界：只读读取分流门、回执模板和索引；仅在 03进化系统03数据输出报告；不触发 n8n，不发送企业微信，不写正式库，不重启服务。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
INCUBATION = ROOT / "02杰哥扩展系统" / "02-00孵化区"
GATE_JSON = INCUBATION / "P2_REAL_MATERIAL_INTAKE_GATE_001_真实材料接入分流门_20260509.json"
TEMPLATE_MD = INCUBATION / "P2_REAL_MATERIAL_INTAKE_RECEIPT_TEMPLATE_001_真实材料接入分流回执模板_20260509.md"
TEMPLATE_JSON = INCUBATION / "P2_REAL_MATERIAL_INTAKE_RECEIPT_TEMPLATE_001_真实材料接入分流回执模板_20260509.json"
TOTAL_INDEX_MD = INCUBATION / "孵化区影子底座总索引_最新.md"
TOTAL_INDEX_JSON = INCUBATION / "孵化区影子底座总索引_最新.json"
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "55P2S6真实材料接入分流回执模板只读检查"
LATEST_JSON = OUTPUT_DIR / "P2S6真实材料接入分流回执模板只读检查_最新.json"
LATEST_MD = OUTPUT_DIR / "P2S6真实材料接入分流回执模板只读检查_最新.md"


EXTRA_REQUIRED_RECEIPT_FIELDS = {
    "receipt_id",
    "received_at",
    "target_entry",
    "pause_reasons",
    "human_review_status",
    "redline_status",
    "redline_reasons",
    "formal_capability_claim",
    "receipt_status",
}

REQUIRED_FALSE_KEYS = {
    "trigger_n8n",
    "send_wecom",
    "write_formal_database",
    "scan_unspecified_directory",
    "copy_sensitive_material",
    "tax_filing",
    "invoice_action",
    "tax_refund_action",
    "trade",
    "connect_real_office_system",
    "render_upload_or_publish_video",
    "claim_formal_capability",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P2-S6 真实材料接入分流回执模板只读检查",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['status']}",
        f"- 错误数：{len(report['errors'])}",
        f"- 提醒数：{len(report['warnings'])}",
        f"- 字段检查数：{report['summary']['field_count']}",
        f"- 红线字段检查数：{report['summary']['redline_false_check_count']}",
        "",
        "## 结论",
        "",
        report["conclusion"],
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in report["errors"]] or ["- 无"])
    lines.extend(["", "## 提醒", ""])
    lines.extend([f"- {item}" for item in report["warnings"]] or ["- 无"])
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 本检查只读读取分流门、回执模板和索引。",
        "- 不触发 n8n，不发送企业微信，不写正式库。",
        "- 不重启服务，不交易，不办理税务，不渲染或发布视频。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    errors: list[str] = []
    warnings: list[str] = []
    field_checks: list[dict[str, Any]] = []
    redline_checks: list[dict[str, Any]] = []

    for path, label in [(GATE_JSON, "分流门"), (TEMPLATE_MD, "回执模板MD"), (TEMPLATE_JSON, "回执模板JSON")]:
        if not path.exists():
            errors.append(f"{label}缺失：{path}")

    gate: dict[str, Any] = {}
    template: dict[str, Any] = {}
    if GATE_JSON.exists():
        try:
            gate = read_json(GATE_JSON)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"分流门 JSON 解析失败：{exc}")
    if TEMPLATE_JSON.exists():
        try:
            template = read_json(TEMPLATE_JSON)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"回执模板 JSON 解析失败：{exc}")

    gate_fields = set(gate.get("required_fields") or [])
    template_fields = set(template.get("required_fields") or [])
    required_fields = gate_fields | EXTRA_REQUIRED_RECEIPT_FIELDS
    missing_fields = sorted(required_fields - template_fields)
    for field in sorted(required_fields):
        field_checks.append({"field": field, "present": field in template_fields})
    if missing_fields:
        errors.append("回执字段缺失：" + "、".join(missing_fields))

    gate_routes = {route.get("target_line") for route in gate.get("routes", []) if isinstance(route, dict)}
    allowed_targets = set(template.get("allowed_target_lines") or [])
    missing_targets = sorted(gate_routes - allowed_targets)
    if missing_targets:
        errors.append("回执允许路由缺失：" + "、".join(missing_targets))

    required_defaults = template.get("required_defaults") or {}
    if required_defaults.get("human_review_required") is not True:
        errors.append("默认 human_review_required 未设为 true")
    if required_defaults.get("formal_capability_claim") is not False:
        errors.append("默认 formal_capability_claim 未设为 false")
    if required_defaults.get("human_review_status") != "待复核":
        errors.append("默认 human_review_status 未设为 待复核")

    forbidden = template.get("forbidden_actions") or {}
    for key in sorted(REQUIRED_FALSE_KEYS):
        value = forbidden.get(key)
        ok = value is False
        redline_checks.append({"key": key, "value": value, "pass": ok})
        if not ok:
            errors.append(f"红线字段未保持 false：{key}={value!r}")

    for index_path in [TOTAL_INDEX_MD, TOTAL_INDEX_JSON]:
        if not index_path.exists():
            errors.append(f"总索引缺失：{index_path}")
            continue
        text = index_path.read_text(encoding="utf-8", errors="ignore")
        if "P2_REAL_MATERIAL_INTAKE_RECEIPT_TEMPLATE_001" not in text:
            warnings.append(f"总索引尚未挂接回执模板：{index_path}")

    status = "pass" if not errors else "fail"
    report = {
        "id": "P2S6_REAL_MATERIAL_INTAKE_RECEIPT_TEMPLATE_READONLY_CHECK",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "summary": {
            "field_count": len(field_checks),
            "missing_field_count": len(missing_fields),
            "allowed_target_count": len(allowed_targets),
            "redline_false_check_count": len(redline_checks),
            "index_warning_count": len(warnings),
        },
        "field_checks": field_checks,
        "redline_checks": redline_checks,
        "errors": errors,
        "warnings": warnings,
        "conclusion": "真实材料接入分流回执模板字段、路由、默认复核状态和红线状态完整；可用于后续真实脱敏材料接入留痕。" if status == "pass" else "真实材料接入分流回执模板存在缺口，需修复后再用于材料接入。",
        "forbidden_actions": {
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
    LATEST_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "总体状态": report["status"],
        "错误数": len(errors),
        "提醒数": len(warnings),
        "字段检查数": len(field_checks),
        "红线字段检查数": len(redline_checks),
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
