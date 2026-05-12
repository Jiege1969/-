# -*- coding: utf-8 -*-
"""
名称：执行P2S7真实材料接入分流回执样例干跑.py
作用：用 P2-S5 的虚拟场景生成 P2-S6 分流回执样例，验证回执模板可承接每条路线。
触发方式：python 执行P2S7真实材料接入分流回执样例干跑.py
安全边界：只读读取 P2-S5/P2-S6 结果；仅输出虚拟回执样例和报告；不读取真实材料，不触发 n8n，不发送企业微信，不写正式库，不重启服务。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
TEMPLATE_JSON = ROOT / "02杰哥扩展系统" / "02-00孵化区" / "P2_REAL_MATERIAL_INTAKE_RECEIPT_TEMPLATE_001_真实材料接入分流回执模板_20260509.json"
P2S5_JSON = ROOT / "03杰哥进化系统" / "03数据" / "54P2S5真实材料接入分流门场景干跑" / "P2S5真实材料接入分流门场景干跑_最新.json"
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "56P2S7真实材料接入分流回执样例干跑"
SAMPLE_RECEIPTS_JSON = OUTPUT_DIR / "P2S7真实材料接入分流虚拟回执样例_20260509.json"
LATEST_JSON = OUTPUT_DIR / "P2S7真实材料接入分流回执样例干跑_最新.json"
LATEST_MD = OUTPUT_DIR / "P2S7真实材料接入分流回执样例干跑_最新.md"


TARGET_ENTRIES = {
    "tax": "TAX_DAILY_INTAKE_002",
    "office_work": "OFFICE_SHADOW_002",
    "video_production": "VIDEO_P2_REVIEW_CHAIN_NEXT_001",
    "shared_policy_evidence": "P2_SHARED_POLICY_READONLY_NEXT_001",
    "pause": "gap_or_redline_record",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def make_receipt(case: dict[str, Any]) -> dict[str, Any]:
    material = case["material"]
    actual = case["actual"]
    target_line = actual["target_line"]
    pause_reasons = actual.get("pause_reasons") or []
    redline_reasons = []
    if any("真实执行请求" in reason for reason in pause_reasons):
        redline_reasons.append("命中真实执行请求")

    return {
        "receipt_id": f"P2S7-RECEIPT-{case['case_id'].split('-')[-1]}",
        "material_id": f"VIRTUAL-{case['case_id']}",
        "received_at": "2026-05-09 00:00:00 +08:00",
        "source_type": material.get("source_type"),
        "source_path_or_url": "virtual_sample_only",
        "authorization_status": material.get("authorization_status"),
        "sensitivity": material.get("sensitivity"),
        "desensitized_status": material.get("desensitized_status"),
        "target_line": target_line,
        "target_entry": TARGET_ENTRIES.get(target_line),
        "can_enter_shadow": actual.get("can_enter_shadow"),
        "pause_reasons": pause_reasons or ["无"],
        "next_allowed_action": actual.get("next_allowed_action"),
        "human_review_required": True,
        "human_review_status": "待复核",
        "redline_status": "blocked" if redline_reasons else "pass",
        "redline_reasons": redline_reasons or ["无"],
        "formal_capability_claim": False,
        "receipt_status": "draft",
        "source_case_id": case["case_id"],
        "virtual_sample_only": True,
        "forbidden_actions": {
            "trigger_n8n": False,
            "send_wecom": False,
            "write_formal_database": False,
            "scan_unspecified_directory": False,
            "copy_sensitive_material": False,
            "tax_filing": False,
            "invoice_action": False,
            "tax_refund_action": False,
            "trade": False,
            "connect_real_office_system": False,
            "render_upload_or_publish_video": False,
            "claim_formal_capability": False,
        },
    }


def check_receipt(receipt: dict[str, Any], template: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    errors = []
    required = set(template.get("required_fields") or [])
    missing = sorted(field for field in required if field not in receipt)
    if missing:
        errors.append("字段缺失：" + "、".join(missing))

    allowed_targets = set(template.get("allowed_target_lines") or [])
    if receipt.get("target_line") not in allowed_targets:
        errors.append(f"target_line 不在允许范围：{receipt.get('target_line')}")

    allowed_actions = set(template.get("allowed_next_actions") or [])
    if receipt.get("next_allowed_action") not in allowed_actions:
        errors.append(f"next_allowed_action 不在允许范围：{receipt.get('next_allowed_action')}")

    if receipt.get("target_line") != case["expected"]["target_line"]:
        errors.append(f"回执路由与场景期望不一致：{receipt.get('target_line')} != {case['expected']['target_line']}")

    if receipt.get("human_review_required") is not True:
        errors.append("human_review_required 未保持 true")
    if receipt.get("formal_capability_claim") is not False:
        errors.append("formal_capability_claim 未保持 false")
    if receipt.get("virtual_sample_only") is not True:
        errors.append("virtual_sample_only 未保持 true")

    for key, value in (receipt.get("forbidden_actions") or {}).items():
        if value is not False:
            errors.append(f"红线字段未关闭：{key}={value!r}")

    if receipt.get("target_line") == "pause" and receipt.get("pause_reasons") == ["无"]:
        errors.append("暂停路线缺少 pause_reasons")

    if any("真实执行请求" in reason for reason in receipt.get("pause_reasons", [])):
        if receipt.get("redline_status") != "blocked":
            errors.append("真实执行请求未标记 redline_status=blocked")

    return {
        "receipt_id": receipt["receipt_id"],
        "source_case_id": case["case_id"],
        "target_line": receipt.get("target_line"),
        "status": "pass" if not errors else "fail",
        "errors": errors,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P2-S7 真实材料接入分流回执样例干跑",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['status']}",
        f"- 虚拟回执数：{report['summary']['receipt_count']}",
        f"- 通过数：{report['summary']['passed']}",
        f"- 失败数：{report['summary']['failed']}",
        "",
        "| 回执 | 场景 | 路由 | 状态 |",
        "|:---|:---|:---|:---|",
    ]
    for item in report["checks"]:
        lines.append(f"| {item['receipt_id']} | {item['source_case_id']} | {item['target_line']} | {item['status']} |")
    lines.extend([
        "",
        "## 结论",
        "",
        report["conclusion"],
        "",
        "## 安全边界",
        "",
        "- 本干跑只生成虚拟回执样例。",
        "- 不读取真实材料，不扫描用户目录。",
        "- 不触发 n8n，不发送企业微信，不写正式库。",
        "- 不重启服务，不交易，不办理税务，不渲染或发布视频。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    template = read_json(TEMPLATE_JSON)
    p2s5 = read_json(P2S5_JSON)
    cases = p2s5.get("cases") or []
    receipts = [make_receipt(case) for case in cases]
    checks = [check_receipt(receipt, template, case) for receipt, case in zip(receipts, cases)]
    failed = [item for item in checks if item["status"] != "pass"]

    report = {
        "id": "P2S7_REAL_MATERIAL_INTAKE_RECEIPT_SAMPLE_DRYRUN",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pass" if not failed else "fail",
        "summary": {
            "receipt_count": len(receipts),
            "passed": len(receipts) - len(failed),
            "failed": len(failed),
            "source_case_count": len(cases),
        },
        "sample_receipts_path": str(SAMPLE_RECEIPTS_JSON),
        "checks": checks,
        "conclusion": "分流回执样例干跑通过；7 个虚拟场景均可生成字段完整、路线一致、红线关闭或阻断明确的分流回执。" if not failed else "分流回执样例干跑存在失败回执，需修复后再用于真实材料接入留痕。",
        "forbidden_actions": {
            "read_real_material": False,
            "scan_user_directory": False,
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
    SAMPLE_RECEIPTS_JSON.write_text(json.dumps({"sample_only": True, "receipts": receipts}, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "总体状态": report["status"],
        "虚拟回执数": report["summary"]["receipt_count"],
        "通过": report["summary"]["passed"],
        "失败": report["summary"]["failed"],
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
