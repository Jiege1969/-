# -*- coding: utf-8 -*-
"""
验证股票线连续施工状态快照。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "股票线连续施工状态快照_最新.json"
RESULT_JSON = DATA_DIR / "股票线连续施工状态快照验收_最新.json"
RESULT_MD = DATA_DIR / "股票线连续施工状态快照验收_最新.md"


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1状态快照":
        errors.append("资产身份必须是 W1状态快照")
    if asset.get("status") != "snapshot":
        errors.append("状态必须是 snapshot")
    if len(asset.get("completed_assets", [])) < 10:
        errors.append("已完成资产少于 10 项")
    if len(asset.get("remaining_debts", [])) < 4:
        errors.append("剩余旧债少于 4 项，可能未完整暴露")
    if len(asset.get("next_auto_queue", [])) < 4:
        errors.append("下一自动队列少于 4 项")

    misread_text = "\n".join(asset.get("must_not_misread", []))
    for phrase in ["不是正式上线", "不代表财报证据已采集", "不代表企业微信真实发送", "W3阻断"]:
        if phrase not in misread_text:
            errors.append(f"禁止误读缺少：{phrase}")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_adapter_write", "not_score_write", "not_entrypoint", "not_broker_interface", "not_auto_trade", "not_real_refresh"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "股票线连续施工状态快照验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": asset.get("summary", {}),
        "next_step": "继续执行快照中的 next_auto_queue 第一项：财报资金证据人工填写回执模板。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 股票线连续施工状态快照验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 已完成资产数：{result['metrics'].get('completed_asset_count', 0)}",
        f"- 最近验收数：{result['metrics'].get('latest_acceptance_count', 0)}",
        f"- 剩余旧债数：{result['metrics'].get('open_debt_count', 0)}",
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
