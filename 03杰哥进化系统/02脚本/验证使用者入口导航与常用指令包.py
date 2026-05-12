# -*- coding: utf-8 -*-
"""验证使用者入口导航与常用指令包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = EVOLUTION_ROOT / "03数据" / "88使用者入口导航与常用指令包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "使用者入口导航与常用指令包验收"

PACKAGE_JSON = DATA_DIR / "使用者入口导航与常用指令包_最新.json"
PACKAGE_MD = DATA_DIR / "使用者入口导航与常用指令包_最新.md"
NAV_MD = DATA_DIR / "使用者入口导航_最新.md"
COMMANDS_JSON = DATA_DIR / "常用指令清单_最新.json"
COMMANDS_MD = DATA_DIR / "常用指令清单_最新.md"
SAFETY_MD = DATA_DIR / "使用安全边界速查_最新.md"
GEN_LOG = LOG_DIR / "生成使用者入口导航与常用指令包_最新.json"
VERIFY_JSON = LOG_DIR / "user-entry-navigation-commands-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, NAV_MD, COMMANDS_JSON, COMMANDS_MD, SAFETY_MD, GEN_LOG]
REQUIRED_SCENARIOS = {"看系统状态", "税收资料草案", "股票研究", "视频脚本预检", "看运行日报", "继续低风险搭建", "触碰外部动作"}
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
    if package.get("状态") != "user_entry_navigation_ready":
        errors.append("状态不正确")
    entries = package.get("入口索引", {})
    if len(entries) < 6:
        errors.append("入口索引不足6项")
    for name, item in entries.items():
        if item.get("存在") is not True:
            errors.append(f"入口不存在：{name}")
    commands = package.get("常用指令", [])
    scenarios = {item.get("场景") for item in commands}
    if not REQUIRED_SCENARIOS.issubset(scenarios):
        errors.append(f"常用指令场景不完整：{sorted(scenarios)}")
    if not any(item.get("红线") is True for item in commands):
        errors.append("常用指令缺少红线场景")
    if not any(item.get("红线") is False for item in commands):
        errors.append("常用指令缺少低风险场景")
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
        "名称": "使用者入口导航与常用指令包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "检查文件数": len(REQUIRED_FILES),
            "入口数": len(entries),
            "指令数": len(commands),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
