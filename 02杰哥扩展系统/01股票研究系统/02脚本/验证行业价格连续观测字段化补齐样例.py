# -*- coding: utf-8 -*-
"""验证行业价格连续观测字段化补齐样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "行业价格连续观测字段化补齐样例_最新.json"
RESULT_JSON = DATA_DIR / "行业价格连续观测字段化补齐样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "行业价格连续观测字段化补齐样例验收结果_最新.md"
REQUIRED_STOCKS = {"云南锗业", "正丹股份", "浙商中拓", "上纬新材", "三花智控"}
REQUIRED_FIELDS = {
    "tracked_product",
    "price_source_status",
    "observation_window_days",
    "price_trend",
    "stock_exposure",
    "frontend_effect",
    "missing_reason",
}


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1行业价格连续观测字段化样例":
        errors.append("资产身份不正确")
    for flag in ["not_real_market_report", "not_external_send", "not_formal_entry", "not_trade_advice"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    samples = asset.get("samples", [])
    stock_names = {item.get("stock_name") for item in samples}
    if stock_names != REQUIRED_STOCKS:
        errors.append("样本股票必须覆盖五个标准样本")
    for sample in samples:
        name = sample.get("stock_name", "")
        fields = sample.get("industry_price_fields", {})
        if not REQUIRED_FIELDS.issubset(fields.keys()):
            errors.append(f"{name}行业价格字段不完整")
        if fields.get("price_source_status") not in {"missing", "partial", "ready"}:
            errors.append(f"{name}价格来源状态不合法")
        if not isinstance(fields.get("observation_window_days"), int) or fields.get("observation_window_days") <= 0:
            errors.append(f"{name}观察窗口必须为正整数")
        exposure = fields.get("stock_exposure")
        if not isinstance(exposure, (int, float)) or not 0 <= exposure <= 1:
            errors.append(f"{name}股票暴露度必须在0-1")
        if fields.get("price_source_status") in {"missing", "partial"} and not fields.get("missing_reason"):
            errors.append(f"{name}缺少价格来源缺口原因")
        if not fields.get("frontend_effect"):
            errors.append(f"{name}缺少前台影响说明")
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
        "name": "行业价格连续观测字段化补齐样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {
            "sample_count": len(samples),
            "missing_or_partial_source_count": asset.get("summary", {}).get("missing_or_partial_source_count", 0),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 行业价格连续观测字段化补齐样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 样本数：{result['metrics']['sample_count']}",
        f"- 来源缺口/半缺口数：{result['metrics']['missing_or_partial_source_count']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
