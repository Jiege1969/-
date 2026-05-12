# -*- coding: utf-8 -*-
"""
生成股票线连续施工自动续建队列。

作用：把“W1/W2低风险小闭环自动续建，红线事项只登记阻断”的节奏写成
股票线内资产，避免完成一个小闭环后停下来等待用户继续。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "股票线连续施工自动续建队列_最新.json"
MD_OUT = DATA_DIR / "股票线连续施工自动续建队列_最新.md"


def build_asset() -> dict:
    return {
        "name": "股票线连续施工自动续建队列",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1连续施工节奏资产",
        "status": "active_for_shadow_construction",
        "purpose": "纠正完成小闭环后等待用户确认的问题；低风险股票线施工自动进入下一小闭环。",
        "role_boundary": {
            "current_role": "股票分析系统局部施工",
            "not_general_manager": True,
            "only_stock_line": True,
            "research_analysis_positioning": True,
            "not_trading_robot": True,
        },
        "mandatory_readonly_before_each_round": [
            r"D:\杰哥智能化系统\00杰哥系统总管\07文档\当前施工面板.md",
            r"D:\杰哥智能化系统\00杰哥系统总管\03数据\开工上下文\一键接续施工包_最新.md",
        ],
        "allowed_write_root": r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统",
        "auto_continue_rule": {
            "w1_w2_low_risk": "完成一个可验证小闭环后，自动进入下一小闭环，不等待用户确认。",
            "final_response_is_report_not_pause": "对话汇报只说明已完成和正在排队的事项，不把下一步建议当成请求确认。",
            "must_self_validate_each_round": True,
            "must_write_alignment_record_each_round": True,
        },
        "redline_handling": {
            "policy": "只登记阻断，不实施。",
            "blocked_actions": [
                "修改总管文件",
                "修改企业微信公共接入配置",
                "触发企业微信真实外发",
                "触发n8n",
                "服务重启",
                "修改或接入19310",
                "修改正式入口",
                "修改正式配置",
                "写正式库",
                "接入券商接口",
                "新增买入/卖出/下单/仓位调整/自动交易能力",
                "修改税务系统或其他业务线文件",
            ],
        },
        "construction_queue": [
            {
                "id": "STOCK-AUTO-001",
                "title": "行业价格观测人工填报回执模板",
                "risk_level": "W1",
                "status": "completed",
                "requires_user_confirmation": False,
                "validation_asset": "行业价格观测人工填报回执模板验收_最新.json",
            },
            {
                "id": "STOCK-AUTO-002",
                "title": "市场风格单股适配人工复核回执模板",
                "risk_level": "W1",
                "status": "completed",
                "requires_user_confirmation": False,
                "validation_asset": "市场风格单股适配人工复核回执模板验收_最新.json",
            },
            {
                "id": "STOCK-AUTO-003",
                "title": "政策事件单股暴露度人工复核回执模板",
                "risk_level": "W1",
                "status": "completed",
                "requires_user_confirmation": False,
                "validation_asset": "政策事件单股暴露度人工复核回执模板验收_最新.json",
                "goal": "把政策强度、股票暴露度、时效衰减和反证风险拆成可复核字段。",
            },
            {
                "id": "STOCK-AUTO-004",
                "title": "五样本及新增样本前台结论型短答统一验收",
                "risk_level": "W1",
                "status": "completed",
                "requires_user_confirmation": False,
                "validation_asset": "前台结论型短答统一验收记录验收_最新.json",
                "goal": "验证云南锗业、天齐锂业、华虹公司、浙商中拓、正丹股份等样本第一行对象明确、结论先行、证据缺口显式。",
            },
            {
                "id": "STOCK-AUTO-005",
                "title": "复盘闭环人工修正规则候选模板",
                "risk_level": "W1",
                "status": "completed",
                "requires_user_confirmation": False,
                "validation_asset": "复盘人工修正规则候选模板验收_最新.json",
                "goal": "人工修正只进入复盘/经验候选，不自动修改正式规则权重。",
            },
            {
                "id": "STOCK-AUTO-006",
                "title": "统一刷新影子验收总表",
                "risk_level": "W2",
                "status": "completed",
                "requires_user_confirmation": False,
                "validation_asset": "股票L3统一刷新影子验收总表验收_最新.json",
                "goal": "汇总前台短答、财报资金、行业价格、政策事件、市场风格、复盘字段的影子验收状态。",
            },
        ],
        "blocked_queue": [
            {
                "id": "STOCK-BLOCK-001",
                "title": "企业微信真实外发接入",
                "risk_level": "W3",
                "status": "blocked_register_only",
                "reason": "涉及真实外发和公共接入配置，必须交回总管判断。",
            },
            {
                "id": "STOCK-BLOCK-002",
                "title": "正式评分脚本/正式配置接入",
                "risk_level": "W3",
                "status": "blocked_register_only",
                "reason": "涉及正式脚本或配置，必须暂停实施并交回总管判断。",
            },
        ],
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
        "# 股票线连续施工自动续建队列",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        f"- 目的：{asset['purpose']}",
        "",
        "## 自动续建规则",
        "",
        f"- W1/W2：{asset['auto_continue_rule']['w1_w2_low_risk']}",
        f"- 汇报口径：{asset['auto_continue_rule']['final_response_is_report_not_pause']}",
        f"- 每轮自验收：{asset['auto_continue_rule']['must_self_validate_each_round']}",
        f"- 每轮回传记录：{asset['auto_continue_rule']['must_write_alignment_record_each_round']}",
        "",
        "## 施工队列",
        "",
    ]
    for item in asset["construction_queue"]:
        lines.append(f"- {item['id']}｜{item['title']}｜{item['risk_level']}｜{item['status']}｜需确认={item['requires_user_confirmation']}")
    lines.extend(["", "## 红线阻断队列", ""])
    for item in asset["blocked_queue"]:
        lines.append(f"- {item['id']}｜{item['title']}｜{item['risk_level']}｜{item['status']}｜{item['reason']}")
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    asset = build_asset()
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({"status": "ok", "json": str(JSON_OUT), "md": str(MD_OUT), "queued": len(asset["construction_queue"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
