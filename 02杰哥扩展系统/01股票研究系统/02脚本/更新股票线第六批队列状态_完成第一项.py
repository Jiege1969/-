# -*- coding: utf-8 -*-
"""更新第六批低风险队列：标记第一项已完成。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
QUEUE_PATH = DATA_DIR / "股票线第六批低风险续建队列_最新.json"
MD_PATH = DATA_DIR / "股票线第六批低风险续建队列_最新.md"


def main() -> None:
    queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8-sig"))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in queue.get("construction_queue", []):
        if item.get("id") == "STOCK-AUTO6-001":
            item["status"] = "completed"
            item["validation_asset"] = "标准股票分析格式前台短答范本样例验收结果_最新.json"
            item["completed_at"] = now
    construction = queue.get("construction_queue", [])
    queue["generated_at"] = now
    queue["summary"] = {
        "queue_count": len(construction),
        "completed_count": len([item for item in construction if item.get("status") == "completed"]),
        "queued_count": len([item for item in construction if item.get("status") == "queued"]),
        "blocked_count": len(queue.get("blocked_queue", [])),
    }
    QUEUE_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票线第六批低风险续建队列",
        "",
        f"- 更新时间：{now}",
        f"- 已完成：{queue['summary']['completed_count']}",
        f"- 待推进：{queue['summary']['queued_count']}",
        f"- 阻断登记：{queue['summary']['blocked_count']}",
        "",
        "## 施工队列",
        "",
    ]
    for item in construction:
        lines.append(f"- {item['id']} | {item['title']} | {item['risk_level']} | {item['status']} | requires_user_confirmation={item['requires_user_confirmation']}")
    lines.extend(["", "## 阻断登记", ""])
    for item in queue.get("blocked_queue", []):
        lines.append(f"- {item['id']} | {item['title']} | {item['risk_level']} | {item['status']} | {item['reason']}")
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": queue["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
