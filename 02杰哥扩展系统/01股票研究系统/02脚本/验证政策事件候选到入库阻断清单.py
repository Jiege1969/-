# -*- coding: utf-8 -*-
"""
验证政策事件候选到入库阻断清单。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "政策事件候选到入库阻断清单_最新.json"
RESULT_JSON = DATA_DIR / "政策事件候选到入库阻断清单验收_最新.json"
RESULT_MD = DATA_DIR / "政策事件候选到入库阻断清单验收_最新.md"


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1政策候选入库阻断清单":
        errors.append("资产身份必须是 W1政策候选入库阻断清单")
    if asset.get("status") != "shadow_blocking_checklist":
        errors.append("状态必须是 shadow_blocking_checklist")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_policy_event_write", "not_score_write", "not_formal_database_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    source = asset.get("source_assets", {})
    if source.get("candidate_draft_exists") is not True:
        errors.append("候选草案不存在")
    if source.get("exposure_review_validation_passed") is not True:
        errors.append("政策暴露度复核模板验收未通过")

    records = asset.get("candidate_blocking_records", [])
    if not records:
        errors.append("候选阻断记录不能为空")
    for item in records:
        decision = item.get("entry_decision", {})
        if item.get("not_for_scoring") is not True:
            errors.append(f"{item.get('candidate_id')} not_for_scoring必须true")
        for gate, value in item.get("entry_gates", {}).items():
            if value is not False:
                errors.append(f"{item.get('candidate_id')} {gate} 初始必须false")
        for field in ["can_write_policy_events", "can_write_stock_exposures", "can_enter_l3_policy_score"]:
            if decision.get(field) is not False:
                errors.append(f"{item.get('candidate_id')} {field} 必须false")
        if "只能作为线索" not in decision.get("blocking_reason", ""):
            errors.append(f"{item.get('candidate_id')} blocking_reason必须说明只能作为线索")

    rules_text = "\n".join(asset.get("global_blocking_rules", []))
    for phrase in ["不得参与L3政策分", "不得直接写入policy_events", "不得直接写入stock_policy_exposures", "只能作为线索", "不得替代结构化政策事件"]:
        if phrase not in rules_text:
            errors.append(f"全局阻断规则缺少：{phrase}")

    summary = asset.get("summary", {})
    if summary.get("entry_allowed_count") != 0:
        errors.append("entry_allowed_count必须为0")
    if summary.get("score_allowed_count") != 0:
        errors.append("score_allowed_count必须为0")
    if summary.get("blocked_count") != summary.get("candidate_count"):
        errors.append("所有候选都必须处于阻断状态")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_formal_config", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "政策事件候选到入库阻断清单验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": summary,
        "auto_continue_policy": "通过后继续执行第二批下一小闭环；不等待用户确认。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 政策事件候选到入库阻断清单验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 候选数：{result['metrics'].get('candidate_count', 0)}",
        f"- 入库允许：{result['metrics'].get('entry_allowed_count', 0)}",
        f"- 入分允许：{result['metrics'].get('score_allowed_count', 0)}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in result["errors"]] or ["- 无"])
    lines.extend(["", "## 警告", ""])
    lines.extend([f"- {item}" for item in result["warnings"]] or ["- 无"])
    lines.extend(["", "## 自动续建口径", "", f"- {result['auto_continue_policy']}", ""])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
