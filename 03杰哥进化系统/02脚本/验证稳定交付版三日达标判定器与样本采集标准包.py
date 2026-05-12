# -*- coding: utf-8 -*-
"""验证稳定交付版三日达标判定器与样本采集标准包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "84稳定交付版三日达标判定器与样本采集标准包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定交付版三日达标判定器与样本采集标准包验收"

ASSET_JSON = DATA_DIR / "稳定交付版三日达标判定器与样本采集标准包_最新.json"
STANDARD_JSON = DATA_DIR / "稳定版自然日样本采集标准_最新.json"
DECISION_JSON = DATA_DIR / "稳定版三日达标判定结果_最新.json"
CHECK_JSON = DATA_DIR / "稳定版三日达标判定器只读核对_最新.json"
LATEST_LOG = LOG_DIR / "stable-delivery-three-day-acceptance-judge-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    standard = read_json(STANDARD_JSON) if STANDARD_JSON.exists() else {}
    decision = read_json(DECISION_JSON) if DECISION_JSON.exists() else {}
    check = read_json(CHECK_JSON) if CHECK_JSON.exists() else {}

    if not asset:
        errors.append(f"总包不存在：{ASSET_JSON}")
    if not standard:
        errors.append(f"样本采集标准不存在：{STANDARD_JSON}")
    if not decision:
        errors.append(f"三日达标判定不存在：{DECISION_JSON}")
    if not check:
        errors.append(f"只读核对不存在：{CHECK_JSON}")

    if asset:
        if asset.get("状态") != "stable_delivery_three_day_acceptance_judge_ready":
            errors.append("总包状态必须为 stable_delivery_three_day_acceptance_judge_ready")
        if asset.get("指标", {}).get("不同自然日通过样本数", 0) < 3 and asset.get("指标", {}).get("三日达标") is not False:
            errors.append("不足3个不同自然日通过样本时，三日达标必须为false")
        if not all(value is False for value in asset.get("安全边界", {}).values()):
            errors.append("安全边界必须全部为false")
        for path_text in asset.get("输出文件", {}).values():
            if not Path(path_text).exists():
                errors.append(f"输出文件不存在：{path_text}")

    if standard and len(standard.get("标准", [])) < 5:
        errors.append("样本采集标准不得少于5条")
    if decision:
        if decision.get("是否生成未来样本") is not False:
            errors.append("判定结果不得生成未来样本")
        if decision.get("不同自然日通过样本数", 0) < 3 and decision.get("三日达标") is not False:
            errors.append("判定结果不足3日时必须未达标")
    if check:
        if check.get("总体状态") != "pass":
            errors.append("只读核对总体状态必须为pass")
        if check.get("汇总", {}).get("失败") != 0:
            errors.append("只读核对失败数必须为0")

    report = {
        "名称": "稳定交付版三日达标判定器与样本采集标准包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "不同自然日通过样本数": decision.get("不同自然日通过样本数") if decision else None,
            "仍缺自然日样本数": decision.get("仍缺自然日样本数") if decision else None,
            "三日达标": decision.get("三日达标") if decision else None,
            "是否生成未来样本": decision.get("是否生成未来样本") if decision else None,
        },
        "验证范围": {
            "总包": str(ASSET_JSON),
            "样本标准": str(STANDARD_JSON),
            "判定结果": str(DECISION_JSON),
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
