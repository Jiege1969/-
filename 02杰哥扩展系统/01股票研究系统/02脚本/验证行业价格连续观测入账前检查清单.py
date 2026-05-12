# -*- coding: utf-8 -*-
"""
验证行业价格连续观测入账前检查清单。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "行业价格连续观测入账前检查清单_最新.json"
RESULT_JSON = DATA_DIR / "行业价格连续观测入账前检查清单验收_最新.json"
RESULT_MD = DATA_DIR / "行业价格连续观测入账前检查清单验收_最新.md"
REQUIRED_CODES = {"sz002428", "sz002466", "sh688347", "sz000906", "sz300641"}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1行业价格入账前检查清单":
        errors.append("资产身份必须是 W1行业价格入账前检查清单")
    if asset.get("status") != "shadow_checklist":
        errors.append("状态必须是 shadow_checklist")

    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write", "not_real_data_fetch"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    source = asset.get("source_assets", {})
    if source.get("receipt_template_exists") is not True:
        errors.append("缺少行业价格回执模板")
    if source.get("receipt_validation_passed") is not True:
        errors.append("行业价格回执模板验收未通过")

    checklists = asset.get("checklists", [])
    codes = {item.get("stock", {}).get("code") for item in checklists}
    if codes != REQUIRED_CODES:
        errors.append(f"股票代码不完整：{sorted(codes)}")
    if len(checklists) != 5:
        errors.append(f"样本数量应为5，实际{len(checklists)}")
    for item in checklists:
        stock_code = item.get("stock", {}).get("code")
        gates = item.get("entry_gates", {})
        decision = item.get("entry_decision", {})
        for gate in [
            "public_or_authorized_source",
            "observation_date_complete",
            "value_or_direction_complete",
            "unit_or_caliber_complete",
            "source_name_complete",
            "source_url_complete",
            "checked_at_complete",
            "same_caliber_continuity",
            "human_review_passed",
        ]:
            if gates.get(gate) is not False:
                errors.append(f"{stock_code} {gate} 初始必须false")
        if decision.get("can_enter_observation_ledger") is not False:
            errors.append(f"{stock_code} can_enter_observation_ledger必须false")
        if decision.get("can_enter_trend_evidence") is not False:
            errors.append(f"{stock_code} can_enter_trend_evidence必须false")
        if decision.get("can_enter_score") is not False:
            errors.append(f"{stock_code} can_enter_score必须false")
        if "不能写趋势确认" not in decision.get("blocking_reason", ""):
            errors.append(f"{stock_code} blocking_reason必须阻断趋势确认")
        wording = item.get("front_wording", {})
        if "不能写趋势确认" not in wording.get("when_less_than_5", ""):
            errors.append(f"{stock_code} 少于5点话术必须阻断趋势确认")
        if "弱趋势参考" not in wording.get("when_5_to_19", ""):
            errors.append(f"{stock_code} 5-19点话术必须限制为弱趋势参考")

    rules_text = "\n".join(asset.get("global_entry_rules", []))
    for phrase in ["日期、数值或方向、单位或口径、来源名称、来源URL、核验时间", "不足5个连续", "5到19个", "20个及以上", "媒体摘要只能作为线索", "can_enter_score必须为false"]:
        if phrase not in rules_text:
            errors.append(f"入账规则缺少：{phrase}")

    summary = asset.get("summary", {})
    if summary.get("trend_ready_count") != 0:
        errors.append("当前trend_ready_count应为0")
    if summary.get("score_allowed_count") != 0:
        errors.append("当前score_allowed_count应为0")
    if summary.get("ledger_entry_allowed_count") != 0:
        errors.append("当前ledger_entry_allowed_count应为0")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_formal_config", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "行业价格连续观测入账前检查清单验收",
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
        "# 行业价格连续观测入账前检查清单验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 样本数：{result['metrics'].get('stock_count', 0)}",
        f"- 已有观测点：{result['metrics'].get('existing_observation_points', 0)}",
        f"- trend_ready_count：{result['metrics'].get('trend_ready_count', 0)}",
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
