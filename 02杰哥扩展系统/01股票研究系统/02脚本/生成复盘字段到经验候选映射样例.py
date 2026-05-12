# -*- coding: utf-8 -*-
"""生成复盘字段到经验候选映射样例。

仅生成股票线W1影子样例，把复盘和人工修正沉淀为经验候选，不自动改正式规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "复盘字段到经验候选映射样例_最新.json"
MD_OUT = DATA_DIR / "复盘字段到经验候选映射样例_最新.md"


MAPPING_RULES = [
    {
        "review_field": "wrong_strength",
        "candidate_type": "conclusion_strength_rule_candidate",
        "rule": "若前台结论过强，先生成结论强度候选，不直接改正式阈值。",
    },
    {
        "review_field": "missing_not_exposed",
        "candidate_type": "missing_exposure_rule_candidate",
        "rule": "若关键缺口未暴露，生成缺口暴露候选，并要求至少3个样本复核。",
    },
    {
        "review_field": "evidence_mismatch",
        "candidate_type": "evidence_mapping_rule_candidate",
        "rule": "若证据与结论不匹配，生成证据映射候选，不自动覆盖报告模板。",
    },
    {
        "review_field": "user_readability_issue",
        "candidate_type": "front_answer_style_candidate",
        "rule": "若用户认为过程太多或结论不清，生成前台表达候选。",
    },
]


SAMPLES = [
    {
        "stock": {"name": "云南锗业", "code": "002428"},
        "review_observation": "政策线索被表述得偏强，但财报和锗价缺口仍在。",
        "review_field": "wrong_strength",
        "experience_candidate": "资源股有政策线索但P0缺口未补齐时，前台结论不得超过可纳入观察。",
        "candidate_status": "pending_human_review",
    },
    {
        "stock": {"name": "天齐锂业", "code": "002466"},
        "review_observation": "锂价缺口没有放在足够靠前位置。",
        "review_field": "missing_not_exposed",
        "experience_candidate": "资源/新能源样本必须把核心商品价格列为P0缺口。",
        "candidate_status": "pending_human_review",
    },
    {
        "stock": {"name": "华虹公司", "code": "688347"},
        "review_observation": "半导体政策方向被泛化，缺少单股暴露度证据。",
        "review_field": "evidence_mismatch",
        "experience_candidate": "行业政策只有方向性时，不能替代单股暴露度和财报证据。",
        "candidate_status": "pending_human_review",
    },
    {
        "stock": {"name": "浙商中拓", "code": "000906"},
        "review_observation": "经营现金流缺口应优先于市场风格描述。",
        "review_field": "missing_not_exposed",
        "experience_candidate": "供应链周期股的经营现金流缺口优先级不得低于P0。",
        "candidate_status": "pending_human_review",
    },
    {
        "stock": {"name": "正丹股份", "code": "300641"},
        "review_observation": "产品价格和利润弹性之间的关系需要更清楚。",
        "review_field": "user_readability_issue",
        "experience_candidate": "化工股前台短答应把产品价格、价差、利润弹性用一句话串联。",
        "candidate_status": "pending_human_review",
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "复盘字段到经验候选映射样例",
        "version": "v1.0",
        "generated_at": generated_at,
        "asset_identity": "W1复盘字段到经验候选映射样例",
        "status": "shadow_review_to_candidate_sample",
        "not_formal_rule_write": True,
        "not_formal_config": True,
        "not_entrypoint": True,
        "mapping_rules": MAPPING_RULES,
        "samples": SAMPLES,
        "promotion_gate": {
            "requires_human_review": True,
            "requires_multi_case_validation": True,
            "min_case_count_before_rule_candidate_upgrade": 3,
            "auto_update_formal_rule_allowed": False,
        },
        "summary": {
            "mapping_rule_count": len(MAPPING_RULES),
            "sample_count": len(SAMPLES),
            "all_candidates_pending_human_review": True,
            "auto_update_formal_rule_allowed": False,
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
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 复盘字段到经验候选映射样例",
        "",
        f"- 生成时间：{generated_at}",
        "- 资产身份：W1复盘字段到经验候选映射样例",
        "- 状态：shadow_review_to_candidate_sample",
        "- 边界：不自动改正式规则。",
        "",
        "## 样本",
        "",
    ]
    for item in SAMPLES:
        lines.append(f"- {item['stock']['name']}（{item['stock']['code']}）：{item['experience_candidate']}（{item['candidate_status']}）")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
