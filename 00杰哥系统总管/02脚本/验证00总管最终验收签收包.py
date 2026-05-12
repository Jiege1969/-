# -*- coding: utf-8 -*-
"""Read-only validator for the 00 manager final acceptance sign-off package."""
from __future__ import annotations

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\杰哥智能化系统\00杰哥系统总管")
PACKAGE_JSON = ROOT / r"03数据\运行状态\00总管_最终验收签收包_最新.json"
PACKAGE_MD = ROOT / r"03数据\运行状态\00总管_最终验收签收包_最新.md"
RECYCLE_JSON = ROOT / r"03数据\并行回收\00总管_最终验收签收包回收报告_最新.json"
RECYCLE_MD = ROOT / r"03数据\并行回收\00总管_最终验收签收包回收报告_最新.md"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(condition: bool, code: str, failures: list[str], detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    suffix = f" {detail}" if detail else ""
    print(f"{status} {code}{suffix}")
    if not condition:
        failures.append(code)


def all_named_pass(items, names: set[str]) -> bool:
    indexed = {item.get("编号"): item for item in items}
    return names.issubset(indexed) and all(indexed[name].get("通过") is True for name in names)


def all_delivery_zero(items, names: set[str]) -> bool:
    indexed = {item.get("编号"): item for item in items}
    return names.issubset(indexed) and all(indexed[name].get("交付阻断") == 0 for name in names)


def main() -> int:
    failures: list[str] = []
    for code, path in {
        "PACKAGE_JSON_EXISTS": PACKAGE_JSON,
        "PACKAGE_MD_EXISTS": PACKAGE_MD,
        "RECYCLE_JSON_EXISTS": RECYCLE_JSON,
        "RECYCLE_MD_EXISTS": RECYCLE_MD,
    }.items():
        check(path.exists(), code, failures, str(path))

    if not PACKAGE_JSON.exists() or not RECYCLE_JSON.exists():
        print("RESULT FAIL")
        return 1

    data = load_json(PACKAGE_JSON)
    recycle = load_json(RECYCLE_JSON)

    check(data.get("结论") == "通过", "PACKAGE_RESULT_PASS", failures)
    check(recycle.get("结论") == "通过", "RECYCLE_RESULT_PASS", failures)
    check(data.get("读取模式") == "read_only_local_files", "READ_ONLY_MODE", failures)
    check(data.get("是否重算进度") is False, "NO_PROGRESS_RECALC", failures)
    check(data.get("是否改写进度口径") is False, "NO_PROGRESS_WORDING_CHANGE", failures)
    check(data.get("是否触发外部服务") is False, "NO_EXTERNAL_SERVICE", failures)
    check(data.get("是否执行真实动作") is False, "NO_REAL_ACTION", failures)
    check(data.get("当前进度口径") == "92%-96%", "PROGRESS_92_96", failures)
    check(data.get("剩余有效工时") == "2-6小时", "HOURS_2_6", failures)

    zero = data.get("交付阻断归零", {})
    check(zero.get("是否归零") is True, "DELIVERY_BLOCKERS_ZERO", failures)
    check(zero.get("交付阻断数量") == 0, "DELIVERY_BLOCKER_COUNT_0", failures)

    tasks = data.get("签收范围", [])
    check(all_named_pass(tasks, {"L", "M", "N", "O"}), "LMNO_ALL_PASS", failures)
    check(all_delivery_zero(tasks, {"L", "M", "N", "O"}), "LMNO_DELIVERY_BLOCKERS_0", failures)
    check(all_named_pass(tasks, {"H", "I", "J", "K"}), "HIJK_ALL_PASS", failures)
    check(all_delivery_zero(tasks, {"H", "I", "J", "K"}), "HIJK_DELIVERY_BLOCKERS_0", failures)
    check(all_named_pass(tasks, {"D", "E", "F", "G"}), "DEFG_ALL_PASS", failures)
    check(all_delivery_zero(tasks, {"D", "E", "F", "G"}), "DEFG_DELIVERY_BLOCKERS_0", failures)

    required_sections = {
        "任务契约层",
        "02入口操作卡",
        "03规则封版",
        "股票analysis-only",
        "安全闸门",
    }
    sections = {item.get("名称") for item in data.get("签收检查项", [])}
    check(required_sections.issubset(sections), "REQUIRED_SIGNOFF_SECTIONS_PRESENT", failures)
    checks = {item.get("名称"): item for item in data.get("签收检查项", [])}
    check(all(checks[name].get("通过") is True for name in required_sections), "REQUIRED_SIGNOFF_SECTIONS_PASS", failures)

    gates = data.get("仍关闭安全闸门", [])
    check(len(gates) >= 9, "CLOSED_GATE_COUNT_GE_9", failures)
    check(all(item.get("状态") in {"关闭", "关闭/暂停"} for item in gates), "ALL_GATES_CLOSED", failures)

    boundary = data.get("真实动作安全边界", {})
    check(boundary and all(value is False for value in boundary.values()), "REAL_ACTION_BOUNDARY_ALL_FALSE", failures)

    remaining = data.get("最终交付确认前剩余动作", [])
    check(len(remaining) >= 5, "REMAINING_ACTIONS_PRESENT", failures)
    check(all(item.get("可自动打开真实动作") is False for item in remaining), "REMAINING_ACTIONS_NO_AUTO_REAL_ACTION", failures)

    source_files = data.get("源证据文件", [])
    missing = [path for path in source_files if not Path(path).exists()]
    check(len(source_files) >= 8, "SOURCE_FILE_COUNT_GE_8", failures)
    check(not missing, "SOURCE_FILES_EXIST", failures)
    for path in missing:
        print(f"MISSING {path}")

    generated = recycle.get("输出文件", {})
    check(str(PACKAGE_JSON) in generated.values(), "RECYCLE_REFERENCES_PACKAGE_JSON", failures)
    check(str(PACKAGE_MD) in generated.values(), "RECYCLE_REFERENCES_PACKAGE_MD", failures)
    check(str(RECYCLE_JSON) in generated.values(), "RECYCLE_REFERENCES_RECYCLE_JSON", failures)
    check(str(RECYCLE_MD) in generated.values(), "RECYCLE_REFERENCES_RECYCLE_MD", failures)

    if failures:
        print("RESULT FAIL")
        return 1
    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
