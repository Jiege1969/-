# -*- coding: utf-8 -*-
"""
验证财报资金缺口主动暴露规则验收。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "财报资金缺口主动暴露规则验收_最新.json"
RESULT_JSON = DATA_DIR / "财报资金缺口主动暴露规则验收结果_最新.json"
RESULT_MD = DATA_DIR / "财报资金缺口主动暴露规则验收结果_最新.md"
REQUIRED_CODES = {"sz002428", "sz002466", "sh688347", "sz000906", "sz300641"}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1财报资金缺口主动暴露规则":
        errors.append("资产身份必须是 W1财报资金缺口主动暴露规则")
    if asset.get("status") != "shadow_acceptance":
        errors.append("状态必须是 shadow_acceptance")

    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write", "not_real_data_fetch"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    source = asset.get("source_assets", {})
    if source.get("receipt_template_exists") is not True:
        errors.append("缺少财报资金回执模板")
    if source.get("receipt_validation_passed") is not True:
        errors.append("财报资金回执模板验收未通过")

    rules = asset.get("stock_gap_rules", [])
    codes = {item.get("stock", {}).get("code") for item in rules}
    if codes != REQUIRED_CODES:
        errors.append(f"股票代码不完整：{sorted(codes)}")
    if len(rules) != 5:
        errors.append(f"样本数量应为5，实际{len(rules)}")
    for item in rules:
        stock_code = item.get("stock", {}).get("code")
        if not item.get("missing_groups"):
            errors.append(f"{stock_code} 必须列出缺口组")
        if "不能强化结论" not in item.get("front_gap_wording", ""):
            errors.append(f"{stock_code} 前台缺口话术必须阻断强化结论")
        blocking = item.get("backend_blocking_fields", {})
        for field in [
            "financial_capital_score_allowed",
            "fundamental_confirmation_allowed",
            "capital_flow_confirmation_allowed",
            "institutional_confirmation_allowed",
            "unlock_risk_confirmation_allowed",
        ]:
            if blocking.get(field) is not False:
                errors.append(f"{stock_code} {field} 必须为false")
        if blocking.get("max_confidence_if_other_evidence_ready") != "medium":
            errors.append(f"{stock_code} 缺财报资金时最高置信度应限制为medium")

    front_text = "\n".join(asset.get("global_front_rules", []))
    for phrase in ["必须主动写", "不能写基本面确认", "不能写资金确认", "不能写机构认可", "不能写风险已排除"]:
        if phrase not in front_text:
            errors.append(f"前台规则缺少：{phrase}")
    backend_text = "\n".join(asset.get("global_backend_rules", []))
    for phrase in ["默认为false", "不得进入L3加分", "空白回执不得作为证据", "复核前保持pending_review"]:
        if phrase not in backend_text:
            errors.append(f"后台规则缺少：{phrase}")

    summary = asset.get("summary", {})
    if summary.get("ready_count") != 0:
        errors.append("当前ready_count应为0")
    if summary.get("score_allowed_count") != 0:
        errors.append("当前score_allowed_count应为0")
    if summary.get("front_gap_required_count") != 5:
        errors.append("5只样本均应要求前台主动暴露缺口")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_formal_config", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "财报资金缺口主动暴露规则验收结果",
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
        "# 财报资金缺口主动暴露规则验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 样本数：{result['metrics'].get('stock_count', 0)}",
        f"- ready_count：{result['metrics'].get('ready_count', 0)}",
        f"- score_allowed_count：{result['metrics'].get('score_allowed_count', 0)}",
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
