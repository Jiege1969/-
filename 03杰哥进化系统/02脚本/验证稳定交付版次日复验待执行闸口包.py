# -*- coding: utf-8 -*-
"""验证稳定交付版次日复验待执行闸口包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "83稳定交付版次日复验待执行闸口包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定交付版次日复验待执行闸口包验收"

ASSET_JSON = DATA_DIR / "稳定交付版次日复验待执行闸口包_最新.json"
GATE_JSON = DATA_DIR / "稳定版次日复验待执行闸口_最新.json"
CHECK_JSON = DATA_DIR / "稳定版次日复验待执行闸口只读核对_最新.json"
LATEST_LOG = LOG_DIR / "stable-delivery-day2-recheck-pending-gate-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    gate = read_json(GATE_JSON) if GATE_JSON.exists() else {}
    check = read_json(CHECK_JSON) if CHECK_JSON.exists() else {}

    if not asset:
        errors.append(f"总包不存在：{ASSET_JSON}")
    if not gate:
        errors.append(f"闸口不存在：{GATE_JSON}")
    if not check:
        errors.append(f"只读核对不存在：{CHECK_JSON}")

    if asset:
        if asset.get("状态") != "stable_delivery_day2_recheck_pending_gate_ready":
            errors.append("总包状态必须为 stable_delivery_day2_recheck_pending_gate_ready")
        if asset.get("是否生成次日样本") is not False:
            errors.append("总包不得生成次日样本")
        if asset.get("指标", {}).get("首日复验通过") is not True:
            errors.append("首日复验必须已通过")
        if asset.get("指标", {}).get("首日验收通过") is not True:
            errors.append("首日验收必须已通过")
        if asset.get("指标", {}).get("问题项") != 0:
            errors.append("首日问题项必须为 0")
        if not all(value is False for value in asset.get("安全边界", {}).values()):
            errors.append("总包安全边界必须全部为 false")
        for path_text in asset.get("输出文件", {}).values():
            if not Path(path_text).exists():
                errors.append(f"输出文件不存在：{path_text}")

    if gate and gate.get("是否生成次日样本") is not False:
        errors.append("闸口不得生成次日样本")
    if check:
        if check.get("总体状态") != "pass":
            errors.append("只读核对总体状态必须为 pass")
        if check.get("汇总", {}).get("失败") != 0:
            errors.append("只读核对失败数必须为 0")

    report = {
        "名称": "稳定交付版次日复验待执行闸口包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "当前是否可执行次日复验": asset.get("当前是否可执行次日复验") if asset else None,
            "是否生成次日样本": asset.get("是否生成次日样本") if asset else None,
            "首日复验通过": asset.get("指标", {}).get("首日复验通过") if asset else None,
            "首日验收通过": asset.get("指标", {}).get("首日验收通过") if asset else None,
        },
        "验证范围": {"总包": str(ASSET_JSON), "闸口": str(GATE_JSON), "只读核对": str(CHECK_JSON), "日志": str(LATEST_LOG)},
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
