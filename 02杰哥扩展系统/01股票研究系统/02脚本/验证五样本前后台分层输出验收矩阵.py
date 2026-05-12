# -*- coding: utf-8 -*-
"""
验证五样本前后台分层输出验收矩阵。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "五样本前后台分层输出验收矩阵_最新.json"
RESULT_JSON = DATA_DIR / "五样本前后台分层输出验收矩阵验收_最新.json"
RESULT_MD = DATA_DIR / "五样本前后台分层输出验收矩阵验收_最新.md"
REQUIRED_CODES = {"sz002428", "sz002466", "sh688347", "sz000906", "sz300641"}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1前后台分层输出验收矩阵":
        errors.append("资产身份必须是 W1前后台分层输出验收矩阵")
    if asset.get("status") != "shadow_acceptance":
        errors.append("状态必须是 shadow_acceptance")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    matrix = asset.get("matrix", [])
    codes = {item.get("stock", {}).get("code") for item in matrix}
    if codes != REQUIRED_CODES:
        errors.append(f"样本代码不完整：{sorted(codes)}")
    if len(matrix) != 5:
        errors.append(f"样本数量应为5，实际{len(matrix)}")
    for item in matrix:
        stock_code = item.get("stock", {}).get("code")
        front = item.get("front_layer", {})
        backend = item.get("backend_layer", {})
        layering = item.get("layering_rule", {})
        for check in ["object_line_clear", "conclusion_line_present", "main_reason_line_present", "key_gap_line_present", "confidence_line_present", "no_forbidden_terms", "allowed_for_shadow_front"]:
            if front.get(check) is not True:
                errors.append(f"{stock_code} 前台检查失败：{check}")
        for check in ["must_keep_evidence", "must_keep_missing", "must_keep_confidence", "must_keep_next_review", "must_keep_source_assets", "must_keep_gate_decisions"]:
            if backend.get(check) is not True:
                errors.append(f"{stock_code} 后台检查失败：{check}")
        if layering.get("front_should_not_dump_indicators") is not True:
            errors.append(f"{stock_code} 必须禁止前台堆指标")
        if layering.get("backend_should_not_be_lost") is not True:
            errors.append(f"{stock_code} 必须保留后台证据链")
        if layering.get("real_wecom_send_allowed") is not False:
            errors.append(f"{stock_code} 不得允许真实企微发送")

    rules_text = json.dumps(asset.get("global_rules", {}), ensure_ascii=False)
    for phrase in ["不堆后台指标", "关键缺口必须显式写出", "保留evidence数组", "后台证据链丢失", "交易执行话术"]:
        if phrase not in rules_text:
            errors.append(f"规则缺少：{phrase}")

    summary = asset.get("summary", {})
    if summary.get("real_wecom_send_allowed") is not False:
        errors.append("real_wecom_send_allowed 必须false")
    if summary.get("formal_entry_allowed") is not False:
        errors.append("formal_entry_allowed 必须false")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_formal_config", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "五样本前后台分层输出验收矩阵验收",
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
        "# 五样本前后台分层输出验收矩阵验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 样本数：{result['metrics'].get('sample_count', 0)}",
        f"- 前台通过：{result['metrics'].get('front_passed_count', 0)}",
        f"- 真实企微允许：{result['metrics'].get('real_wecom_send_allowed')}",
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
