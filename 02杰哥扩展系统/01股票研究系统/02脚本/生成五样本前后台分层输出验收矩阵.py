# -*- coding: utf-8 -*-
"""
生成五样本前后台分层输出验收矩阵。

目标：前台给用户结论型短答；后台保留 evidence/missing/confidence/next_review
等证据链，不把分析过程原样堆给用户。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
FRONT_SOURCE = DATA_DIR / "前台结论型短答统一验收记录_最新.json"
GATE_SOURCE = DATA_DIR / "L3报告生成前置闸口矩阵_最新.json"
JSON_OUT = DATA_DIR / "五样本前后台分层输出验收矩阵_最新.json"
MD_OUT = DATA_DIR / "五样本前后台分层输出验收矩阵_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def sample_record(sample: dict[str, Any]) -> dict[str, Any]:
    stock = sample.get("stock", {})
    checks = sample.get("checks", {})
    front_answer = sample.get("front_answer", [])
    return {
        "stock": stock,
        "front_layer": {
            "line_count": len(front_answer),
            "object_line_clear": checks.get("object_line") is True,
            "conclusion_line_present": checks.get("conclusion_line") is True,
            "main_reason_line_present": checks.get("main_reason_line") is True,
            "key_gap_line_present": checks.get("key_gap_line") is True,
            "confidence_line_present": checks.get("confidence_line") is True,
            "no_forbidden_terms": checks.get("no_forbidden_terms") is True,
            "allowed_for_shadow_front": sample.get("passed") is True,
        },
        "backend_layer": {
            "must_keep_evidence": True,
            "must_keep_missing": True,
            "must_keep_confidence": True,
            "must_keep_next_review": True,
            "must_keep_source_assets": True,
            "must_keep_gate_decisions": True,
        },
        "layering_rule": {
            "front_should_not_dump_indicators": True,
            "front_should_not_hide_key_gap": True,
            "backend_should_not_be_lost": True,
            "real_wecom_send_allowed": False,
        },
    }


def build_asset() -> dict[str, Any]:
    front = load_json(FRONT_SOURCE)
    gate = load_json(GATE_SOURCE)
    samples = front.get("sample_checks", [])
    matrix = [sample_record(item) for item in samples]
    return {
        "name": "五样本前后台分层输出验收矩阵",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1前后台分层输出验收矩阵",
        "status": "shadow_acceptance",
        "source_assets": {
            "front_short_answer": str(FRONT_SOURCE),
            "front_short_answer_exists": FRONT_SOURCE.exists(),
            "gate_matrix": str(GATE_SOURCE),
            "gate_matrix_exists": GATE_SOURCE.exists(),
            "gate_count": gate.get("summary", {}).get("gate_count"),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "matrix": matrix,
        "global_rules": {
            "front": [
                "第一行必须明确股票名称和代码。",
                "第二行先给结论。",
                "原因只写最关键的1-2条，不堆后台指标。",
                "关键缺口必须显式写出。",
                "置信度和复核重点必须保留。",
            ],
            "backend": [
                "保留evidence数组。",
                "保留missing数组。",
                "保留confidence理由。",
                "保留next_review_date或下一复核重点。",
                "保留闸口阻断原因。",
            ],
            "forbidden": [
                "前台堆技术指标",
                "后台证据链丢失",
                "缺口不写",
                "把影子短答说成真实企业微信已发送",
                "出现买卖、下单、仓位或交易执行话术",
            ],
        },
        "summary": {
            "sample_count": len(matrix),
            "front_passed_count": len([item for item in matrix if item["front_layer"]["allowed_for_shadow_front"]]),
            "backend_required_count": len(matrix),
            "real_wecom_send_allowed": False,
            "formal_entry_allowed": False,
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


def write_markdown(asset: dict[str, Any]) -> None:
    lines = [
        "# 五样本前后台分层输出验收矩阵",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：影子验收矩阵，不真实发送企业微信，不改正式入口。",
        "",
        "## 样本",
        "",
    ]
    for item in asset["matrix"]:
        stock = item["stock"]
        lines.append(
            f"- {stock.get('name')}（{stock.get('code')}）："
            f"front={item['front_layer']['allowed_for_shadow_front']}，"
            f"backend_evidence={item['backend_layer']['must_keep_evidence']}"
        )
    lines.extend(["", "## 禁止项", ""])
    lines.extend([f"- {item}" for item in asset["global_rules"]["forbidden"]])
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
