# -*- coding: utf-8 -*-
"""验证首周运行趋势与问题升级包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = EVOLUTION_ROOT / "03数据" / "83首周运行趋势与问题升级包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "首周运行趋势与问题升级包验收"

PACKAGE_JSON = DATA_DIR / "首周运行趋势与问题升级包_最新.json"
PACKAGE_MD = DATA_DIR / "首周运行趋势与问题升级包_最新.md"
TREND_JSON = DATA_DIR / "首周运行趋势记录模板_最新.json"
TREND_MD = DATA_DIR / "首周运行趋势记录模板_最新.md"
ESCALATION_MD = DATA_DIR / "问题升级矩阵_最新.md"
WEEK_REVIEW_MD = DATA_DIR / "首周复盘清单_最新.md"
GEN_LOG = LOG_DIR / "生成首周运行趋势与问题升级包_最新.json"
VERIFY_JSON = LOG_DIR / "week1-runtime-trend-escalation-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, TREND_JSON, TREND_MD, ESCALATION_MD, WEEK_REVIEW_MD, GEN_LOG]
FORBIDDEN_MARKERS = [
    "允许真实发送",
    "允许真实触发",
    "允许接券商",
    "允许交易",
    "允许登录电子税务局",
    "允许接财税软件",
    "允许真实渲染",
    "允许自动发布",
    "允许写正式规则",
    "允许自动转正式规则",
    "允许重载19310",
    "允许重载19302",
]


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"缺少文件：{path}")
    package = json.loads(PACKAGE_JSON.read_text(encoding="utf-8-sig")) if PACKAGE_JSON.exists() else {}
    if package.get("状态") != "week1_trend_escalation_ready":
        errors.append("状态不正确")
    if package.get("当前总巡检", {}).get("总体状态") != "pass":
        errors.append("当前总巡检不是pass")
    if package.get("当前总回归", {}).get("指标", {}).get("错误数", 0) != 0:
        errors.append("当前总回归错误数不为0")
    if len(package.get("趋势记录模板", [])) != 7:
        errors.append("趋势记录模板必须为7天")
    if len(package.get("问题升级矩阵", [])) < 5:
        errors.append("问题升级矩阵不足5级")
    if len(package.get("周复盘清单", [])) < 5:
        errors.append("周复盘清单不足5项")
    if not any(item.get("是否需总管确认") is True for item in package.get("问题升级矩阵", [])):
        errors.append("升级矩阵缺少需总管确认项")
    if not any(item.get("是否需总管确认") is False for item in package.get("问题升级矩阵", [])):
        errors.append("升级矩阵缺少低风险自主项")
    for flag, value in package.get("安全边界", {}).items():
        if value is not False:
            errors.append(f"安全边界必须为false：{flag}")
    all_text = json.dumps(package, ensure_ascii=False)
    for path in REQUIRED_FILES:
        if path.exists() and path.suffix.lower() == ".md":
            all_text += "\n" + path.read_text(encoding="utf-8-sig")
    hits = [marker for marker in FORBIDDEN_MARKERS if marker in all_text]
    if hits:
        errors.append(f"命中禁止开放措辞：{hits}")
    report = {
        "名称": "首周运行趋势与问题升级包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "检查文件数": len(REQUIRED_FILES),
            "趋势天数": len(package.get("趋势记录模板", [])),
            "升级级别": len(package.get("问题升级矩阵", [])),
            "周复盘项": len(package.get("周复盘清单", [])),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
