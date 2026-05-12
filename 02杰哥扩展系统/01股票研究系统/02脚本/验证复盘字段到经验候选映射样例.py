# -*- coding: utf-8 -*-
"""验收复盘字段到经验候选映射样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "复盘字段到经验候选映射样例_最新.json"
RESULT_JSON = DATA_DIR / "复盘字段到经验候选映射样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "复盘字段到经验候选映射样例验收结果_最新.md"
REQUIRED_CODES = {"002428", "002466", "688347", "000906", "300641"}
REQUIRED_FIELDS = {"wrong_strength", "missing_not_exposed", "evidence_mismatch", "user_readability_issue"}


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1复盘字段到经验候选映射样例":
        errors.append("资产身份不正确")
    if asset.get("status") != "shadow_review_to_candidate_sample":
        errors.append("状态不是shadow_review_to_candidate_sample")
    for flag in ["not_formal_rule_write", "not_formal_config", "not_entrypoint"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    mapping_rules = asset.get("mapping_rules", [])
    fields = {item.get("review_field") for item in mapping_rules}
    if fields != REQUIRED_FIELDS:
        errors.append(f"复盘字段覆盖不完整：{sorted(fields)}")
    samples = asset.get("samples", [])
    codes = {item.get("stock", {}).get("code") for item in samples}
    if codes != REQUIRED_CODES:
        errors.append(f"样本股票代码不完整：{sorted(codes)}")
    for item in samples:
        stock = item.get("stock", {})
        if item.get("review_field") not in REQUIRED_FIELDS:
            errors.append(f"{stock.get('code')}review_field不合规")
        if item.get("candidate_status") != "pending_human_review":
            errors.append(f"{stock.get('code')}候选状态必须为pending_human_review")
        if not item.get("experience_candidate"):
            errors.append(f"{stock.get('code')}缺少experience_candidate")
    gate = asset.get("promotion_gate", {})
    if gate.get("requires_human_review") is not True:
        errors.append("requires_human_review必须为true")
    if gate.get("requires_multi_case_validation") is not True:
        errors.append("requires_multi_case_validation必须为true")
    if gate.get("auto_update_formal_rule_allowed") is not False:
        errors.append("auto_update_formal_rule_allowed必须为false")
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
        "name": "复盘字段到经验候选映射样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {"mapping_rule_count": len(mapping_rules), "sample_count": len(samples)},
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 复盘字段到经验候选映射样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 映射规则数：{result['metrics']['mapping_rule_count']}",
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
