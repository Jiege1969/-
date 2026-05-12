# -*- coding: utf-8 -*-
"""验证 L3 证据缺口统一刷新验收样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "L3证据缺口统一刷新验收样例_最新.json"
RESULT_JSON = DATA_DIR / "L3证据缺口统一刷新验收样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "L3证据缺口统一刷新验收样例验收结果_最新.md"


REQUIRED_SAMPLE_FIELDS = {
    "stock_name",
    "stock_code",
    "frontend_first_line",
    "ready_evidence",
    "key_missing",
    "conclusion_cap",
    "confidence_cap",
    "frontend_output_guard",
    "backend_required_fields",
}


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W2 L3证据缺口统一刷新验收样例":
        errors.append("资产身份不正确")
    if asset.get("status") != "shadow_refresh_acceptance":
        errors.append("状态必须为 shadow_refresh_acceptance")
    for flag in [
        "not_formal_config",
        "not_formal_entry",
        "not_external_send",
        "not_real_market_data",
        "not_score_write",
        "not_rule_update",
    ]:
        if asset.get(flag) is not True:
            errors.append(f"{flag} 必须为 true")
    contract = asset.get("refresh_contract", {})
    for field in ["frontend_rule", "backend_rule", "missing_rule", "score_rule", "replay_rule"]:
        if not contract.get(field):
            errors.append(f"refresh_contract 缺少 {field}")
    source_validations = asset.get("source_validations", [])
    if len(source_validations) < 6:
        errors.append("来源验收不得少于6项")
    if not all(item.get("exists") is True for item in source_validations):
        errors.append("存在缺失的来源验收文件")
    if not all(item.get("passed") is True for item in source_validations if item.get("required_for_frontend") is True):
        errors.append("前台必需来源验收存在未通过项")
    samples = asset.get("samples", [])
    if len(samples) < 5:
        errors.append("样本不得少于5只股票")
    for sample in samples:
        name = sample.get("stock_name", "")
        missing_fields = REQUIRED_SAMPLE_FIELDS - sample.keys()
        if missing_fields:
            errors.append(f"{name} 缺少字段：{sorted(missing_fields)}")
        if not sample.get("key_missing"):
            errors.append(f"{name} 必须显式列出 key_missing")
        if sample.get("confidence_cap") == "high":
            errors.append(f"{name} 当前缺口未关闭时不得为 high confidence")
        first_line = sample.get("frontend_first_line", "")
        if sample.get("stock_name") not in first_line or sample.get("stock_code") not in first_line:
            errors.append(f"{name} 前台第一行必须包含名称和代码")
        backend_fields = set(sample.get("backend_required_fields", []))
        for required in ["evidence", "missing", "confidence", "next_review_date", "replay_candidate"]:
            if required not in backend_fields:
                errors.append(f"{name} 后台字段缺少 {required}")
    summary = asset.get("summary", {})
    if summary.get("formal_score_write_allowed") is not False:
        errors.append("不得允许正式评分写入")
    if summary.get("real_external_send_allowed") is not False:
        errors.append("不得允许真实外发")
    safety = asset.get("safety_boundary", {})
    for flag in [
        "not_n8n",
        "not_external_send",
        "not_service_restart",
        "not_19310",
        "not_real_account",
        "not_formal_database_write",
        "not_formal_config",
        "not_entrypoint",
        "not_broker_interface",
        "not_auto_trade",
        "not_order",
        "not_position_adjustment",
    ]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")
    result = {
        "name": "L3证据缺口统一刷新验收样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {
            "source_validation_count": len(source_validations),
            "source_validation_passed_count": len([item for item in source_validations if item.get("passed") is True]),
            "sample_count": len(samples),
            "formal_score_write_allowed": summary.get("formal_score_write_allowed"),
            "real_external_send_allowed": summary.get("real_external_send_allowed"),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# L3证据缺口统一刷新验收样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 来源验收数：{result['metrics']['source_validation_count']}",
        f"- 来源通过数：{result['metrics']['source_validation_passed_count']}",
        f"- 样本数：{result['metrics']['sample_count']}",
        f"- 正式评分写入允许：{result['metrics']['formal_score_write_allowed']}",
        f"- 真实外发允许：{result['metrics']['real_external_send_allowed']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
