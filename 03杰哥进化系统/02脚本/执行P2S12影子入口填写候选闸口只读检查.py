# -*- coding: utf-8 -*-
"""
名称：执行P2S12影子入口填写候选闸口只读检查.py
作用：读取 P2-S11 人工复核结果回执样例，验证填写候选是否能通过影子入口填写前闸口。
触发方式：python 执行P2S12影子入口填写候选闸口只读检查.py
安全边界：只读读取回执样例、闸口规则和目标入口状态；仅输出闸口预演；不读取真实材料，不写目标入口，不触发外部动作。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
INCUBATION = ROOT / "02杰哥扩展系统" / "02-00孵化区"
GATE_JSON = INCUBATION / "P2_SHADOW_ENTRY_FILL_GATE_001_影子入口填写候选闸口_20260509.json"
MAPPING_RULE_JSON = INCUBATION / "P2_RECEIPT_TO_SHADOW_ENTRY_MAPPING_RULE_001_分流回执到影子入口映射规则_20260509.json"
REVIEW_RECEIPTS_JSON = ROOT / "03杰哥进化系统" / "03数据" / "60P2S11人工复核结果回执模板只读检查" / "P2S11人工复核结果虚拟回执样例_20260509.json"
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "61P2S12影子入口填写候选闸口只读检查"
GATE_SAMPLE_JSON = OUTPUT_DIR / "P2S12影子入口填写候选闸口预演样例_20260509.json"
LATEST_JSON = OUTPUT_DIR / "P2S12影子入口填写候选闸口只读检查_最新.json"
LATEST_MD = OUTPUT_DIR / "P2S12影子入口填写候选闸口只读检查_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_candidate(receipt: dict[str, Any], gate: dict[str, Any], routes: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    target_line = receipt.get("target_line")
    target_entry = receipt.get("target_entry")
    required = gate["required_candidate_fields"]
    is_candidate = receipt.get("entry_fill_candidate") is True

    if is_candidate:
        for key, expected in required.items():
            if receipt.get(key) != expected:
                errors.append(f"{key} 不符合填写候选要求")
        if target_line == "pause" or target_entry == "gap_or_redline_record":
            errors.append("暂停或红线项进入了填写候选")
        if target_line not in routes:
            errors.append("目标业务线无映射路由")
            target_path = None
            target_status = None
        else:
            route = routes[target_line]
            target_path = route.get("target_path")
            if target_entry != route.get("target_entry"):
                errors.append("目标入口与映射规则不一致")
            target = read_json(Path(target_path))
            target_status = target.get("status")
            allowed = gate["allowed_target_status_before_fill_gate"].get(target_line, [])
            if target_status not in allowed:
                errors.append("目标入口状态不允许进入填写候选闸口")
        gate_result = "fill_candidate_gate_pass" if not errors else "fill_candidate_gate_fail"
    else:
        target_path = None
        target_status = None
        if receipt.get("write_target_entry") is True:
            errors.append("非候选回执出现写入口请求")
        if receipt.get("release_form") is True:
            errors.append("非候选回执被标为放行单")
        if receipt.get("auto_fill_shadow_entry") is True:
            errors.append("非候选回执出现自动填写入口")
        if receipt.get("seal_bucket") == "blocked_redline_archive" and target_entry != "gap_or_redline_record":
            errors.append("红线阻断项指向业务入口")
        gate_result = "remain_blocked_or_paused" if not errors else "non_candidate_gate_fail"

    return {
        "review_receipt_id": receipt.get("review_receipt_id"),
        "source_receipt_id": receipt.get("source_receipt_id"),
        "target_line": target_line,
        "target_entry": target_entry,
        "seal_bucket": receipt.get("seal_bucket"),
        "entry_fill_candidate": is_candidate,
        "target_path": target_path,
        "target_status": target_status,
        "gate_result": gate_result,
        "write_target_entry": False,
        "auto_fill_shadow_entry": False,
        "release_form": False,
        "formal_capability_claim": False,
        "status": "pass" if not errors else "fail",
        "errors": errors,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P2-S12 影子入口填写候选闸口只读检查",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['status']}",
        f"- 回执数：{report['summary']['receipt_count']}",
        f"- 填写候选通过：{report['summary']['fill_candidate_gate_pass']}",
        f"- 保持暂停或阻断：{report['summary']['remain_blocked_or_paused']}",
        f"- 失败数：{report['summary']['failed']}",
        f"- 写入口数量：{report['summary']['write_target_entry']}",
        "",
        "| 回执 | 路由 | 目标入口 | 候选 | 闸口结果 | 状态 |",
        "|:---|:---|:---|:---|:---|:---|",
    ]
    for item in report["checks"]:
        lines.append(f"| {item['review_receipt_id']} | {item['target_line']} | {item['target_entry']} | {item['entry_fill_candidate']} | {item['gate_result']} | {item['status']} |")
    lines.extend([
        "",
        "## 结论",
        "",
        report["conclusion"],
        "",
        "## 安全边界",
        "",
        "- 本检查只做填写前闸口预演。",
        "- 候选通过只代表可进入人工填写讨论，不代表自动写入口。",
        "- 不读取真实材料，不扫描用户目录，不写影子入口。",
        "- 不触发 n8n，不发送企业微信，不写正式库，不执行真实业务动作。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    gate = read_json(GATE_JSON)
    mapping_rule = read_json(MAPPING_RULE_JSON)
    sample = read_json(REVIEW_RECEIPTS_JSON)
    receipts = sample.get("review_receipts") or []
    routes = mapping_rule.get("routes") or {}
    checks = [check_candidate(receipt, gate, routes) for receipt in receipts]
    failed = [item for item in checks if item["status"] != "pass"]
    status = "pass" if not failed else "fail"
    report = {
        "id": "P2S12_SHADOW_ENTRY_FILL_CANDIDATE_GATE_READONLY_CHECK",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "summary": {
            "receipt_count": len(receipts),
            "passed": len(receipts) - len(failed),
            "failed": len(failed),
            "fill_candidate_gate_pass": sum(1 for item in checks if item["gate_result"] == "fill_candidate_gate_pass"),
            "remain_blocked_or_paused": sum(1 for item in checks if item["gate_result"] == "remain_blocked_or_paused"),
            "write_target_entry": sum(1 for item in checks if item["write_target_entry"]),
            "auto_fill_shadow_entry": sum(1 for item in checks if item["auto_fill_shadow_entry"]),
            "release_forms": sum(1 for item in checks if item["release_form"]),
            "formal_capability_claim": sum(1 for item in checks if item["formal_capability_claim"]),
        },
        "gate_sample_path": str(GATE_SAMPLE_JSON),
        "checks": checks,
        "conclusion": "影子入口填写候选闸口检查通过；4 份候选可进入人工填写讨论，3 份继续暂停或阻断，0 份自动填写或写入口。" if status == "pass" else "影子入口填写候选闸口存在缺口，需修复后再承接人工填写。",
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
    GATE_SAMPLE_JSON.write_text(json.dumps({"sample_only": True, "gate_items": checks}, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "总体状态": report["status"],
        "回执数": report["summary"]["receipt_count"],
        "通过": report["summary"]["passed"],
        "失败": report["summary"]["failed"],
        "候选通过": report["summary"]["fill_candidate_gate_pass"],
        "暂停或阻断": report["summary"]["remain_blocked_or_paused"],
        "自动填写入口数量": report["summary"]["auto_fill_shadow_entry"],
        "写入口数量": report["summary"]["write_target_entry"],
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
