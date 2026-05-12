# -*- coding: utf-8 -*-
"""验证使用者首周试用场景演练包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = EVOLUTION_ROOT / "03数据" / "90使用者首周试用场景演练包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "使用者首周试用场景演练包验收"

PACKAGE_JSON = DATA_DIR / "使用者首周试用场景演练包_最新.json"
PACKAGE_MD = DATA_DIR / "使用者首周试用场景演练包_最新.md"
SCENARIOS_JSON = DATA_DIR / "首周试用场景清单_最新.json"
SCENARIOS_MD = DATA_DIR / "首周试用场景清单_最新.md"
ACCEPTANCE_MD = DATA_DIR / "试用场景验收清单_最新.md"
GEN_LOG = LOG_DIR / "生成使用者首周试用场景演练包_最新.json"
VERIFY_JSON = LOG_DIR / "user-week1-trial-scenarios-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, SCENARIOS_JSON, SCENARIOS_MD, ACCEPTANCE_MD, GEN_LOG]
REQUIRED_SCENARIOS = {"查看系统状态", "税收待复核草案", "股票研究展示", "视频脚本与预检", "运行看板", "问题登记", "继续低风险搭建", "红线停机"}
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
    if package.get("状态") != "user_week1_trial_scenarios_ready":
        errors.append("状态不正确")
    sources = package.get("来源摘要", {})
    if len(sources) < 5:
        errors.append("来源摘要不足5项")
    for name, item in sources.items():
        if item.get("存在") is not True:
            errors.append(f"来源不存在：{name}")
    scenarios = package.get("试用场景", [])
    scenario_names = {item.get("场景") for item in scenarios}
    if not REQUIRED_SCENARIOS.issubset(scenario_names):
        errors.append(f"试用场景不完整：{sorted(scenario_names)}")
    if len(scenarios) < 8:
        errors.append("试用场景不足8条")
    if not any(item.get("红线") is True for item in scenarios):
        errors.append("缺少红线停机场景")
    if not any(item.get("红线") is False for item in scenarios):
        errors.append("缺少低风险试用场景")
    if len(package.get("验收口径", [])) < 3:
        errors.append("验收口径不足3条")
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
        "名称": "使用者首周试用场景演练包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "检查文件数": len(REQUIRED_FILES),
            "来源数": len(sources),
            "场景数": len(scenarios),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
