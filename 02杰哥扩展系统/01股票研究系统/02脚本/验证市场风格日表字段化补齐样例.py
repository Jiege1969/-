# -*- coding: utf-8 -*-
"""验证市场风格日表字段化补齐样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "市场风格日表字段化补齐样例_最新.json"
RESULT_JSON = DATA_DIR / "市场风格日表字段化补齐样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "市场风格日表字段化补齐样例验收结果_最新.md"
REQUIRED_DAILY_FIELDS = {
    "trade_date",
    "risk_appetite",
    "sector_heat",
    "size_style",
    "liquidity",
    "style_fit_by_stock_type",
    "frontend_effect",
    "missing_reason",
}


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1市场风格日表字段化样例":
        errors.append("资产身份不正确")
    for flag in ["not_real_market_data", "not_external_send", "not_formal_entry", "not_score_write"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    daily = asset.get("daily_style", {})
    if not REQUIRED_DAILY_FIELDS.issubset(daily.keys()):
        errors.append("市场风格日表字段不完整")
    if daily.get("data_status") != "shadow_not_real_market_data":
        errors.append("必须明确不是真实市场数据")
    if not daily.get("frontend_effect"):
        errors.append("必须说明前台影响")
    if not daily.get("missing_reason"):
        errors.append("必须说明缺口原因")
    samples = asset.get("samples", [])
    if len(samples) < 3:
        errors.append("股票适配样本不得少于3个")
    for sample in samples:
        name = sample.get("stock_name", "")
        if sample.get("style_fit_status") not in {"missing", "partial", "ready"}:
            errors.append(f"{name}风格适配状态不合法")
        if not sample.get("conclusion_effect"):
            errors.append(f"{name}缺少结论影响说明")
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
        "name": "市场风格日表字段化补齐样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {
            "field_count": asset.get("summary", {}).get("field_count", 0),
            "sample_count": len(samples),
            "real_market_data_ready": asset.get("summary", {}).get("real_market_data_ready"),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 市场风格日表字段化补齐样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 字段数：{result['metrics']['field_count']}",
        f"- 样本数：{result['metrics']['sample_count']}",
        f"- 真实市场数据ready：{result['metrics']['real_market_data_ready']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
