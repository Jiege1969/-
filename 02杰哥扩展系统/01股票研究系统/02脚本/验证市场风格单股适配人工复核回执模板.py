# -*- coding: utf-8 -*-
"""
验证市场风格单股适配人工复核回执模板。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "市场风格单股适配人工复核回执模板_最新.json"
RESULT_JSON = DATA_DIR / "市场风格单股适配人工复核回执模板验收_最新.json"
RESULT_MD = DATA_DIR / "市场风格单股适配人工复核回执模板验收_最新.md"

REQUIRED_CODES = {"sz002428", "sz002466", "sh688347", "sz000906", "sz300641"}
REQUIRED_FIELDS = {"risk_appetite_fit", "sector_heat_fit", "size_style_fit", "liquidity_fit", "stock_style_fit_score"}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1市场风格单股适配复核模板":
        errors.append("资产身份必须是 W1市场风格单股适配复核模板")
    if asset.get("status") != "blank_template":
        errors.append("状态必须是 blank_template")

    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write", "not_formal_database_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    receipts = asset.get("receipts", [])
    codes = {item.get("stock", {}).get("code") for item in receipts}
    if codes != REQUIRED_CODES:
        errors.append(f"股票代码不完整：{sorted(codes)}")
    if len(receipts) != 5:
        errors.append(f"回执数量应为5，实际{len(receipts)}")

    for item in receipts:
        stock = item.get("stock", {})
        fields = item.get("review_fields", {})
        if set(fields) != REQUIRED_FIELDS:
            errors.append(f"{stock.get('code')} 复核字段不完整：{sorted(fields)}")
        if item.get("receipt_status") != "blank":
            errors.append(f"{stock.get('code')} receipt_status必须blank")
        if not item.get("stock_type_tags"):
            errors.append(f"{stock.get('code')} 缺stock_type_tags")
        if not item.get("style_focus"):
            errors.append(f"{stock.get('code')} 缺style_focus")
        for field_name, field in fields.items():
            if field.get("value") is not None:
                errors.append(f"{stock.get('code')} {field_name} 不得预填value")
            if field.get("evidence_status") != "missing":
                errors.append(f"{stock.get('code')} {field_name} evidence_status必须missing")
            if field.get("review_status") != "pending_review":
                errors.append(f"{stock.get('code')} {field_name} review_status必须pending_review")
        ready = item.get("ready_review", {})
        if ready.get("style_fit_ready") is not False:
            errors.append(f"{stock.get('code')} style_fit_ready必须false")
        if ready.get("score_ready") is not False:
            errors.append(f"{stock.get('code')} score_ready必须false")
        if "不能仅凭市场整体强弱" not in ready.get("blocking_reason", ""):
            errors.append(f"{stock.get('code')} blocking_reason必须阻断市场整体强弱直接推单股")
        missing_rule = item.get("front_output_rule", {}).get("when_missing", "")
        if "不能写强适配结论" not in missing_rule:
            errors.append(f"{stock.get('code')} 前台缺口话术必须阻断强适配结论")

    rules_text = "\n".join(asset.get("review_rules", []))
    for phrase in ["不能自动推出单股适配结论", "stock_style_fit_score不得填写", "结论性短答", "不触发n8n"]:
        if phrase not in rules_text:
            errors.append(f"复核规则缺少：{phrase}")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_adapter_write", "not_score_write", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "市场风格单股适配人工复核回执模板验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": asset.get("summary", {}),
        "auto_continue_policy": "通过后继续进入下一低风险小闭环；不等待用户确认。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 市场风格单股适配人工复核回执模板验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 回执数量：{result['metrics'].get('receipt_count', 0)}",
        f"- 股票数量：{result['metrics'].get('stock_count', 0)}",
        f"- 日表状态：{result['metrics'].get('daily_style_status')}",
        f"- style_fit_ready_count：{result['metrics'].get('style_fit_ready_count', 0)}",
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
