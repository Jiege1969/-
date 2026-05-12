# -*- coding: utf-8 -*-
"""
验证行业价格观测人工填报回执模板。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "行业价格观测人工填报回执模板_最新.json"
RESULT_JSON = DATA_DIR / "行业价格观测人工填报回执模板验收_最新.json"
RESULT_MD = DATA_DIR / "行业价格观测人工填报回执模板验收_最新.md"

REQUIRED_CODES = {"sz002428", "sz002466", "sh688347", "sz000906", "sz300641"}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1行业价格人工填报回执模板":
        errors.append("资产身份必须是 W1行业价格人工填报回执模板")
    if asset.get("status") != "blank_template":
        errors.append("状态必须是 blank_template")

    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write", "not_real_data_fetch", "not_formal_database_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    receipts = asset.get("receipts", [])
    codes = {item.get("stock", {}).get("code") for item in receipts}
    if codes != REQUIRED_CODES:
        errors.append(f"股票代码不完整：{sorted(codes)}")
    if len(receipts) != 5:
        errors.append(f"回执数量应为5，实际{len(receipts)}")

    for item in receipts:
        stock_code = item.get("stock", {}).get("code")
        product_name = item.get("product_name")
        target = item.get("target_min_observation_count")
        rows = item.get("observation_rows", [])
        if item.get("receipt_status") != "blank":
            errors.append(f"{stock_code}/{product_name} receipt_status默认必须blank")
        if target != 5:
            errors.append(f"{stock_code}/{product_name} target_min_observation_count必须为5")
        if len(rows) != 5:
            errors.append(f"{stock_code}/{product_name} observation_rows必须为5行")
        ready = item.get("ready_review", {})
        if ready.get("trend_ready") is not False:
            errors.append(f"{stock_code}/{product_name} trend_ready必须false")
        if ready.get("score_ready") is not False:
            errors.append(f"{stock_code}/{product_name} score_ready必须false")
        if "观测点不足" not in ready.get("blocking_reason", ""):
            errors.append(f"{stock_code}/{product_name} blocking_reason必须说明观测点不足")
        if "不足" not in item.get("front_gap_wording", ""):
            errors.append(f"{stock_code}/{product_name} front_gap_wording必须说明不足")
        for row in rows:
            for field in ["observation_date", "value_or_direction", "unit_or_caliber", "source_name", "source_url", "checked_at"]:
                if row.get(field) is not None:
                    errors.append(f"{stock_code}/{product_name} 第{row.get('row_no')}行 {field} 不得预填")
            if row.get("evidence_status") != "missing":
                errors.append(f"{stock_code}/{product_name} 第{row.get('row_no')}行 evidence_status必须missing")
            if row.get("review_status") != "pending_review":
                errors.append(f"{stock_code}/{product_name} 第{row.get('row_no')}行 review_status必须pending_review")
            if row.get("can_enter_trend") is not False:
                errors.append(f"{stock_code}/{product_name} 第{row.get('row_no')}行 can_enter_trend必须false")
            if row.get("can_enter_score") is not False:
                errors.append(f"{stock_code}/{product_name} 第{row.get('row_no')}行 can_enter_score必须false")

    rules_text = "\n".join(asset.get("receipt_rules", []))
    for phrase in ["不足5个连续", "不能写价格趋势确认", "不能进入L3评分", "不抓取真实价格"]:
        if phrase not in rules_text:
            errors.append(f"填报规则缺少：{phrase}")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_adapter_write", "not_score_write", "not_entrypoint", "not_broker_interface", "not_auto_trade", "not_real_data_fetch"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "行业价格观测人工填报回执模板验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": asset.get("summary", {}),
        "auto_continue_policy": "通过后自动进入下一低风险小闭环；不把下一步建议作为等待用户确认。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 行业价格观测人工填报回执模板验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 回执数量：{result['metrics'].get('receipt_count', 0)}",
        f"- 股票数量：{result['metrics'].get('stock_count', 0)}",
        f"- 需补观测点：{result['metrics'].get('required_observation_points', 0)}",
        f"- 已有观测点：{result['metrics'].get('existing_observation_points', 0)}",
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
