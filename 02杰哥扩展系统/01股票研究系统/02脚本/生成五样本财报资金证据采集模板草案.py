# -*- coding: utf-8 -*-
"""
生成五样本财报/资金证据采集模板草案。

只生成 W1 空白采集模板，不抓取真实数据、不写正式库、不改评分、不触发外发。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ROUTE_PATH = DATA_DIR / "五样本财报资金证据补齐路线图_最新.json"
JSON_OUT = DATA_DIR / "五样本财报资金证据采集模板草案_最新.json"
MD_OUT = DATA_DIR / "五样本财报资金证据采集模板草案_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def blank_value(field_name: str) -> dict[str, Any]:
    return {
        "value": None,
        "source_name": None,
        "source_url": None,
        "as_of_date": None,
        "evidence_status": "missing",
        "review_status": "pending_review",
        "note": f"{field_name} 待填；未填前不得进入评分。",
    }


def build_template_for_group(group: dict[str, Any]) -> dict[str, Any]:
    return {
        "field_group": group["field_group"],
        "display_name": group["display_name"],
        "priority": group["priority"],
        "minimum_ready_condition": group["minimum_ready_condition"],
        "front_gap_wording": group["front_gap_wording"],
        "score_status": "not_scored_until_evidence_ready",
        "fields": {field: blank_value(field) for field in group["fields"]},
        "ready_check": {
            "ready": False,
            "reason": "模板为空白草案，尚未采集任何真实证据。",
            "required_before_scoring": group["fields"][: min(5, len(group["fields"]))],
        },
    }


def build_asset() -> dict[str, Any]:
    route = load_json(ROUTE_PATH)
    templates = []
    for stock_route in route.get("stock_routes", []):
        stock = stock_route.get("stock", {})
        templates.append(
            {
                "stock": stock,
                "asset_identity": "W1空白采集模板",
                "status": "draft",
                "stock_specific_fields": {
                    item: blank_value(item) for item in stock_route.get("stock_specific_fields", [])
                },
                "evidence_groups": [
                    build_template_for_group(group)
                    for group in stock_route.get("evidence_groups", [])
                ],
                "front_answer_constraint": stock_route.get("front_answer_rule"),
                "overall_ready": False,
                "overall_score_status": "not_scored_until_evidence_ready",
            }
        )

    return {
        "name": "五样本财报资金证据采集模板草案",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1空白采集模板草案",
        "status": "draft",
        "source_assets": {
            "route_map": str(ROUTE_PATH),
            "route_map_exists": bool(route),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "not_real_data_fetch": True,
        "not_formal_database_write": True,
        "templates": templates,
        "summary": {
            "sample_count": len(templates),
            "group_count": sum(len(item["evidence_groups"]) for item in templates),
            "blank_field_count": sum(
                len(group["fields"]) + len(item["stock_specific_fields"])
                for item in templates
                for group in item["evidence_groups"]
            ),
            "ready_count": 0,
        },
        "input_rules": [
            "每个字段必须有 value、source_name、source_url、as_of_date、evidence_status、review_status。",
            "evidence_status 只能从 missing 变为 candidate，再经人工或规则验收变为 evidence_ready。",
            "未达到 evidence_ready 前不得进入 L3 评分。",
            "字段可以人工填写或后续只读采集，但本模板不抓取真实数据。",
        ],
        "quality_gates": [
            "五个样本均必须生成采集模板。",
            "每个样本必须覆盖财报摘要、估值位置、资金流向、机构持仓、解禁/减持。",
            "所有字段默认 missing，不能预填假数据或示例值冒充证据。",
            "必须保留 source_name、source_url、as_of_date 和 review_status。",
            "不得写企业微信入口、正式库、评分结果或交易能力。",
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
            "not_real_data_fetch": True,
        },
    }


def write_markdown(asset: dict[str, Any]) -> None:
    lines = [
        "# 五样本财报资金证据采集模板草案",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：W1 空白模板，不抓取真实数据，不写正式库，不改评分，不接企业微信入口。",
        "",
        "## 汇总",
        "",
        f"- 样本数：{asset['summary']['sample_count']}",
        f"- 证据组数：{asset['summary']['group_count']}",
        f"- 空白字段数：{asset['summary']['blank_field_count']}",
        f"- ready 数：{asset['summary']['ready_count']}",
        "",
        "## 样本模板",
        "",
    ]
    for item in asset["templates"]:
        stock = item["stock"]
        lines.extend(
            [
                f"### {stock.get('name')}（{stock.get('code')}）",
                "",
                f"- overall_ready：{item['overall_ready']}",
                f"- overall_score_status：{item['overall_score_status']}",
                f"- 股票特有字段：{'；'.join(item['stock_specific_fields'].keys())}",
                "",
            ]
        )
        for group in item["evidence_groups"]:
            lines.extend(
                [
                    f"- {group['display_name']}（{group['field_group']}）：{len(group['fields'])} 个字段，{group['score_status']}",
                    f"  - ready 条件：{group['minimum_ready_condition']}",
                    f"  - 前台缺口话术：{group['front_gap_wording']}",
                ]
            )
    lines.extend(["", "## 输入规则", ""])
    lines.extend([f"- {item}" for item in asset["input_rules"]])
    lines.extend(["", "## 下一步自动推进", ""])
    lines.append("- 继续生成“财报资金证据采集模板草案验收”后，可进入“统一刷新验收清单”或“资金证据人工填写回执模板”。")
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    asset = build_asset()
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({"status": "ok", "json": str(JSON_OUT), "md": str(MD_OUT), "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
