# -*- coding: utf-8 -*-
"""验证稳定交付版运行指挥台每日刷新入口包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "88稳定交付版运行指挥台每日刷新入口包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定交付版运行指挥台每日刷新入口包验收"

ASSET_JSON = DATA_DIR / "稳定交付版运行指挥台每日刷新入口包_最新.json"
PLAN_JSON = DATA_DIR / "稳定版运行指挥台每日刷新入口计划_最新.json"
RESULT_JSON = DATA_DIR / "稳定版运行指挥台每日刷新入口执行结果_最新.json"
LATEST_LOG = LOG_DIR / "stable-delivery-runtime-dashboard-daily-refresh-entry-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    plan = read_json(PLAN_JSON) if PLAN_JSON.exists() else {}
    result = read_json(RESULT_JSON) if RESULT_JSON.exists() else {}

    if not asset:
        errors.append(f"总包不存在：{ASSET_JSON}")
    if not plan:
        errors.append(f"计划不存在：{PLAN_JSON}")
    if not result:
        errors.append(f"执行结果不存在：{RESULT_JSON}")

    if asset:
        if asset.get("状态") != "stable_delivery_runtime_dashboard_daily_refresh_entry_ready":
            errors.append("总包状态必须为 stable_delivery_runtime_dashboard_daily_refresh_entry_ready")
        if asset.get("指标", {}).get("任务数", 0) < 8:
            errors.append("任务数不得少于8")
        if not all(value is False for value in asset.get("安全边界", {}).values()):
            errors.append("总包安全边界必须全部为false")
        for path_text in asset.get("输出文件", {}).values():
            if not Path(path_text).exists():
                errors.append(f"输出文件不存在：{path_text}")
    if plan:
        if len(plan.get("任务", [])) < 8:
            errors.append("计划任务不得少于8")
        if not all(value is False for value in plan.get("安全边界", {}).values()):
            errors.append("计划安全边界必须全部为false")
    if result:
        if result.get("总体状态") != "pass":
            errors.append("执行结果总体状态必须为pass")
        if result.get("汇总", {}).get("失败") != 0:
            errors.append("执行结果失败数必须为0")
        if result.get("指挥台摘要", {}).get("运行灯号") not in {"green", "yellow", "red"}:
            errors.append("运行灯号不合法")
        if result.get("指挥台摘要", {}).get("每日刷新失败") != 0:
            errors.append("每日刷新失败必须为0")
        if result.get("指挥台摘要", {}).get("总巡检失败") != 0:
            errors.append("总巡检失败必须为0")
        if result.get("指挥台摘要", {}).get("总回归失败") != 0:
            errors.append("总回归失败必须为0")
        if result.get("指挥台摘要", {}).get("反馈拒收数", 0) != 0:
            errors.append("反馈拒收数必须为0")
        if not all(value is False for value in result.get("安全边界", {}).values()):
            errors.append("执行结果安全边界必须全部为false")

    report = {
        "名称": "稳定交付版运行指挥台每日刷新入口包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "任务数": len(plan.get("任务", [])) if plan else 0,
            "执行通过": result.get("汇总", {}).get("通过") if result else 0,
            "执行失败": result.get("汇总", {}).get("失败") if result else None,
            "运行灯号": result.get("指挥台摘要", {}).get("运行灯号") if result else None,
            "三日达标": result.get("指挥台摘要", {}).get("三日达标") if result else None,
        },
        "验证范围": {"总包": str(ASSET_JSON), "计划": str(PLAN_JSON), "执行结果": str(RESULT_JSON), "日志": str(LATEST_LOG)},
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
