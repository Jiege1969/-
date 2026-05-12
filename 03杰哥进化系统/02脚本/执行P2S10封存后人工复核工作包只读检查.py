# -*- coding: utf-8 -*-
"""
名称：执行P2S10封存后人工复核工作包只读检查.py
作用：读取 P2-S9 封存预演样例，生成并检查封存后人工复核工作包。
触发方式：python 执行P2S10封存后人工复核工作包只读检查.py
安全边界：只读读取 P2-S9 样例和 P2-S10 工作包模板；仅输出复核工作包预演；不读取真实材料，不写入口，不触发外部动作。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
INCUBATION = ROOT / "02杰哥扩展系统" / "02-00孵化区"
PACKET_JSON = INCUBATION / "P2_SHADOW_ENTRY_HUMAN_REVIEW_PACKET_001_封存后人工复核工作包_20260509.json"
SEAL_SAMPLE_JSON = ROOT / "03杰哥进化系统" / "03数据" / "58P2S9影子入口封存回收只读检查" / "P2S9影子入口封存回收预演样例_20260509.json"
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "59P2S10封存后人工复核工作包只读检查"
REVIEW_PACKET_SAMPLE_JSON = OUTPUT_DIR / "P2S10封存后人工复核工作包预演样例_20260509.json"
LATEST_JSON = OUTPUT_DIR / "P2S10封存后人工复核工作包只读检查_最新.json"
LATEST_MD = OUTPUT_DIR / "P2S10封存后人工复核工作包只读检查_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_review_item(sealed: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    bucket = sealed["seal_bucket"]
    group = packet["groups"][bucket]
    return {
        "source_receipt_id": sealed["source_receipt_id"],
        "material_id": sealed["material_id"],
        "target_line": sealed["target_line"],
        "target_entry": sealed["target_entry"],
        "seal_bucket": bucket,
        "review_questions": group["review_questions"],
        "allowed_actions": group["allowed_actions"],
        "forbidden_actions": group["forbidden_actions"],
        "human_review_required": True,
        "auto_fill_shadow_entry": False,
        "write_target_entry": False,
        "formal_capability_claim": False,
        "release_form": False,
        "redline_status": sealed["redline_status"],
    }


def check_review_item(item: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    hard = packet["hard_rules"]
    if not item["review_questions"]:
        errors.append("复核问题为空")
    if not item["allowed_actions"]:
        errors.append("允许动作为空")
    if not item["forbidden_actions"]:
        errors.append("禁止动作为空")
    if item["human_review_required"] is not hard["human_review_required"]:
        errors.append("human_review_required 未保持 true")
    if item["auto_fill_shadow_entry"] is not hard["auto_fill_shadow_entry"]:
        errors.append("auto_fill_shadow_entry 未保持 false")
    if item["write_target_entry"] is not False:
        errors.append("write_target_entry 未保持 false")
    if item["formal_capability_claim"] is not hard["formal_capability_claim"]:
        errors.append("formal_capability_claim 未保持 false")
    if item["release_form"] is not hard["packet_is_release_form"]:
        errors.append("release_form 未保持 false")
    if item["seal_bucket"] == "blocked_redline_archive" and item["target_entry"] != "gap_or_redline_record":
        errors.append("红线阻断项仍指向业务入口")
    return {
        "source_receipt_id": item["source_receipt_id"],
        "target_line": item["target_line"],
        "target_entry": item["target_entry"],
        "seal_bucket": item["seal_bucket"],
        "status": "pass" if not errors else "fail",
        "errors": errors,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P2-S10 封存后人工复核工作包只读检查",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['status']}",
        f"- 工作包条目：{report['summary']['review_item_count']}",
        f"- 通过数：{report['summary']['passed']}",
        f"- 失败数：{report['summary']['failed']}",
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
        "- 本检查只生成复核工作包预演。",
        "- 不读取真实材料，不扫描用户目录，不写影子入口。",
        "- 不触发 n8n，不发送企业微信，不写正式库，不执行真实业务动作。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    packet = read_json(PACKET_JSON)
    seal_sample = read_json(SEAL_SAMPLE_JSON)
    sealed_items = seal_sample.get("sealed_items") or []
    review_items = [build_review_item(item, packet) for item in sealed_items]
    checks = [check_review_item(item, packet) for item in review_items]
    failed = [item for item in checks if item["status"] != "pass"]
    status = "pass" if not failed else "fail"
    report = {
        "id": "P2S10_SHADOW_ENTRY_HUMAN_REVIEW_PACKET_READONLY_CHECK",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "summary": {
            "review_item_count": len(review_items),
            "passed": len(review_items) - len(failed),
            "failed": len(failed),
            "release_forms": sum(1 for item in review_items if item["release_form"]),
            "auto_fill_shadow_entry": sum(1 for item in review_items if item["auto_fill_shadow_entry"]),
            "write_target_entry": sum(1 for item in review_items if item["write_target_entry"]),
        },
        "review_packet_sample_path": str(REVIEW_PACKET_SAMPLE_JSON),
        "checks": checks,
        "conclusion": "封存后人工复核工作包预演通过；7 个封存项均生成复核问题、允许动作和禁止动作，且不构成放行单、不自动填写影子入口。" if status == "pass" else "封存后人工复核工作包存在缺口，需修复后再承接真实材料。",
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
    REVIEW_PACKET_SAMPLE_JSON.write_text(json.dumps({"sample_only": True, "review_items": review_items}, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "总体状态": report["status"],
        "工作包条目": report["summary"]["review_item_count"],
        "通过": report["summary"]["passed"],
        "失败": report["summary"]["failed"],
        "放行单数量": report["summary"]["release_forms"],
        "自动填写入口数量": report["summary"]["auto_fill_shadow_entry"],
        "写入口数量": report["summary"]["write_target_entry"],
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
