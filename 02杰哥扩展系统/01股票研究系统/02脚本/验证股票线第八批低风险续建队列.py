# -*- coding: utf-8 -*-
"""验证股票线第八批低风险续建队列。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
QUEUE_JSON = DATA_DIR / "股票线第八批低风险续建队列_最新.json"
RESULT_JSON = DATA_DIR / "股票线第八批低风险续建队列验收_最新.json"
RESULT_MD = DATA_DIR / "股票线第八批低风险续建队列验收_最新.md"


def main() -> None:
    errors: list[str] = []
    queue = json.loads(QUEUE_JSON.read_text(encoding="utf-8-sig")) if QUEUE_JSON.exists() else {}
    asset_identity = str(queue.get("asset_identity", ""))
    if not asset_identity.startswith("W1/W2"):
        errors.append("资产身份必须以 W1/W2 开头")
    if queue.get("status") != "active":
        errors.append("队列状态必须为 active")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send"]:
        if queue.get(flag) is not True:
            errors.append(f"{flag} 必须为 true")
    construction = queue.get("construction_queue", [])
    if len(construction) != 5:
        errors.append("施工队列必须为5项")
    if not all(item.get("risk_level") in {"W1", "W2"} for item in construction):
        errors.append("施工队列只能包含 W1/W2 事项")
    if not all(item.get("requires_user_confirmation") is False for item in construction):
        errors.append("低风险连续施工项不得等待用户确认")
    blocked = queue.get("blocked_queue", [])
    if len(blocked) < 2:
        errors.append("必须登记红线阻断项")
    if not all(item.get("status") == "blocked_register_only" for item in blocked):
        errors.append("红线事项只能登记阻断")
    summary = queue.get("summary", {})
    if summary.get("queue_count") != len(construction):
        errors.append("summary.queue_count 与施工队列数量不一致")
    if summary.get("completed_count") != len([item for item in construction if item.get("status") == "completed"]):
        errors.append("summary.completed_count 与施工队列状态不一致")
    if summary.get("queued_count") != len([item for item in construction if item.get("status") == "queued"]):
        errors.append("summary.queued_count 与施工队列状态不一致")
    if summary.get("blocked_count") != len(blocked):
        errors.append("summary.blocked_count 与阻断登记数量不一致")
    safety = queue.get("safety_boundary", {})
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
        "name": "股票线第八批低风险续建队列验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": summary,
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票线第八批低风险续建队列验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 队列项：{summary.get('queue_count', 0)}",
        f"- 已完成：{summary.get('completed_count', 0)}",
        f"- 待推进：{summary.get('queued_count', 0)}",
        f"- 阻断登记：{summary.get('blocked_count', 0)}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
