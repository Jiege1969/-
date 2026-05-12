# -*- coding: utf-8 -*-
"""验证复盘结果到规则候选二次门禁样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "复盘结果到规则候选二次门禁样例_最新.json"
RESULT_JSON = DATA_DIR / "复盘结果到规则候选二次门禁样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "复盘结果到规则候选二次门禁样例验收结果_最新.md"


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1复盘到规则候选门禁样例":
        errors.append("资产身份不正确")
    for flag in ["not_formal_rule_update", "not_formal_config", "not_external_send", "not_formal_entry"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    gates = asset.get("gate_rules", [])
    if len(gates) < 4:
        errors.append("二次门禁规则不得少于4条")
    samples = asset.get("samples", [])
    if len(samples) < 3:
        errors.append("复盘候选样本不得少于3条")
    for item in samples:
        review_id = item.get("review_id", "")
        if item.get("candidate_status") != "pending_human_review":
            errors.append(f"{review_id}必须保持pending_human_review")
        if item.get("formal_rule_update_allowed") is not False:
            errors.append(f"{review_id}不得允许正式规则自动更新")
        if not item.get("allowed_output", "").startswith("经验候选"):
            errors.append(f"{review_id}允许输出必须是经验候选")
    summary = asset.get("summary", {})
    if summary.get("any_formal_rule_update_allowed") is not False:
        errors.append("any_formal_rule_update_allowed必须为false")
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
        "name": "复盘结果到规则候选二次门禁样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {
            "gate_count": len(gates),
            "sample_count": len(samples),
            "any_formal_rule_update_allowed": summary.get("any_formal_rule_update_allowed"),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 复盘结果到规则候选二次门禁样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 门禁数：{result['metrics']['gate_count']}",
        f"- 样本数：{result['metrics']['sample_count']}",
        f"- 允许正式规则自动更新：{result['metrics']['any_formal_rule_update_allowed']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
