from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
PRIORITY_REPORT = DATA_DIR / "L3五样本证据缺口优先级报告_最新.json"
OUTPUT_SUMMARY_JSON = DATA_DIR / "五样本资金机构解禁证据卡候选_最新.json"
OUTPUT_SUMMARY_MD = DATA_DIR / "五样本资金机构解禁证据卡候选_最新.md"


def display_code(code: str) -> str:
    if code.startswith("sz"):
        return f"{code[2:]}.SZ"
    if code.startswith("sh"):
        return f"{code[2:]}.SH"
    return code


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_requirements() -> list[dict]:
    return [
        {
            "source_name": "交易所/巨潮资讯上市公司公告",
            "source_type": "公告",
            "required_fields": ["公告日期", "公告标题", "公告链接", "减持计划/进展/完成状态", "限售解禁数量与比例"],
            "status": "candidate_source_registered",
            "usage_boundary": "只用于确认是否存在减持、解禁或其他公开披露压力，不得自动生成交易动作。"
        },
        {
            "source_name": "上市公司定期报告前十大股东/机构持仓章节",
            "source_type": "定期报告",
            "required_fields": ["报告期", "机构名称", "持股数量", "持股比例", "环比变化", "来源链接"],
            "status": "candidate_source_registered",
            "usage_boundary": "只用于判断机构持仓证据是否增强或减弱；没有完整报告期对比时不得写机构持续加仓。"
        },
        {
            "source_name": "公开资金流向页面",
            "source_type": "公开行情衍生数据",
            "required_fields": ["交易日", "主力净流入额", "主力净流入占比", "成交额", "来源页面", "采集时间"],
            "status": "candidate_source_registered",
            "usage_boundary": "只能作为辅助证据；单日资金流不得直接改变L3结论。"
        },
        {
            "source_name": "交易公开信息/龙虎榜（如适用）",
            "source_type": "交易公开信息",
            "required_fields": ["交易日", "上榜原因", "买卖席位性质", "净买入/净卖出", "来源链接"],
            "status": "candidate_source_registered",
            "usage_boundary": "只用于解释异常交易背景；不上榜则写不适用或缺失，不得虚构席位。"
        }
    ]


def evidence_slots() -> list[dict]:
    return [
        {
            "slot": "capital_flow",
            "display_name": "资金流向",
            "status": "candidate_source_registered",
            "required_fields": ["交易日", "主力净流入额", "主力净流入占比", "成交额", "来源页面", "采集时间"],
            "evidence": [],
            "missing": ["尚未采集可复核的资金流向字段。"],
            "front_usage": "未采集前只能写资金证据仍缺，不能写资金明显流入或流出。"
        },
        {
            "slot": "institutional_holding",
            "display_name": "机构持仓",
            "status": "candidate_source_registered",
            "required_fields": ["报告期", "机构名称", "持股数量", "持股比例", "环比变化", "来源链接"],
            "evidence": [],
            "missing": ["尚未合并定期报告或公开持仓数据。"],
            "front_usage": "未形成报告期对比前，不能写机构持续增配或明显撤退。"
        },
        {
            "slot": "unlock_schedule",
            "display_name": "限售解禁",
            "status": "candidate_source_registered",
            "required_fields": ["解禁日期", "解禁数量", "占总股本比例", "解禁股东", "来源链接"],
            "evidence": [],
            "missing": ["尚未采集未来解禁日期、数量和比例。"],
            "front_usage": "未核验前只能写解禁压力待核验。"
        },
        {
            "slot": "reduction_plan",
            "display_name": "减持计划/进展",
            "status": "candidate_source_registered",
            "required_fields": ["公告日期", "股东名称", "计划减持数量/比例", "进展状态", "来源链接"],
            "evidence": [],
            "missing": ["尚未采集近期限售股东或董监高减持计划与进展。"],
            "front_usage": "未核验前不能写减持压力已消除或风险明显释放。"
        },
        {
            "slot": "public_trading_disclosure",
            "display_name": "交易公开信息",
            "status": "candidate_source_registered",
            "required_fields": ["交易日", "上榜原因", "席位信息", "净买入/净卖出", "来源链接"],
            "evidence": [],
            "missing": ["尚未检查是否存在近期交易公开信息或龙虎榜。"],
            "front_usage": "不上榜或未核验时，不得用席位叙事强化结论。"
        }
    ]


def build_card(sample: dict, today: str) -> dict:
    stock = sample["stock"]
    name = stock["name"]
    code = stock["code"]
    reasons = sample.get("priority_reasons", [])
    inherited_missing = [
        item for item in sample.get("missing", [])
        if any(key in item for key in ["资金", "机构", "减持", "解禁"])
    ]
    if not inherited_missing:
        inherited_missing = ["资金流、机构持仓、减持解禁尚未形成可复核结构化证据。"]

    return {
        "名称": f"{name}资金机构解禁证据卡候选",
        "版本": "shadow_v1.0",
        "生成日期": today,
        "所属系统": "02杰哥扩展系统/01股票研究系统",
        "资产身份": "W1证据候选卡",
        "状态": "source_requirements_ready",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "stock": {
            "name": name,
            "code": code,
            "display_code": display_code(code)
        },
        "evidence_scope": {
            "capital_flow": "公开资金流向字段，作为L3基本面/资金分项的辅助证据。",
            "institutional_holding": "定期报告或公开持仓中的机构持股结构和报告期变化。",
            "unlock_reduction": "限售解禁、股东减持计划、减持进展或减持完成公告。",
            "public_trading_disclosure": "交易公开信息、龙虎榜等异常交易公开披露，仅在适用时使用。"
        },
        "source_requirements": source_requirements(),
        "evidence_slots": evidence_slots(),
        "capital_institution_shadow_score": {
            "score": 0,
            "max_score": 5,
            "score_status": "not_scored",
            "score_reason": "本卡当前只完成证据位和来源要求登记，尚未采集可复核数值，因此不得给资金/机构/解禁加分。",
            "positive_evidence": [],
            "negative_evidence": [],
            "missing": inherited_missing,
            "confidence": "low"
        },
        "front_output_compression": {
            "one_sentence": "资金、机构和解禁减持证据位已建立，但当前仍是待采集状态，不能作为强化结论的依据。",
            "user_facing_reason": "前台可以说明该项仍是关键缺口；后台必须等公开字段入账后再参与评分。",
            "missing_sentence": "缺少可复核的资金流向、机构持仓变化、限售解禁和减持计划/进展字段。",
            "do_not_say": [
                "资金明显流入",
                "机构持续加仓",
                "减持压力已经释放",
                "可以据此买入或卖出",
                "可以调整仓位"
            ]
        },
        "linked_l3_gap": {
            "priority": sample.get("priority", "P0"),
            "priority_reasons": reasons,
            "source_l3_report": sample.get("paths", {}).get("l3_report", "")
        },
        "safety_boundary": {
            "only_for_research": True,
            "not_investment_advice": True,
            "not_buy_sell_signal": True,
            "not_position_adjustment": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
            "not_external_send": True
        }
    }


def render_md(summary: dict) -> str:
    lines = [
        "# 五样本资金机构解禁证据卡候选",
        "",
        f"- 生成时间：{summary['generated_at']}",
        "- 资产身份：W1证据候选卡，不是正式配置，不是入口，不写正式库。",
        "- 安全边界：未触发n8n、未发送企业微信、未重启服务、未调用券商接口、未自动交易。",
        "",
        "## 覆盖样本",
        "",
        "| 股票 | 代码 | 状态 | 评分状态 | 置信度 | 缺口数量 |",
        "|---|---|---|---|---|---:|"
    ]
    for card in summary["cards"]:
        score = card["capital_institution_shadow_score"]
        lines.append(
            f"| {card['stock']['name']} | {card['stock']['display_code']} | {card['状态']} | "
            f"{score['score_status']} | {score['confidence']} | {len(score['missing'])} |"
        )
    lines.extend([
        "",
        "## 统一前台口径",
        "",
        "资金、机构和解禁减持证据位已建立，但当前仍是待采集状态；前台只能把它写成关键缺口，不能写成强化结论。",
        "",
        "## 下一步",
        "",
        "1. 只从公开公告、定期报告、公开资金流向页面和交易公开信息补字段。",
        "2. 每条证据必须保留日期、来源、链接和字段值。",
        "3. 未形成可复核字段前，L3基本面/资金分项不得因本卡加分。",
        "4. 本卡不生成买卖、仓位、下单、券商接口或真实外发动作。"
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    priority_report = read_json(PRIORITY_REPORT)

    cards = [build_card(sample, today) for sample in priority_report.get("samples", [])]
    written_paths = []
    for card in cards:
        file_name = f"{card['stock']['name']}_资金机构解禁证据卡候选_最新.json"
        out_path = DATA_DIR / file_name
        write_json(out_path, card)
        written_paths.append(str(out_path))

    summary = {
        "名称": "五样本资金机构解禁证据卡候选",
        "generated_at": now,
        "asset_identity": "W1证据候选卡集合",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "status": "source_requirements_ready",
        "card_count": len(cards),
        "cards": cards,
        "written_paths": written_paths,
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_delete_or_move_old_assets": True,
            "not_formal_database_write": True,
            "not_broker_interface": True,
            "not_auto_trade": True
        }
    }
    write_json(OUTPUT_SUMMARY_JSON, summary)
    OUTPUT_SUMMARY_MD.write_text(render_md(summary), encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "card_count": len(cards),
        "summary_json": str(OUTPUT_SUMMARY_JSON),
        "summary_md": str(OUTPUT_SUMMARY_MD)
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
