# -*- coding: utf-8 -*-
"""
生成五样本财报/资金证据补齐路线图。

本脚本只在股票线目录内生成 W1 路线图，不抓取外部数据、不写正式库、
不修改评分规则、不触发企业微信或 n8n。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
CAPITAL_CARD_SUMMARY = DATA_DIR / "五样本资金机构解禁证据卡候选_最新.json"
GAP_REPORT = DATA_DIR / "L3五样本证据缺口优先级报告_最新.json"
JSON_OUT = DATA_DIR / "五样本财报资金证据补齐路线图_最新.json"
MD_OUT = DATA_DIR / "五样本财报资金证据补齐路线图_最新.md"


SAMPLES = [
    {"name": "云南锗业", "code": "sz002428", "profile": "资源/小金属"},
    {"name": "天齐锂业", "code": "sz002466", "profile": "锂资源"},
    {"name": "华虹公司", "code": "sh688347", "profile": "半导体制造"},
    {"name": "浙商中拓", "code": "sz000906", "profile": "供应链服务"},
    {"name": "正丹股份", "code": "sz300641", "profile": "化工材料"},
]

EVIDENCE_FIELDS = [
    {
        "field_group": "financial_report",
        "display_name": "财报摘要",
        "priority": "P0",
        "fields": [
            "report_period",
            "revenue_yoy",
            "net_profit_yoy",
            "gross_margin",
            "operating_cash_flow",
            "debt_ratio",
            "inventory_change",
            "management_discussion_summary",
        ],
        "minimum_ready_condition": "至少有最近一期财报期间、营收同比、净利同比、现金流和管理层讨论摘要。",
        "front_gap_wording": "财报摘要待补，不能把基本面写成确认改善。",
    },
    {
        "field_group": "valuation",
        "display_name": "估值位置",
        "priority": "P1",
        "fields": [
            "pe_ttm",
            "pb",
            "ps_ttm",
            "industry_percentile",
            "valuation_comment",
        ],
        "minimum_ready_condition": "至少有当前估值指标和行业分位，且注明口径日期。",
        "front_gap_wording": "估值分位待补，不能判断便宜或偏贵。",
    },
    {
        "field_group": "capital_flow",
        "display_name": "资金流向",
        "priority": "P0",
        "fields": [
            "main_net_inflow_1d",
            "main_net_inflow_5d",
            "main_net_inflow_20d",
            "turnover_rate",
            "volume_amount_rank",
            "capital_flow_comment",
        ],
        "minimum_ready_condition": "至少有 1日、5日、20日主力净流入或替代口径，并注明来源。",
        "front_gap_wording": "资金证据待采集，不能写资金面确认转强。",
    },
    {
        "field_group": "institution_holding",
        "display_name": "机构持仓",
        "priority": "P1",
        "fields": [
            "institution_holding_ratio",
            "fund_holding_change",
            "top10_shareholder_change",
            "northbound_or_qfii_status",
            "institution_comment",
        ],
        "minimum_ready_condition": "至少有最近一期机构持仓或前十大股东变化，且注明报告期。",
        "front_gap_wording": "机构持仓证据待补，不能写机构持续加仓。",
    },
    {
        "field_group": "unlock_reduction",
        "display_name": "解禁/减持",
        "priority": "P1",
        "fields": [
            "next_unlock_date",
            "unlock_ratio",
            "announced_reduction_plan",
            "reduction_progress",
            "unlock_reduction_comment",
        ],
        "minimum_ready_condition": "至少有未来 90 日解禁和已公告减持计划的检查结果。",
        "front_gap_wording": "解禁/减持证据待补，不能写压力已经释放。",
    },
]

STOCK_SPECIFIC_NOTES = {
    "sz002428": ["锗业务收入/毛利占比", "锗价变化对毛利弹性", "出口管制后订单或价格兑现证据"],
    "sz002466": ["碳酸锂价格对盈利敏感性", "资产减值或库存影响", "现金流和负债压力"],
    "sh688347": ["产能利用率", "晶圆代工景气", "研发投入和折旧压力"],
    "sz000906": ["供应链业务毛利率", "应收/存货周转", "大宗商品价格波动风险"],
    "sz300641": ["TMA价格兑现", "毛利率持续性", "产能和客户集中度"],
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_stock_route(stock: dict[str, str]) -> dict[str, Any]:
    groups = []
    for group in EVIDENCE_FIELDS:
        groups.append(
            {
                "field_group": group["field_group"],
                "display_name": group["display_name"],
                "priority": group["priority"],
                "fields": group["fields"],
                "current_status": "missing_or_candidate",
                "score_status": "not_scored_until_evidence_ready",
                "minimum_ready_condition": group["minimum_ready_condition"],
                "front_gap_wording": group["front_gap_wording"],
                "allowed_action_now": "登记待补字段和验收口径",
                "blocked_action": "自动抓取真实数据、写正式库、改评分或写企业微信入口",
            }
        )

    return {
        "stock": stock,
        "evidence_groups": groups,
        "stock_specific_fields": STOCK_SPECIFIC_NOTES.get(stock["code"], []),
        "front_answer_rule": "财报/资金证据未达到 evidence_ready 前，前台只能写缺口，不能强化基本面或资金结论。",
        "next_collection_order": [
            "financial_report",
            "capital_flow",
            "institution_holding",
            "unlock_reduction",
            "valuation",
        ],
    }


def build_asset() -> dict[str, Any]:
    capital_summary = load_json(CAPITAL_CARD_SUMMARY)
    gap_report = load_json(GAP_REPORT)
    routes = [build_stock_route(stock) for stock in SAMPLES]
    return {
        "name": "五样本财报资金证据补齐路线图",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1证据补齐路线图",
        "status": "draft",
        "source_assets": {
            "capital_card_summary": str(CAPITAL_CARD_SUMMARY),
            "gap_report": str(GAP_REPORT),
            "capital_card_summary_exists": bool(capital_summary),
            "gap_report_exists": bool(gap_report),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "purpose": "把财报、估值、资金、机构、解禁旧债拆成可采集字段、前台缺口话术和验收条件。",
        "global_evidence_groups": EVIDENCE_FIELDS,
        "stock_routes": routes,
        "summary": {
            "sample_count": len(routes),
            "field_group_count_per_stock": len(EVIDENCE_FIELDS),
            "total_route_items": len(routes) * len(EVIDENCE_FIELDS),
            "p0_group_count_per_stock": sum(1 for group in EVIDENCE_FIELDS if group["priority"] == "P0"),
            "p1_group_count_per_stock": sum(1 for group in EVIDENCE_FIELDS if group["priority"] == "P1"),
        },
        "quality_gates": [
            "每只股票必须覆盖财报摘要、估值位置、资金流向、机构持仓、解禁/减持。",
            "每组证据必须有字段清单、最低 ready 条件和前台缺口话术。",
            "证据未 ready 前 score_status 必须保持 not_scored_until_evidence_ready。",
            "不得用空值、横杠或模型推断冒充财报/资金结论。",
            "不得自动抓取真实账号数据、不得外发、不得交易。",
        ],
        "formalization_blockers": [
            {
                "action": "接入真实行情/财报/资金数据源并写正式库",
                "risk_level": "W3",
                "handling": "本轮只登记路线图，不实施；交回总管判断。",
            },
            {
                "action": "把补齐路线写入企业微信短答适配器、正式入口或服务脚本",
                "risk_level": "W3",
                "handling": "只登记阻断，不实施。",
            },
            {
                "action": "新增买入、卖出、下单、仓位调整、券商接口或自动交易",
                "risk_level": "W3",
                "handling": "禁止新增；股票线保持研究分析系统定位。",
            },
        ],
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_adapter_write": True,
            "not_score_write": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }


def write_markdown(asset: dict[str, Any]) -> None:
    lines = [
        "# 五样本财报资金证据补齐路线图",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：W1 路线图，不抓取外部数据，不写正式库，不改评分，不接企业微信入口。",
        "",
        "## 汇总",
        "",
        f"- 样本数：{asset['summary']['sample_count']}",
        f"- 每只股票字段组：{asset['summary']['field_group_count_per_stock']}",
        f"- 路线项总数：{asset['summary']['total_route_items']}",
        "",
        "## 全局证据组",
        "",
    ]
    for group in asset["global_evidence_groups"]:
        lines.extend(
            [
                f"### {group['display_name']}（{group['field_group']}）",
                "",
                f"- 优先级：{group['priority']}",
                f"- 字段：{'；'.join(group['fields'])}",
                f"- ready 条件：{group['minimum_ready_condition']}",
                f"- 前台缺口话术：{group['front_gap_wording']}",
                "",
            ]
        )

    lines.extend(["## 五样本路线", ""])
    for route in asset["stock_routes"]:
        stock = route["stock"]
        lines.extend(
            [
                f"### {stock['name']}（{stock['code']}）",
                "",
                f"- 股票特有字段：{'；'.join(route['stock_specific_fields'])}",
                f"- 前台规则：{route['front_answer_rule']}",
                f"- 补齐顺序：{' -> '.join(route['next_collection_order'])}",
                "",
            ]
        )

    lines.extend(["## 质量闸口", ""])
    lines.extend([f"- {item}" for item in asset["quality_gates"]])

    lines.extend(["", "## 正式化阻断", ""])
    for blocker in asset["formalization_blockers"]:
        lines.append(f"- {blocker['action']}：{blocker['risk_level']}，{blocker['handling']}")

    lines.extend(["", "## 下一步自动推进", ""])
    lines.append("- 生成“五样本财报资金证据补齐路线图验收”后，继续做“财报资金证据采集模板草案”，仍只做 W1 样本/模板。")
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
