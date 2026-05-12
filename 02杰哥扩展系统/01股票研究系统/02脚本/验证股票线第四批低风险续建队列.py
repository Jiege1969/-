# -*- coding: utf-8 -*-
"""验收股票线第四批W1/W2低风险续建队列。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
QUEUE_PATH = DATA_DIR / "股票线第四批低风险续建队列_最新.json"
RESULT_JSON = DATA_DIR / "股票线第四批低风险续建队列验收_最新.json"
RESULT_MD = DATA_DIR / "股票线第四批低风险续建队列验收_最新.md"


def main() -> None:
    errors: list[str] = []
    queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8-sig")) if QUEUE_PATH.exists() else {}
    if queue.get("asset_identity") != "W1/W2股票线低风险连续施工队列":
        errors.append("资产身份不正确")
    items = queue.get("construction_queue", [])
    if len(items) != 5:
        errors.append("施工队列必须为5项")
    if any(item.get("risk_level") not in {"W1", "W2"} for item in items):
        errors.append("存在非W1/W2施工项")
    if any(item.get("requires_user_confirmation") is not False for item in items):
        errors.append("低风险续建项不应等待用户确认")
    blocked = queue.get("blocked_queue", [])
    if len(blocked) < 2:
        errors.append("阻断登记不足")
    summary = queue.get("summary", {})
    if summary.get("queue_count") != len(items):
        errors.append("queue_count与施工项数量不一致")
    safety = queue.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_formal_config", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界{flag}必须为true")
    result = {
        "name": "股票线第四批低风险续建队列验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {
            "queue_count": len(items),
            "completed_count": len([item for item in items if item.get("status") == "completed"]),
            "queued_count": len([item for item in items if item.get("status") == "queued"]),
            "blocked_count": len(blocked),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票线第四批低风险续建队列验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 已完成：{result['metrics']['completed_count']}/{result['metrics']['queue_count']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
