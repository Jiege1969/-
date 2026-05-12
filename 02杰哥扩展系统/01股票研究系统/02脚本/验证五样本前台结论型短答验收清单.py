# -*- coding: utf-8 -*-
"""
验证五样本前台结论型短答验收清单。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "五样本前台结论型短答验收清单_最新.json"
RESULT_JSON = DATA_DIR / "五样本前台结论型短答验收清单验收_最新.json"
RESULT_MD = DATA_DIR / "五样本前台结论型短答验收清单验收_最新.md"

EXPECTED_CODES = {"sz002428", "sz002466", "sh688347", "sz000906", "sz300641"}
REQUIRED_CHECKS = {
    "object_first_line",
    "conclusion_first",
    "evidence_gap_explicit",
    "rule_wording_hit",
    "no_trade_terms",
    "no_overclaim_when_missing",
    "front_readability",
}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []

    if not ASSET_PATH.exists():
        errors.append(f"缺少资产文件：{ASSET_PATH}")
        asset = {}
    else:
        asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig"))

    if asset.get("asset_identity") != "W1验收清单":
        errors.append("资产身份必须是 W1验收清单")
    if asset.get("status") != "draft":
        errors.append("状态必须保持 draft")

    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    safety = asset.get("safety_boundary", {})
    for flag in [
        "not_n8n",
        "not_external_send",
        "not_service_restart",
        "not_19310",
        "not_real_account",
        "not_formal_database_write",
        "not_adapter_write",
        "not_score_write",
        "not_entrypoint",
        "not_broker_interface",
        "not_auto_trade",
    ]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    sample_checks = asset.get("sample_checks", [])
    codes = {item.get("stock", {}).get("code") for item in sample_checks}
    if codes != EXPECTED_CODES:
        errors.append(f"样本代码不完整：{sorted(codes)}")
    if len(sample_checks) != 5:
        errors.append(f"样本数量应为 5，实际 {len(sample_checks)}")

    for item in sample_checks:
        stock = item.get("stock", {})
        checks = item.get("checks", {})
        missing_checks = REQUIRED_CHECKS - set(checks)
        if missing_checks:
            errors.append(f"{stock.get('name')} 缺少检查项：{sorted(missing_checks)}")
        if item.get("source_text_length", 0) <= 0:
            errors.append(f"{stock.get('name')} 未识别到短答预演文本")
        if item.get("prohibited_trade_terms"):
            errors.append(f"{stock.get('name')} 出现交易相关词：{item.get('prohibited_trade_terms')}")
        if item.get("overclaim_terms"):
            warnings.append(f"{stock.get('name')} 出现强结论词，需人工复核：{item.get('overclaim_terms')}")

    contract_text = "\n".join(asset.get("acceptance_contract", []))
    for phrase in ["第一行", "先给结论", "证据缺失", "结构化证据", "不得出现买入"]:
        if phrase not in contract_text:
            errors.append(f"验收契约缺少关键约束：{phrase}")

    result = {
        "name": "五样本前台结论型短答验收清单验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "sample_count": len(sample_checks),
            "pass_count": asset.get("summary", {}).get("pass_count", 0),
            "needs_revision_count": asset.get("summary", {}).get("needs_revision_count", 0),
        },
        "next_step": "可继续生成五样本前台结论型短答修订样例；仍不得写企业微信正式入口。",
    }

    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 五样本前台结论型短答验收清单验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 样本数量：{result['metrics']['sample_count']}",
        f"- 通过样本：{result['metrics']['pass_count']}",
        f"- 待修样本：{result['metrics']['needs_revision_count']}",
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
