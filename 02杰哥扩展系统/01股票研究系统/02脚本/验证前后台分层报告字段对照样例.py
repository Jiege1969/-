# -*- coding: utf-8 -*-
"""验证前后台分层报告字段对照样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "前后台分层报告字段对照样例_最新.json"
RESULT_JSON = DATA_DIR / "前后台分层报告字段对照样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "前后台分层报告字段对照样例验收结果_最新.md"
FORBIDDEN_FRONTEND = ["MACD", "RSI", "量比", "K线", "计算过程", "买入", "卖出", "下单", "仓位", "自动交易", "券商接口"]


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W2前后台字段映射样例":
        errors.append("资产身份不正确")
    for flag in ["not_real_market_report", "not_external_send", "not_formal_entry", "not_trade_advice"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    mapping = asset.get("field_mapping", [])
    if len(mapping) < 8:
        errors.append("字段映射不得少于8项")
    backend_only = [item for item in mapping if not item.get("frontend_visible")]
    if len(backend_only) < 2:
        errors.append("必须明确至少2类后台字段不直接前台展示")
    constraints = asset.get("frontend_constraints", {})
    for flag in [
        "must_include_stock_identity_first",
        "must_include_missing_when_present",
        "must_hide_raw_indicators",
        "must_hide_calculation_trace",
        "must_not_include_trade_action",
    ]:
        if constraints.get(flag) is not True:
            errors.append(f"前台约束{flag}必须为true")
    if constraints.get("max_main_reasons") != 3:
        errors.append("前台主要依据上限必须为3条")
    for sample in asset.get("samples", []):
        name = sample.get("stock_name", "")
        code = sample.get("stock_code", "")
        front = sample.get("frontend_output", {})
        if not front.get("first_line", "").startswith(f"{name}（{code}）："):
            errors.append(f"{name}前台第一行未明确对象和代码")
        if len(front.get("main_reasons", [])) > 3:
            errors.append(f"{name}前台主要依据超过3条")
        if sample.get("backend_snapshot", {}).get("missing") and not front.get("key_missing"):
            errors.append(f"{name}后台有missing时前台必须展示关键缺口")
        text = json.dumps(front, ensure_ascii=False)
        for word in FORBIDDEN_FRONTEND:
            if word in text:
                errors.append(f"{name}前台包含禁止展示/执行词：{word}")
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
        "name": "前后台分层报告字段对照样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {
            "mapping_count": len(mapping),
            "sample_count": len(asset.get("samples", [])),
            "backend_only_count": len(backend_only),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 前后台分层报告字段对照样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 映射项：{result['metrics']['mapping_count']}",
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
