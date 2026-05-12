# -*- coding: utf-8 -*-
"""验证稳定交付版每日运行日报与次日待办包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "85稳定交付版每日运行日报与次日待办包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定交付版每日运行日报与次日待办包验收"

ASSET_JSON = DATA_DIR / "稳定交付版每日运行日报与次日待办包_最新.json"
DAILY_REPORT_JSON = DATA_DIR / "稳定版每日运行日报_最新.json"
NEXT_TODO_JSON = DATA_DIR / "稳定版次日待办清单_最新.json"
CHECK_JSON = DATA_DIR / "稳定版每日运行日报只读核对_最新.json"
LATEST_LOG = LOG_DIR / "stable-delivery-daily-report-next-todo-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    daily = read_json(DAILY_REPORT_JSON) if DAILY_REPORT_JSON.exists() else {}
    todo = read_json(NEXT_TODO_JSON) if NEXT_TODO_JSON.exists() else {}
    check = read_json(CHECK_JSON) if CHECK_JSON.exists() else {}

    if not asset:
        errors.append(f"总包不存在：{ASSET_JSON}")
    if not daily:
        errors.append(f"日报不存在：{DAILY_REPORT_JSON}")
    if not todo:
        errors.append(f"次日待办不存在：{NEXT_TODO_JSON}")
    if not check:
        errors.append(f"只读核对不存在：{CHECK_JSON}")

    if asset:
        if asset.get("状态") != "stable_delivery_daily_report_next_todo_ready":
            errors.append("总包状态必须为 stable_delivery_daily_report_next_todo_ready")
        if not all(value is False for value in asset.get("安全边界", {}).values()):
            errors.append("总包安全边界必须全部为false")
        for path_text in asset.get("输出文件", {}).values():
            if not Path(path_text).exists():
                errors.append(f"输出文件不存在：{path_text}")

    if daily:
        if daily.get("稳定版运行状态") not in {"green", "yellow", "red"}:
            errors.append("日报运行状态不合法")
        if daily.get("次日闸口", {}).get("是否生成次日样本") is not False:
            errors.append("日报不得生成次日样本")
        if daily.get("三日稳定样本", {}).get("三日达标") is True and daily.get("三日稳定样本", {}).get("通过样本数", 0) < 3:
            errors.append("不足3日样本不得达标")
    if todo and len(todo.get("待办", [])) < 4:
        errors.append("次日待办不得少于4项")
    if check:
        if check.get("总体状态") != "pass":
            errors.append("只读核对总体状态必须为pass")
        if check.get("汇总", {}).get("失败") != 0:
            errors.append("只读核对失败数必须为0")

    report = {
        "名称": "稳定交付版每日运行日报与次日待办包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "运行状态": daily.get("稳定版运行状态") if daily else None,
            "三日达标": daily.get("三日稳定样本", {}).get("三日达标") if daily else None,
            "仍缺自然日样本": daily.get("三日稳定样本", {}).get("仍缺样本数") if daily else None,
            "次日待办数": len(todo.get("待办", [])) if todo else 0,
        },
        "验证范围": {
            "总包": str(ASSET_JSON),
            "日报": str(DAILY_REPORT_JSON),
            "次日待办": str(NEXT_TODO_JSON),
            "只读核对": str(CHECK_JSON),
            "日志": str(LATEST_LOG),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
