# -*- coding: utf-8 -*-
"""生成标准股票分析格式前台短答范本样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "标准股票分析格式前台短答范本样例_最新.json"
MD_OUT = DATA_DIR / "标准股票分析格式前台短答范本样例_最新.md"


SAMPLES = [
    {
        "stock_name": "云南锗业",
        "stock_code": "002428",
        "conclusion": "可纳入观察",
        "first_line": "云南锗业（002428）：可纳入观察。",
        "one_sentence": "主线看政策和资源属性有支撑，但财报、锗价连续数据和资金证据还需要补齐，暂不输出强结论。",
        "main_reasons": ["锗相关政策事件候选对行业预期有支撑", "资源/小金属方向与市场风格存在适配可能", "技术结构只能作为辅助确认"],
        "key_missing": ["P0：近期财报与盈利质量未完成结构化校验", "P0：锗价连续观测和公司暴露度仍需复核"],
        "review_hint": "下一次复核优先补财报、锗价和政策暴露度证据。",
    },
    {
        "stock_name": "三花智控",
        "stock_code": "002050",
        "conclusion": "可纳入观察",
        "first_line": "三花智控（002050）：可纳入观察。",
        "one_sentence": "公司产业位置较清晰，但前台结论必须等财报、资金和行业景气证据同时进入后再提高置信度。",
        "main_reasons": ["行业位置和产业链标签较明确", "适合用基本面/资金证据进一步验证", "单靠技术面不足以形成强判断"],
        "key_missing": ["P0：最新财报核心指标未结构化进入本样例", "P1：机构和资金变化证据待补"],
        "review_hint": "下一次复核优先补财报摘要、估值位置和机构资金变化。",
    },
    {
        "stock_name": "上纬新材",
        "stock_code": "688585",
        "conclusion": "暂不建议关注",
        "first_line": "上纬新材（688585）：暂不建议关注。",
        "one_sentence": "当前样例证据不足以支撑积极结论，需先补行业景气、财报质量和市场风格适配证据。",
        "main_reasons": ["前台样例未获得足够结构化财报证据", "行业景气证据不足", "市场风格适配未形成明确加分"],
        "key_missing": ["P0：财报与盈利质量证据缺失", "P0：行业景气与订单/价格线索缺失"],
        "review_hint": "下一次复核先补财报和行业价格/需求证据，暂不提高结论强度。",
    },
    {
        "stock_name": "浙商中拓",
        "stock_code": "000906",
        "conclusion": "可纳入观察",
        "first_line": "浙商中拓（000906）：可纳入观察。",
        "one_sentence": "作为新增样本，当前先进入观察池验证供应链/大宗商品属性、财报质量和资金变化，不直接给强结论。",
        "main_reasons": ["新增样本已纳入前台格式验收", "业务属性需要结合大宗商品和供应链景气验证", "财报资金证据决定后续结论上限"],
        "key_missing": ["P0：财报与经营现金流证据待结构化", "P1：大宗商品景气和资金流向证据待补"],
        "review_hint": "下一次复核优先补财报、经营现金流和行业景气证据。",
    },
    {
        "stock_name": "正丹股份",
        "stock_code": "300641",
        "conclusion": "可纳入观察",
        "first_line": "正丹股份（300641）：可纳入观察。",
        "one_sentence": "作为新增样本，若化工品价格和盈利弹性证据能连续验证，结论可上修；证据不足前只保留观察。",
        "main_reasons": ["新增样本已纳入前台格式验收", "化工品价格和盈利弹性是核心证据", "需要市场风格和资金承接共同确认"],
        "key_missing": ["P0：核心产品价格连续数据待补", "P0：最新财报盈利弹性和持续性待复核"],
        "review_hint": "下一次复核优先补核心产品价格、财报和资金承接证据。",
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "标准股票分析格式前台短答范本样例",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W1前台短答格式样例",
        "status": "shadow_sample",
        "purpose": "把企业微信股票分析助手的前台回答固定为对象先明确、结论先行、依据少而准、缺口显式、复核提醒收尾的格式。",
        "not_real_market_report": True,
        "not_external_send": True,
        "not_formal_entry": True,
        "not_trade_advice": True,
        "format_contract": {
            "line_1": "股票名称（代码）：结论词。",
            "line_2": "一句话判断，直接说当前怎么看。",
            "line_3": "主要依据，最多3条，只保留能支撑结论的原因。",
            "line_4": "关键缺口，必须显式列出P0/P1缺证据项。",
            "line_5": "复核提醒，只说明下一次看什么，不给交易指令。",
        },
        "allowed_conclusions": ["重点关注", "可纳入观察", "暂不建议关注"],
        "samples": SAMPLES,
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
        "summary": {
            "sample_count": len(SAMPLES),
            "included_new_samples": ["浙商中拓", "正丹股份"],
            "frontend_first": True,
            "requires_missing": True,
            "max_reason_count": 3,
        },
    }
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 标准股票分析格式前台短答范本样例",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：W1前台短答格式样例",
        "- 真实外发：否",
        "- 交易建议：否",
        "",
        "## 格式契约",
        "",
        "1. 股票名称（代码）：结论词。",
        "2. 一句话判断，直接说当前怎么看。",
        "3. 主要依据，最多3条，只保留能支撑结论的原因。",
        "4. 关键缺口，必须显式列出P0/P1缺证据项。",
        "5. 复核提醒，只说明下一次看什么，不给交易指令。",
        "",
        "## 样例",
        "",
    ]
    for sample in SAMPLES:
        lines.extend(
            [
                f"### {sample['stock_name']}（{sample['stock_code']}）",
                "",
                sample["first_line"],
                "",
                sample["one_sentence"],
                "",
                "主要依据：" + "；".join(sample["main_reasons"]) + "。",
                "",
                "关键缺口：" + "；".join(sample["key_missing"]) + "。",
                "",
                "复核提醒：" + sample["review_hint"],
                "",
            ]
        )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
