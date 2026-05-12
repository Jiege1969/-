# -*- coding: utf-8 -*-
"""执行稳定交付版运行指挥台只读核对。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "87稳定交付版运行指挥台索引包"

ASSET_JSON = DATA_DIR / "稳定交付版运行指挥台索引包_最新.json"
DASHBOARD_JSON = DATA_DIR / "稳定版运行指挥台_最新.json"
CHECK_JSON = DATA_DIR / "稳定版运行指挥台只读核对_最新.json"
CHECK_MD = DATA_DIR / "稳定版运行指挥台只读核对_最新.md"


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
            "# 稳定版运行指挥台只读核对",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 运行灯号：{report['运行灯号']}",
            f"- 失败数：{report['汇总']['失败']}",
            "",
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    dashboard = read_json(DASHBOARD_JSON)
    errors: list[str] = []
    if asset.get("状态") != "stable_delivery_runtime_dashboard_index_ready":
        errors.append("总包状态不正确")
    if asset.get("指标", {}).get("来源存在数") != asset.get("指标", {}).get("来源数"):
        errors.append("来源文件必须全部存在")
    if dashboard.get("运行灯号") not in {"green", "yellow", "red"}:
        errors.append("运行灯号不合法")
    if dashboard.get("每日刷新", {}).get("失败") != 0:
        errors.append("每日刷新失败数必须为0")
    if dashboard.get("总巡检", {}).get("失败") != 0:
        errors.append("总巡检失败数必须为0")
    if dashboard.get("总回归", {}).get("失败") != 0:
        errors.append("总回归失败数必须为0")
    if dashboard.get("三日稳定", {}).get("达标") is True and dashboard.get("三日稳定", {}).get("仍缺样本数", 0) != 0:
        errors.append("仍缺样本时不得三日达标")
    if dashboard.get("次日闸口", {}).get("是否生成次日样本") is not False:
        errors.append("不得生成次日样本")
    if dashboard.get("试运行反馈", {}).get("拒收数", 0) != 0:
        errors.append("试运行反馈拒收数必须为0")
    if dashboard.get("试运行反馈", {}).get("需总管确认数", 0) != 0:
        errors.append("试运行反馈需总管确认数必须为0")
    if not all(value is False for value in asset.get("安全边界", {}).values()):
        errors.append("总包安全边界必须全部为false")
    if not all(value is False for value in dashboard.get("安全边界", {}).values()):
        errors.append("指挥台安全边界必须全部为false")

    report = {
        "名称": "稳定版运行指挥台只读核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not errors else "blocked",
        "错误": errors,
        "汇总": {"总数": 12, "通过": 12 - len(errors), "失败": len(errors)},
        "运行灯号": dashboard.get("运行灯号"),
    }
    write_json(CHECK_JSON, report)
    write_text(CHECK_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "失败": len(errors), "运行灯号": report["运行灯号"], "输出": str(CHECK_JSON)}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
