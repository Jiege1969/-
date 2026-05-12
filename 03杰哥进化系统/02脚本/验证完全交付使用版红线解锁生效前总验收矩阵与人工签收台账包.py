# -*- coding: utf-8 -*-
"""验证完全交付使用版红线解锁生效前总验收矩阵与人工签收台账包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
PACKAGE_JSON = EVOLUTION_ROOT / "03数据" / "110完全交付使用版红线解锁生效前总验收矩阵与人工签收台账包" / "完全交付使用版红线解锁生效前总验收矩阵与人工签收台账包_最新.json"
MATRIX_JSON = EVOLUTION_ROOT / "03数据" / "110完全交付使用版红线解锁生效前总验收矩阵与人工签收台账包" / "红线解锁生效前总验收矩阵_最新.json"
LEDGER_JSON = EVOLUTION_ROOT / "03数据" / "110完全交付使用版红线解锁生效前总验收矩阵与人工签收台账包" / "红线解锁人工签收台账_最新.json"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版红线解锁生效前总验收矩阵与人工签收台账包验收"
LATEST_LOG = LOG_DIR / "full-delivery-redline-unlock-preactivation-ledger-verify-最新.json"


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
    matrix = read_json(MATRIX_JSON) if MATRIX_JSON.exists() else []
    ledger = read_json(LEDGER_JSON) if LEDGER_JSON.exists() else []

    if package.get("状态") != "full_delivery_redline_unlock_pre_activation_acceptance_ledger_ready":
        errors.append("总包状态不是生效前总验收台账就绪")
    if len(matrix) < 7:
        errors.append("总验收矩阵少于7项")
    if len(ledger) != len(matrix):
        errors.append("人工签收台账与总验收矩阵数量不一致")

    matrix_allowed = [item for item in matrix if item.get("允许进入生效") is not False or item.get("允许自动执行") is not False]
    ledger_allowed = [item for item in ledger if item.get("允许进入生效") is not False or item.get("允许自动执行") is not False]
    signed = [item for item in ledger if item.get("签收状态") != "待签收"]
    missing_sources = [
        item for item in matrix if not item.get("确认单存在") or not item.get("拒收样本存在") or not item.get("回滚演练存在")
    ]
    missing_required = [item for item in matrix if not all(item.get("必填项覆盖", {}).values())]

    if matrix_allowed:
        errors.append("总验收矩阵存在允许生效或自动执行项")
    if ledger_allowed:
        errors.append("人工签收台账存在允许生效或自动执行项")
    if signed:
        errors.append("存在非待签收台账项")
    if missing_sources:
        errors.append("存在来源材料不完整的矩阵项")
    if missing_required:
        errors.append("存在必填项覆盖不完整的矩阵项")
    if package.get("安全边界", {}).get("红线解锁生效") is not False:
        errors.append("安全边界未保持红线解锁不生效")

    result = {
        "名称": "完全交付使用版红线解锁生效前总验收矩阵与人工签收台账包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not errors,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "矩阵项数量": len(matrix),
            "台账项数量": len(ledger),
            "待签收数量": len([item for item in ledger if item.get("签收状态") == "待签收"]),
            "允许进入生效数量": len(matrix_allowed) + len(ledger_allowed),
            "已签收数量": len(signed),
        },
        "验证范围": {
            "总包": str(PACKAGE_JSON),
            "总验收矩阵": str(MATRIX_JSON),
            "人工签收台账": str(LEDGER_JSON),
            "日志": str(LATEST_LOG),
        },
    }
    write_json(LATEST_LOG, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
