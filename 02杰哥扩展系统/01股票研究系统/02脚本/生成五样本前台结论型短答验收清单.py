# -*- coding: utf-8 -*-
"""
生成五样本前台结论型短答验收清单。

本脚本只生成 W1 验收清单，用于检查股票助手前台回答是否更像使用者需要的
结论型短答；不写企业微信入口，不外发，不改正式适配器。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
PREVIEW_PATH = DATA_DIR / "五样本前台缺口压缩预演_最新.json"
RULE_PATH = DATA_DIR / "前台缺口话术规则草案_最新.json"
JSON_OUT = DATA_DIR / "五样本前台结论型短答验收清单_最新.json"
MD_OUT = DATA_DIR / "五样本前台结论型短答验收清单_最新.md"

SAMPLES = [
    {"name": "云南锗业", "code": "sz002428"},
    {"name": "天齐锂业", "code": "sz002466"},
    {"name": "华虹公司", "code": "sh688347"},
    {"name": "浙商中拓", "code": "sz000906"},
    {"name": "正丹股份", "code": "sz300641"},
]

TRADE_TERMS = ["买入", "卖出", "加仓", "减仓", "下单", "仓位调整", "自动交易", "券商接口"]
OVERCLAIM_TERMS = ["确认受益", "确定上涨", "明确买点", "无风险", "强烈推荐", "闭眼关注"]
GAP_TERMS = [
    "待采集",
    "不能强化结论",
    "未匹配直接结构化政策",
    "政策项不能加分",
    "尚未结构化",
    "证据待补",
    "观测点不足",
    "不能写趋势确认",
    "缺口",
    "missing",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "\n".join(stringify(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{key}: {stringify(val)}" for key, val in value.items())
    return str(value)


def find_text_for_stock(data: Any, stock: dict[str, str]) -> str:
    matches: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            text_blob = stringify(node)
            if stock["name"] in text_blob or stock["code"] in text_blob:
                matches.append(text_blob)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    if not matches:
        return ""
    matches.sort(key=len)
    return matches[0]


def first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        clean = line.strip()
        if clean:
            return clean
    return ""


def build_sample_check(stock: dict[str, str], text: str, rules: list[dict[str, Any]]) -> dict[str, Any]:
    first_line = first_non_empty_line(text)
    rule_wordings = [rule.get("recommended_wording", "") for rule in rules]
    rule_hits = [wording for wording in rule_wordings if wording and wording in text]
    prohibited_hits = [term for term in TRADE_TERMS if term in text]
    overclaim_hits = [term for term in OVERCLAIM_TERMS if term in text]

    checks = {
        "object_first_line": stock["name"] in first_line and stock["code"] in first_line,
        "conclusion_first": any(word in text[:160] for word in ["结论", "观察", "暂不", "重点关注", "可纳入观察"]),
        "evidence_gap_explicit": any(term in text for term in GAP_TERMS),
        "rule_wording_hit": len(rule_hits) > 0,
        "no_trade_terms": len(prohibited_hits) == 0,
        "no_overclaim_when_missing": len(overclaim_hits) == 0,
        "front_readability": 0 < len(text) <= 1800,
    }

    return {
        "stock": stock,
        "source_text_length": len(text),
        "first_line": first_line,
        "checks": checks,
        "rule_wording_hits": rule_hits,
        "prohibited_trade_terms": prohibited_hits,
        "overclaim_terms": overclaim_hits,
        "result": "pass" if all(checks.values()) else "needs_revision",
        "revision_hint": build_revision_hint(stock, checks),
    }


def build_revision_hint(stock: dict[str, str], checks: dict[str, bool]) -> str:
    hints: list[str] = []
    if not checks["object_first_line"]:
        hints.append(f"第一行改为明确对象：{stock['name']}（{stock['code']}）。")
    if not checks["conclusion_first"]:
        hints.append("开头先给结论词，不先堆指标。")
    if not checks["evidence_gap_explicit"]:
        hints.append("缺财报、资金、政策、行业价格或市场风格证据时必须一句话标明缺口。")
    if not checks["rule_wording_hit"]:
        hints.append("套用已生成的缺口话术规则，避免临场发挥。")
    if not checks["no_trade_terms"]:
        hints.append("删除买卖、下单、仓位或交易执行相关话术。")
    if not checks["no_overclaim_when_missing"]:
        hints.append("证据缺失时删除强确定性表达。")
    if not checks["front_readability"]:
        hints.append("压缩为前台可读短答，后台证据链另存。")
    return "；".join(hints) if hints else "通过，可作为前台短答样例继续观察。"


def build_asset() -> dict[str, Any]:
    preview = load_json(PREVIEW_PATH)
    rule_asset = load_json(RULE_PATH)
    rules = rule_asset.get("rules", [])

    sample_checks = []
    for stock in SAMPLES:
        text = find_text_for_stock(preview, stock)
        sample_checks.append(build_sample_check(stock, text, rules))

    return {
        "name": "五样本前台结论型短答验收清单",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1验收清单",
        "status": "draft",
        "source_assets": {
            "preview": str(PREVIEW_PATH),
            "wording_rules": str(RULE_PATH),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "acceptance_contract": [
            "第一行必须明确股票名称和代码。",
            "前台先给结论，不把后台分析过程原样堆给用户。",
            "依据只保留关键原因，后台证据链另存。",
            "证据缺失必须显式标注缺口，不得用空值或横杠冒充判断。",
            "L3 评分和政策/市场风格判断必须读取结构化证据，不得由模型凭空补分。",
            "不得出现买入、卖出、下单、仓位调整、自动交易或券商接口能力。",
        ],
        "sample_checks": sample_checks,
        "summary": {
            "sample_count": len(sample_checks),
            "pass_count": sum(1 for item in sample_checks if item["result"] == "pass"),
            "needs_revision_count": sum(1 for item in sample_checks if item["result"] != "pass"),
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
    lines = [
        "# 五样本前台结论型短答验收清单",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：只验收样本短答，不写企业微信入口，不真实外发，不改正式适配器。",
        "",
        "## 验收契约",
        "",
    ]
    lines.extend([f"- {item}" for item in asset["acceptance_contract"]])
    lines.extend(
        [
            "",
            "## 样本结果",
            "",
            f"- 样本数：{asset['summary']['sample_count']}",
            f"- 通过：{asset['summary']['pass_count']}",
            f"- 待修：{asset['summary']['needs_revision_count']}",
            "",
        ]
    )

    for item in asset["sample_checks"]:
        stock = item["stock"]
        lines.extend(
            [
                f"### {stock['name']}（{stock['code']}）",
                "",
                f"- 结果：{item['result']}",
                f"- 第一行：{item['first_line'] or '未识别'}",
                f"- 规则命中：{len(item['rule_wording_hits'])}",
                f"- 交易词命中：{item['prohibited_trade_terms'] or '无'}",
                f"- 强结论词命中：{item['overclaim_terms'] or '无'}",
                f"- 修正提示：{item['revision_hint']}",
                "",
            ]
        )
        for key, value in item["checks"].items():
            lines.append(f"  - {key}：{value}")
        lines.append("")

    lines.extend(
        [
            "## 下一步建议",
            "",
            "- 可继续生成“五样本前台结论型短答修订样例”，只在样本资产中重写短答，不接企业微信真实入口。",
            "- 若要把短答规则写入企业微信适配器或正式入口，升级为 W3 阻断并交回总管判断。",
            "",
        ]
    )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    asset = build_asset()
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({"status": "ok", "json": str(JSON_OUT), "md": str(MD_OUT), "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
