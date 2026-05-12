# -*- coding: utf-8 -*-
"""生成股票线第八批低风险续建队列。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
QUEUE_JSON = DATA_DIR / "股票线第八批低风险续建队列_最新.json"
QUEUE_MD = DATA_DIR / "股票线第八批低风险续建队列_最新.md"
SEVENTH_ACCEPTANCE = DATA_DIR / "股票线第七批统一影子验收总表验收_最新.json"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    seventh = json.loads(SEVENTH_ACCEPTANCE.read_text(encoding="utf-8-sig")) if SEVENTH_ACCEPTANCE.exists() else {}
    queue = {
        "name": "股票线第八批低风险续建队列",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W1/W2股票线低风险连续施工队列",
        "status": "active",
        "direction": "继续补政策事件库、市场风格日表、复盘闭环和统一刷新验收，强化L3证据结构化。",
        "source_assets": {
            "seventh_batch_acceptance_passed": seventh.get("passed") is True,
            "seventh_batch_metrics": seventh.get("metrics", {}),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "construction_queue": [
            {
                "id": "STOCK-AUTO8-001",
                "title": "政策事件库字段化补齐样例",
                "risk_level": "W1",
                "status": "queued",
                "requires_user_confirmation": False,
                "goal": "把政策事件的来源、方向、强度、暴露度、时效和缺口状态拆成结构化字段。",
            },
            {
                "id": "STOCK-AUTO8-002",
                "title": "市场风格日表字段化补齐样例",
                "risk_level": "W1",
                "status": "queued",
                "requires_user_confirmation": False,
                "goal": "把风险偏好、板块热度、大小盘风格、流动性和前台影响拆成字段。",
            },
            {
                "id": "STOCK-AUTO8-003",
                "title": "复盘结果到规则候选二次门禁样例",
                "risk_level": "W1",
                "status": "queued",
                "requires_user_confirmation": False,
                "goal": "确保复盘只生成经验候选，不自动改正式评分规则。",
            },
            {
                "id": "STOCK-AUTO8-004",
                "title": "L3证据缺口统一刷新验收样例",
                "risk_level": "W2",
                "status": "queued",
                "requires_user_confirmation": False,
                "goal": "统一刷新前台门禁、财报资金、行业价格、政策事件和市场风格缺口状态。",
            },
            {
                "id": "STOCK-AUTO8-005",
                "title": "第八批统一影子验收总表",
                "risk_level": "W2",
                "status": "queued",
                "requires_user_confirmation": False,
                "goal": "汇总第八批影子资产验收状态，形成本批收口记录。",
            },
        ],
        "blocked_queue": [
            {
                "id": "STOCK-AUTO8-BLOCK-001",
                "title": "接入真实企业微信外发或正式入口",
                "risk_level": "W3",
                "status": "blocked_register_only",
                "reason": "真实外发、正式入口、路由和服务变更属于红线事项，本业务线只登记阻断。",
            },
            {
                "id": "STOCK-AUTO8-BLOCK-002",
                "title": "接入券商接口或交易执行能力",
                "risk_level": "W3",
                "status": "blocked_register_only",
                "reason": "股票系统定位为研究分析系统，不新增交易执行能力。",
            },
        ],
        "summary": {"queue_count": 5, "completed_count": 0, "queued_count": 5, "blocked_count": 2},
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
            "not_order": True,
            "not_position_adjustment": True,
        },
    }
    QUEUE_JSON.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票线第八批低风险续建队列",
        "",
        f"- 生成时间：{now}",
        f"- 方向：{queue['direction']}",
        f"- 队列数：{queue['summary']['queue_count']}",
        f"- 阻断登记：{queue['summary']['blocked_count']}",
        "",
        "## 施工队列",
        "",
    ]
    for item in queue["construction_queue"]:
        lines.append(f"- {item['id']} | {item['title']} | {item['risk_level']} | {item['status']} | requires_user_confirmation={item['requires_user_confirmation']}")
    lines.extend(["", "## 阻断登记", ""])
    for item in queue["blocked_queue"]:
        lines.append(f"- {item['id']} | {item['title']} | {item['risk_level']} | {item['status']} | {item['reason']}")
    QUEUE_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": queue["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
