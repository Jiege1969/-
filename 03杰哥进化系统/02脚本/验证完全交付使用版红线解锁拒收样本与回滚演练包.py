# -*- coding: utf-8 -*-
"""验证完全交付使用版红线解锁拒收样本与回滚演练包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
PACKAGE_JSON = EVOLUTION_ROOT / "03数据" / "109完全交付使用版红线解锁拒收样本与回滚演练包" / "完全交付使用版红线解锁拒收样本与回滚演练包_最新.json"
REJECT_JSON = EVOLUTION_ROOT / "03数据" / "109完全交付使用版红线解锁拒收样本与回滚演练包" / "红线解锁拒收样本_最新.json"
ROLLBACK_JSON = EVOLUTION_ROOT / "03数据" / "109完全交付使用版红线解锁拒收样本与回滚演练包" / "红线解锁回滚演练清单_最新.json"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版红线解锁拒收样本与回滚演练包验收"
LATEST_LOG = LOG_DIR / "full-delivery-redline-unlock-reject-rollback-verify-最新.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    if not PACKAGE_JSON.exists():
        errors.append(f"总包不存在：{PACKAGE_JSON}")
        package: dict[str, Any] = {}
    else:
        package = read_json(PACKAGE_JSON)
    reject_samples = read_json(REJECT_JSON) if REJECT_JSON.exists() else []
    rollback_drills = read_json(ROLLBACK_JSON) if ROLLBACK_JSON.exists() else []

    if package.get("状态") != "full_delivery_redline_unlock_reject_rollback_drill_ready":
        errors.append("总包状态不是拒收回滚演练就绪")
    if len(reject_samples) < 7:
        errors.append("拒收样本少于7项")
    if len(rollback_drills) < 7:
        errors.append("回滚演练少于7项")
    if len(reject_samples) != len(rollback_drills):
        errors.append("拒收样本与回滚演练数量不一致")

    allowed_activation = [item for item in reject_samples if item.get("允许生效") is not False]
    allowed_auto = [item for item in reject_samples if item.get("允许自动执行") is not False]
    real_rollback = [item for item in rollback_drills if item.get("是否真实执行回滚") is not False]
    missing_reject_condition = [item for item in reject_samples if len(item.get("拒收条件", [])) < 5]
    rollback_not_closed = [
        item
        for item in rollback_drills
        if item.get("回滚后状态", {}).get("红线解锁生效") is not False
        or item.get("回滚后状态", {}).get("允许生效") is not False
        or item.get("回滚后状态", {}).get("允许自动执行") is not False
    ]

    if allowed_activation:
        errors.append("存在允许生效的拒收样本")
    if allowed_auto:
        errors.append("存在允许自动执行的拒收样本")
    if real_rollback:
        errors.append("存在真实执行回滚的演练项")
    if missing_reject_condition:
        errors.append("存在拒收条件不完整的样本")
    if rollback_not_closed:
        errors.append("存在回滚后状态未关闭的演练项")
    if package.get("安全边界", {}).get("红线解锁生效") is not False:
        errors.append("安全边界未保持红线解锁不生效")
    if package.get("安全边界", {}).get("真实执行回滚") is not False:
        errors.append("安全边界未保持不真实执行回滚")

    result = {
        "名称": "完全交付使用版红线解锁拒收样本与回滚演练包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not errors,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "拒收样本数量": len(reject_samples),
            "回滚演练数量": len(rollback_drills),
            "允许生效数量": len(allowed_activation),
            "允许自动执行数量": len(allowed_auto),
            "真实执行回滚数量": len(real_rollback),
        },
        "验证范围": {
            "总包": str(PACKAGE_JSON),
            "拒收样本": str(REJECT_JSON),
            "回滚演练": str(ROLLBACK_JSON),
            "日志": str(LATEST_LOG),
        },
    }
    write_json(LATEST_LOG, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
