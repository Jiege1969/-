# -*- coding: utf-8 -*-
"""
生成后台证据链到前台短答字段映射草案。

仅生成股票线 W1 草案资产，不修改企业微信入口、正式适配器、评分规则或真实服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
SAMPLE_PATH = DATA_DIR / "五样本前台结论型短答修订样例_最新.json"
RULE_PATH = DATA_DIR / "前台缺口话术规则草案_最新.json"
JSON_OUT = DATA_DIR / "后台证据链到前台短答字段映射草案_最新.json"
MD_OUT = DATA_DIR / "后台证据链到前台短答字段映射草案_最新.md"


FIELD_MAPPINGS = [
    {
        "front_field": "object_line",
        "display_name": "对象行",
        "format": "{股票名称}（{股票代码}）",
        "backend_sources": ["stock_identity.name", "stock_identity.code"],
        "required": True,
        "missing_behavior": "无法确认股票名称或代码时，不生成分析结论，改为澄清对象。",
        "forbidden_behavior": "不得只写简称、板块名或用户输入原文。",
    },
    {
        "front_field": "conclusion_line",
        "display_name": "结论行",
        "format": "结论：{重点关注/可纳入观察/暂不建议关注}，{一句话限定条件}",
        "backend_sources": ["l3_score.total_score", "l3_score.conclusion_text", "confidence.level", "missing_summary"],
        "required": True,
        "decision_rule": "结论词必须来自 L3 评分契约阈值；关键证据缺失时不得输出重点关注。",
        "missing_behavior": "缺少 L3 总分或关键证据时，最高只能写可观察或暂不建议强化关注。",
        "forbidden_behavior": "不得使用买入、卖出、下单、仓位调整、强烈推荐等交易执行话术。",
    },
    {
        "front_field": "main_reason_line",
        "display_name": "主要原因行",
        "format": "主要原因：{1-2条最强证据，优先结构化政策/市场风格/行业景气/财报资金共振}",
        "backend_sources": [
            "item_scores.technical_structure.evidence",
            "item_scores.fundamentals_capital.evidence",
            "item_scores.policy_events.evidence",
            "item_scores.market_style_fit.evidence",
            "industry_price_observation.evidence",
        ],
        "required": True,
        "selection_rule": "只选有结构化证据的原因；不把后台指标逐项堆给前台。",
        "missing_behavior": "证据不足时写保守原因，并把不足转入关键缺口行。",
        "forbidden_behavior": "不得把未结构化政策、单点价格或模型推断写成确定利好。",
    },
    {
        "front_field": "key_gap_line",
        "display_name": "关键缺口行",
        "format": "关键缺口：{最影响结论等级的1-3个缺口}",
        "backend_sources": [
            "item_scores.*.missing",
            "fundamental_report.missing",
            "capital_institution_unlock_card.status",
            "policy_event_match.status",
            "market_style_daily.status",
            "industry_price_observation.status",
        ],
        "required": True,
        "selection_rule": "优先列出导致不能上调结论的缺口，例如财报、资金/机构/解禁、政策结构化、行业价格连续观测、市场风格。",
        "missing_behavior": "没有后台缺口字段时，必须写“缺口字段未生成”，不能用横杠、空值或省略替代。",
        "forbidden_behavior": "不得用无、-、暂无等空泛词冒充证据判断。",
    },
    {
        "front_field": "confidence_review_line",
        "display_name": "置信度与复核行",
        "format": "置信度：{high/medium/low}。下一次复核重点看{1-2项}",
        "backend_sources": ["confidence.level", "confidence.reason", "next_review_date", "missing_summary"],
        "required": True,
        "decision_rule": "存在关键证据缺失时，confidence 不得为 high。",
        "missing_behavior": "缺少置信度字段时默认 low，并提示需补置信度原因。",
        "forbidden_behavior": "不得把样本草案写成正式结论或确定投资建议。",
    },
]


BACKEND_TO_FRONT_PRIORITY = [
    {
        "backend_evidence": "policy_events",
        "front_role": "有直接结构化匹配时可进入主要原因；无匹配时进入关键缺口。",
        "front_wording_guard": "未匹配直接结构化政策，政策项不能加分。",
    },
    {
        "backend_evidence": "market_style_fit",
        "front_role": "只用于解释当前环境是否配合，不单独决定结论。",
        "front_wording_guard": "市场风格证据缺失时，不得写市场情绪配合。",
    },
    {
        "backend_evidence": "industry_price_observation",
        "front_role": "连续观测达标才可写趋势；不足时进入关键缺口。",
        "front_wording_guard": "价格/景气观测点不足，不能写趋势确认。",
    },
    {
        "backend_evidence": "fundamentals_capital",
        "front_role": "财报、估值、资金、机构、解禁证据齐备时可加强结论；缺失时必须降低置信度。",
        "front_wording_guard": "资金/机构/解禁证据仍待采集，不能强化结论。",
    },
    {
        "backend_evidence": "technical_structure",
        "front_role": "可作为辅助原因，但不得压过政策、财报、市场风格和行业证据缺口。",
        "front_wording_guard": "技术面只解释当前结构，不替代行业、政策和财报证据。",
    },
]


def load_source_status() -> dict:
    return {
        "sample_asset_exists": SAMPLE_PATH.exists(),
        "wording_rule_asset_exists": RULE_PATH.exists(),
        "sample_asset": str(SAMPLE_PATH),
        "wording_rule_asset": str(RULE_PATH),
    }


def build_asset() -> dict:
    return {
        "name": "后台证据链到前台短答字段映射草案",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1映射草案",
        "status": "draft",
        "source_status": load_source_status(),
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "purpose": "把后台 L3 证据、缺口和置信度压缩为企业微信前台可读的结论型短答字段。",
        "front_output_shape": [
            "对象行",
            "结论行",
            "主要原因行",
            "关键缺口行",
            "置信度与复核行",
        ],
        "field_mappings": FIELD_MAPPINGS,
        "backend_to_front_priority": BACKEND_TO_FRONT_PRIORITY,
        "quality_gates": [
            "第一行必须明确股票名称和代码。",
            "结论词必须来自评分契约或显式降级规则。",
            "证据先于判断：没有结构化证据就写缺口，不补分。",
            "前台只保留关键原因，不堆完整技术指标。",
            "后台报告继续保留 evidence、missing、confidence、review 字段。",
            "人工修正只进入复盘/经验候选，不自动改正式规则。",
        ],
        "formalization_blockers": [
            {
                "action": "写入企业微信短答适配器、正式入口或服务脚本",
                "risk_level": "W3",
                "handling": "只登记阻断，不实施；交回总管判断。",
            },
            {
                "action": "触发真实企业微信外发、n8n、19310、服务重启或真实账号",
                "risk_level": "W3",
                "handling": "停止实施，只登记阻断原因。",
            },
            {
                "action": "新增买入、卖出、下单、仓位调整、券商接口或自动交易能力",
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


def write_markdown(asset: dict) -> None:
    lines = [
        "# 后台证据链到前台短答字段映射草案",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：W1 映射草案，不写企业微信入口，不真实外发，不改正式适配器。",
        "",
        "## 前台输出形状",
        "",
    ]
    lines.extend([f"- {item}" for item in asset["front_output_shape"]])
    lines.extend(["", "## 字段映射", ""])
    for item in asset["field_mappings"]:
        lines.extend(
            [
                f"### {item['display_name']}（{item['front_field']}）",
                "",
                f"- 格式：{item['format']}",
                f"- 后台来源：{'；'.join(item['backend_sources'])}",
                f"- 缺失处理：{item['missing_behavior']}",
                f"- 禁止行为：{item['forbidden_behavior']}",
                "",
            ]
        )
        if item.get("decision_rule"):
            lines.insert(len(lines) - 1, f"- 判定规则：{item['decision_rule']}")
        if item.get("selection_rule"):
            lines.insert(len(lines) - 1, f"- 选择规则：{item['selection_rule']}")

    lines.extend(["## 后台证据优先级", ""])
    for item in asset["backend_to_front_priority"]:
        lines.extend(
            [
                f"- {item['backend_evidence']}：{item['front_role']} 守门话术：{item['front_wording_guard']}",
            ]
        )

    lines.extend(["", "## 质量闸口", ""])
    lines.extend([f"- {item}" for item in asset["quality_gates"]])

    lines.extend(["", "## 正式化阻断", ""])
    for blocker in asset["formalization_blockers"]:
        lines.append(f"- {blocker['action']}：{blocker['risk_level']}，{blocker['handling']}")

    lines.extend(["", "## 下一步建议", ""])
    lines.append("- 可继续生成“五样本后台到前台字段映射验收样例”，用五样本检查每个前台字段是否都有后台来源和缺口承接。")
    lines.append("- 若要写入正式适配器或企业微信入口，升级为 W3，本轮不实施。")
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    asset = build_asset()
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({"status": "ok", "json": str(JSON_OUT), "md": str(MD_OUT), "field_count": len(FIELD_MAPPINGS)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
