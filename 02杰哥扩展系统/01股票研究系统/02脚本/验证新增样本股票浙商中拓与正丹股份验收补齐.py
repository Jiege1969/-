# -*- coding: utf-8 -*-
"""验证新增样本股票浙商中拓与正丹股份验收补齐样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "新增样本股票浙商中拓与正丹股份验收补齐_最新.json"
RESULT_JSON = DATA_DIR / "新增样本股票浙商中拓与正丹股份验收补齐验收结果_最新.json"
RESULT_MD = DATA_DIR / "新增样本股票浙商中拓与正丹股份验收补齐验收结果_最新.md"
EXPECTED = {"浙商中拓": "000906", "正丹股份": "300641"}


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1新增样本验收矩阵":
        errors.append("资产身份不正确")
    for flag in ["not_real_market_report", "not_external_send", "not_formal_entry", "not_trade_advice"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    samples = asset.get("samples", [])
    if len(samples) != 2:
        errors.append("新增样本必须为2只")
    got = {item.get("stock_name"): item.get("stock_code") for item in samples}
    if got != EXPECTED:
        errors.append("新增样本必须为浙商中拓000906和正丹股份300641")
    for item in samples:
        name = item.get("stock_name", "")
        obj = item.get("object_identification", {})
        if obj.get("passed") is not True:
            errors.append(f"{name}对象识别必须通过")
        if not str(obj.get("first_line_required", "")).startswith(f"{name}（{item.get('stock_code')}）："):
            errors.append(f"{name}标准首行不正确")
        if not item.get("industry_tags"):
            errors.append(f"{name}必须有行业标签")
        gaps = item.get("evidence_gaps", [])
        if not any(gap.get("priority") == "P0" for gap in gaps):
            errors.append(f"{name}必须有P0缺口")
        front = item.get("frontend_expression_check", {})
        if front.get("must_include_missing") is not True:
            errors.append(f"{name}前台必须包含缺口")
        if front.get("must_not_include_trade_action") is not True:
            errors.append(f"{name}必须禁止交易动作")
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
        "name": "新增样本股票浙商中拓与正丹股份验收补齐验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {"sample_count": len(samples), "expected_count": 2},
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 新增样本股票浙商中拓与正丹股份验收补齐验收结果",
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
