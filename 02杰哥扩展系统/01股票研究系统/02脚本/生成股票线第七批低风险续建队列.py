# -*- coding: utf-8 -*-
"""生成股票线第七批低风险续建队列。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
QUEUE_JSON = DATA_DIR / "股票线第七批低风险续建队列_最新.json"
QUEUE_MD = DATA_DIR / "股票线第七批低风险续建队列_最新.md"
SIXTH_ACCEPTANCE = DATA_DIR / "股票线第六批统一影子验收总表验收_最新.json"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sixth = json.loads(SIXTH_ACCEPTANCE.read_text(encoding="utf-8-sig")) if SIXTH_ACCEPTANCE.exists() else {}
    queue = {
        "name": "股票线第七批低风险续建队列",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W1/W2股票线低风险连续施工队列",
        "status": "active",
        "direction": "继续把股票分析系统从可生成样例推进为可门禁、可字段化、可刷新验收的前台结论型研究系统。",
        "source_assets": {
            "sixth_batch_acceptance_passed": sixth.get("passed") is True,
            "sixth_batch_metrics": sixth.get("metrics", {}),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "construction_queue": [
            {
                "id": "STOCK-AUTO7-001",
                "title": "标准前台报告输出门禁样例",
                "risk_level": "W1",
                "status": "queued",
                "requires_user_confirmation": False,
                "goal": "把企业微信前台回答必须满足的对象、结论、主因、缺口、置信度、复核提醒和禁止项做成门禁样例。",
            },
            {
                "id": "STOCK-AUTO7-002",
                "title": "财报资金证据字段化补齐样例",
                "risk_level": "W1",
                "status": "queued",
                "requires_user_confirmation": False,
                "goal": "把财报、估值、机构、资金证据拆成结构化字段和缺口状态，服务前台结论上限。",
            },
            {
                "id": "STOCK-AUTO7-003",
                "title": "行业价格连续观测字段化补齐样例",
                "risk_level": "W1",
                "status": "queued",
                "requires_user_confirmation": False,
                "goal": "把锗价、化工品价格、大宗商品景气等行业价格线索拆成连续观测字段和复核状态。",
            },
            {
                "id": "STOCK-AUTO7-004",
                "title": "企业微信模拟问答回归验收样例",
                "risk_level": "W2",
                "status": "queued",
                "requires_user_confirmation": False,
                "goal": "仅本地模拟企业微信提问和回答，不真实发送，验收前台短答是否符合门禁。",
            },
            {
                "id": "STOCK-AUTO7-005",
                "title": "第七批统一影子验收总表",
                "risk_level": "W2",
                "status": "queued",
                "requires_user_confirmation": False,
                "goal": "汇总第七批影子资产验收状态，形成本批收口记录。",
            },
        ],
        "blocked_queue": [
            {
                "id": "STOCK-AUTO7-BLOCK-001",
                "title": "把门禁样例接入企业微信真实发送链路",
                "risk_level": "W3",
                "status": "blocked_register_only",
                "reason": "企业微信真实外发、路由和正式入口属于红线事项，本业务线只登记阻断，不实施。",
            },
            {
                "id": "STOCK-AUTO7-BLOCK-002",
                "title": "把门禁样例写入正式报告生成配置",
                "risk_level": "W3",
                "status": "blocked_register_only",
                "reason": "正式配置和正式脚本入口属于W3，必须交回总管判断。",
            },
            {
                "id": "STOCK-AUTO7-BLOCK-003",
                "title": "新增买卖、下单、仓位调整或自动交易能力",
                "risk_level": "W3",
                "status": "blocked_register_only",
                "reason": "股票系统定位为研究分析系统，不新增交易执行能力。",
            },
        ],
        "summary": {"queue_count": 5, "completed_count": 0, "queued_count": 5, "blocked_count": 3},
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
        "# 股票线第七批低风险续建队列",
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
