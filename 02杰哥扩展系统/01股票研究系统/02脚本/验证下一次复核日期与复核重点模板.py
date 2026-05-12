# -*- coding: utf-8 -*-
"""验收下一次复核日期与复核重点模板。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "下一次复核日期与复核重点模板_最新.json"
RESULT_JSON = DATA_DIR / "下一次复核日期与复核重点模板验收结果_最新.json"
RESULT_MD = DATA_DIR / "下一次复核日期与复核重点模板验收结果_最新.md"
REQUIRED_CODES = {"002428", "002466", "688347", "000906", "300641"}


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1下一次复核日期与复核重点影子模板":
        errors.append("资产身份不正确")
    if asset.get("status") != "shadow_review_template":
        errors.append("状态不是shadow_review_template")
    for flag in ["not_formal_config", "not_scheduler", "not_external_send"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    rules = asset.get("rules", [])
    if len(rules) < 4:
        errors.append("复核规则不足4条")
    required_fields = set(asset.get("required_output_fields", []))
    for field in ["next_review_date", "review_focus", "review_trigger", "missing_to_check", "confidence_recheck_condition"]:
        if field not in required_fields:
            errors.append(f"缺少输出字段：{field}")
    samples = asset.get("samples", [])
    codes = {item.get("stock", {}).get("code") for item in samples}
    if codes != REQUIRED_CODES:
        errors.append(f"样本股票代码不完整：{sorted(codes)}")
    for item in samples:
        stock = item.get("stock", {})
        if not item.get("next_review_date"):
            errors.append(f"{stock.get('code')}缺少next_review_date")
        if not item.get("review_focus") or len(item.get("review_focus", [])) < 2:
            errors.append(f"{stock.get('code')}复核重点不足")
        if item.get("confidence") not in {"high", "medium", "low"}:
            errors.append(f"{stock.get('code')}置信度值不合规")
    summary = asset.get("summary", {})
    if summary.get("real_reminder_allowed") is not False:
        errors.append("real_reminder_allowed必须为false")
    if summary.get("external_send_allowed") is not False:
        errors.append("external_send_allowed必须为false")
    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_formal_config", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界{flag}必须为true")
    result = {
        "name": "下一次复核日期与复核重点模板验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {
            "rule_count": len(rules),
            "sample_count": len(samples),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 下一次复核日期与复核重点模板验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 规则数：{result['metrics']['rule_count']}",
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
