# -*- coding: utf-8 -*-
"""
验证财报资金证据人工填写回执模板。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "财报资金证据人工填写回执模板_最新.json"
RESULT_JSON = DATA_DIR / "财报资金证据人工填写回执模板验收_最新.json"
RESULT_MD = DATA_DIR / "财报资金证据人工填写回执模板验收_最新.md"

REQUIRED_CODES = {"sz002428", "sz002466", "sh688347", "sz000906", "sz300641"}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1人工填写回执模板":
        errors.append("资产身份必须是 W1人工填写回执模板")
    if asset.get("status") != "blank_template":
        errors.append("状态必须是 blank_template")

    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write", "not_real_data_fetch", "not_formal_database_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    receipts = asset.get("receipts", [])
    codes = {item.get("stock", {}).get("code") for item in receipts}
    if codes != REQUIRED_CODES:
        errors.append(f"股票代码不完整：{sorted(codes)}")
    if len(receipts) != 25:
        errors.append(f"回执数量应为25，实际{len(receipts)}")

    for item in receipts:
        if item.get("receipt_status") != "blank":
            errors.append("receipt_status 默认必须 blank")
        if item.get("ready_review", {}).get("ready") is not False:
            errors.append(f"{item.get('display_name')} ready 必须 false")
        for field_name, field in item.get("field_receipts", {}).items():
            if field.get("value") is not None:
                errors.append(f"{field_name} 不得预填 value")
            if field.get("evidence_status") != "missing":
                errors.append(f"{field_name} evidence_status 默认必须 missing")
            if field.get("can_enter_score") is not False:
                errors.append(f"{field_name} can_enter_score 默认必须 false")

    rules_text = "\n".join(asset.get("receipt_rules", []))
    for phrase in ["来源名称", "evidence_ready", "can_enter_score", "不代表证据已补齐", "不得用回执空白字段"]:
        if phrase not in rules_text:
            errors.append(f"填写规则缺少：{phrase}")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_adapter_write", "not_score_write", "not_entrypoint", "not_broker_interface", "not_auto_trade", "not_real_data_fetch"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "财报资金证据人工填写回执模板验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": asset.get("summary", {}),
        "next_step": "继续生成行业价格观测人工填报回执模板；仍不得抓取真实数据或写正式库。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 财报资金证据人工填写回执模板验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 回执数量：{result['metrics'].get('receipt_count', 0)}",
        f"- 股票数量：{result['metrics'].get('stock_count', 0)}",
        f"- ready 数：{result['metrics'].get('ready_count', 0)}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in result["errors"]] or ["- 无"])
    lines.extend(["", "## 警告", ""])
    lines.extend([f"- {item}" for item in result["warnings"]] or ["- 无"])
    lines.extend(["", "## 下一步", "", f"- {result['next_step']}", ""])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
