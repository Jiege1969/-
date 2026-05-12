# -*- coding: utf-8 -*-
"""
验证五样本后台到前台字段映射验收样例。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "五样本后台到前台字段映射验收样例_最新.json"
RESULT_JSON = DATA_DIR / "五样本后台到前台字段映射验收样例验收_最新.json"
RESULT_MD = DATA_DIR / "五样本后台到前台字段映射验收样例验收_最新.md"

EXPECTED_CODES = {"sz002428", "sz002466", "sh688347", "sz000906", "sz300641"}
REQUIRED_FIELDS = {"object_line", "conclusion_line", "main_reason_line", "key_gap_line", "confidence_review_line"}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1字段映射验收样例":
        errors.append("资产身份必须是 W1字段映射验收样例")
    if asset.get("status") != "draft":
        errors.append("状态必须保持 draft")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_adapter_write", "not_score_write", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    sample_mappings = asset.get("sample_mappings", [])
    codes = {item.get("stock", {}).get("code") for item in sample_mappings}
    if codes != EXPECTED_CODES:
        errors.append(f"样本代码不完整：{sorted(codes)}")
    if len(sample_mappings) != 5:
        errors.append(f"样本数量应为5，实际{len(sample_mappings)}")

    for item in sample_mappings:
        stock = item.get("stock", {})
        field_checks = item.get("field_checks", {})
        if set(field_checks) != REQUIRED_FIELDS:
            errors.append(f"{stock.get('name')} 字段不完整：{sorted(field_checks)}")
        if not item.get("backend_trace_present"):
            errors.append(f"{stock.get('name')} 后台来源未完整承接")
        if not item.get("gap_line_present"):
            errors.append(f"{stock.get('name')} 缺口未承接到前台")
        for field_name, check in field_checks.items():
            if not check.get("backend_trace"):
                errors.append(f"{stock.get('name')} {field_name} 缺少后台来源")
            if not check.get("front_value"):
                errors.append(f"{stock.get('name')} {field_name} 缺少前台值")
            if check.get("passed") is not True:
                warnings.append(f"{stock.get('name')} {field_name} 待修")

    blockers = asset.get("formalization_blockers", [])
    if len(blockers) < 3:
        errors.append("正式化阻断登记不足")
    if not all(item.get("risk_level") == "W3" for item in blockers):
        errors.append("正式化阻断必须全部标注 W3")

    serialized = json.dumps(asset, ensure_ascii=False)
    for term in ["买入", "卖出", "下单", "仓位调整", "自动交易", "券商接口"]:
        if term in serialized and "禁止新增" not in serialized:
            errors.append(f"交易词 {term} 未作为禁止边界表达")

    result = {
        "name": "五样本后台到前台字段映射验收样例验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "sample_count": len(sample_mappings),
            "pass_count": asset.get("summary", {}).get("pass_count", 0),
            "needs_revision_count": asset.get("summary", {}).get("needs_revision_count", 0),
            "warning_count": len(warnings),
        },
        "next_step": "若本样例通过，可转向财报/资金证据补齐或统一刷新验收；仍不得写正式企业微信入口。",
    }

    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 五样本后台到前台字段映射验收样例验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 样本数量：{result['metrics']['sample_count']}",
        f"- 通过样本：{result['metrics']['pass_count']}",
        f"- 待修样本：{result['metrics']['needs_revision_count']}",
        f"- 警告数量：{result['metrics']['warning_count']}",
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
