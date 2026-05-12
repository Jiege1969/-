# -*- coding: utf-8 -*-
"""验证稳定版每日唯一入口操作卡同步包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "98稳定版每日唯一入口操作卡同步包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定版每日唯一入口操作卡同步包验收"
PACKAGE_JSON = DATA_DIR / "稳定版每日唯一入口操作卡同步包_最新.json"
CARD_MD = DATA_DIR / "稳定版每日唯一入口操作卡_最新.md"
ENTRY_MATRIX_JSON = DATA_DIR / "稳定版每日入口关系表_最新.json"
LOG_JSON = LOG_DIR / "stable-daily-single-entry-operation-card-verify-最新.json"


def read_json(path: Path) -> dict[str, Any] | list[dict[str, Any]]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    package = read_json(PACKAGE_JSON)
    matrix = read_json(ENTRY_MATRIX_JSON)
    errors: list[str] = []

    if not isinstance(package, dict) or package.get("状态") != "stable_daily_single_entry_operation_card_ready":
        errors.append("总包状态不正确")
    if not isinstance(matrix, list) or len(matrix) < 3:
        errors.append("入口关系表不足")
    recommended = [item for item in matrix if item.get("是否推荐手动运行") is True] if isinstance(matrix, list) else []
    if len(recommended) != 1:
        errors.append("必须且只能有一个推荐手动入口")
    if recommended and "自然日样本采集与达标刷新" not in recommended[0].get("名称", ""):
        errors.append("推荐手动入口必须是自然日样本采集与达标刷新入口")
    summary = package.get("当前运行摘要", {}) if isinstance(package, dict) else {}
    if summary.get("入口包状态") != "stable_natural_day_sample_refresh_entry_ready":
        errors.append("97入口包状态未就绪")
    if summary.get("最近执行状态") != "pass":
        errors.append("97入口最近执行未通过")
    if not CARD_MD.exists() or "每天只跑这个" not in CARD_MD.read_text(encoding="utf-8"):
        errors.append("每日唯一入口操作卡缺失或内容不完整")
    if isinstance(package, dict) and not all(value is False for value in package.get("安全边界", {}).values()):
        errors.append("安全边界必须全部为 false")
    if isinstance(package, dict):
        for path_text in package.get("输出文件", {}).values():
            if not Path(path_text).exists():
                errors.append(f"输出文件不存在：{path_text}")

    report = {
        "名称": "稳定版每日唯一入口操作卡同步包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not errors,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "推荐手动入口数": len(recommended),
            "入口关系数": len(matrix) if isinstance(matrix, list) else 0,
            "三日达标": summary.get("三日达标"),
            "仍缺自然日样本数": summary.get("仍缺自然日样本数"),
        },
        "验证范围": {"总包": str(PACKAGE_JSON), "操作卡": str(CARD_MD), "入口关系表": str(ENTRY_MATRIX_JSON), "日志": str(LOG_JSON)},
    }
    write_json(LOG_JSON, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
