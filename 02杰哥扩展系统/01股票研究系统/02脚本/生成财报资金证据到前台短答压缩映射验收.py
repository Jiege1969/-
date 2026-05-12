# -*- coding: utf-8 -*-
"""生成财报/资金证据到前台短答压缩映射验收样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "财报资金证据到前台短答压缩映射验收_最新.json"
MD_OUT = DATA_DIR / "财报资金证据到前台短答压缩映射验收_最新.md"


RECORDS = [
    {
        "stock": {"name": "云南锗业", "code": "002428"},
        "backend_evidence": {"financial": "财报结构化摘要待补", "capital": "资金承接证据待补"},
        "front_phrase": "财报和资金证据尚未补齐，因此当前只能作为资源主题观察，不能把技术信号扩展成全面判断。",
        "missing": ["最新财报结构化摘要", "主力资金/机构变化"],
    },
    {
        "stock": {"name": "天齐锂业", "code": "002466"},
        "backend_evidence": {"financial": "盈利修复证据待补", "capital": "资金趋势待补"},
        "front_phrase": "基本面修复还要等财报和资金证据确认，当前结论以观察为主。",
        "missing": ["盈利修复拆解", "资金趋势"],
    },
    {
        "stock": {"name": "华虹公司", "code": "688347"},
        "backend_evidence": {"financial": "毛利率趋势待补", "capital": "机构资金变化待补"},
        "front_phrase": "半导体方向有研究价值，但财报质量和机构资金还没形成充分证据。",
        "missing": ["毛利率趋势", "机构资金变化"],
    },
    {
        "stock": {"name": "浙商中拓", "code": "000906"},
        "backend_evidence": {"financial": "经营现金流待补", "capital": "资金承接待补"},
        "front_phrase": "经营现金流和资金承接证据不足，当前不适合给强结论。",
        "missing": ["经营现金流", "资金承接"],
    },
    {
        "stock": {"name": "正丹股份", "code": "300641"},
        "backend_evidence": {"financial": "利润弹性待补", "capital": "承接强弱待补"},
        "front_phrase": "化工景气需要产品价格和财报利润弹性共同确认，资金承接还需复核。",
        "missing": ["利润弹性", "资金承接强弱"],
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "财报资金证据到前台短答压缩映射验收",
        "version": "v1.0",
        "generated_at": generated_at,
        "asset_identity": "W1财报资金证据到前台短答压缩映射验收",
        "status": "shadow_mapping_acceptance",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_score_write": True,
        "records": RECORDS,
        "mapping_rules": [
            "后台保留证据字段，前台只输出结论依据和关键缺口。",
            "财报或资金缺失时，不允许把技术面判断包装成全面研究结论。",
            "缺口必须进入missing，且影响confidence上限。",
        ],
        "summary": {
            "sample_count": len(RECORDS),
            "all_front_phrases_conclusion_oriented": True,
            "all_missing_explicit": True,
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
        "# 财报资金证据到前台短答压缩映射验收",
        "",
        f"- 生成时间：{generated_at}",
        "- 资产身份：W1财报资金证据到前台短答压缩映射验收",
        "- 状态：shadow_mapping_acceptance",
        "",
    ]
    for item in RECORDS:
        lines.append(f"- {item['stock']['name']}（{item['stock']['code']}）：{item['front_phrase']}")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
