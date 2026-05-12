# -*- coding: utf-8 -*-
"""生成股票线第九批低风险续建队列。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
QUEUE_JSON = DATA_DIR / "股票线第九批低风险续建队列_最新.json"
QUEUE_MD = DATA_DIR / "股票线第九批低风险续建队列_最新.md"


QUEUE = [
    {
        "id": "STOCK-AUTO9-001",
        "title": "前台结论型短答压缩回归样例",
        "risk_level": "W1",
        "status": "queued",
        "requires_user_confirmation": False,
        "goal": "把后台 evidence/missing/confidence 压缩为企业微信前台结论型短答，避免用户看到技术指标堆叠。",
    },
    {
        "id": "STOCK-AUTO9-002",
        "title": "财报资金真实来源接入前字段候选卡",
        "risk_level": "W2",
        "status": "queued",
        "requires_user_confirmation": False,
        "goal": "只登记财报、估值、机构、资金字段的候选来源和缺口，不接正式接口、不写正式配置。",
    },
    {
        "id": "STOCK-AUTO9-003",
        "title": "行业价格连续观测真实来源候选卡",
        "risk_level": "W2",
        "status": "queued",
        "requires_user_confirmation": False,
        "goal": "只登记锗、化工、新材料等价格连续观测候选来源和字段，不接生产数据源。",
    },
    {
        "id": "STOCK-AUTO9-004",
        "title": "政策事件真实来源替换准备清单",
        "risk_level": "W2",
        "status": "queued",
        "requires_user_confirmation": False,
        "goal": "为政策事件库从样例走向真实来源做只读准备清单，保持人工复核和来源链接待补。",
    },
    {
        "id": "STOCK-AUTO9-005",
        "title": "第九批统一影子验收总表",
        "risk_level": "W2",
        "status": "queued",
        "requires_user_confirmation": False,
        "goal": "汇总第九批影子资产验收状态并登记剩余阻断。",
    },
]


BLOCKED = [
    {
        "id": "STOCK-AUTO9-BLOCK-001",
        "title": "企业微信真实外发、正式入口或路由变更",
        "risk_level": "W3",
        "status": "blocked_register_only",
        "reason": "企业微信真实外发、正式入口和路由变更属于红线事项，本业务线只登记阻断。",
    },
    {
        "id": "STOCK-AUTO9-BLOCK-002",
        "title": "券商接口、自动交易、下单或仓位调整",
        "risk_level": "W3",
        "status": "blocked_register_only",
        "reason": "股票系统定位为研究分析系统，不新增交易执行能力。",
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "股票线第九批低风险续建队列",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W1/W2 股票线低风险连续施工队列",
        "status": "active",
        "direction": "继续强化使用者前台感知、真实数据源接入前准备和统一影子验收。",
        "source_assets": {
            "eighth_batch_acceptance_passed": True,
            "eighth_batch_asset": "股票线第八批统一影子验收总表验收结果_最新.json",
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
            "not_order": True,
            "not_position_adjustment": True,
        },
    }
    QUEUE_JSON.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票线第九批低风险续建队列",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：W1/W2 股票线低风险连续施工队列",
        "- 状态：active",
        "- 正式入口：否",
        "- 真实外发：否",
        "",
        "## 施工队列",
        "",
    ]
    for item in QUEUE:
        lines.append(f"- {item['id']} | {item['title']} | {item['risk_level']} | {item['status']} | {item['goal']}")
    lines.extend(["", "## 阻断登记", ""])
    for item in BLOCKED:
        lines.append(f"- {item['id']} | {item['title']} | {item['risk_level']} | {item['status']} | {item['reason']}")
    QUEUE_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
