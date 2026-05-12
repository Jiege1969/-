# -*- coding: utf-8 -*-
"""生成复盘结果到规则候选二次门禁样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "复盘结果到规则候选二次门禁样例_最新.json"
MD_OUT = DATA_DIR / "复盘结果到规则候选二次门禁样例_最新.md"


GATE_RULES = [
    {
        "gate_id": "REPLAY-GATE-001",
        "name": "复盘只进候选",
        "rule": "任何复盘发现只能生成experience_candidate，不得直接写正式评分规则。",
    },
    {
        "gate_id": "REPLAY-GATE-002",
        "name": "多案例验证",
        "rule": "经验候选必须等待多案例验证，不得凭单个样本自动提权。",
    },
    {
        "gate_id": "REPLAY-GATE-003",
        "name": "人工复核",
        "rule": "正式规则调整必须人工复核并交回总管判断，本业务线不得越权实施。",
    },
    {
        "gate_id": "REPLAY-GATE-004",
        "name": "前台影响限制",
        "rule": "待复核经验候选只可作为missing或review_hint，不得改变前台结论词。",
    },
]


SAMPLES = [
    {
        "review_id": "REPLAY-SHADOW-001",
        "stock_name": "云南锗业",
        "finding": "政策事件候选对结论影响较大，但来源ready数为0。",
        "candidate_type": "policy_source_quality_rule",
        "candidate_status": "pending_human_review",
        "allowed_output": "经验候选：政策来源未ready时，不得单独支撑重点关注。",
        "formal_rule_update_allowed": False,
    },
    {
        "review_id": "REPLAY-SHADOW-002",
        "stock_name": "正丹股份",
        "finding": "产品价格弹性叙事容易放大结论，但价格源仍缺失。",
        "candidate_type": "industry_price_missing_rule",
        "candidate_status": "pending_human_review",
        "allowed_output": "经验候选：核心产品价格源缺失时，盈利弹性只作为观察线索。",
        "formal_rule_update_allowed": False,
    },
    {
        "review_id": "REPLAY-SHADOW-003",
        "stock_name": "上纬新材",
        "finding": "技术面局部信号容易被误读为完整结论。",
        "candidate_type": "technical_only_downgrade_rule",
        "candidate_status": "pending_human_review",
        "allowed_output": "经验候选：只有技术面证据时，前台结论必须保持低置信或暂不建议关注。",
        "formal_rule_update_allowed": False,
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "复盘结果到规则候选二次门禁样例",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W1复盘到规则候选门禁样例",
        "status": "shadow_gate_sample",
        "purpose": "确保复盘结果只沉淀为经验候选，不自动修改正式评分规则、正式配置或前台结论词。",
        "not_formal_rule_update": True,
        "not_formal_config": True,
        "not_external_send": True,
        "not_formal_entry": True,
        "gate_rules": GATE_RULES,
        "samples": SAMPLES,
        "summary": {
            "gate_count": len(GATE_RULES),
            "sample_count": len(SAMPLES),
            "all_candidates_pending_human_review": all(item["candidate_status"] == "pending_human_review" for item in SAMPLES),
            "any_formal_rule_update_allowed": any(item["formal_rule_update_allowed"] for item in SAMPLES),
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
        "# 复盘结果到规则候选二次门禁样例",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：W1复盘到规则候选门禁样例",
        "- 正式规则更新：否",
        "- 真实外发：否",
        "",
        "## 门禁规则",
        "",
    ]
    for rule in GATE_RULES:
        lines.append(f"- {rule['gate_id']}｜{rule['name']}：{rule['rule']}")
    lines.extend(["", "## 样本", ""])
    for item in SAMPLES:
        lines.extend(
            [
                f"### {item['review_id']}｜{item['stock_name']}",
                "",
                f"- 复盘发现：{item['finding']}",
                f"- 候选类型：{item['candidate_type']}",
                f"- 候选状态：{item['candidate_status']}",
                f"- 允许输出：{item['allowed_output']}",
                f"- 允许正式规则更新：{item['formal_rule_update_allowed']}",
                "",
            ]
        )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
