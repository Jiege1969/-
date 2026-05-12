# -*- coding: utf-8 -*-
"""
验证前台结论型短答统一验收记录。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "前台结论型短答统一验收记录_最新.json"
RESULT_JSON = DATA_DIR / "前台结论型短答统一验收记录验收_最新.json"
RESULT_MD = DATA_DIR / "前台结论型短答统一验收记录验收_最新.md"

REQUIRED_CODES = {"sz002428", "sz002466", "sh688347", "sz000906", "sz300641"}
REQUIRED_GATES = {"financial_capital", "industry_price", "policy_event_exposure", "market_style_fit"}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1前台短答统一验收记录":
        errors.append("资产身份必须是 W1前台短答统一验收记录")
    if asset.get("status") != "shadow_acceptance":
        errors.append("状态必须是 shadow_acceptance")

    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write", "not_real_wecom_send"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    contract = asset.get("front_answer_contract", {})
    if len(contract.get("required_lines", [])) != 5:
        errors.append("前台短答必须保持5行契约")
    if "不能强行补分" not in contract.get("missing_rule", ""):
        errors.append("缺口规则必须禁止强行补分")
    for term in ["买入", "卖出", "下单", "仓位调整", "自动交易", "券商接口"]:
        if term not in contract.get("forbidden", []):
            errors.append(f"禁止词缺少：{term}")

    gates = asset.get("evidence_gate_checks", [])
    gate_names = {item.get("name") for item in gates}
    if gate_names != REQUIRED_GATES:
        errors.append(f"证据闸口不完整：{sorted(gate_names)}")
    for gate in gates:
        if gate.get("exists") is not True:
            errors.append(f"{gate.get('name')} 验收资产不存在")
        if gate.get("passed") is not True:
            errors.append(f"{gate.get('name')} 验收未通过")

    samples = asset.get("sample_checks", [])
    codes = {item.get("stock", {}).get("code") for item in samples}
    if codes != REQUIRED_CODES:
        errors.append(f"样本股票代码不完整：{sorted(codes)}")
    if len(samples) != 5:
        errors.append(f"样本数量应为5，实际{len(samples)}")
    for item in samples:
        checks = item.get("checks", {})
        for check_name in ["object_line", "conclusion_line", "main_reason_line", "key_gap_line", "confidence_line", "missing_explicit", "no_forbidden_terms"]:
            if checks.get(check_name) is not True:
                errors.append(f"{item.get('stock', {}).get('code')} 检查失败：{check_name}")
        if item.get("passed") is not True:
            errors.append(f"{item.get('stock', {}).get('code')} 样本验收未通过")

    summary = asset.get("summary", {})
    if summary.get("allow_real_wecom_send") is not False:
        errors.append("影子验收不得允许真实企业微信发送")
    if summary.get("allow_formal_entry") is not False:
        errors.append("影子验收不得允许正式入口")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_adapter_write", "not_score_write", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "前台结论型短答统一验收记录验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": summary,
        "auto_continue_policy": "通过后继续进入下一低风险小闭环；不等待用户确认。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 前台结论型短答统一验收记录验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 样本通过：{result['metrics'].get('sample_passed_count', 0)}/{result['metrics'].get('sample_count', 0)}",
        f"- 证据闸口通过：{result['metrics'].get('gate_passed_count', 0)}/{result['metrics'].get('gate_count', 0)}",
        f"- 允许真实企微发送：{result['metrics'].get('allow_real_wecom_send')}",
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
