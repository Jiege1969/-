# -*- coding: utf-8 -*-
"""验证股票线第八批统一影子验收总表。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "股票线第八批统一影子验收总表_最新.json"
RESULT_JSON = DATA_DIR / "股票线第八批统一影子验收总表验收结果_最新.json"
RESULT_MD = DATA_DIR / "股票线第八批统一影子验收总表验收结果_最新.md"


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W2 股票线第八批统一影子验收总表":
        errors.append("资产身份不正确")
    if asset.get("status") != "shadow_batch_acceptance":
        errors.append("状态必须为 shadow_batch_acceptance")
    for flag in [
        "not_formal_config",
        "not_formal_entry",
        "not_external_send",
        "not_formal_database_write",
        "not_rule_update",
        "not_trade",
    ]:
        if asset.get(flag) is not True:
            errors.append(f"{flag} 必须为 true")
    checks = asset.get("checks", [])
    if len(checks) != 5:
        errors.append("第八批检查项必须为5项")
    if not all(item.get("exists") is True for item in checks):
        errors.append("存在缺失的验收文件")
    if not all(item.get("passed") is True for item in checks):
        errors.append("存在未通过的验收项")
    queue_summary = asset.get("queue_summary", {})
    if queue_summary.get("completed_count") != 5:
        errors.append("第八批队列必须完成5/5")
    if queue_summary.get("queued_count") != 0:
        errors.append("第八批队列不得仍有 queued 项")
    summary = asset.get("summary", {})
    if summary.get("real_system_triggered") is not False:
        errors.append("不得触发真实系统")
    if summary.get("failed_count") != 0:
        errors.append("failed_count 必须为0")
    if not asset.get("batch_effect", {}).get("remaining_debt"):
        errors.append("必须保留剩余旧债说明")
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
        "name": "股票线第八批统一影子验收总表验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {
            "check_count": len(checks),
            "passed_count": len([item for item in checks if item.get("passed") is True]),
            "failed_count": len([item for item in checks if item.get("passed") is not True]),
            "queue_completed_count": queue_summary.get("completed_count", 0),
            "queue_count": queue_summary.get("queue_count", 0),
            "real_system_triggered": summary.get("real_system_triggered"),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票线第八批统一影子验收总表验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 检查项：{result['metrics']['check_count']}",
        f"- 通过：{result['metrics']['passed_count']}",
        f"- 失败：{result['metrics']['failed_count']}",
        f"- 队列完成：{result['metrics']['queue_completed_count']}/{result['metrics']['queue_count']}",
        f"- 真实系统触发：{result['metrics']['real_system_triggered']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
