# -*- coding: utf-8 -*-
"""执行稳定交付版每日运行日报只读核对。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "85稳定交付版每日运行日报与次日待办包"

ASSET_JSON = DATA_DIR / "稳定交付版每日运行日报与次日待办包_最新.json"
DAILY_REPORT_JSON = DATA_DIR / "稳定版每日运行日报_最新.json"
NEXT_TODO_JSON = DATA_DIR / "稳定版次日待办清单_最新.json"
CHECK_JSON = DATA_DIR / "稳定版每日运行日报只读核对_最新.json"
CHECK_MD = DATA_DIR / "稳定版每日运行日报只读核对_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版每日运行日报只读核对",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 失败数：{report['汇总']['失败']}",
            "",
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    daily = read_json(DAILY_REPORT_JSON)
    todo = read_json(NEXT_TODO_JSON)
    errors: list[str] = []

    if asset.get("状态") != "stable_delivery_daily_report_next_todo_ready":
        errors.append("总包状态不正确")
    if daily.get("稳定版运行状态") not in {"green", "yellow", "red"}:
        errors.append("日报运行状态不正确")
    if daily.get("三日稳定样本", {}).get("三日达标") is True and daily.get("三日稳定样本", {}).get("通过样本数", 0) < 3:
        errors.append("不足3个样本时不得三日达标")
    if daily.get("次日闸口", {}).get("是否生成次日样本") is not False:
        errors.append("日报不得显示已生成次日样本")
    if len(todo.get("待办", [])) < 4:
        errors.append("次日待办不得少于4项")
    if not all(value is False for value in asset.get("安全边界", {}).values()):
        errors.append("总包安全边界必须全部为false")
    if not all(value is False for value in daily.get("安全边界", {}).values()):
        errors.append("日报安全边界必须全部为false")
    if not all(value is False for value in todo.get("安全边界", {}).values()):
        errors.append("待办安全边界必须全部为false")

    report = {
        "名称": "稳定版每日运行日报只读核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not errors else "blocked",
        "错误": errors,
        "汇总": {"总数": 8, "通过": 8 - len(errors), "失败": len(errors)},
        "运行状态": daily.get("稳定版运行状态"),
        "次日待办数": len(todo.get("待办", [])),
    }
    write_json(CHECK_JSON, report)
    write_text(CHECK_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "失败": len(errors), "运行状态": report["运行状态"], "输出": str(CHECK_JSON)}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
