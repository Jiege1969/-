# -*- coding: utf-8 -*-
"""验证稳定版试运行回传入口导航与闭环索引包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "91稳定版试运行回传入口导航与闭环索引包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定版试运行回传入口导航与闭环索引包验收"

ASSET_JSON = DATA_DIR / "稳定版试运行回传入口导航与闭环索引包_最新.json"
NAV_MD = DATA_DIR / "稳定版试运行回传入口导航_最新.md"
CLOSE_LOOP_MD = DATA_DIR / "稳定版试运行问题闭环索引_最新.md"
LATEST_LOG = LOG_DIR / "stable-trial-feedback-navigation-loop-index-verify-最新.json"


def main() -> int:
    errors: list[str] = []
    asset = json.loads(ASSET_JSON.read_text(encoding="utf-8-sig")) if ASSET_JSON.exists() else {}
    nav = NAV_MD.read_text(encoding="utf-8-sig") if NAV_MD.exists() else ""
    loop = CLOSE_LOOP_MD.read_text(encoding="utf-8-sig") if CLOSE_LOOP_MD.exists() else ""

    if asset.get("状态") != "stable_trial_feedback_navigation_loop_index_ready":
        errors.append("总包状态必须为 stable_trial_feedback_navigation_loop_index_ready")
    if asset.get("指标", {}).get("来源存在数") != asset.get("指标", {}).get("来源数"):
        errors.append("来源文件必须全部存在")
    if "问题回传模板" not in nav or "每天先刷新" not in nav:
        errors.append("导航必须包含每日刷新和问题回传模板")
    if "不自动转正式规则" not in loop or "需总管确认" not in loop:
        errors.append("闭环索引必须包含正式规则和总管确认边界")
    for path_text in asset.get("输出文件", {}).values():
        if not Path(path_text).exists():
            errors.append(f"输出文件不存在：{path_text}")
    if not all(value is False for value in asset.get("安全边界", {}).values()):
        errors.append("安全边界必须全部为 false")

    report = {
        "名称": "稳定版试运行回传入口导航与闭环索引包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "来源数": asset.get("指标", {}).get("来源数"),
            "来源存在数": asset.get("指标", {}).get("来源存在数"),
        },
        "验证范围": {
            "总包": str(ASSET_JSON),
            "导航": str(NAV_MD),
            "闭环索引": str(CLOSE_LOOP_MD),
            "日志": str(LATEST_LOG),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
