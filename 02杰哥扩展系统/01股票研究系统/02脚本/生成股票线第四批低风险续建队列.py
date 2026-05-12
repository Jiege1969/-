# -*- coding: utf-8 -*-
"""生成股票线第四批W1/W2低风险续建队列。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
THIRD_QUEUE = DATA_DIR / "股票线第三批低风险续建队列_最新.json"
JSON_OUT = DATA_DIR / "股票线第四批低风险续建队列_最新.json"
MD_OUT = DATA_DIR / "股票线第四批低风险续建队列_最新.md"


QUEUE = [
    {
        "id": "STOCK-AUTO4-001",
        "title": "财报资金证据到前台短答压缩映射验收",
        "risk_level": "W1",
        "status": "queued",
        "requires_user_confirmation": False,
        "goal": "把后台财报/资金证据压缩成用户可读的结论依据，不堆指标，不凭空补分。",
    },
    {
        "id": "STOCK-AUTO4-002",
        "title": "行业价格连续观测到复核字段联动样例",
        "risk_level": "W1",
        "status": "queued",
        "requires_user_confirmation": False,
        "goal": "把行业价格连续观测映射到前台复核重点和后台missing字段。",
    },
    {
        "id": "STOCK-AUTO4-003",
        "title": "政策事件候选到前台表述约束验收",
        "risk_level": "W1",
        "status": "queued",
        "requires_user_confirmation": False,
        "goal": "约束政策候选只能作为线索或结构化证据，不让模型凭空强化结论。",
    },
    {
        "id": "STOCK-AUTO4-004",
        "title": "市场风格适配到结论强度限制样例",
        "risk_level": "W1",
        "status": "queued",
        "requires_user_confirmation": False,
        "goal": "把市场风格适配结果转成结论强度限制和缺口提示。",
    },
    {
        "id": "STOCK-AUTO4-005",
        "title": "第四批统一影子验收总表",
        "risk_level": "W2",
        "status": "queued",
        "requires_user_confirmation": False,
        "goal": "汇总第四批所有影子资产验收状态，形成本批收口记录。",
    },
]


BLOCKED = [
    {
        "id": "STOCK-AUTO4-BLOCK-001",
        "title": "接入企业微信真实发送",
        "risk_level": "W3",
        "status": "blocked_register_only",
        "reason": "真实外发属于红线事项，本业务线不得实施。",
    },
    {
        "id": "STOCK-AUTO4-BLOCK-002",
        "title": "修改正式评分配置或正式入口",
        "risk_level": "W3",
        "status": "blocked_register_only",
        "reason": "正式配置/入口属于W3，必须交回总管判断。",
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    third = json.loads(THIRD_QUEUE.read_text(encoding="utf-8-sig")) if THIRD_QUEUE.exists() else {}
    asset = {
        "name": "股票线第四批低风险续建队列",
        "version": "v1.0",
        "generated_at": generated_at,
        "asset_identity": "W1/W2股票线低风险连续施工队列",
        "status": "active",
        "source_assets": {
            "third_queue_completed_count": third.get("summary", {}).get("completed_count", 0),
            "third_queue_queued_count": third.get("summary", {}).get("queued_count", 0),
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
        "# 股票线第四批低风险续建队列",
        "",
        f"- 生成时间：{generated_at}",
        "- 资产身份：W1/W2股票线低风险连续施工队列",
        f"- 第三批完成：{asset['source_assets']['third_queue_completed_count']}",
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
