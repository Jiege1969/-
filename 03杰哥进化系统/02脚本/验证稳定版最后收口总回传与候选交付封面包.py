# -*- coding: utf-8 -*-
"""验证稳定版最后收口总回传与候选交付封面包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
PACKAGE_DIR = EVOLUTION_ROOT / "03数据" / "67稳定版最后收口总回传与候选交付封面包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定版最后收口总回传与候选交付封面包验收"

PACKAGE_JSON = PACKAGE_DIR / "稳定版最后收口总回传与候选交付封面包_最新.json"
CHECK_JSON = PACKAGE_DIR / "稳定版最后收口总回传只读核对_最新.json"
LATEST_LOG = LOG_DIR / "stable-final-closeout-cover-verify-最新.json"

REQUIRED_SECTIONS = ["当前结论", "可用能力", "仍阻断能力", "阅读入口", "核心验收证据", "下一步最小动作"]
REQUIRED_EVIDENCE_CATEGORIES = {"自主巡检快照", "只读总回归", "最终复核", "最终只读总验收", "并行合并验收"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    package: dict[str, Any] = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    check: dict[str, Any] = read_json(CHECK_JSON) if CHECK_JSON.exists() else {}

    if not package:
        errors.append("总包 JSON 不存在")
    if not check:
        errors.append("只读核对 JSON 不存在")

    if package:
        if package.get("状态") != "stable_final_closeout_cover_ready":
            errors.append("总包状态必须为 stable_final_closeout_cover_ready")
        for section in REQUIRED_SECTIONS:
            if not package.get(section):
                errors.append(f"候选交付封面缺少必要栏目：{section}")
        categories = {item.get("类别") for item in package.get("核心验收证据", [])}
        missing_categories = sorted(REQUIRED_EVIDENCE_CATEGORIES - categories)
        if missing_categories:
            errors.append(f"核心验收证据类别缺失：{missing_categories}")
        if len(package.get("核心验收证据", [])) < 5:
            errors.append("核心验收证据不得少于 5 项")
        for item in package.get("核心验收证据", []):
            for key in ["编号", "名称", "类别", "路径", "验收口径", "期望"]:
                if not item.get(key):
                    errors.append(f"核心证据项缺少字段：{item.get('编号')} {key}")
            if item.get("路径") and not Path(item["路径"]).exists():
                errors.append(f"核心证据路径不存在：{item.get('编号')} {item.get('路径')}")
        for name, path_text in package.get("输出文件", {}).items():
            if not Path(path_text).exists():
                errors.append(f"输出文件不存在：{name} {path_text}")
        for flag, value in package.get("只读安全边界", {}).items():
            if value is not False:
                errors.append(f"只读安全边界 {flag} 必须为 false")

    if check:
        if check.get("总体状态") != "pass":
            errors.append("只读核对必须通过")
        summary = check.get("汇总", {})
        if summary.get("错误数") != 0:
            errors.append("只读核对错误数必须为 0")
        if summary.get("失败") != 0:
            errors.append("只读核对失败数必须为 0")
        if summary.get("总数", 0) < 5:
            errors.append("只读核对总数不得少于 5")
        for item in check.get("核对结果", []):
            if item.get("当前结果") != "pass":
                errors.append(f"核心证据未通过：{item.get('编号')} {item.get('名称')}")
        extra = check.get("附加核对", {})
        for key in ["输出文件全部存在", "安全边界全部为false", "封面必要栏目齐全", "证据数量不少于5"]:
            if extra.get(key) is not True:
                errors.append(f"附加核对未通过：{key}")

    report = {
        "名称": "稳定版最后收口总回传与候选交付封面包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "错误数": len(errors),
        "指标": {
            "核心验收证据": len(package.get("核心验收证据", [])) if package else 0,
            "核心验收证据类别": len({item.get("类别") for item in package.get("核心验收证据", [])}) if package else 0,
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
