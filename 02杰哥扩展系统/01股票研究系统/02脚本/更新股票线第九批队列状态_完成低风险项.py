# -*- coding: utf-8 -*-
"""将股票线第九批低风险队列的 002-005 标记为已完成。

只更新队列状态产物，不改评分逻辑、不接券商、不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
QUEUE_JSON = DATA_DIR / "股票线第九批低风险续建队列_最新.json"
QUEUE_MD = DATA_DIR / "股票线第九批低风险续建队列_最新.md"


COMPLETED_ASSETS = {
    "STOCK-AUTO9-002": "财报资金真实来源接入前字段候选卡_最新.json",
    "STOCK-AUTO9-003": "行业价格连续观测真实来源候选卡_最新.json",
    "STOCK-AUTO9-004": "政策事件真实来源替换准备清单_最新.json",
    "STOCK-AUTO9-005": "股票线第九批统一影子验收总表_最新.json",
}


def main() -> None:
    queue = json.loads(QUEUE_JSON.read_text(encoding="utf-8-sig"))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in queue.get("construction_queue", []):
        item_id = item.get("id")
        if item_id in COMPLETED_ASSETS:
            item["status"] = "completed"
            item["validation_asset"] = COMPLETED_ASSETS[item_id]
            item["completed_at"] = now
    construction = queue.get("construction_queue", [])
    queue["summary"]["completed_count"] = len([item for item in construction if item.get("status") == "completed"])
    queue["summary"]["queued_count"] = len([item for item in construction if item.get("status") == "queued"])
    queue["summary"]["queue_count"] = len(construction)
    queue["generated_at"] = now
    QUEUE_JSON.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 股票线第九批低风险续建队列",
        "",
        f"- 更新时间：{now}",
        "- 资产身份：W1/W2 股票线低风险连续施工队列",
        "- 状态：active",
        "- 正式入口：否",
        "- 真实外发：否",
        "",
        "## 施工队列",
        "",
    ]
    for item in construction:
        lines.append(f"- {item['id']} | {item['title']} | {item['risk_level']} | {item['status']} | {item.get('validation_asset', '未登记')}")
    lines.extend(["", "## 阻断登记", ""])
    for item in queue.get("blocked_queue", []):
        lines.append(f"- {item['id']} | {item['title']} | {item['risk_level']} | {item['status']} | {item['reason']}")
    QUEUE_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": queue["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
