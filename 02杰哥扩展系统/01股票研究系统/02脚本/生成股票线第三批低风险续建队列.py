# -*- coding: utf-8 -*-
"""
生成股票线第三批低风险续建队列。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
SECOND_QUEUE = DATA_DIR / "股票线第二批低风险续建队列_最新.json"
JSON_OUT = DATA_DIR / "股票线第三批低风险续建队列_最新.json"
MD_OUT = DATA_DIR / "股票线第三批低风险续建队列_最新.md"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_asset() -> dict:
    second = load_json(SECOND_QUEUE)
    queue = [
        {
            "id": "STOCK-AUTO3-001",
            "title": "股票提问对象识别与别名映射验收",
            "risk_level": "W1",
            "status": "queued",
            "requires_user_confirmation": False,
            "goal": "用户问股票时，第一行必须明确股票名称和代码；别名和简称不得误配。",
        },
        {
            "id": "STOCK-AUTO3-002",
            "title": "企业微信前台短答模拟输入输出样例",
            "risk_level": "W1",
            "status": "queued",
            "requires_user_confirmation": False,
            "goal": "只生成本地影子输入输出样例，不真实发送企业微信。",
        },
        {
            "id": "STOCK-AUTO3-003",
            "title": "置信度上限与缺口联动矩阵",
            "risk_level": "W1",
            "status": "queued",
            "requires_user_confirmation": False,
            "goal": "关键证据缺失时自动限制confidence和结论强度。",
        },
        {
            "id": "STOCK-AUTO3-004",
            "title": "下一次复核日期与复核重点模板",
            "risk_level": "W1",
            "status": "queued",
            "requires_user_confirmation": False,
            "goal": "每份影子报告必须给下一次复核重点，不把缺口丢掉。",
        },
        {
            "id": "STOCK-AUTO3-005",
            "title": "第三批统一影子验收总表",
            "risk_level": "W2",
            "status": "queued",
            "requires_user_confirmation": False,
            "goal": "汇总第三批队列验收结果。",
        },
    ]
    return {
        "name": "股票线第三批低风险续建队列",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1第三批连续施工队列",
        "status": "active",
        "source_assets": {
            "second_queue": str(SECOND_QUEUE),
            "second_queue_completed_count": second.get("summary", {}).get("completed_count"),
            "second_queue_queued_count": second.get("summary", {}).get("queued_count"),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_real_refresh": True,
        "not_score_write": True,
        "construction_queue": queue,
        "blocked_queue": [
            {
                "id": "STOCK-AUTO3-BLOCK-001",
                "title": "企业微信真实发送",
                "risk_level": "W3",
                "status": "blocked_register_only",
                "reason": "真实外发必须交回总管判断。",
            },
            {
                "id": "STOCK-AUTO3-BLOCK-002",
                "title": "正式入口或正式配置接入",
                "risk_level": "W3",
                "status": "blocked_register_only",
                "reason": "正式入口/配置必须交回总管判断。",
            },
        ],
        "summary": {
            "queue_count": len(queue),
            "completed_count": 0,
            "queued_count": len(queue),
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


def write_markdown(asset: dict) -> None:
    lines = [
        "# 股票线第三批低风险续建队列",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：W1/W2影子施工，不外发、不交易、不改正式入口。",
        "",
        "## 队列",
        "",
    ]
    for item in asset["construction_queue"]:
        lines.append(f"- {item['id']}｜{item['title']}｜{item['risk_level']}｜{item['status']}｜需确认={item['requires_user_confirmation']}")
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    asset = build_asset()
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
