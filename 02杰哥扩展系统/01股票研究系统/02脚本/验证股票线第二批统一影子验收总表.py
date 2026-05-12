# -*- coding: utf-8 -*-
"""
验证股票线第二批统一影子验收总表。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "股票线第二批统一影子验收总表_最新.json"
RESULT_JSON = DATA_DIR / "股票线第二批统一影子验收总表验收_最新.json"
RESULT_MD = DATA_DIR / "股票线第二批统一影子验收总表验收_最新.md"
REQUIRED_KEYS = {
    "l3_report_gate_matrix",
    "front_backend_layering",
    "financial_capital_gap",
    "industry_price_entry_check",
    "policy_candidate_blocking",
    "second_queue",
}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")
    if asset.get("asset_identity") != "W2第二批统一影子验收总表":
        errors.append("资产身份必须是 W2第二批统一影子验收总表")
    if asset.get("status") != "passed":
        errors.append("状态必须是 passed")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_real_refresh", "not_score_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    checks = asset.get("checks", [])
    keys = {item.get("key") for item in checks}
    if keys != REQUIRED_KEYS:
        errors.append(f"检查项不完整：{sorted(keys)}")
    for item in checks:
        if item.get("exists") is not True:
            errors.append(f"{item.get('key')} 不存在")
        if item.get("passed") is not True:
            errors.append(f"{item.get('key')} 未通过")

    summary = asset.get("summary", {})
    if summary.get("check_count") != 6:
        errors.append("检查项数量必须为6")
    if summary.get("passed_count") != 6:
        errors.append("通过数量必须为6")
    for flag in ["allow_real_wecom_send", "allow_formal_entry", "allow_formal_score_update"]:
        if summary.get(flag) is not False:
            errors.append(f"{flag} 必须为 false")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_formal_config", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "股票线第二批统一影子验收总表验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": summary,
        "auto_continue_policy": "通过后由heartbeat检查是否生成第三批W1/W2低风险续建队列；不等待用户确认。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 股票线第二批统一影子验收总表验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 检查项：{result['metrics'].get('check_count', 0)}",
        f"- 通过：{result['metrics'].get('passed_count', 0)}",
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
