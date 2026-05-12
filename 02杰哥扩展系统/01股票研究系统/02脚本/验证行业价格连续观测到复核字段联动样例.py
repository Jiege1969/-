# -*- coding: utf-8 -*-
"""验收行业价格连续观测到复核字段联动样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "行业价格连续观测到复核字段联动样例_最新.json"
RESULT_JSON = DATA_DIR / "行业价格连续观测到复核字段联动样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "行业价格连续观测到复核字段联动样例验收结果_最新.md"
REQUIRED_CODES = {"002428", "002466", "688347", "000906", "300641"}
FORBIDDEN = ["接入真实API", "写正式库", "真实外发", "下单", "交易"]


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1行业价格连续观测到复核字段联动样例":
        errors.append("资产身份不正确")
    if asset.get("status") != "shadow_mapping_sample":
        errors.append("状态不是shadow_mapping_sample")
    for flag in ["not_formal_config", "not_price_api", "not_formal_database_write"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    records = asset.get("records", [])
    codes = {item.get("stock", {}).get("code") for item in records}
    if codes != REQUIRED_CODES:
        errors.append(f"样本股票代码不完整：{sorted(codes)}")
    for item in records:
        stock = item.get("stock", {})
        if not item.get("price_series", {}).get("commodity"):
            errors.append(f"{stock.get('code')}缺少价格品种")
        if not item.get("backend_missing_update") or len(item.get("backend_missing_update", [])) < 2:
            errors.append(f"{stock.get('code')}后台missing更新不足")
        if "复核重点" not in item.get("front_review_focus", ""):
            errors.append(f"{stock.get('code')}前台复核话术未明确复核重点")
        if not item.get("confidence_effect"):
            errors.append(f"{stock.get('code')}缺少置信度影响")
        combined = json.dumps(item, ensure_ascii=False)
        for phrase in FORBIDDEN:
            if phrase in combined:
                errors.append(f"{stock.get('code')}出现禁止表达：{phrase}")
    rules = "\n".join(asset.get("mapping_rules", []))
    for required in ["不直接生成强结论", "前台只展示复核重点", "不得给high置信度"]:
        if required not in rules:
            errors.append(f"映射规则缺少：{required}")
    summary = asset.get("summary", {})
    if summary.get("sample_count") != 5:
        errors.append("sample_count必须为5")
    if summary.get("real_price_api_allowed") is not False:
        errors.append("real_price_api_allowed必须为false")
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
    ]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界{flag}必须为true")
    result = {
        "name": "行业价格连续观测到复核字段联动样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {"sample_count": len(records)},
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 行业价格连续观测到复核字段联动样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
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
