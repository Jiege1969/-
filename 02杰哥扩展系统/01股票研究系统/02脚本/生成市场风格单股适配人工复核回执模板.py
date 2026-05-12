# -*- coding: utf-8 -*-
"""
生成市场风格单股适配人工复核回执模板。

市场风格日表可以作为环境证据，但不能自动等同于单股适配分。
本脚本只生成 W1 复核模板，不改正式评分，不触发外发。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
STYLE_SOURCE = DATA_DIR / "market_style_daily_latest.json"
JSON_OUT = DATA_DIR / "市场风格单股适配人工复核回执模板_最新.json"
MD_OUT = DATA_DIR / "市场风格单股适配人工复核回执模板_最新.md"

SAMPLE_STOCKS = [
    {
        "name": "云南锗业",
        "code": "sz002428",
        "stock_type_tags": ["资源股", "稀有金属", "半导体材料", "小盘弹性"],
        "style_focus": ["风险偏好", "有色/稀有金属板块热度", "小盘风格", "成交活跃度"],
    },
    {
        "name": "天齐锂业",
        "code": "sz002466",
        "stock_type_tags": ["资源股", "新能源材料", "锂盐", "周期弹性"],
        "style_focus": ["风险偏好", "新能源材料板块热度", "资源周期热度", "成交活跃度"],
    },
    {
        "name": "华虹公司",
        "code": "sh688347",
        "stock_type_tags": ["半导体", "晶圆代工", "科创板", "成长风格"],
        "style_focus": ["科技成长热度", "半导体板块热度", "大小盘风格", "风险偏好"],
    },
    {
        "name": "浙商中拓",
        "code": "sz000906",
        "stock_type_tags": ["大宗供应链", "周期服务", "低估值", "国企"],
        "style_focus": ["大宗商品景气", "低估值风格", "成交活跃度", "市场风险偏好"],
    },
    {
        "name": "正丹股份",
        "code": "sz300641",
        "stock_type_tags": ["化工", "TMA", "周期弹性", "主题弹性"],
        "style_focus": ["化工板块热度", "TMA主题热度", "小盘风格", "风险偏好"],
    },
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def style_snapshot(style: dict[str, Any]) -> dict[str, Any]:
    return {
        "date": style.get("date"),
        "status": style.get("status", "missing"),
        "risk_appetite_score": style.get("risk_appetite", {}).get("score"),
        "top_sectors": style.get("sector_heat", {}).get("top_sectors", [])[:5],
        "bottom_sectors": style.get("sector_heat", {}).get("bottom_sectors", [])[:5],
        "size_style_dominant": style.get("size_style", {}).get("dominant"),
        "liquidity_percentile": style.get("liquidity", {}).get("total_amount_rank_percentile"),
        "final_adaptation_score": style.get("final_adaptation_score"),
        "moderate_coefficient": style.get("moderate_coefficient"),
        "missing_summary": style.get("missing_summary"),
    }


def build_receipt(stock: dict[str, Any], style: dict[str, Any]) -> dict[str, Any]:
    daily_status = style.get("status", "missing")
    return {
        "stock": {"name": stock["name"], "code": stock["code"]},
        "stock_type_tags": stock["stock_type_tags"],
        "style_focus": stock["style_focus"],
        "daily_style_source": str(STYLE_SOURCE),
        "daily_style_status": daily_status,
        "receipt_status": "blank",
        "review_fields": {
            "risk_appetite_fit": {
                "value": None,
                "allowed_values": ["positive", "neutral", "negative"],
                "evidence_status": "missing",
                "review_status": "pending_review",
            },
            "sector_heat_fit": {
                "value": None,
                "allowed_values": ["positive", "neutral", "negative"],
                "evidence_status": "missing",
                "review_status": "pending_review",
            },
            "size_style_fit": {
                "value": None,
                "allowed_values": ["positive", "neutral", "negative"],
                "evidence_status": "missing",
                "review_status": "pending_review",
            },
            "liquidity_fit": {
                "value": None,
                "allowed_values": ["positive", "neutral", "negative"],
                "evidence_status": "missing",
                "review_status": "pending_review",
            },
            "stock_style_fit_score": {
                "value": None,
                "range": [0, 20],
                "evidence_status": "missing",
                "review_status": "pending_review",
            },
        },
        "ready_review": {
            "style_fit_ready": False,
            "score_ready": False,
            "ready_condition": "市场风格日表有效，且四个单股适配字段均有证据和人工复核后，才可进入L3市场风格适配分。",
            "blocking_reason": "缺少单股风格适配复核，不能仅凭市场整体强弱提高个股结论。",
        },
        "front_output_rule": {
            "when_missing": "市场风格日表可作背景，但该股风格适配尚未复核，前台只能写环境参考，不能写强适配结论。",
            "when_ready": "输出一句结论型环境适配判断，并保留后台证据链。",
        },
    }


def build_asset() -> dict[str, Any]:
    style = load_json(STYLE_SOURCE)
    receipts = [build_receipt(stock, style) for stock in SAMPLE_STOCKS]
    return {
        "name": "市场风格单股适配人工复核回执模板",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1市场风格单股适配复核模板",
        "status": "blank_template",
        "style_daily_snapshot": style_snapshot(style),
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "not_formal_database_write": True,
        "receipts": receipts,
        "review_rules": [
            "市场风格日表只能说明市场环境，不能自动推出单股适配结论。",
            "单股适配必须同时看风险偏好、板块热度、大小盘风格和成交活跃度。",
            "任一核心适配字段缺证据时，stock_style_fit_score不得填写。",
            "前台输出应给结论性短答；证据和缺口保留在后台，不堆指标。",
            "本模板不改正式评分、不接企业微信、不触发n8n、不外发。",
        ],
        "summary": {
            "receipt_count": len(receipts),
            "stock_count": len(receipts),
            "daily_style_status": style.get("status", "missing"),
            "style_fit_ready_count": 0,
            "score_allowed_count": 0,
        },
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


def write_markdown(asset: dict[str, Any]) -> None:
    style = asset["style_daily_snapshot"]
    lines = [
        "# 市场风格单股适配人工复核回执模板",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：W1复核模板，不改正式评分，不触发企业微信或n8n。",
        "",
        "## 市场风格日表快照",
        "",
        f"- 交易日：{style.get('date')}",
        f"- 日表状态：{style.get('status')}",
        f"- 风险偏好：{style.get('risk_appetite_score')}",
        f"- 大小盘风格：{style.get('size_style_dominant')}",
        f"- 流动性分位：{style.get('liquidity_percentile')}",
        f"- 通用市场风格分：{style.get('final_adaptation_score')}",
        "",
        "## 回执清单",
        "",
    ]
    for item in asset["receipts"]:
        stock = item["stock"]
        lines.append(
            f"- {stock['name']}（{stock['code']}）："
            f"关注 {', '.join(item['style_focus'])}；style_fit_ready={item['ready_review']['style_fit_ready']}"
        )
    lines.extend(["", "## 复核规则", ""])
    lines.extend([f"- {rule}" for rule in asset["review_rules"]])
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
