# -*- coding: utf-8 -*-
"""
名称：执行P2S9影子入口封存回收只读检查.py
作用：读取 P2-S8 映射预演样例，验证入口封存与问题回收分桶是否正确。
触发方式：python 执行P2S9影子入口封存回收只读检查.py
安全边界：只读读取 P2-S8 样例和 P2-S9 规则；仅输出封存预演；不读取真实材料，不写目标入口，不触发 n8n，不发送企业微信，不写正式库。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
INCUBATION = ROOT / "02杰哥扩展系统" / "02-00孵化区"
RULE_JSON = INCUBATION / "P2_SHADOW_ENTRY_SEAL_AND_RECOVERY_RULE_001_入口封存与问题回收规则_20260509.json"
MAPPING_SAMPLE_JSON = ROOT / "03杰哥进化系统" / "03数据" / "57P2S8分流回执到影子入口映射预演" / "P2S8分流回执到影子入口映射预演样例_20260509.json"
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "58P2S9影子入口封存回收只读检查"
SEAL_SAMPLE_JSON = OUTPUT_DIR / "P2S9影子入口封存回收预演样例_20260509.json"
LATEST_JSON = OUTPUT_DIR / "P2S9影子入口封存回收只读检查_最新.json"
LATEST_MD = OUTPUT_DIR / "P2S9影子入口封存回收只读检查_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def decide_bucket(mapping: dict[str, Any]) -> str:
    if mapping.get("redline_status") == "blocked":
        return "blocked_redline_archive"
    if mapping.get("target_line") == "pause":
        return "pause_gap_archive"
    return "ready_shadow_preview"


def seal_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    bucket = decide_bucket(mapping)
    sealed = {
        "source_receipt_id": mapping.get("source_receipt_id"),
        "material_id": mapping.get("material_id"),
        "target_line": mapping.get("target_line"),
        "target_entry": mapping.get("target_entry"),
        "seal_bucket": bucket,
        "preview_only": True,
        "write_target_entry": False,
        "human_review_required": True,
        "formal_capability_claim": False,
        "redline_status": mapping.get("redline_status"),
        "next_allowed_action": "",
    }
    if bucket == "ready_shadow_preview":
        sealed["next_allowed_action"] = "等待人工复核后再决定是否填写对应影子入口"
    elif bucket == "pause_gap_archive":
        sealed["next_allowed_action"] = "只记录缺口、来源不清或条件不足，不生成业务结论"
    else:
        sealed["next_allowed_action"] = "阻断并进入问题回收，不进入任何业务入口"
    return sealed


def check_seal(sealed: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    bucket = sealed["seal_bucket"]
    hard_rules = rule["hard_rules"]

    for key in ("preview_only", "human_review_required"):
        if sealed.get(key) is not hard_rules[key]:
            errors.append(f"{key} 未保持 {hard_rules[key]}")
    for key in ("write_target_entry", "formal_capability_claim"):
        if sealed.get(key) is not hard_rules[key]:
            errors.append(f"{key} 未保持 {hard_rules[key]}")

    if sealed["redline_status"] == "blocked" and bucket != "blocked_redline_archive":
        errors.append("blocked 回执未进入红线阻断封存")
    if sealed["redline_status"] != "blocked" and bucket == "blocked_redline_archive":
        errors.append("非 blocked 回执误入红线阻断封存")
    if sealed["target_line"] == "pause" and sealed["redline_status"] == "pass" and bucket != "pause_gap_archive":
        errors.append("pause/pass 回执未进入缺口封存")
    if sealed["target_line"] != "pause" and sealed["redline_status"] == "pass" and bucket != "ready_shadow_preview":
        errors.append("业务线 pass 回执未进入待复核影子封存")
    if bucket in ("pause_gap_archive", "blocked_redline_archive") and sealed["target_entry"] != "gap_or_redline_record":
        errors.append("暂停或红线封存仍指向了业务入口")

    return {
        "source_receipt_id": sealed["source_receipt_id"],
        "target_line": sealed["target_line"],
        "target_entry": sealed["target_entry"],
        "seal_bucket": bucket,
        "status": "pass" if not errors else "fail",
        "errors": errors,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P2-S9 影子入口封存回收只读检查",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['status']}",
        f"- 输入映射数：{report['summary']['input_mapping_count']}",
        f"- 通过数：{report['summary']['passed']}",
        f"- 失败数：{report['summary']['failed']}",
        f"- 待复核影子封存：{report['summary']['ready_shadow_preview']}",
        f"- 缺口封存：{report['summary']['pause_gap_archive']}",
        f"- 红线阻断封存：{report['summary']['blocked_redline_archive']}",
        "",
        "| 回执 | 路由 | 目标入口 | 封存桶 | 状态 |",
        "|:---|:---|:---|:---|:---|",
    ]
    for item in report["checks"]:
        lines.append(f"| {item['source_receipt_id']} | {item['target_line']} | {item['target_entry']} | {item['seal_bucket']} | {item['status']} |")
    lines.extend([
        "",
        "## 结论",
        "",
        report["conclusion"],
        "",
        "## 安全边界",
        "",
        "- 只读读取 P2-S8 映射样例和 P2-S9 规则。",
        "- 不读取真实材料，不扫描用户目录。",
        "- 不写影子入口，不触发 n8n，不发送企业微信，不写正式库。",
        "- 不重启服务，不交易，不办理税务，不渲染或发布视频。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    rule = read_json(RULE_JSON)
    mapping_sample = read_json(MAPPING_SAMPLE_JSON)
    mappings = mapping_sample.get("mappings") or []
    sealed_items = [seal_mapping(mapping) for mapping in mappings]
    checks = [check_seal(sealed, rule) for sealed in sealed_items]
    failed = [item for item in checks if item["status"] != "pass"]
    bucket_counts = {
        "ready_shadow_preview": sum(1 for item in sealed_items if item["seal_bucket"] == "ready_shadow_preview"),
        "pause_gap_archive": sum(1 for item in sealed_items if item["seal_bucket"] == "pause_gap_archive"),
        "blocked_redline_archive": sum(1 for item in sealed_items if item["seal_bucket"] == "blocked_redline_archive"),
    }

    status = "pass" if not failed else "fail"
    report = {
        "id": "P2S9_SHADOW_ENTRY_SEAL_AND_RECOVERY_READONLY_CHECK",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "summary": {
            "input_mapping_count": len(mappings),
            "passed": len(mappings) - len(failed),
            "failed": len(failed),
            **bucket_counts,
        },
        "seal_preview_path": str(SEAL_SAMPLE_JSON),
        "checks": checks,
        "conclusion": "入口封存与问题回收预演通过；业务线映射进入待复核封存，缺口进入缺口封存，真实执行请求进入红线阻断封存，且未改写任何影子入口。" if status == "pass" else "入口封存与问题回收预演存在错误分桶，需修复后再用于真实材料接入。",
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
    SEAL_SAMPLE_JSON.write_text(json.dumps({"sample_only": True, "sealed_items": sealed_items}, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "总体状态": report["status"],
        "输入映射数": report["summary"]["input_mapping_count"],
        "通过": report["summary"]["passed"],
        "失败": report["summary"]["failed"],
        "待复核影子封存": report["summary"]["ready_shadow_preview"],
        "缺口封存": report["summary"]["pause_gap_archive"],
        "红线阻断封存": report["summary"]["blocked_redline_archive"],
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
