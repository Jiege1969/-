# -*- coding: utf-8 -*-
"""
名称：执行P2S4真实材料接入分流门只读检查.py
作用：只读检查真实材料进入影子入口前的分流门是否完整、受控、可追溯。
触发方式：python 执行P2S4真实材料接入分流门只读检查.py
安全边界：只读读取分流门、入口卡和索引；仅在 03进化系统03数据输出检查报告；不触发 n8n，不发送企业微信，不写正式库，不重启服务。
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
GATE_MD = INCUBATION / "P2_REAL_MATERIAL_INTAKE_GATE_001_真实材料接入分流门_20260509.md"
TOTAL_INDEX_MD = INCUBATION / "孵化区影子底座总索引_最新.md"
TOTAL_INDEX_JSON = INCUBATION / "孵化区影子底座总索引_最新.json"
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "53P2S4真实材料接入分流门只读检查"
LATEST_JSON = OUTPUT_DIR / "P2S4真实材料接入分流门只读检查_最新.json"
LATEST_MD = OUTPUT_DIR / "P2S4真实材料接入分流门只读检查_最新.md"


REQUIRED_FIELDS = {
    "material_id",
    "source_type",
    "source_path_or_url",
    "authorization_status",
    "sensitivity",
    "desensitized_status",
    "target_line",
    "can_enter_shadow",
    "human_review_required",
    "next_allowed_action",
}

REQUIRED_ROUTES = {
    "tax",
    "office_work",
    "video_production",
    "shared_policy_evidence",
    "pause",
}

REQUIRED_PAUSE_TERMS = {
    "未授权",
    "禁止使用",
    "来源不清",
    "敏感内容未脱敏",
    "请求申报",
    "请求开票",
    "请求退税",
    "请求交易",
    "请求审批",
    "请求上传",
    "请求发布",
    "请求外发",
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
        "# P2-S4 真实材料接入分流门只读检查",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['status']}",
        f"- 错误数：{len(report['errors'])}",
        f"- 提醒数：{len(report['warnings'])}",
        f"- 路由数：{report['summary']['route_count']}",
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
        "- 本检查只读读取分流门、入口卡和索引。",
        "- 不触发 n8n，不发送企业微信，不写正式库。",
        "- 不重启服务，不交易，不办理税务，不渲染或发布视频。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    errors: list[str] = []
    warnings: list[str] = []
    redline_checks: list[dict[str, Any]] = []
    route_checks: list[dict[str, Any]] = []

    if not GATE_MD.exists():
        errors.append(f"分流门 MD 缺失：{GATE_MD}")
    if not GATE_JSON.exists():
        errors.append(f"分流门 JSON 缺失：{GATE_JSON}")
        gate: dict[str, Any] = {}
    else:
        try:
            gate = read_json(GATE_JSON)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"分流门 JSON 解析失败：{exc}")
            gate = {}

    fields = set(gate.get("required_fields") or [])
    missing_fields = sorted(REQUIRED_FIELDS - fields)
    if missing_fields:
        errors.append("分流字段缺失：" + "、".join(missing_fields))

    routes = gate.get("routes") or []
    route_names = {route.get("target_line") for route in routes if isinstance(route, dict)}
    missing_routes = sorted(REQUIRED_ROUTES - route_names)
    if missing_routes:
        errors.append("分流路由缺失：" + "、".join(missing_routes))

    for route in routes:
        if not isinstance(route, dict):
            continue
        target = route.get("target_line")
        entry_path = route.get("entry_path")
        exists = True
        if entry_path and entry_path != "none":
            exists = Path(entry_path).exists()
            if not exists:
                errors.append(f"路由入口不存在：{target} -> {entry_path}")
        route_checks.append({
            "target_line": target,
            "entry": route.get("entry"),
            "entry_path": entry_path,
            "entry_exists": exists,
            "rule": route.get("rule"),
        })

    pause_terms = set(gate.get("pause_conditions") or [])
    missing_pause_terms = sorted(REQUIRED_PAUSE_TERMS - pause_terms)
    if missing_pause_terms:
        errors.append("暂停条件缺失：" + "、".join(missing_pause_terms))

    forbidden = gate.get("forbidden_actions") or {}
    for key in sorted(REQUIRED_FALSE_KEYS):
        value = forbidden.get(key)
        ok = value is False
        redline_checks.append({"key": key, "value": value, "pass": ok})
        if not ok:
            errors.append(f"红线字段未保持 false：{key}={value!r}")

    if gate.get("human_review_required") is not True:
        errors.append("分流门未强制 human_review_required=true")

    for index_path in [TOTAL_INDEX_MD, TOTAL_INDEX_JSON]:
        if not index_path.exists():
            errors.append(f"总索引缺失：{index_path}")
            continue
        text = index_path.read_text(encoding="utf-8", errors="ignore")
        if "P2_REAL_MATERIAL_INTAKE_GATE_001" not in text:
            warnings.append(f"总索引尚未挂接分流门：{index_path}")

    status = "pass" if not errors else "fail"
    report = {
        "id": "P2S4_REAL_MATERIAL_INTAKE_ROUTING_GATE_READONLY_CHECK",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "summary": {
            "route_count": len(route_checks),
            "redline_false_check_count": len(redline_checks),
            "missing_field_count": len(missing_fields),
            "missing_route_count": len(missing_routes),
            "missing_pause_term_count": len(missing_pause_terms),
        },
        "route_checks": route_checks,
        "redline_checks": redline_checks,
        "errors": errors,
        "warnings": warnings,
        "conclusion": "真实材料接入分流门完整且红线关闭；真实材料进入前可先走分流门，再进入对应影子入口。" if status == "pass" else "真实材料接入分流门存在缺口，需先修复后再允许接入材料。",
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
        "路由数": len(route_checks),
        "红线字段检查数": len(redline_checks),
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
