# -*- coding: utf-8 -*-
"""
生成前台缺口话术规则草案。

本脚本只在股票线目录内生成 W1 草案资产，不写企业微信入口、不写正式适配器、
不写评分结果、不触发外发。
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
SOURCE_PATH = DATA_DIR / "前台缺口话术候选分层清单_最新.json"
JSON_OUT = DATA_DIR / "前台缺口话术规则草案_最新.json"
MD_OUT = DATA_DIR / "前台缺口话术规则草案_最新.md"


RULES = [
    {
        "rule_id": "FRONT_GAP_WORDING_001",
        "rule_name": "资金机构解禁证据缺口",
        "source_action_type": "front_wording_rule_candidate",
        "status": "draft",
        "layer": "W1_rule_draft",
        "trigger_condition": "资金/机构/解禁证据卡未达到 evidence_ready，或 score_status 为 not_scored。",
        "recommended_wording": "资金/机构/解禁证据仍待采集，不能强化结论。",
        "front_output_position": "前台结论型短答的缺口一句话或结论原因末句。",
        "evidence_requirement": "必须读取结构化证据卡状态；不得由模型凭空判断资金或机构趋势。",
        "do_not_say": [
            "资金明显流入",
            "机构持续加仓",
            "解禁压力已经释放",
            "资金面确认转强",
        ],
        "blocked_if_formalized": "若写入企业微信短答适配器、正式脚本或生产入口，升级为 W3，必须交回总管判断。",
    },
    {
        "rule_id": "FRONT_GAP_WORDING_002",
        "rule_name": "无直接结构化政策匹配",
        "source_action_type": "policy_wording_rule_candidate",
        "status": "draft",
        "layer": "W1_rule_draft",
        "trigger_condition": "policy_score_allowed 为 false，且政策分类为 no_direct_structured_policy。",
        "recommended_wording": "未匹配直接结构化政策，政策项不能加分。",
        "front_output_position": "前台结论型短答的政策/行业原因句。",
        "evidence_requirement": "必须读取政策事件库匹配结果；未入库或未匹配时只能标缺口。",
        "do_not_say": [
            "政策不强",
            "政策利好已经确认",
            "受益政策明确",
            "政策面支撑充分",
        ],
        "blocked_if_formalized": "若新增政策事件入正式库或修改 L3 政策评分规则，升级为 W3，必须交回总管判断。",
    },
    {
        "rule_id": "FRONT_GAP_WORDING_003",
        "rule_name": "候选政策尚未结构化到单股",
        "source_action_type": "policy_wording_rule_candidate",
        "status": "draft",
        "layer": "W1_rule_draft",
        "trigger_condition": "政策分类为 candidate_policy_needed，存在行业政策背景但尚未形成单股结构化事件。",
        "recommended_wording": "政策背景存在，但尚未结构化到单股事件，政策证据待补。",
        "front_output_position": "前台结论型短答的政策/行业原因句。",
        "evidence_requirement": "必须读取政策事件候选状态并保留 candidate 标识；不得把候选政策直接折算为政策分。",
        "do_not_say": [
            "政策已经落地到公司",
            "政策分可以计入",
            "政策驱动确认",
            "公司确定受益",
        ],
        "blocked_if_formalized": "若要把候选政策转为正式政策事件，升级为 W3，必须走政策事件入库和人工复核闸口。",
    },
    {
        "rule_id": "FRONT_GAP_WORDING_004",
        "rule_name": "行业价格或景气观测点不足",
        "source_action_type": "industry_price_wording_rule_candidate",
        "status": "draft",
        "layer": "W1_rule_draft",
        "trigger_condition": "行业价格/景气连续观测点少于 5 个，或 observation_status 非 evidence_ready。",
        "recommended_wording": "价格/景气观测点不足，不能写趋势确认。",
        "front_output_position": "前台结论型短答的行业/景气原因句。",
        "evidence_requirement": "必须读取行业价格连续观测台账；0 个点写尚未入账，1-4 个点写只能弱参考。",
        "variants": [
            {
                "condition": "observation_count == 0",
                "wording": "价格/景气尚未入账，不能写趋势确认。",
            },
            {
                "condition": "1 <= observation_count < 5",
                "wording": "只有 N 个价格/景气观测点，只能弱参考，不能写趋势确认。",
            },
        ],
        "do_not_say": [
            "价格趋势已经确认",
            "景气度明确上行",
            "行业拐点确认",
            "价格连续走强",
        ],
        "blocked_if_formalized": "若补真实价格点、写入价格台账或改评分，升级为 W3，需走行业价格观测入账流程。",
    },
]


def read_source() -> dict:
    if not SOURCE_PATH.exists():
        return {
            "status": "source_missing",
            "candidates": [],
            "summary": {},
        }
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8-sig"))


def build_asset(source: dict) -> dict:
    w1_candidates = [
        item
        for item in source.get("candidates", [])
        if item.get("layer") == "W1_rule_draft" and item.get("can_implement_now") is True
    ]
    w3_blocked = [
        item
        for item in source.get("candidates", [])
        if item.get("layer") == "W3_blocked" or item.get("can_implement_now") is False
    ]

    coverage = defaultdict(list)
    for item in w1_candidates:
        coverage[item.get("action_type", "unknown")].append(item.get("stock", {}))

    return {
        "name": "前台缺口话术规则草案",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1规则草案",
        "status": "draft",
        "source_asset": str(SOURCE_PATH),
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "scope": {
            "business_line": "股票分析系统",
            "purpose": "把前台结论型短答中的证据缺口表达统一为可复核话术草案。",
            "front_output_principle": "用户看到结论和关键原因；后台保留 evidence/missing/confidence。",
            "non_goals": [
                "不修改企业微信入口",
                "不修改正式适配器",
                "不新增真实外发",
                "不新增交易、下单或仓位能力",
                "不把草案说成正式结论",
            ],
        },
        "source_summary": {
            "candidate_count": len(source.get("candidates", [])),
            "w1_candidate_count": len(w1_candidates),
            "w3_blocked_count": len(w3_blocked),
        },
        "rules": RULES,
        "coverage_by_candidate_type": {
            key: [{"name": stock.get("name"), "code": stock.get("code")} for stock in stocks]
            for key, stocks in coverage.items()
        },
        "formalization_blockers": [
            {
                "blocked_action": "写入企业微信短答适配器或正式入口",
                "risk_level": "W3",
                "handling": "只登记阻断，不实施；交回总管判断。",
            },
            {
                "blocked_action": "真实发送企业微信、触发 n8n、重启服务或修改 19310",
                "risk_level": "W3",
                "handling": "本业务线停止实施，只登记阻断原因。",
            },
            {
                "blocked_action": "新增买入、卖出、下单、仓位调整、券商接口或自动交易",
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
        "# 前台缺口话术规则草案",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：W1 草案，不写企业微信入口，不写正式适配器，不真实外发，不改评分。",
        "",
        "## 来源统计",
        "",
        f"- 候选总数：{asset['source_summary']['candidate_count']}",
        f"- W1 候选：{asset['source_summary']['w1_candidate_count']}",
        f"- W3 阻断：{asset['source_summary']['w3_blocked_count']}",
        "",
        "## 规则草案",
        "",
    ]

    for rule in asset["rules"]:
        lines.extend(
            [
                f"### {rule['rule_id']} {rule['rule_name']}",
                "",
                f"- 状态：{rule['status']}",
                f"- 触发条件：{rule['trigger_condition']}",
                f"- 推荐话术：{rule['recommended_wording']}",
                f"- 输出位置：{rule['front_output_position']}",
                f"- 证据要求：{rule['evidence_requirement']}",
            ]
        )
        if rule.get("variants"):
            lines.append("- 变体：")
            for variant in rule["variants"]:
                lines.append(f"  - {variant['condition']}：{variant['wording']}")
        lines.extend(
            [
                f"- 禁止写法：{'；'.join(rule['do_not_say'])}",
                f"- 正式化阻断：{rule['blocked_if_formalized']}",
                "",
            ]
        )

    lines.extend(
        [
            "## 红线登记",
            "",
        ]
    )
    for blocker in asset["formalization_blockers"]:
        lines.append(f"- {blocker['blocked_action']}：{blocker['risk_level']}，{blocker['handling']}")

    lines.extend(
        [
            "",
            "## 下一步建议",
            "",
            "- 可继续生成“前台结论型短答样例验收清单”，用本草案检查五样本短答是否只说结论、少讲过程、缺证据时显式标注缺口。",
            "- 若要写入企业微信短答适配器、正式入口或服务，必须升级为 W3 阻断并交回总管判断。",
            "",
        ]
    )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    source = read_source()
    asset = build_asset(source)
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({"status": "ok", "json": str(JSON_OUT), "md": str(MD_OUT), "rule_count": len(RULES)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
