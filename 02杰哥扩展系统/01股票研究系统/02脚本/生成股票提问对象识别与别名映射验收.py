# -*- coding: utf-8 -*-
"""生成股票提问对象识别与别名映射验收。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "股票提问对象识别与别名映射验收_最新.json"
MD_OUT = DATA_DIR / "股票提问对象识别与别名映射验收_最新.md"

SAMPLES = [
    {"canonical_name": "云南锗业", "code": "sz002428", "aliases": ["云南锗业", "002428", "锗业", "云南锗"], "query": "云南锗业现在怎么样"},
    {"canonical_name": "天齐锂业", "code": "sz002466", "aliases": ["天齐锂业", "002466", "天齐"], "query": "天齐锂业能看吗"},
    {"canonical_name": "华虹公司", "code": "sh688347", "aliases": ["华虹公司", "688347", "华虹"], "query": "华虹公司现在怎么样"},
    {"canonical_name": "浙商中拓", "code": "sz000906", "aliases": ["浙商中拓", "000906", "中拓"], "query": "浙商中拓怎么样"},
    {"canonical_name": "正丹股份", "code": "sz300641", "aliases": ["正丹股份", "300641", "正丹"], "query": "正丹股份现在怎么看"},
]


def build_asset() -> dict:
    records = []
    for item in SAMPLES:
        records.append({
            "query": item["query"],
            "matched_stock": {"name": item["canonical_name"], "code": item["code"]},
            "aliases": item["aliases"],
            "first_line_required": f"{item['canonical_name']}（{item['code']}）",
            "object_clear": True,
            "ambiguous": False,
            "requires_disambiguation": False,
            "front_output_blocking": {
                "if_ambiguous": "先澄清股票名称和代码，不生成分析结论。",
                "if_unmatched": "提示未识别到股票对象，不生成分析结论。",
            },
        })
    return {
        "name": "股票提问对象识别与别名映射验收",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1股票对象识别验收",
        "status": "shadow_acceptance",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "records": records,
        "rules": [
            "前台第一行必须明确股票名称和代码。",
            "未识别对象时不得输出分析结论。",
            "对象歧义时先澄清，不得猜测。",
            "别名只用于本地影子识别验收，不写正式路由。",
        ],
        "summary": {
            "sample_count": len(records),
            "object_clear_count": len([item for item in records if item["object_clear"]]),
            "ambiguous_count": len([item for item in records if item["ambiguous"]]),
            "formal_route_write_allowed": False,
            "real_wecom_send_allowed": False,
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


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    asset = build_asset()
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票提问对象识别与别名映射验收",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "",
        "## 样本",
        "",
    ]
    for item in asset["records"]:
        lines.append(f"- {item['query']} -> {item['first_line_required']}")
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
