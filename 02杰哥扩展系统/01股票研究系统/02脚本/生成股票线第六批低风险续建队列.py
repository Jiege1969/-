# -*- coding: utf-8 -*-
"""生成股票线第六批低风险续建队列。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
QUEUE_JSON = DATA_DIR / "股票线第六批低风险续建队列_最新.json"
QUEUE_MD = DATA_DIR / "股票线第六批低风险续建队列_最新.md"
FIFTH_ACCEPTANCE = DATA_DIR / "股票线第五批统一影子验收总表验收_最新.json"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fifth = json.loads(FIFTH_ACCEPTANCE.read_text(encoding="utf-8-sig")) if FIFTH_ACCEPTANCE.exists() else {}
    queue = {
        "name": "股票线第六批低风险续建队列",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W1/W2股票线低风险连续施工队列",
        "status": "active",
        "direction": "把股票分析报告从后台技术分析堆叠继续压实为企业微信前台可读的标准结论型回答。",
        "source_assets": {
            "fifth_batch_acceptance_passed": fifth.get("passed") is True,
            "fifth_batch_metrics": fifth.get("metrics", {}),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "construction_queue": [
            {
                "id": "STOCK-AUTO6-001",
                "title": "标准股票分析格式前台短答范本样例",
                "risk_level": "W1",
                "status": "queued",
                "requires_user_confirmation": False,
                "goal": "用云南锗业、三花智控、上纬新材、浙商中拓、正丹股份生成统一前台结论型短答范本，验证对象先明确、结论先行、证据少而准、缺口显式。",
            },
            {
                "id": "STOCK-AUTO6-002",
                "title": "财报资金缺口到前台结论约束样例",
                "risk_level": "W1",
                "status": "queued",
                "requires_user_confirmation": False,
                "goal": "当财报、估值、机构、资金证据缺失时，前台结论必须降级表达，不能假装已有判断依据。",
            },
            {
                "id": "STOCK-AUTO6-003",
                "title": "新增样本股票浙商中拓与正丹股份验收补齐",
                "risk_level": "W1",
                "status": "queued",
                "requires_user_confirmation": False,
                "goal": "把浙商中拓、正丹股份纳入样本验收矩阵，检查对象识别、行业标签、证据缺口和前台表达。",
            },
            {
                "id": "STOCK-AUTO6-004",
                "title": "前后台分层报告字段对照样例",
                "risk_level": "W2",
                "status": "queued",
                "requires_user_confirmation": False,
                "goal": "把后台证据链、评分、missing、confidence映射到前台结论、主因、缺口、复核提醒，避免前台堆指标。",
            },
            {
                "id": "STOCK-AUTO6-005",
                "title": "第六批统一影子验收总表",
                "risk_level": "W2",
                "status": "queued",
                "requires_user_confirmation": False,
                "goal": "汇总第六批影子资产验收状态，形成本批收口记录。",
            },
        ],
        "blocked_queue": [
            {
                "id": "STOCK-AUTO6-BLOCK-001",
                "title": "把前台短答范本接入企业微信真实发送",
                "risk_level": "W3",
                "status": "blocked_register_only",
                "reason": "真实外发、企业微信路由和正式入口属于红线事项，本业务线只登记阻断，不实施。",
            },
            {
                "id": "STOCK-AUTO6-BLOCK-002",
                "title": "把样本结论改写为买入卖出或仓位建议",
                "risk_level": "W3",
                "status": "blocked_register_only",
                "reason": "股票系统定位为研究分析系统，不新增买卖、下单、仓位调整或自动交易能力。",
            },
        ],
        "summary": {
            "queue_count": 5,
            "completed_count": 0,
            "queued_count": 5,
            "blocked_count": 2,
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
            "not_order": True,
            "not_position_adjustment": True,
        },
    }
    QUEUE_JSON.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票线第六批低风险续建队列",
        "",
        f"- 生成时间：{now}",
        "- 方向：把股票分析报告从后台技术分析堆叠继续压实为企业微信前台可读的标准结论型回答。",
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
