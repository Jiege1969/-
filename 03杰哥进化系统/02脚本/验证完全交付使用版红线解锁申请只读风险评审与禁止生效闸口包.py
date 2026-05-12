# -*- coding: utf-8 -*-
"""验证完全交付使用版红线解锁申请只读风险评审与禁止生效闸口包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "107完全交付使用版红线解锁申请只读风险评审与禁止生效闸口包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版红线解锁申请只读风险评审与禁止生效闸口包验收"
PACKAGE_JSON = DATA_DIR / "完全交付使用版红线解锁申请只读风险评审与禁止生效闸口包_最新.json"
RISK_REVIEW_JSON = DATA_DIR / "红线解锁申请只读风险评审_最新.json"
NO_ACTIVATE_GATE_JSON = DATA_DIR / "红线解锁禁止生效闸口_最新.json"
LOG_JSON = LOG_DIR / "full-delivery-redline-unlock-readonly-risk-gate-verify-最新.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    package = read_json(PACKAGE_JSON)
    reviews = read_json(RISK_REVIEW_JSON)
    gate = read_json(NO_ACTIVATE_GATE_JSON)
    errors: list[str] = []

    if package.get("状态") != "full_delivery_redline_unlock_readonly_risk_gate_ready":
        errors.append("总包状态不正确")
    if not isinstance(reviews, list) or len(reviews) < 7:
        errors.append("红线评审数量不足")
    if any(item.get("允许生效") is not False for item in reviews if isinstance(item, dict)):
        errors.append("所有红线必须禁止生效")
    if any(item.get("允许自动执行") is not False for item in reviews if isinstance(item, dict)):
        errors.append("所有红线必须禁止自动执行")
    if gate.get("红线解锁生效") is not False or gate.get("允许生效数量") != 0:
        errors.append("红线解锁不得生效")
    if gate.get("全部未确认") is not True or gate.get("全部禁止自动执行") is not True:
        errors.append("闸口必须保持全部未确认且禁止自动执行")
    if not all(value is False for value in package.get("安全边界", {}).values()):
        errors.append("安全边界必须全部为 false")
    for path_text in package.get("输出文件", {}).values():
        if not Path(path_text).exists():
            errors.append(f"输出文件不存在：{path_text}")

    report = {
        "名称": "完全交付使用版红线解锁申请只读风险评审与禁止生效闸口包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not errors,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "评审红线数": len(reviews) if isinstance(reviews, list) else 0,
            "允许生效数量": gate.get("允许生效数量"),
            "禁止生效数量": gate.get("禁止生效数量"),
            "红线解锁生效": gate.get("红线解锁生效"),
        },
        "验证范围": {"总包": str(PACKAGE_JSON), "只读风险评审": str(RISK_REVIEW_JSON), "禁止生效闸口": str(NO_ACTIVATE_GATE_JSON), "日志": str(LOG_JSON)},
    }
    write_json(LOG_JSON, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
