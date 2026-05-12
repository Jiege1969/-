# -*- coding: utf-8 -*-
"""生成政策事件候选到前台表述约束验收样例。

仅生成股票线W1影子约束，不写正式政策库、不改L3正式评分。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "政策事件候选到前台表述约束验收_最新.json"
MD_OUT = DATA_DIR / "政策事件候选到前台表述约束验收_最新.md"


CONSTRAINTS = [
    {
        "status": "candidate_unverified",
        "front_allowed_phrase": "政策线索待核实，只能作为后续复核重点。",
        "front_forbidden_phrase": "政策已经构成确定性利好。",
        "score_permission": "not_allowed",
    },
    {
        "status": "source_verified_exposure_pending",
        "front_allowed_phrase": "政策来源已确认，但单股暴露度仍待复核。",
        "front_forbidden_phrase": "该股票确定充分受益。",
        "score_permission": "partial_or_pending",
    },
    {
        "status": "verified_with_exposure",
        "front_allowed_phrase": "政策证据已匹配，仍需结合财报、行业价格和市场风格确认。",
        "front_forbidden_phrase": "只因政策即可给强结论。",
        "score_permission": "allowed_by_contract",
    },
]


SAMPLES = [
    {
        "stock": {"name": "云南锗业", "code": "002428"},
        "policy_candidate": "锗相关出口管制政策",
        "status": "source_verified_exposure_pending",
        "front_phrase": "政策来源可作为研究依据，但单股暴露度和时效衰减仍要复核，不能单靠政策给强结论。",
        "backend_missing": ["stock_exposure", "decay_factor_review", "source_url_final_check"],
    },
    {
        "stock": {"name": "天齐锂业", "code": "002466"},
        "policy_candidate": "新能源/锂电产业支持政策",
        "status": "candidate_unverified",
        "front_phrase": "相关政策目前只能作为行业线索，需先确认政策来源、影响方向和公司暴露度。",
        "backend_missing": ["source_url", "impact_direction", "stock_exposure"],
    },
    {
        "stock": {"name": "华虹公司", "code": "688347"},
        "policy_candidate": "半导体国产化政策",
        "status": "candidate_unverified",
        "front_phrase": "半导体政策方向具备研究价值，但未匹配到本股结构化政策证据前，只能列为复核重点。",
        "backend_missing": ["event_id", "source_url", "stock_exposure"],
    },
    {
        "stock": {"name": "浙商中拓", "code": "000906"},
        "policy_candidate": "供应链/大宗商品流通政策",
        "status": "candidate_unverified",
        "front_phrase": "政策关联度还不清晰，当前不能把政策作为主要判断依据。",
        "backend_missing": ["industry_match", "event_strength", "stock_exposure"],
    },
    {
        "stock": {"name": "正丹股份", "code": "300641"},
        "policy_candidate": "化工安全环保或出口相关政策",
        "status": "candidate_unverified",
        "front_phrase": "政策线索需要先确认具体文件和影响方向，未核实前只进入待补证据。",
        "backend_missing": ["source_url", "impact_direction", "valid_until"],
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "政策事件候选到前台表述约束验收",
        "version": "v1.0",
        "generated_at": generated_at,
        "asset_identity": "W1政策事件候选到前台表述约束验收",
        "status": "shadow_expression_gate",
        "not_formal_policy_database": True,
        "not_formal_config": True,
        "not_score_write": True,
        "constraints": CONSTRAINTS,
        "samples": SAMPLES,
        "global_rules": [
            "政策候选不得直接作为确定性结论。",
            "未核实来源、暴露度、强度、时效衰减前，不得进入正式政策分。",
            "前台表达必须区分线索、已核实来源、已匹配暴露度三类状态。",
        ],
        "summary": {
            "constraint_count": len(CONSTRAINTS),
            "sample_count": len(SAMPLES),
            "formal_policy_database_write_allowed": False,
            "formal_score_update_allowed": False,
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
        "# 政策事件候选到前台表述约束验收",
        "",
        f"- 生成时间：{generated_at}",
        "- 资产身份：W1政策事件候选到前台表述约束验收",
        "- 状态：shadow_expression_gate",
        "- 边界：不写正式政策库，不改L3正式评分。",
        "",
        "## 样本",
        "",
    ]
    for item in SAMPLES:
        lines.append(f"- {item['stock']['name']}（{item['stock']['code']}）：{item['front_phrase']}")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
