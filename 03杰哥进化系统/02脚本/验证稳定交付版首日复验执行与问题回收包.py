# -*- coding: utf-8 -*-
"""验证稳定交付版首日复验执行与问题回收包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "82稳定交付版首日复验执行与问题回收包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定交付版首日复验执行与问题回收包验收"

ASSET_JSON = DATA_DIR / "稳定交付版首日复验执行与问题回收包_最新.json"
PLAN_JSON = DATA_DIR / "稳定版首日只读复验执行计划_最新.json"
RESULT_JSON = DATA_DIR / "稳定版首日只读复验执行结果_最新.json"
LEDGER_JSON = DATA_DIR / "稳定版首日问题回收台账_最新.json"
LATEST_LOG = LOG_DIR / "stable-delivery-day1-recheck-issue-intake-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    plan = read_json(PLAN_JSON) if PLAN_JSON.exists() else {}
    result = read_json(RESULT_JSON) if RESULT_JSON.exists() else {}
    ledger = read_json(LEDGER_JSON) if LEDGER_JSON.exists() else {}

    if not asset:
        errors.append(f"总包不存在：{ASSET_JSON}")
    if not plan:
        errors.append(f"执行计划不存在：{PLAN_JSON}")
    if not result:
        errors.append(f"执行结果不存在：{RESULT_JSON}")
    if not ledger:
        errors.append(f"问题台账不存在：{LEDGER_JSON}")

    if asset:
        if asset.get("状态") != "stable_delivery_day1_recheck_issue_intake_ready":
            errors.append("总包状态必须为 stable_delivery_day1_recheck_issue_intake_ready")
        if len(asset.get("只读复验任务", [])) < 5:
            errors.append("只读复验任务不得少于 5 项")
        if not all(value is False for value in asset.get("安全边界", {}).values()):
            errors.append("总包安全边界必须全部为 false")
        for path_text in asset.get("输出文件", {}).values():
            if not Path(path_text).exists():
                errors.append(f"输出文件不存在：{path_text}")

    if plan and not all(value is False for value in plan.get("安全边界", {}).values()):
        errors.append("执行计划安全边界必须全部为 false")

    if result:
        if result.get("总体状态") != "pass":
            errors.append("首日只读复验结果必须为 pass")
        if result.get("汇总", {}).get("失败") != 0:
            errors.append("首日只读复验失败数必须为 0")
        if result.get("问题项"):
            errors.append("本轮首日问题回收台账应为空问题项")
        if not all(value is False for value in result.get("安全边界", {}).values()):
            errors.append("执行结果安全边界必须全部为 false")

    if ledger:
        if ledger.get("问题项"):
            errors.append("问题回收台账当前应无问题项")
        if not all(value is False for value in ledger.get("安全边界", {}).values()):
            errors.append("问题回收台账安全边界必须全部为 false")

    report = {
        "名称": "稳定交付版首日复验执行与问题回收包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "只读复验任务": len(asset.get("只读复验任务", [])) if asset else 0,
            "复验通过": result.get("汇总", {}).get("通过") if result else 0,
            "复验失败": result.get("汇总", {}).get("失败") if result else None,
            "问题项": len(ledger.get("问题项", [])) if ledger else None,
        },
        "验证范围": {
            "总包": str(ASSET_JSON),
            "执行计划": str(PLAN_JSON),
            "执行结果": str(RESULT_JSON),
            "问题台账": str(LEDGER_JSON),
            "日志": str(LATEST_LOG),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
