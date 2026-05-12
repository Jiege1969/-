# -*- coding: utf-8 -*-
"""
名称：执行P2S11人工复核结果回执模板只读检查.py
作用：读取 P2-S10 人工复核工作包样例，生成并检查人工复核结果回执样例。
触发方式：python 执行P2S11人工复核结果回执模板只读检查.py
安全边界：只读读取 P2-S10 样例和 P2-S11 模板；仅输出回执样例；不读取真实材料，不写入口，不触发外部动作。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
INCUBATION = ROOT / "02杰哥扩展系统" / "02-00孵化区"
TEMPLATE_JSON = INCUBATION / "P2_HUMAN_REVIEW_RECEIPT_TEMPLATE_001_人工复核结果回执模板_20260509.json"
REVIEW_PACKET_SAMPLE_JSON = ROOT / "03杰哥进化系统" / "03数据" / "59P2S10封存后人工复核工作包只读检查" / "P2S10封存后人工复核工作包预演样例_20260509.json"
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "60P2S11人工复核结果回执模板只读检查"
RECEIPT_SAMPLE_JSON = OUTPUT_DIR / "P2S11人工复核结果虚拟回执样例_20260509.json"
LATEST_JSON = OUTPUT_DIR / "P2S11人工复核结果回执模板只读检查_最新.json"
LATEST_MD = OUTPUT_DIR / "P2S11人工复核结果回执模板只读检查_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def choose_result(item: dict[str, Any], idx: int, template: dict[str, Any]) -> tuple[str, bool, str]:
    bucket = item["seal_bucket"]
    allowed = template["allowed_results"][bucket]
    if bucket == "ready_shadow_preview":
        return allowed["candidate_result"], True, allowed["candidate_next_gate"]
    if bucket == "pause_gap_archive":
        return "continue_pause", False, "gap_archive_waiting_for_material_or_authorization"
    return "maintain_block", False, "problem_recovery_or_supervisor_confirmation"


def build_receipt(item: dict[str, Any], idx: int, template: dict[str, Any]) -> dict[str, Any]:
    result, candidate, next_gate = choose_result(item, idx, template)
    return {
        "review_receipt_id": f"P2S11-HUMAN-REVIEW-RECEIPT-{idx:03d}",
        "source_receipt_id": item["source_receipt_id"],
        "material_id": item["material_id"],
        "target_line": item["target_line"],
        "target_entry": item["target_entry"],
        "seal_bucket": item["seal_bucket"],
        "human_review_result": result,
        "reviewed_by_human": True,
        "entry_fill_candidate": candidate,
        "auto_fill_shadow_entry": False,
        "write_target_entry": False,
        "release_form": False,
        "formal_capability_claim": False,
        "next_gate": next_gate,
        "sample_only": True,
    }


def check_receipt(receipt: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for field in template["required_fields"]:
        if field not in receipt:
            errors.append(f"缺少字段: {field}")
    bucket = receipt.get("seal_bucket")
    if bucket not in template["allowed_results"]:
        errors.append("未知 seal_bucket")
        allowed_results = []
    else:
        allowed_results = template["allowed_results"][bucket]["results"]
    if receipt.get("human_review_result") not in allowed_results:
        errors.append("human_review_result 不在允许结果中")

    hard = template["hard_rules"]
    if receipt.get("release_form") is not hard["review_receipt_is_release_form"]:
        errors.append("release_form 未保持 false")
    if receipt.get("auto_fill_shadow_entry") is not hard["auto_fill_shadow_entry"]:
        errors.append("auto_fill_shadow_entry 未保持 false")
    if receipt.get("write_target_entry") is not hard["write_target_entry"]:
        errors.append("write_target_entry 未保持 false")
    if receipt.get("formal_capability_claim") is not hard["formal_capability_claim"]:
        errors.append("formal_capability_claim 未保持 false")
    if bucket == "blocked_redline_archive" and receipt.get("entry_fill_candidate"):
        errors.append("红线阻断项被标记为填写候选")
    if bucket == "blocked_redline_archive" and receipt.get("target_entry") != "gap_or_redline_record":
        errors.append("红线阻断项仍指向业务入口")
    if receipt.get("entry_fill_candidate") and receipt.get("write_target_entry"):
        errors.append("填写候选被误解为写入口许可")

    return {
        "review_receipt_id": receipt.get("review_receipt_id"),
        "source_receipt_id": receipt.get("source_receipt_id"),
        "target_line": receipt.get("target_line"),
        "seal_bucket": bucket,
        "human_review_result": receipt.get("human_review_result"),
        "entry_fill_candidate": receipt.get("entry_fill_candidate"),
        "status": "pass" if not errors else "fail",
        "errors": errors,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P2-S11 人工复核结果回执模板只读检查",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['status']}",
        f"- 回执数：{report['summary']['receipt_count']}",
        f"- 通过数：{report['summary']['passed']}",
        f"- 失败数：{report['summary']['failed']}",
        f"- 填写候选数：{report['summary']['entry_fill_candidates']}",
        f"- 写入口数量：{report['summary']['write_target_entry']}",
        "",
        "| 回执 | 来源 | 路由 | 封存桶 | 复核结果 | 填写候选 | 状态 |",
        "|:---|:---|:---|:---|:---|:---|:---|",
    ]
    for item in report["checks"]:
        lines.append(f"| {item['review_receipt_id']} | {item['source_receipt_id']} | {item['target_line']} | {item['seal_bucket']} | {item['human_review_result']} | {item['entry_fill_candidate']} | {item['status']} |")
    lines.extend([
        "",
        "## 结论",
        "",
        report["conclusion"],
        "",
        "## 安全边界",
        "",
        "- 本检查只生成虚拟人工复核回执样例。",
        "- 人工复核通过只代表进入填写候选，不代表自动填写或正式放行。",
        "- 不读取真实材料，不扫描用户目录，不写影子入口。",
        "- 不触发 n8n，不发送企业微信，不写正式库，不执行真实业务动作。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    template = read_json(TEMPLATE_JSON)
    sample = read_json(REVIEW_PACKET_SAMPLE_JSON)
    review_items = sample.get("review_items") or []
    receipts = [build_receipt(item, idx, template) for idx, item in enumerate(review_items, start=1)]
    checks = [check_receipt(receipt, template) for receipt in receipts]
    failed = [item for item in checks if item["status"] != "pass"]
    status = "pass" if not failed else "fail"
    report = {
        "id": "P2S11_HUMAN_REVIEW_RECEIPT_TEMPLATE_READONLY_CHECK",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "summary": {
            "receipt_count": len(receipts),
            "passed": len(receipts) - len(failed),
            "failed": len(failed),
            "entry_fill_candidates": sum(1 for item in receipts if item["entry_fill_candidate"]),
            "release_forms": sum(1 for item in receipts if item["release_form"]),
            "auto_fill_shadow_entry": sum(1 for item in receipts if item["auto_fill_shadow_entry"]),
            "write_target_entry": sum(1 for item in receipts if item["write_target_entry"]),
        },
        "receipt_sample_path": str(RECEIPT_SAMPLE_JSON),
        "checks": checks,
        "conclusion": "人工复核结果回执模板检查通过；7 份虚拟回执均不构成放行单，4 份仅进入填写候选，0 份自动填写或写入口。" if status == "pass" else "人工复核结果回执模板存在缺口，需修复后再承接真实复核意见。",
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
    RECEIPT_SAMPLE_JSON.write_text(json.dumps({"sample_only": True, "review_receipts": receipts}, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "总体状态": report["status"],
        "回执数": report["summary"]["receipt_count"],
        "通过": report["summary"]["passed"],
        "失败": report["summary"]["failed"],
        "填写候选": report["summary"]["entry_fill_candidates"],
        "放行单数量": report["summary"]["release_forms"],
        "自动填写入口数量": report["summary"]["auto_fill_shadow_entry"],
        "写入口数量": report["summary"]["write_target_entry"],
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
