# -*- coding: utf-8 -*-
"""验证稳定交付版运行指挥台索引包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "87稳定交付版运行指挥台索引包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定交付版运行指挥台索引包验收"

ASSET_JSON = DATA_DIR / "稳定交付版运行指挥台索引包_最新.json"
DASHBOARD_JSON = DATA_DIR / "稳定版运行指挥台_最新.json"
CHECK_JSON = DATA_DIR / "稳定版运行指挥台只读核对_最新.json"
LATEST_LOG = LOG_DIR / "stable-delivery-runtime-dashboard-index-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    dashboard = read_json(DASHBOARD_JSON) if DASHBOARD_JSON.exists() else {}
    check = read_json(CHECK_JSON) if CHECK_JSON.exists() else {}

    if not asset:
        errors.append(f"总包不存在：{ASSET_JSON}")
    if not dashboard:
        errors.append(f"指挥台不存在：{DASHBOARD_JSON}")
    if not check:
        errors.append(f"只读核对不存在：{CHECK_JSON}")

    if asset:
        if asset.get("状态") != "stable_delivery_runtime_dashboard_index_ready":
            errors.append("总包状态必须为 stable_delivery_runtime_dashboard_index_ready")
        if asset.get("指标", {}).get("来源存在数") != asset.get("指标", {}).get("来源数"):
            errors.append("来源必须全部存在")
        if not all(value is False for value in asset.get("安全边界", {}).values()):
            errors.append("总包安全边界必须全部为false")
        for path_text in asset.get("输出文件", {}).values():
            if not Path(path_text).exists():
                errors.append(f"输出文件不存在：{path_text}")

    if dashboard:
        if dashboard.get("运行灯号") not in {"green", "yellow", "red"}:
            errors.append("运行灯号不合法")
        if dashboard.get("每日刷新", {}).get("失败") != 0:
            errors.append("每日刷新必须无失败")
        if dashboard.get("总巡检", {}).get("失败") != 0:
            errors.append("总巡检必须无失败")
        if dashboard.get("总回归", {}).get("失败") != 0:
            errors.append("总回归必须无失败")
        if dashboard.get("次日闸口", {}).get("是否生成次日样本") is not False:
            errors.append("不得生成次日样本")
        if dashboard.get("试运行反馈", {}).get("拒收数", 0) != 0:
            errors.append("试运行反馈拒收数必须为0")
        if dashboard.get("试运行反馈", {}).get("需总管确认数", 0) != 0:
            errors.append("试运行反馈需总管确认数必须为0")

    if check:
        if check.get("总体状态") != "pass":
            errors.append("只读核对总体状态必须为pass")
        if check.get("汇总", {}).get("失败") != 0:
            errors.append("只读核对失败数必须为0")

    report = {
        "名称": "稳定交付版运行指挥台索引包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "来源数": asset.get("指标", {}).get("来源数") if asset else 0,
            "运行灯号": dashboard.get("运行灯号") if dashboard else None,
            "三日达标": dashboard.get("三日稳定", {}).get("达标") if dashboard else None,
            "仍缺样本数": dashboard.get("三日稳定", {}).get("仍缺样本数") if dashboard else None,
            "反馈接收数": dashboard.get("试运行反馈", {}).get("接收数") if dashboard else None,
            "反馈拒收数": dashboard.get("试运行反馈", {}).get("拒收数") if dashboard else None,
        },
        "验证范围": {
            "总包": str(ASSET_JSON),
            "指挥台": str(DASHBOARD_JSON),
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
