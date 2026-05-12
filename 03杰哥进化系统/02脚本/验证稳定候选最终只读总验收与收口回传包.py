# -*- coding: utf-8 -*-
"""验证稳定候选最终只读总验收与收口回传包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
PACKAGE_DIR = ROOT / "03数据" / "63稳定候选最终只读总验收与收口回传包"
LOG_DIR = ROOT / "04日志" / "稳定候选最终只读总验收与收口回传包验收"

ASSET_JSON = PACKAGE_DIR / "稳定候选最终只读总验收与收口回传包_最新.json"
CHECK_JSON = PACKAGE_DIR / "稳定候选最终只读总验收核对_最新.json"
LATEST_LOG = LOG_DIR / "stable-candidate-final-readonly-acceptance-closeout-verify-最新.json"

REQUIRED_CATEGORIES = {
    "日常总回归",
    "自主巡检快照",
    "稳定候选最终复核",
    "最终总索引",
    "可交付声明",
    "三日首日样本",
    "异常演练",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset: dict[str, Any] = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    check: dict[str, Any] = read_json(CHECK_JSON) if CHECK_JSON.exists() else {}

    if not asset:
        errors.append("总包 JSON 不存在")
    if not check:
        errors.append("只读总验收核对 JSON 不存在")

    if asset:
        if asset.get("状态") != "stable_candidate_final_readonly_acceptance_closeout_ready":
            errors.append("总包状态必须为 stable_candidate_final_readonly_acceptance_closeout_ready")
        evidence = asset.get("证据清单", [])
        categories = {item.get("类别") for item in evidence}
        missing_categories = sorted(REQUIRED_CATEGORIES - categories)
        if missing_categories:
            errors.append(f"证据类别缺失：{missing_categories}")
        if len(evidence) < 7:
            errors.append("证据清单不得少于 7 项")
        for item in evidence:
            for key in ["编号", "名称", "类别", "路径", "通过口径"]:
                if not item.get(key):
                    errors.append(f"证据项缺少字段：{item.get('编号')} {key}")
            if item.get("路径") and not Path(item["路径"]).exists():
                errors.append(f"证据路径不存在：{item.get('编号')} {item.get('路径')}")
        for name, path_text in asset.get("输出文件", {}).items():
            if not Path(path_text).exists():
                errors.append(f"输出文件不存在：{name} {path_text}")
        for flag, value in asset.get("安全边界", {}).items():
            if value is not False:
                errors.append(f"安全边界 {flag} 必须为 false")

    if check:
        if check.get("总体状态") != "pass":
            errors.append("只读总验收核对必须通过")
        summary = check.get("汇总", {})
        if summary.get("错误数") != 0:
            errors.append("只读总验收核对错误数必须为 0")
        if summary.get("失败") != 0:
            errors.append("只读总验收核对失败数必须为 0")
        if summary.get("总数", 0) < 7:
            errors.append("只读总验收核对总数不得少于 7")
        for item in check.get("核对结果", []):
            if item.get("当前结果") != "pass":
                errors.append(f"证据未通过：{item.get('编号')} {item.get('名称')}")

    report = {
        "名称": "稳定候选最终只读总验收与收口回传包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "错误数": len(errors),
        "指标": {
            "证据数量": len(asset.get("证据清单", [])) if asset else 0,
            "证据类别数量": len({item.get("类别") for item in asset.get("证据清单", [])}) if asset else 0,
            "核对总数": check.get("汇总", {}).get("总数", 0) if check else 0,
            "核对失败": check.get("汇总", {}).get("失败", 0) if check else 0,
            "错误数": len(errors),
        },
    }

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
