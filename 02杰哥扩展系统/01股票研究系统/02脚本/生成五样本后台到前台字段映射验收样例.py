# -*- coding: utf-8 -*-
"""
生成五样本后台到前台字段映射验收样例。

本脚本只在股票线目录内生成 W1 样例资产，不写企业微信入口、不外发、
不改正式适配器、不改评分规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
MAPPING_PATH = DATA_DIR / "后台证据链到前台短答字段映射草案_最新.json"
SAMPLE_PATH = DATA_DIR / "五样本前台结论型短答修订样例_最新.json"
JSON_OUT = DATA_DIR / "五样本后台到前台字段映射验收样例_最新.json"
MD_OUT = DATA_DIR / "五样本后台到前台字段映射验收样例_最新.md"


EVIDENCE_TRACE = {
    "sz002428": {
        "policy_events": "锗出口管制政策事件已结构化匹配，可进入主要原因。",
        "fundamentals_capital": "资金/机构/解禁证据仍待采集，进入关键缺口。",
        "industry_price_observation": "锗价/景气尚未入账，进入关键缺口。",
        "market_style_fit": "市场风格字段未在短答中强化，需后台继续承接。",
        "technical_structure": "技术结构未作为前台主因展开，避免前台堆指标。",
    },
    "sz002466": {
        "policy_events": "未匹配直接结构化政策，政策项不能加分。",
        "fundamentals_capital": "资金/机构/解禁证据仍待采集，进入关键缺口。",
        "industry_price_observation": "碳酸锂价格/景气观测点不足，不能写趋势确认。",
        "market_style_fit": "市场风格字段未在短答中强化，需后台继续承接。",
        "technical_structure": "技术结构未作为前台主因展开，避免前台堆指标。",
    },
    "sh688347": {
        "policy_events": "半导体政策背景存在，但尚未结构化到单股事件。",
        "fundamentals_capital": "资金/机构/解禁证据仍待采集，进入关键缺口。",
        "industry_price_observation": "晶圆代工景气观测点不足，不能写趋势确认。",
        "market_style_fit": "市场风格字段未在短答中强化，需后台继续承接。",
        "technical_structure": "技术结构未作为前台主因展开，避免前台堆指标。",
    },
    "sz000906": {
        "policy_events": "没有匹配到直接结构化政策，不能写政策支撑。",
        "fundamentals_capital": "财报质量、资金证据仍待补，进入复核重点。",
        "industry_price_observation": "供应链景气尚未形成连续观测，进入关键缺口。",
        "market_style_fit": "市场风格字段未在短答中强化，需后台继续承接。",
        "technical_structure": "技术结构未作为前台主因展开，避免前台堆指标。",
    },
    "sz300641": {
        "policy_events": "未匹配直接结构化政策，政策项不能加分。",
        "fundamentals_capital": "财报摘要和资金证据仍待补，进入关键缺口。",
        "industry_price_observation": "TMA价格/景气观测点不足，不能写趋势确认。",
        "market_style_fit": "市场风格字段未在短答中强化，需后台继续承接。",
        "technical_structure": "技术结构未作为前台主因展开，避免前台堆指标。",
    },
}


FIELD_BACKEND_TRACE = {
    "object_line": ["stock_identity.name", "stock_identity.code"],
    "conclusion_line": ["l3_score.conclusion_text", "missing_summary", "confidence.level"],
    "main_reason_line": ["policy_events", "industry_price_observation", "fundamentals_capital", "market_style_fit"],
    "key_gap_line": ["item_scores.*.missing", "policy_event_match.status", "industry_price_observation.status", "capital_institution_unlock_card.status"],
    "confidence_review_line": ["confidence.level", "missing_summary", "next_review_date"],
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def line_by_prefix(lines: list[str], prefix: str) -> str:
    return next((line for line in lines if line.startswith(prefix)), "")


def field_checks(sample: dict[str, Any]) -> dict[str, Any]:
    stock = sample.get("stock", {})
    name = stock.get("name", "")
    code = stock.get("code", "")
    lines = sample.get("front_answer", [])
    text = "\n".join(lines)
    trace = EVIDENCE_TRACE.get(code, {})
    return {
        "object_line": {
            "front_value": lines[0] if lines else "",
            "backend_trace": FIELD_BACKEND_TRACE["object_line"],
            "evidence_status": "ready" if lines and lines[0] == f"{name}（{code}）" else "missing",
            "gap_carried": False,
            "passed": bool(lines and lines[0] == f"{name}（{code}）"),
        },
        "conclusion_line": {
            "front_value": line_by_prefix(lines, "结论："),
            "backend_trace": FIELD_BACKEND_TRACE["conclusion_line"],
            "evidence_status": "guarded_by_missing",
            "gap_carried": any(term in text for term in ["不能", "暂不", "可观察", "待"]),
            "passed": "结论：" in text and any(term in text for term in ["可纳入观察", "可观察", "暂不建议", "暂不强化"]),
        },
        "main_reason_line": {
            "front_value": line_by_prefix(lines, "主要原因："),
            "backend_trace": FIELD_BACKEND_TRACE["main_reason_line"],
            "evidence_status": "mixed_ready_and_missing",
            "evidence_trace_detail": trace,
            "gap_carried": any(term in text for term in ["未匹配", "尚未结构化", "待采集", "不足", "尚未"]),
            "passed": "主要原因：" in text and len(line_by_prefix(lines, "主要原因：")) >= 12,
        },
        "key_gap_line": {
            "front_value": line_by_prefix(lines, "关键缺口："),
            "backend_trace": FIELD_BACKEND_TRACE["key_gap_line"],
            "evidence_status": "missing_explicit",
            "gap_carried": any(term in line_by_prefix(lines, "关键缺口：") for term in ["待采集", "未匹配", "不足", "尚未", "需要补齐", "待补"]),
            "passed": "关键缺口：" in text and any(term in line_by_prefix(lines, "关键缺口：") for term in ["待采集", "不足", "尚未", "需要补齐", "待补"]),
        },
        "confidence_review_line": {
            "front_value": line_by_prefix(lines, "置信度："),
            "backend_trace": FIELD_BACKEND_TRACE["confidence_review_line"],
            "evidence_status": "confidence_present",
            "gap_carried": any(term in line_by_prefix(lines, "置信度：") for term in ["复核", "重点看", "补上", "证据"]),
            "passed": "置信度：" in text and "复核" in text,
        },
    }


def build_asset() -> dict[str, Any]:
    mapping = load_json(MAPPING_PATH)
    samples_asset = load_json(SAMPLE_PATH)
    samples = samples_asset.get("samples", [])

    sample_mappings = []
    for sample in samples:
        checks = field_checks(sample)
        sample_mappings.append(
            {
                "stock": sample.get("stock", {}),
                "field_checks": checks,
                "passed": all(item.get("passed") for item in checks.values()),
                "gap_line_present": checks["key_gap_line"]["gap_carried"],
                "backend_trace_present": all(item.get("backend_trace") for item in checks.values()),
            }
        )

    return {
        "name": "五样本后台到前台字段映射验收样例",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1字段映射验收样例",
        "status": "draft",
        "source_assets": {
            "mapping_contract": str(MAPPING_PATH),
            "front_answer_samples": str(SAMPLE_PATH),
            "mapping_contract_exists": bool(mapping),
            "front_answer_samples_exists": bool(samples_asset),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "sample_mappings": sample_mappings,
        "summary": {
            "sample_count": len(sample_mappings),
            "pass_count": sum(1 for item in sample_mappings if item["passed"]),
            "needs_revision_count": sum(1 for item in sample_mappings if not item["passed"]),
            "front_field_count_per_sample": 5,
        },
        "formalization_blockers": [
            {
                "action": "将字段映射验收样例写入企业微信短答适配器或正式入口",
                "risk_level": "W3",
                "handling": "只登记阻断，不实施；交回总管判断。",
            },
            {
                "action": "触发真实外发、n8n、服务重启、19310或真实账号",
                "risk_level": "W3",
                "handling": "停止实施，只登记阻断原因。",
            },
            {
                "action": "新增买入、卖出、下单、仓位调整、券商接口或自动交易",
                "risk_level": "W3",
                "handling": "禁止新增；股票线保持研究分析系统定位。",
            },
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
        },
    }


def write_markdown(asset: dict[str, Any]) -> None:
    lines = [
        "# 五样本后台到前台字段映射验收样例",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：W1 验收样例，不写企业微信入口，不真实外发，不改正式适配器。",
        "",
        "## 汇总",
        "",
        f"- 样本数：{asset['summary']['sample_count']}",
        f"- 通过：{asset['summary']['pass_count']}",
        f"- 待修：{asset['summary']['needs_revision_count']}",
        "",
        "## 样本映射",
        "",
    ]
    for sample in asset["sample_mappings"]:
        stock = sample["stock"]
        lines.extend(
            [
                f"### {stock.get('name')}（{stock.get('code')}）",
                "",
                f"- 样本结论：{'通过' if sample['passed'] else '待修'}",
                f"- 后台来源存在：{sample['backend_trace_present']}",
                f"- 缺口承接存在：{sample['gap_line_present']}",
                "",
            ]
        )
        for field_name, check in sample["field_checks"].items():
            lines.extend(
                [
                    f"- {field_name}：{'通过' if check['passed'] else '待修'}",
                    f"  - 前台值：{check['front_value']}",
                    f"  - 后台来源：{'；'.join(check['backend_trace'])}",
                    f"  - 证据状态：{check['evidence_status']}",
                ]
            )
    lines.extend(["", "## 下一步建议", ""])
    lines.append("- 可继续生成“字段映射缺口修复队列”，把本样例发现的问题转成待补队列；若全部通过，则转向财报/资金证据补齐。")
    lines.append("- 写入正式企业微信入口、适配器、服务或配置属于 W3，本轮不实施。")
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
