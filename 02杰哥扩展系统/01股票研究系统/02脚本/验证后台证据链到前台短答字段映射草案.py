# -*- coding: utf-8 -*-
"""
验证后台证据链到前台短答字段映射草案。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "后台证据链到前台短答字段映射草案_最新.json"
RESULT_JSON = DATA_DIR / "后台证据链到前台短答字段映射草案验收_最新.json"
RESULT_MD = DATA_DIR / "后台证据链到前台短答字段映射草案验收_最新.md"

REQUIRED_FRONT_FIELDS = {
    "object_line",
    "conclusion_line",
    "main_reason_line",
    "key_gap_line",
    "confidence_review_line",
}
REQUIRED_BACKEND_EVIDENCE = {
    "technical_structure",
    "fundamentals_capital",
    "policy_events",
    "market_style_fit",
    "industry_price_observation",
}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []

    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1映射草案":
        errors.append("资产身份必须是 W1映射草案")
    if asset.get("status") != "draft":
        errors.append("状态必须保持 draft")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_adapter_write", "not_score_write", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    fields = asset.get("field_mappings", [])
    field_ids = {item.get("front_field") for item in fields}
    if field_ids != REQUIRED_FRONT_FIELDS:
        errors.append(f"前台字段不完整：{sorted(field_ids)}")

    for item in fields:
        if not item.get("backend_sources"):
            errors.append(f"{item.get('front_field')} 缺少后台来源")
        if not item.get("missing_behavior"):
            errors.append(f"{item.get('front_field')} 缺少缺失处理")
        if not item.get("forbidden_behavior"):
            errors.append(f"{item.get('front_field')} 缺少禁止行为")

    priority_ids = {item.get("backend_evidence") for item in asset.get("backend_to_front_priority", [])}
    missing_backend = REQUIRED_BACKEND_EVIDENCE - priority_ids
    if missing_backend:
        errors.append(f"后台证据优先级缺少：{sorted(missing_backend)}")

    gate_text = "\n".join(asset.get("quality_gates", []))
    for phrase in ["第一行", "评分契约", "结构化证据", "不堆完整技术指标", "evidence", "人工修正"]:
        if phrase not in gate_text:
            errors.append(f"质量闸口缺少关键约束：{phrase}")

    serialized = json.dumps(asset, ensure_ascii=False)
    for term in ["买入", "卖出", "下单", "仓位调整", "自动交易", "券商接口"]:
        if term in serialized and "禁止新增" not in serialized and "不得使用" not in serialized:
            errors.append(f"交易词 {term} 未作为禁止边界表达")

    blockers = asset.get("formalization_blockers", [])
    if len(blockers) < 3:
        errors.append("正式化阻断登记不足")
    if not all("W3" in item.get("risk_level", "") for item in blockers):
        errors.append("正式化阻断必须标注 W3")

    result = {
        "name": "后台证据链到前台短答字段映射草案验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "front_field_count": len(fields),
            "backend_priority_count": len(asset.get("backend_to_front_priority", [])),
            "formalization_blocker_count": len(blockers),
        },
        "next_step": "可继续生成五样本后台到前台字段映射验收样例；不得写正式企业微信入口。",
    }

    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 后台证据链到前台短答字段映射草案验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 前台字段数量：{result['metrics']['front_field_count']}",
        f"- 后台证据优先级数量：{result['metrics']['backend_priority_count']}",
        f"- 正式化阻断数量：{result['metrics']['formalization_blocker_count']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in result["errors"]] or ["- 无"])
    lines.extend(["", "## 警告", ""])
    lines.extend([f"- {item}" for item in result["warnings"]] or ["- 无"])
    lines.extend(["", "## 下一步", "", f"- {result['next_step']}", ""])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
