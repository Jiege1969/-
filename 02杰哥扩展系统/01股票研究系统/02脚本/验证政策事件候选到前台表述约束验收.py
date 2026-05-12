# -*- coding: utf-8 -*-
"""验收政策事件候选到前台表述约束样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "政策事件候选到前台表述约束验收_最新.json"
RESULT_JSON = DATA_DIR / "政策事件候选到前台表述约束验收结果_最新.json"
RESULT_MD = DATA_DIR / "政策事件候选到前台表述约束验收结果_最新.md"
REQUIRED_CODES = {"002428", "002466", "688347", "000906", "300641"}
FORBIDDEN_FRONT = ["确定性利好", "确定充分受益", "只因政策即可给强结论", "必然上涨"]


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1政策事件候选到前台表述约束验收":
        errors.append("资产身份不正确")
    if asset.get("status") != "shadow_expression_gate":
        errors.append("状态不是shadow_expression_gate")
    for flag in ["not_formal_policy_database", "not_formal_config", "not_score_write"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    constraints = asset.get("constraints", [])
    statuses = {item.get("status") for item in constraints}
    if statuses != {"candidate_unverified", "source_verified_exposure_pending", "verified_with_exposure"}:
        errors.append(f"状态约束覆盖不完整：{sorted(statuses)}")
    samples = asset.get("samples", [])
    codes = {item.get("stock", {}).get("code") for item in samples}
    if codes != REQUIRED_CODES:
        errors.append(f"样本股票代码不完整：{sorted(codes)}")
    for item in samples:
        stock = item.get("stock", {})
        phrase = item.get("front_phrase", "")
        if not item.get("backend_missing"):
            errors.append(f"{stock.get('code')}缺少backend_missing")
        if item.get("status") not in statuses:
            errors.append(f"{stock.get('code')}状态不在约束表中")
        for forbidden in FORBIDDEN_FRONT:
            if forbidden in phrase:
                errors.append(f"{stock.get('code')}前台话术出现禁止表达：{forbidden}")
    rules = "\n".join(asset.get("global_rules", []))
    for required in ["不得直接作为确定性结论", "不得进入正式政策分", "区分线索"]:
        if required not in rules:
            errors.append(f"全局规则缺少：{required}")
    summary = asset.get("summary", {})
    if summary.get("formal_policy_database_write_allowed") is not False:
        errors.append("formal_policy_database_write_allowed必须为false")
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
        "name": "政策事件候选到前台表述约束验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {"constraint_count": len(constraints), "sample_count": len(samples)},
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 政策事件候选到前台表述约束验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 约束数：{result['metrics']['constraint_count']}",
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
