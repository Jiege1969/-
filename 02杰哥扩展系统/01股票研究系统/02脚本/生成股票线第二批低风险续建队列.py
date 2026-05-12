# -*- coding: utf-8 -*-
"""
生成股票线第二批低风险续建队列。

首批连续施工队列完成后，自动生成下一批W1/W2低风险小闭环，避免因
“没有排队项”而停下来等待用户确认。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
FIRST_QUEUE = DATA_DIR / "股票线连续施工自动续建队列_最新.json"
UNIFIED_ACCEPTANCE = DATA_DIR / "股票L3统一刷新影子验收总表验收_最新.json"
JSON_OUT = DATA_DIR / "股票线第二批低风险续建队列_最新.json"
MD_OUT = DATA_DIR / "股票线第二批低风险续建队列_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def build_asset() -> dict[str, Any]:
    first_queue = load_json(FIRST_QUEUE)
    unified = load_json(UNIFIED_ACCEPTANCE)
    second_queue = [
        {
            "id": "STOCK-AUTO2-001",
            "title": "L3报告生成前置闸口矩阵",
            "risk_level": "W1",
            "status": "queued",
            "requires_user_confirmation": False,
            "goal": "把财报资金、行业价格、政策事件、市场风格、复盘候选的ready状态转成报告允许/禁止口径。",
        },
        {
            "id": "STOCK-AUTO2-002",
            "title": "五样本前后台分层输出验收矩阵",
            "risk_level": "W1",
            "status": "queued",
            "requires_user_confirmation": False,
            "goal": "验证前台结论短答少而准，后台保留evidence/missing/confidence/next_review。",
        },
        {
            "id": "STOCK-AUTO2-003",
            "title": "财报资金缺口主动暴露规则验收",
            "risk_level": "W1",
            "status": "queued",
            "requires_user_confirmation": False,
            "goal": "把财报缺失、资金缺失、机构缺失转成前台固定缺口话术和后台阻断字段。",
        },
        {
            "id": "STOCK-AUTO2-004",
            "title": "行业价格连续观测入账前检查清单",
            "risk_level": "W1",
            "status": "queued",
            "requires_user_confirmation": False,
            "goal": "明确5点、20点、同口径、来源URL、核验时间等入账前条件。",
        },
        {
            "id": "STOCK-AUTO2-005",
            "title": "政策事件候选到入库阻断清单",
            "risk_level": "W1",
            "status": "queued",
            "requires_user_confirmation": False,
            "goal": "政策候选未完成官方来源、方向、强度、暴露度、时效衰减前不得入分。",
        },
        {
            "id": "STOCK-AUTO2-006",
            "title": "第二批统一影子验收总表",
            "risk_level": "W2",
            "status": "queued",
            "requires_user_confirmation": False,
            "goal": "汇总第二批队列所有低风险闭环验收结果。",
        },
    ]
    return {
        "name": "股票线第二批低风险续建队列",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1第二批连续施工队列",
        "status": "active",
        "source_assets": {
            "first_queue": str(FIRST_QUEUE),
            "first_queue_completed_count": first_queue.get("summary", {}).get("completed_count")
            or len([item for item in first_queue.get("construction_queue", []) if item.get("status") == "completed"]),
            "unified_acceptance": str(UNIFIED_ACCEPTANCE),
            "unified_acceptance_passed": unified.get("passed") is True,
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_real_refresh": True,
        "not_score_write": True,
        "not_formal_database_write": True,
        "auto_continue_rule": {
            "when_queue_completed": "自动生成下一批W1/W2低风险续建队列，不等待用户确认。",
            "when_redline_detected": "只登记阻断，不实施。",
            "final_response_policy": "最终回复只做阶段汇报，不把下一步建议当成等待确认。",
        },
        "construction_queue": second_queue,
        "blocked_queue": [
            {
                "id": "STOCK-AUTO2-BLOCK-001",
                "title": "接入企业微信真实发送",
                "risk_level": "W3",
                "status": "blocked_register_only",
                "reason": "涉及真实外发和公共接入配置，必须交回总管判断。",
            },
            {
                "id": "STOCK-AUTO2-BLOCK-002",
                "title": "将影子闸口写入正式评分脚本或配置",
                "risk_level": "W3",
                "status": "blocked_register_only",
                "reason": "涉及正式脚本/配置/评分权重，必须交回总管判断。",
            },
        ],
        "summary": {
            "queue_count": len(second_queue),
            "completed_count": 0,
            "queued_count": len(second_queue),
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
        },
    }


def write_markdown(asset: dict[str, Any]) -> None:
    lines = [
        "# 股票线第二批低风险续建队列",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：股票线W1/W2低风险续建队列，不改正式入口、不外发、不交易。",
        "",
        "## 自动续建规则",
        "",
    ]
    lines.extend([f"- {value}" for value in asset["auto_continue_rule"].values()])
    lines.extend(["", "## 队列", ""])
    for item in asset["construction_queue"]:
        lines.append(f"- {item['id']}｜{item['title']}｜{item['risk_level']}｜{item['status']}｜需确认={item['requires_user_confirmation']}")
    lines.extend(["", "## 红线阻断", ""])
    for item in asset["blocked_queue"]:
        lines.append(f"- {item['id']}｜{item['title']}｜{item['status']}｜{item['reason']}")
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    asset = build_asset()
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({"status": "ok", "json": str(JSON_OUT), "md": str(MD_OUT), "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
