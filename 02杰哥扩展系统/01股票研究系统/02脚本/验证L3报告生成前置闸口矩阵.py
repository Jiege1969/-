# -*- coding: utf-8 -*-
"""
验证L3报告生成前置闸口矩阵。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "L3报告生成前置闸口矩阵_最新.json"
RESULT_JSON = DATA_DIR / "L3报告生成前置闸口矩阵验收_最新.json"
RESULT_MD = DATA_DIR / "L3报告生成前置闸口矩阵验收_最新.md"

REQUIRED_FORBIDDEN = {
    "缺财报资金仍写基本面确认",
    "缺价格连续观测仍写趋势确认",
    "缺政策复核仍写政策强驱动",
    "缺单股风格复核仍写市场强适配",
    "缺关键证据仍输出重点关注",
}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1报告生成前置闸口矩阵":
        errors.append("资产身份必须是 W1报告生成前置闸口矩阵")
    if asset.get("status") != "shadow_gate_matrix":
        errors.append("状态必须是 shadow_gate_matrix")

    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_score_write", "not_formal_database_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    gates = asset.get("gates", [])
    if len(gates) < 8:
        errors.append("闸口数量至少应为8")
    text = json.dumps(gates, ensure_ascii=False)
    for phrase in ["对象明确", "财报资金", "行业价格", "政策事件", "市场风格", "强结论", "复盘候选"]:
        if phrase not in text:
            errors.append(f"闸口缺少主题：{phrase}")
    for phrase in ["不得输出重点关注", "不得写趋势确认", "不得写政策强驱动", "不能写该股强适配"]:
        if phrase not in text:
            errors.append(f"阻断口径缺少：{phrase}")

    forbidden = set(asset.get("report_output_contract", {}).get("forbidden_when_missing", []))
    if not REQUIRED_FORBIDDEN.issubset(forbidden):
        errors.append(f"禁止口径不完整：{sorted(forbidden)}")

    summary = asset.get("summary", {})
    if summary.get("formal_entry_allowed") is not False:
        errors.append("formal_entry_allowed 必须false")
    if summary.get("real_wecom_allowed") is not False:
        errors.append("real_wecom_allowed 必须false")
    if summary.get("auto_weight_change_allowed") is not False:
        errors.append("auto_weight_change_allowed 必须false")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_formal_config", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "L3报告生成前置闸口矩阵验收",
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
        "# L3报告生成前置闸口矩阵验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 闸口数量：{result['metrics'].get('gate_count', 0)}",
        f"- 正式入口允许：{result['metrics'].get('formal_entry_allowed')}",
        f"- 真实企微允许：{result['metrics'].get('real_wecom_allowed')}",
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
