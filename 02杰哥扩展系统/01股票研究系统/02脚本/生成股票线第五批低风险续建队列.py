# -*- coding: utf-8 -*-
"""生成股票线第五批W1/W2低风险续建队列。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
FOURTH_QUEUE = DATA_DIR / "股票线第四批低风险续建队列_最新.json"
JSON_OUT = DATA_DIR / "股票线第五批低风险续建队列_最新.json"
MD_OUT = DATA_DIR / "股票线第五批低风险续建队列_最新.md"


QUEUE = [
    {
        "id": "STOCK-AUTO5-001",
        "title": "前台短答综合样例二次压缩验收",
        "risk_level": "W1",
        "status": "queued",
        "requires_user_confirmation": False,
        "goal": "把对象、结论、主因、关键缺口、置信度压缩为更贴近企业微信使用场景的短答。",
    },
    {
        "id": "STOCK-AUTO5-002",
        "title": "报告缺口优先级排序样例",
        "risk_level": "W1",
        "status": "queued",
        "requires_user_confirmation": False,
        "goal": "把missing从平铺列表改成P0/P1/P2优先级，便于后续补证和复盘。",
    },
    {
        "id": "STOCK-AUTO5-003",
        "title": "复盘字段到经验候选映射样例",
        "risk_level": "W1",
        "status": "queued",
        "requires_user_confirmation": False,
        "goal": "把人工修正和复盘结果沉淀为经验候选，不自动改正式规则。",
    },
    {
        "id": "STOCK-AUTO5-004",
        "title": "用户视角报告读感验收样例",
        "risk_level": "W1",
        "status": "queued",
        "requires_user_confirmation": False,
        "goal": "检查前台输出是否结论先行、少过程、依据够用、缺口清楚。",
    },
    {
        "id": "STOCK-AUTO5-005",
        "title": "第五批统一影子验收总表",
        "risk_level": "W2",
        "status": "queued",
        "requires_user_confirmation": False,
        "goal": "汇总第五批影子资产验收状态，形成本批收口记录。",
    },
]


BLOCKED = [
    {
        "id": "STOCK-AUTO5-BLOCK-001",
        "title": "把影子短答接入企业微信真实发送",
        "risk_level": "W3",
        "status": "blocked_register_only",
        "reason": "真实外发属于红线事项，本业务线不得实施。",
    },
    {
        "id": "STOCK-AUTO5-BLOCK-002",
        "title": "把复盘候选自动改成正式评分规则",
        "risk_level": "W3",
        "status": "blocked_register_only",
        "reason": "正式规则调整必须人工复核并交回总管判断。",
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fourth = json.loads(FOURTH_QUEUE.read_text(encoding="utf-8-sig")) if FOURTH_QUEUE.exists() else {}
    asset = {
        "name": "股票线第五批低风险续建队列",
        "version": "v1.0",
        "generated_at": generated_at,
        "asset_identity": "W1/W2股票线低风险连续施工队列",
        "status": "active",
        "source_assets": {
            "fourth_queue_completed_count": fourth.get("summary", {}).get("completed_count", 0),
            "fourth_queue_queued_count": fourth.get("summary", {}).get("queued_count", 0),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "construction_queue": QUEUE,
        "blocked_queue": BLOCKED,
        "summary": {
            "queue_count": len(QUEUE),
            "completed_count": 0,
            "queued_count": len(QUEUE),
            "blocked_count": len(BLOCKED),
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_formal_config": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票线第五批低风险续建队列",
        "",
        f"- 生成时间：{generated_at}",
        "- 资产身份：W1/W2股票线低风险连续施工队列",
        f"- 第四批完成：{asset['source_assets']['fourth_queue_completed_count']}",
        "",
        "## 施工队列",
        "",
    ]
    for item in QUEUE:
        lines.append(f"- {item['id']} | {item['title']} | {item['risk_level']} | {item['status']}")
    lines.extend(["", "## 阻断登记", ""])
    for item in BLOCKED:
        lines.append(f"- {item['id']} | {item['title']} | {item['risk_level']} | {item['reason']}")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
