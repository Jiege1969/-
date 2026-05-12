# -*- coding: utf-8 -*-
"""
验证股票 L3 五样本统一刷新验收清单。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "股票L3五样本统一刷新验收清单_最新.json"
RESULT_JSON = DATA_DIR / "股票L3五样本统一刷新验收清单验收_最新.json"
RESULT_MD = DATA_DIR / "股票L3五样本统一刷新验收清单验收_最新.md"

REQUIRED_KEYS = {
    "l3_gap_priority",
    "policy_gap_queue",
    "industry_price_queue",
    "financial_capital_template",
    "front_answer_samples",
    "backend_front_mapping",
    "sample_mapping_acceptance",
}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1统一刷新验收清单":
        errors.append("资产身份必须是 W1统一刷新验收清单")
    if asset.get("status") != "draft":
        errors.append("状态必须保持 draft")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write", "not_real_refresh"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_adapter_write", "not_score_write", "not_entrypoint", "not_broker_interface", "not_auto_trade", "not_real_refresh"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    checks = asset.get("asset_checks", [])
    keys = {item.get("asset_key") for item in checks}
    if keys != REQUIRED_KEYS:
        errors.append(f"资产 key 不完整：{sorted(keys)}")
    for item in checks:
        if item.get("exists") is not True:
            errors.append(f"{item.get('display_name')} 缺失")
        if item.get("refresh_check") != "pass":
            errors.append(f"{item.get('display_name')} refresh_check 非 pass")
        if not item.get("blocking_if_missing"):
            errors.append(f"{item.get('display_name')} 缺少缺失阻断说明")

    contract = "\n".join(asset.get("refresh_contract", []))
    for phrase in ["先验收结构化证据", "前台必须写缺口", "不抓取真实数据", "不等于正式上线"]:
        if phrase not in contract:
            errors.append(f"刷新契约缺少：{phrase}")

    result = {
        "name": "股票L3五样本统一刷新验收清单验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": asset.get("summary", {}),
        "next_step": "继续生成统一刷新验收执行记录模板；仍不得真实刷新、外发或写正式库。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 股票L3五样本统一刷新验收清单验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 资产数：{result['metrics'].get('asset_count', 0)}",
        f"- 已存在：{result['metrics'].get('exists_count', 0)}",
        f"- 缺失：{result['metrics'].get('missing_count', 0)}",
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
