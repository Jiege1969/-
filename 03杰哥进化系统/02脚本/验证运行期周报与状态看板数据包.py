# -*- coding: utf-8 -*-
"""验证运行期周报与状态看板数据包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = EVOLUTION_ROOT / "03数据" / "85运行期周报与状态看板数据包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "运行期周报与状态看板数据包验收"

PACKAGE_JSON = DATA_DIR / "运行期周报与状态看板数据包_最新.json"
PACKAGE_MD = DATA_DIR / "运行期周报与状态看板数据包_最新.md"
WEEKLY_MD = DATA_DIR / "运行期周报摘要_最新.md"
DASHBOARD_JSON = DATA_DIR / "状态看板数据_最新.json"
DASHBOARD_MD = DATA_DIR / "状态看板数据_最新.md"
REDLINE_MD = DATA_DIR / "红线状态摘要_最新.md"
GEN_LOG = LOG_DIR / "生成运行期周报与状态看板数据包_最新.json"
VERIFY_JSON = LOG_DIR / "runtime-weekly-dashboard-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, WEEKLY_MD, DASHBOARD_JSON, DASHBOARD_MD, REDLINE_MD, GEN_LOG]
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
    dashboard = json.loads(DASHBOARD_JSON.read_text(encoding="utf-8-sig")) if DASHBOARD_JSON.exists() else {}
    if package.get("状态") != "runtime_weekly_dashboard_ready":
        errors.append("总包状态不正确")
    if dashboard.get("总体状态") != "pass":
        errors.append("看板总体状态不是pass")
    if dashboard.get("总巡检", {}).get("失败", 0) != 0:
        errors.append("总巡检失败数不为0")
    if dashboard.get("一键总回归", {}).get("错误数", 0) != 0:
        errors.append("一键总回归错误数不为0")
    if dashboard.get("交付状态") != "delivery_closeout_ready":
        errors.append("交付状态不正确")
    if dashboard.get("红线全部关闭") is not True:
        errors.append("红线未全部关闭")
    if dashboard.get("红线关闭数量") != dashboard.get("红线总数"):
        errors.append("红线关闭数量不等于总数")
    if len(package.get("红线状态", [])) < 14:
        errors.append("红线状态条目不足")
    for flag, value in package.get("安全边界", {}).items():
        if value is not False:
            errors.append(f"安全边界必须为false：{flag}")
    all_text = json.dumps(package, ensure_ascii=False) + json.dumps(dashboard, ensure_ascii=False)
    for path in REQUIRED_FILES:
        if path.exists() and path.suffix.lower() == ".md":
            all_text += "\n" + path.read_text(encoding="utf-8-sig")
    hits = [marker for marker in FORBIDDEN_MARKERS if marker in all_text]
    if hits:
        errors.append(f"命中禁止开放措辞：{hits}")
    report = {
        "名称": "运行期周报与状态看板数据包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "检查文件数": len(REQUIRED_FILES),
            "红线条目": len(package.get("红线状态", [])),
            "来源数": len(dashboard.get("来源状态", {})),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
