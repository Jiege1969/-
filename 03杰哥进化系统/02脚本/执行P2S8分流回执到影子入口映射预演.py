# -*- coding: utf-8 -*-
"""
名称：执行P2S8分流回执到影子入口映射预演.py
作用：用 P2-S7 虚拟回执预演映射到影子入口字段，验证不改写入口、不越级生成结论。
触发方式：python 执行P2S8分流回执到影子入口映射预演.py
安全边界：只读读取回执样例、映射规则和目标入口；仅输出映射预演；不读取真实材料，不写目标入口，不触发 n8n，不发送企业微信，不写正式库。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
INCUBATION = ROOT / "02杰哥扩展系统" / "02-00孵化区"
RULE_JSON = INCUBATION / "P2_RECEIPT_TO_SHADOW_ENTRY_MAPPING_RULE_001_分流回执到影子入口映射规则_20260509.json"
RECEIPTS_JSON = ROOT / "03杰哥进化系统" / "03数据" / "56P2S7真实材料接入分流回执样例干跑" / "P2S7真实材料接入分流虚拟回执样例_20260509.json"
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "57P2S8分流回执到影子入口映射预演"
MAPPING_PREVIEW_JSON = OUTPUT_DIR / "P2S8分流回执到影子入口映射预演样例_20260509.json"
LATEST_JSON = OUTPUT_DIR / "P2S8分流回执到影子入口映射预演_最新.json"
LATEST_MD = OUTPUT_DIR / "P2S8分流回执到影子入口映射预演_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def map_receipt(receipt: dict[str, Any], routes: dict[str, Any]) -> dict[str, Any]:
    target_line = receipt["target_line"]
    route = routes[target_line]
    common = {
        "source_receipt_id": receipt["receipt_id"],
        "material_id": receipt["material_id"],
        "target_line": target_line,
        "target_entry": route["target_entry"],
        "preview_only": True,
        "write_target_entry": False,
        "human_review_required": True,
        "formal_capability_claim": False,
        "redline_status": receipt["redline_status"],
    }
    if target_line == "tax":
        fields = {
            "source_type": receipt["source_type"],
            "taxpayer_profile": "待人工从脱敏材料填写",
            "tax_item_or_scenario": "待人工从脱敏材料填写",
            "target_output": "待复核草案前置",
            "known_basis": "待补",
            "missing_materials": "待补",
            "human_review_required": True,
        }
    elif target_line == "office_work":
        fields = {
            "source_materials": receipt["material_id"],
            "input_summary": "待人工从授权材料填写",
            "output_draft": "待复核",
            "basis_or_reference": "待补",
            "human_review_required": True,
        }
    elif target_line == "video_production":
        fields = {
            "related_project": "待填写",
            "script_source": receipt["material_id"],
            "storyboard_source": "待填写",
            "asset_source": "待填写",
            "platform_rule_source": "待填写",
            "release_gate": "closed",
            "human_review_required": True,
        }
    elif target_line == "shared_policy_evidence":
        fields = {
            "target_business_line": "待填写",
            "policy_source": receipt["source_path_or_url"],
            "query_purpose": "依据候选只读登记",
            "expected_use": "只提供出处、有效性线索和适用边界提示",
            "human_review_required": True,
        }
    else:
        fields = {
            "pause_reasons": receipt["pause_reasons"],
            "redline_status": receipt["redline_status"],
            "redline_reasons": receipt["redline_reasons"],
            "next_allowed_action": "只记录缺口" if receipt["redline_status"] == "pass" else "暂停",
            "human_review_required": True,
        }
    return {**common, "mapped_fields": fields}


def check_mapping(mapping: dict[str, Any], receipt: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    target_line = mapping["target_line"]
    route = rule["routes"][target_line]
    if mapping["target_entry"] != route["target_entry"]:
        errors.append("目标入口不一致")
    if mapping["preview_only"] is not True:
        errors.append("preview_only 未保持 true")
    if mapping["write_target_entry"] is not False:
        errors.append("write_target_entry 未保持 false")
    if mapping["human_review_required"] is not True:
        errors.append("human_review_required 未保持 true")
    if mapping["formal_capability_claim"] is not False:
        errors.append("formal_capability_claim 未保持 false")
    if receipt["target_line"] == "pause" and mapping["target_entry"] != "gap_or_redline_record":
        errors.append("pause 路线进入了业务入口")
    if receipt["redline_status"] == "blocked" and mapping["mapped_fields"].get("next_allowed_action") != "暂停":
        errors.append("blocked 回执未映射为暂停")
    return {
        "source_receipt_id": receipt["receipt_id"],
        "target_line": target_line,
        "target_entry": mapping["target_entry"],
        "status": "pass" if not errors else "fail",
        "errors": errors,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P2-S8 分流回执到影子入口映射预演",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['status']}",
        f"- 映射数：{report['summary']['mapping_count']}",
        f"- 通过数：{report['summary']['passed']}",
        f"- 失败数：{report['summary']['failed']}",
        "",
        "| 回执 | 路由 | 目标入口 | 状态 |",
        "|:---|:---|:---|:---|",
    ]
    for item in report["checks"]:
        lines.append(f"| {item['source_receipt_id']} | {item['target_line']} | {item['target_entry']} | {item['status']} |")
    lines.extend([
        "",
        "## 结论",
        "",
        report["conclusion"],
        "",
        "## 安全边界",
        "",
        "- 本预演只生成映射建议。",
        "- 不读取真实材料，不扫描用户目录。",
        "- 不改写目标入口 JSON。",
        "- 不触发 n8n，不发送企业微信，不写正式库。",
        "- 不重启服务，不交易，不办理税务，不渲染或发布视频。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    rule = read_json(RULE_JSON)
    sample = read_json(RECEIPTS_JSON)
    receipts = sample.get("receipts") or []
    routes = rule.get("routes") or {}

    mappings = [map_receipt(receipt, routes) for receipt in receipts]
    checks = [check_mapping(mapping, receipt, rule) for mapping, receipt in zip(mappings, receipts)]
    failed = [item for item in checks if item["status"] != "pass"]

    target_status_checks = []
    for target_line, route in routes.items():
        target_path = route.get("target_path")
        if target_path and target_path != "none":
            target = read_json(Path(target_path))
            allowed = (rule.get("allowed_target_status_before_mapping") or {}).get(target_line, [])
            actual = target.get("status")
            target_status_checks.append({
                "target_line": target_line,
                "target_path": target_path,
                "actual_status": actual,
                "allowed": allowed,
                "pass": actual in allowed,
            })

    status_failed = [item for item in target_status_checks if not item["pass"]]
    report_status = "pass" if not failed and not status_failed else "fail"
    report = {
        "id": "P2S8_RECEIPT_TO_SHADOW_ENTRY_MAPPING_PREVIEW",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": report_status,
        "summary": {
            "mapping_count": len(mappings),
            "passed": len(mappings) - len(failed),
            "failed": len(failed),
            "target_status_failed": len(status_failed),
        },
        "mapping_preview_path": str(MAPPING_PREVIEW_JSON),
        "checks": checks,
        "target_status_checks": target_status_checks,
        "conclusion": "分流回执到影子入口映射预演通过；7 份虚拟回执均可生成入口预填建议或暂停缺口建议，且未改写目标入口。" if report_status == "pass" else "分流回执映射预演存在缺口，需修复后再用于真实材料接入。",
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
    MAPPING_PREVIEW_JSON.write_text(json.dumps({"sample_only": True, "mappings": mappings}, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "总体状态": report["status"],
        "映射数": report["summary"]["mapping_count"],
        "通过": report["summary"]["passed"],
        "失败": report["summary"]["failed"],
        "目标状态失败": report["summary"]["target_status_failed"],
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
