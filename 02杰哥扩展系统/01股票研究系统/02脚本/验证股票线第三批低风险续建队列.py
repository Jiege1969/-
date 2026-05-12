# -*- coding: utf-8 -*-
"""验证股票线第三批低风险续建队列。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "股票线第三批低风险续建队列_最新.json"
RESULT_JSON = DATA_DIR / "股票线第三批低风险续建队列验收_最新.json"
RESULT_MD = DATA_DIR / "股票线第三批低风险续建队列验收_最新.md"


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1第三批连续施工队列":
        errors.append("资产身份必须是 W1第三批连续施工队列")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_real_refresh", "not_score_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")
    queue = asset.get("construction_queue", [])
    if len(queue) < 5:
        errors.append("第三批队列至少5项")
    for item in queue:
        if item.get("risk_level") not in {"W1", "W2"}:
            errors.append(f"{item.get('id')} 风险等级必须W1/W2")
        if item.get("requires_user_confirmation") is not False:
            errors.append(f"{item.get('id')} 不得等待用户确认")
        if item.get("status") not in {"queued", "completed"}:
            errors.append(f"{item.get('id')} 状态必须queued/completed")
    for item in asset.get("blocked_queue", []):
        if item.get("risk_level") != "W3" or item.get("status") != "blocked_register_only":
            errors.append(f"{item.get('id')} 红线只能登记阻断")
    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_formal_config", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")
    result = {
        "name": "股票线第三批低风险续建队列验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": [],
        "metrics": asset.get("summary", {}),
        "auto_continue_policy": "通过后自动执行第三批第一项；不等待用户确认。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票线第三批低风险续建队列验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 队列数量：{result['metrics'].get('queue_count', 0)}",
        f"- 待执行：{result['metrics'].get('queued_count', 0)}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
