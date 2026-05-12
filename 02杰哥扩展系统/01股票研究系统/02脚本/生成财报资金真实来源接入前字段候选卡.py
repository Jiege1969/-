# -*- coding: utf-8 -*-
"""生成财报资金真实来源接入前字段候选卡。

本脚本只产出影子候选资产，不接正式接口、不写正式配置、不触发外发。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "财报资金真实来源接入前字段候选卡_最新.json"
MD_OUT = DATA_DIR / "财报资金真实来源接入前字段候选卡_最新.md"


SOURCE_CARDS = [
    {
        "domain": "financial_report",
        "display_name": "财报核心指标",
        "priority": "P0",
        "candidate_sources": [
            {
                "source_name": "巨潮资讯定期报告",
                "source_type": "official_disclosure",
                "read_mode": "manual_or_readonly_snapshot",
                "candidate_fields": ["营业收入", "归母净利润", "扣非净利润", "毛利率", "经营现金流", "资产负债率"],
                "why": "A股定期报告披露集中，适合作为财报字段的主来源。",
            },
            {
                "source_name": "交易所/上市公司公告",
                "source_type": "official_disclosure",
                "read_mode": "manual_or_readonly_snapshot",
                "candidate_fields": ["业绩预告", "业绩快报", "重大经营变化", "风险提示"],
                "why": "用于补齐报告期之间的财务变化线索。",
            },
        ],
        "frontend_gate": "缺少最近一期财报核心指标时，前台不得给出强研究结论，confidence最高为medium。",
    },
    {
        "domain": "valuation_position",
        "display_name": "估值位置",
        "priority": "P0",
        "candidate_sources": [
            {
                "source_name": "公开行情/估值快照",
                "source_type": "market_data_snapshot",
                "read_mode": "readonly_snapshot_candidate",
                "candidate_fields": ["PE_TTM", "PB", "PS_TTM", "行业分位", "近三年分位"],
                "why": "用于判断估值是否处于历史或同行偏高/偏低区间。",
            }
        ],
        "frontend_gate": "缺少估值位置时，前台不能使用低估、高估、估值便宜等判断词。",
    },
    {
        "domain": "institutional_holding",
        "display_name": "机构持仓",
        "priority": "P1",
        "candidate_sources": [
            {
                "source_name": "基金定期报告/上市公司十大流通股东",
                "source_type": "public_disclosure",
                "read_mode": "manual_or_readonly_snapshot",
                "candidate_fields": ["机构持股比例", "基金持仓数量", "环比变化", "前十大流通股东变化"],
                "why": "用于验证机构关注度和筹码结构变化。",
            }
        ],
        "frontend_gate": "缺少机构持仓时，前台不得用机构加仓、机构认可等词强化结论。",
    },
    {
        "domain": "capital_flow",
        "display_name": "资金流向",
        "priority": "P1",
        "candidate_sources": [
            {
                "source_name": "公开资金流向快照",
                "source_type": "market_data_snapshot",
                "read_mode": "readonly_snapshot_candidate",
                "candidate_fields": ["主力净流入", "北向持股变化", "成交额分位", "量比"],
                "why": "用于补充短期承接和交易活跃度证据。",
            }
        ],
        "frontend_gate": "缺少资金流向时，前台不得声称资金承接强或资金持续流入。",
    },
    {
        "domain": "announcement_quality",
        "display_name": "公告质量",
        "priority": "P1",
        "candidate_sources": [
            {
                "source_name": "巨潮资讯/交易所公告",
                "source_type": "official_disclosure",
                "read_mode": "manual_or_readonly_snapshot",
                "candidate_fields": ["重大合同", "产能投放", "减持增持", "监管问询", "诉讼担保"],
                "why": "用于识别近期公告是增量利好、普通信息还是风险信号。",
            }
        ],
        "frontend_gate": "缺少公告质量结构化字段时，公告只能作为线索，不能作为主判断依据。",
    },
]


SAMPLE_STOCKS = [
    {"stock_name": "云南锗业", "stock_code": "002428", "must_prioritize": ["financial_report", "valuation_position", "capital_flow"]},
    {"stock_name": "天齐锂业", "stock_code": "002466", "must_prioritize": ["financial_report", "valuation_position", "announcement_quality"]},
    {"stock_name": "浙商中拓", "stock_code": "000906", "must_prioritize": ["financial_report", "capital_flow", "announcement_quality"]},
    {"stock_name": "正丹股份", "stock_code": "300641", "must_prioritize": ["financial_report", "valuation_position", "capital_flow"]},
    {"stock_name": "上纬新材", "stock_code": "688585", "must_prioritize": ["financial_report", "institutional_holding", "announcement_quality"]},
]


def build_markdown(asset: dict) -> str:
    lines = [
        "# 财报资金真实来源接入前字段候选卡",
        "",
        f"- 生成时间：{asset['generated_at']}",
        "- 资产身份：W2 低风险影子候选卡",
        "- 真实接入：否",
        "- 正式配置：否",
        "- 企业微信外发：否",
        "- 交易能力：否",
        "",
        "## 字段候选来源",
        "",
        "| 字段域 | 优先级 | 候选来源 | 读取方式 | 前台门禁 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for card in asset["source_cards"]:
        sources = "；".join(source["source_name"] for source in card["candidate_sources"])
        modes = "；".join(source["read_mode"] for source in card["candidate_sources"])
        lines.append(f"| {card['display_name']} | {card['priority']} | {sources} | {modes} | {card['frontend_gate']} |")

    lines.extend(["", "## 样本优先补齐字段", "", "| 股票 | 代码 | 优先补齐字段 |", "| --- | --- | --- |"])
    name_by_domain = {card["domain"]: card["display_name"] for card in asset["source_cards"]}
    for sample in asset["sample_stocks"]:
        fields = "、".join(name_by_domain.get(item, item) for item in sample["must_prioritize"])
        lines.append(f"| {sample['stock_name']} | {sample['stock_code']} | {fields} |")

    lines.extend(
        [
            "",
            "## 接入前约束",
            "",
            "- 本候选卡只登记字段与来源，不调用接口。",
            "- 未人工核验前，不得把候选来源写入正式配置。",
            "- 字段缺失必须进入 evidence/missing/confidence，不允许由模型凭空补分。",
            "- 前台短答只输出结论和关键原因，后台保留证据链和缺口。",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "财报资金真实来源接入前字段候选卡",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W2_shadow_candidate_card",
        "status": "candidate_only_not_connected",
        "purpose": "登记财报、估值、机构、资金、公告质量的候选来源与前台门禁，避免缺证据仍输出强结论。",
        "source_cards": SOURCE_CARDS,
        "sample_stocks": SAMPLE_STOCKS,
        "acceptance_rules": [
            "必须覆盖财报核心指标、估值位置、机构持仓、资金流向、公告质量五个字段域。",
            "每个字段域必须有候选来源、读取方式和前台门禁。",
            "P0字段缺失时必须限制前台结论强度和置信度。",
            "不得调用真实接口、不得写正式配置、不得触发外发。",
        ],
        "summary": {
            "field_domain_count": len(SOURCE_CARDS),
            "sample_stock_count": len(SAMPLE_STOCKS),
            "p0_domain_count": len([item for item in SOURCE_CARDS if item["priority"] == "P0"]),
            "candidate_only": True,
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
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_OUT.write_text(build_markdown(asset), encoding="utf-8")
    print(json.dumps({"status": "ok", "path": str(JSON_OUT), "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
