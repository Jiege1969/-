# -*- coding: utf-8 -*-
"""验证财报资金缺口到前台结论约束样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "财报资金缺口到前台结论约束样例_最新.json"
RESULT_JSON = DATA_DIR / "财报资金缺口到前台结论约束样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "财报资金缺口到前台结论约束样例验收结果_最新.md"
FORBIDDEN = ["买入", "卖出", "下单", "仓位", "自动交易", "券商接口"]


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1前台结论约束样例":
        errors.append("资产身份不正确")
    for flag in ["not_real_market_report", "not_external_send", "not_formal_entry", "not_trade_advice"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    rules = asset.get("constraint_rules", [])
    if len(rules) < 4:
        errors.append("约束规则不得少于4条")
    samples = asset.get("samples", [])
    if len(samples) != 5:
        errors.append("样本数量必须为5")
    for item in samples:
        name = item.get("stock_name", "")
        missing = item.get("missing_evidence", [])
        if not missing:
            errors.append(f"{name}必须列出缺失证据")
        before = item.get("frontend_conclusion_before_constraint")
        after = item.get("frontend_conclusion_after_constraint")
        confidence = item.get("confidence_after_constraint")
        if not after:
            errors.append(f"{name}必须有约束后结论")
        if "financial_report" in missing and before == "重点关注" and after == "重点关注":
            errors.append(f"{name}财报缺失时不得保持重点关注")
        if len(missing) >= 3 and confidence == "high":
            errors.append(f"{name}关键缺口较多时confidence不得为high")
        if not item.get("must_say"):
            errors.append(f"{name}必须有前台说明")
        text = json.dumps(item, ensure_ascii=False)
        for word in FORBIDDEN:
            if word in text:
                errors.append(f"{name}包含禁止交易/执行词：{word}")
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
        "name": "财报资金缺口到前台结论约束样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {
            "sample_count": len(samples),
            "rules_count": len(rules),
            "forbidden_word_count": len([err for err in errors if "禁止交易/执行词" in err]),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 财报资金缺口到前台结论约束样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 样本数：{result['metrics']['sample_count']}",
        f"- 规则数：{result['metrics']['rules_count']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
