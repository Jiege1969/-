# -*- coding: utf-8 -*-
"""验收市场风格适配到结论强度限制样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "市场风格适配到结论强度限制样例_最新.json"
RESULT_JSON = DATA_DIR / "市场风格适配到结论强度限制样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "市场风格适配到结论强度限制样例验收结果_最新.md"
REQUIRED_CODES = {"002428", "002466", "688347", "000906", "300641"}
REQUIRED_STYLE_STATES = {"risk_appetite_low", "sector_hot_but_market_weak", "sector_hot_and_market_active", "style_missing"}


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1市场风格适配到结论强度限制样例":
        errors.append("资产身份不正确")
    if asset.get("status") != "shadow_style_gate_sample":
        errors.append("状态不是shadow_style_gate_sample")
    for flag in ["not_formal_config", "not_formal_market_style_table", "not_score_write"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    style_gates = asset.get("style_gates", [])
    states = {item.get("style_state") for item in style_gates}
    if states != REQUIRED_STYLE_STATES:
        errors.append(f"市场风格状态覆盖不完整：{sorted(states)}")
    samples = asset.get("samples", [])
    codes = {item.get("stock", {}).get("code") for item in samples}
    if codes != REQUIRED_CODES:
        errors.append(f"样本股票代码不完整：{sorted(codes)}")
    for item in samples:
        stock = item.get("stock", {})
        if item.get("style_state") not in states:
            errors.append(f"{stock.get('code')}style_state不在闸口表中")
        if not item.get("front_strength_rule"):
            errors.append(f"{stock.get('code')}缺少前台结论强度规则")
        if len(item.get("backend_required", [])) < 2:
            errors.append(f"{stock.get('code')}后台必需字段不足")
    rules = "\n".join(asset.get("global_rules", []))
    for required in ["不能替代个股证据", "confidence不得为high", "保留观察或复核口径"]:
        if required not in rules:
            errors.append(f"全局规则缺少：{required}")
    summary = asset.get("summary", {})
    if summary.get("formal_market_style_write_allowed") is not False:
        errors.append("formal_market_style_write_allowed必须为false")
    if summary.get("formal_score_update_allowed") is not False:
        errors.append("formal_score_update_allowed必须为false")
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
        "name": "市场风格适配到结论强度限制样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {"style_gate_count": len(style_gates), "sample_count": len(samples)},
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 市场风格适配到结论强度限制样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 闸口数：{result['metrics']['style_gate_count']}",
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
