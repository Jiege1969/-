# -*- coding: utf-8 -*-
"""验证财报资金证据字段化补齐样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "财报资金证据字段化补齐样例_最新.json"
RESULT_JSON = DATA_DIR / "财报资金证据字段化补齐样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "财报资金证据字段化补齐样例验收结果_最新.md"
REQUIRED_FIELDS = {"financial_report", "valuation_position", "institutional_holding", "capital_flow", "announcement_quality"}
REQUIRED_STOCKS = {"云南锗业", "三花智控", "上纬新材", "浙商中拓", "正丹股份"}


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1财报资金证据字段化样例":
        errors.append("资产身份不正确")
    for flag in ["not_real_market_report", "not_external_send", "not_formal_entry", "not_trade_advice"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    field_schema = asset.get("field_schema", [])
    schema_fields = {item.get("field") for item in field_schema}
    if schema_fields != REQUIRED_FIELDS:
        errors.append("字段定义必须覆盖财报、估值、机构、资金、公告")
    samples = asset.get("samples", [])
    stock_names = {item.get("stock_name") for item in samples}
    if stock_names != REQUIRED_STOCKS:
        errors.append("样本股票必须覆盖五个标准样本")
    for sample in samples:
        name = sample.get("stock_name", "")
        fields = sample.get("evidence_fields", {})
        if set(fields.keys()) != REQUIRED_FIELDS:
            errors.append(f"{name}字段不完整")
        if not any(value.get("priority") == "P0" for value in fields.values()):
            errors.append(f"{name}必须至少有P0字段")
        for field, value in fields.items():
            if value.get("status") not in {"missing", "partial", "ready"}:
                errors.append(f"{name}.{field}状态不合法")
            if value.get("status") in {"missing", "partial"} and not value.get("missing_reason"):
                errors.append(f"{name}.{field}缺少缺口原因")
        front = sample.get("frontend_constraint", {})
        if front.get("must_expose_missing") is not True:
            errors.append(f"{name}前台必须暴露缺口")
        if front.get("confidence_cap") not in {"low", "medium", "high"}:
            errors.append(f"{name}置信度上限不合法")
    safety = asset.get("safety_boundary", {})
    for flag in [
        "not_n8n",
        "not_external_send",
        "not_service_restart",
        "not_19310",
        "not_real_account",
        "not_formal_database_write",
        "not_formal_config",
        "not_entrypoint",
        "not_broker_interface",
        "not_auto_trade",
        "not_order",
        "not_position_adjustment",
    ]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界{flag}必须为true")
    result = {
        "name": "财报资金证据字段化补齐样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {"field_count": len(field_schema), "sample_count": len(samples)},
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 财报资金证据字段化补齐样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 字段数：{result['metrics']['field_count']}",
        f"- 样本数：{result['metrics']['sample_count']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
