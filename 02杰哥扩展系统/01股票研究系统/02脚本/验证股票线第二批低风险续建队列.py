# -*- coding: utf-8 -*-
"""
验证股票线第二批低风险续建队列。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "股票线第二批低风险续建队列_最新.json"
RESULT_JSON = DATA_DIR / "股票线第二批低风险续建队列验收_最新.json"
RESULT_MD = DATA_DIR / "股票线第二批低风险续建队列验收_最新.md"


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1第二批连续施工队列":
        errors.append("资产身份必须是 W1第二批连续施工队列")
    if asset.get("status") != "active":
        errors.append("状态必须是 active")

    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_real_refresh", "not_score_write", "not_formal_database_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    queue = asset.get("construction_queue", [])
    if len(queue) < 6:
        errors.append("第二批队列至少应有6项")
    for item in queue:
        if item.get("risk_level") not in {"W1", "W2"}:
            errors.append(f"{item.get('id')} 风险等级必须为W1/W2")
        if item.get("requires_user_confirmation") is not False:
            errors.append(f"{item.get('id')} 不得要求用户确认")
        if item.get("status") not in {"queued", "completed"}:
            errors.append(f"{item.get('id')} 状态必须为queued或completed")
        if item.get("status") == "completed" and not item.get("validation_asset"):
            errors.append(f"{item.get('id')} 已完成项必须登记validation_asset")

    rules = "\n".join(asset.get("auto_continue_rule", {}).values())
    for phrase in ["不等待用户确认", "只登记阻断", "不把下一步建议当成等待确认"]:
        if phrase not in rules:
            errors.append(f"自动续建规则缺少：{phrase}")

    blocked = asset.get("blocked_queue", [])
    if len(blocked) < 2:
        errors.append("红线阻断队列至少应有2项")
    for item in blocked:
        if item.get("risk_level") != "W3":
            errors.append(f"{item.get('id')} 阻断项必须W3")
        if item.get("status") != "blocked_register_only":
            errors.append(f"{item.get('id')} 阻断项只能登记")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_formal_config", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "股票线第二批低风险续建队列验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": asset.get("summary", {}),
        "auto_continue_policy": "通过后自动执行第二批第一项；不等待用户确认。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 股票线第二批低风险续建队列验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 队列数量：{result['metrics'].get('queue_count', 0)}",
        f"- 待执行：{result['metrics'].get('queued_count', 0)}",
        f"- 阻断数量：{result['metrics'].get('blocked_count', 0)}",
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
