# -*- coding: utf-8 -*-
"""生成标准前台报告输出门禁样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "标准前台报告输出门禁样例_最新.json"
MD_OUT = DATA_DIR / "标准前台报告输出门禁样例_最新.md"


GATE_RULES = [
    {
        "gate_id": "FRONT-GATE-001",
        "name": "对象首行门禁",
        "must_have": ["stock_name", "stock_code", "conclusion"],
        "rule": "第一行必须明确股票名称、代码和结论词。",
    },
    {
        "gate_id": "FRONT-GATE-002",
        "name": "结论词门禁",
        "must_have": ["重点关注", "可纳入观察", "暂不建议关注"],
        "rule": "结论词只能来自标准三档，不允许自由发挥成交易动作。",
    },
    {
        "gate_id": "FRONT-GATE-003",
        "name": "主因数量门禁",
        "max_count": 3,
        "rule": "主要依据最多3条，只保留支撑结论的关键原因。",
    },
    {
        "gate_id": "FRONT-GATE-004",
        "name": "缺口显式门禁",
        "must_have_when_missing_exists": ["key_missing"],
        "rule": "后台存在P0/P1缺口时，前台必须显式说明关键缺口。",
    },
    {
        "gate_id": "FRONT-GATE-005",
        "name": "置信度门禁",
        "must_have": ["confidence_text"],
        "rule": "前台必须说明高/中/低置信度及限制原因。",
    },
    {
        "gate_id": "FRONT-GATE-006",
        "name": "后台指标隐藏门禁",
        "forbidden_words": ["MACD", "RSI", "K线", "量比", "均线排列", "计算过程", "item_scores"],
        "rule": "企业微信前台短答不直接堆后台指标和计算字段。",
    },
    {
        "gate_id": "FRONT-GATE-007",
        "name": "交易执行禁止门禁",
        "forbidden_words": ["买入", "卖出", "下单", "仓位", "自动交易", "券商接口"],
        "rule": "股票系统只做研究分析，不输出交易执行动作。",
    },
]


SAMPLES = [
    {
        "sample_id": "FRONT-SAMPLE-001",
        "stock_name": "云南锗业",
        "stock_code": "002428",
        "backend_missing_exists": True,
        "frontend_output": {
            "first_line": "云南锗业（002428）：可纳入观察。",
            "one_sentence": "政策和资源属性有支撑，但财报、锗价和资金证据还没补齐，暂不输出强结论。",
            "main_reasons": ["锗相关政策事件候选有支撑", "资源品主题与市场风格适配", "技术结构只作辅助确认"],
            "key_missing": ["P0：财报和盈利质量未结构化", "P0：锗价连续观测待补"],
            "confidence_text": "置信度中等，主要受财报和价格连续数据缺口限制。",
            "review_hint": "下一次优先复核财报、锗价和资金证据。",
        },
        "expected_gate_result": "pass",
    },
    {
        "sample_id": "FRONT-SAMPLE-002",
        "stock_name": "正丹股份",
        "stock_code": "300641",
        "backend_missing_exists": True,
        "frontend_output": {
            "first_line": "正丹股份（300641）：可纳入观察。",
            "one_sentence": "产品价格和盈利弹性值得跟踪，但关键证据未连续验证前只保留观察。",
            "main_reasons": ["化工品价格弹性线索值得跟踪", "新增样本已纳入验收"],
            "key_missing": ["P0：核心产品价格连续数据待补", "P0：最新财报盈利弹性待复核"],
            "confidence_text": "置信度中等，关键取决于价格和财报能否连续验证。",
            "review_hint": "下一次优先复核核心产品价格、财报和资金承接。",
        },
        "expected_gate_result": "pass",
    },
    {
        "sample_id": "FRONT-SAMPLE-003",
        "stock_name": "上纬新材",
        "stock_code": "688585",
        "backend_missing_exists": True,
        "frontend_output": {
            "first_line": "上纬新材（688585）：暂不建议关注。",
            "one_sentence": "当前证据主要停留在局部技术面，财报、行业和资金证据不足。",
            "main_reasons": ["结构化财报证据不足", "行业景气证据不足"],
            "key_missing": ["P0：财报与盈利质量证据缺失", "P0：行业景气与订单价格线索缺失"],
            "confidence_text": "置信度低，缺口集中在财报、行业和资金证据。",
            "review_hint": "下一次先补财报和行业价格/需求证据。",
        },
        "expected_gate_result": "pass",
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "标准前台报告输出门禁样例",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W1前台输出门禁样例",
        "status": "shadow_gate_sample",
        "purpose": "把股票分析助手前台回答的必填项、禁止项和缺口约束做成可验收门禁。",
        "not_real_market_report": True,
        "not_external_send": True,
        "not_formal_entry": True,
        "not_trade_advice": True,
        "gate_rules": GATE_RULES,
        "samples": SAMPLES,
        "summary": {
            "gate_count": len(GATE_RULES),
            "sample_count": len(SAMPLES),
            "all_samples_expected_pass": all(item["expected_gate_result"] == "pass" for item in SAMPLES),
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
    lines = [
        "# 标准前台报告输出门禁样例",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：W1前台输出门禁样例",
        "- 真实外发：否",
        "- 交易建议：否",
        "",
        "## 门禁规则",
        "",
    ]
    for rule in GATE_RULES:
        lines.append(f"- {rule['gate_id']}｜{rule['name']}：{rule['rule']}")
    lines.extend(["", "## 样本", ""])
    for sample in SAMPLES:
        front = sample["frontend_output"]
        lines.extend(
            [
                f"### {sample['stock_name']}（{sample['stock_code']}）",
                "",
                front["first_line"],
                "",
                front["one_sentence"],
                "",
                "主要依据：" + "；".join(front["main_reasons"]) + "。",
                "",
                "关键缺口：" + "；".join(front["key_missing"]) + "。",
                "",
                front["confidence_text"],
                "",
                "复核提醒：" + front["review_hint"],
                "",
            ]
        )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
