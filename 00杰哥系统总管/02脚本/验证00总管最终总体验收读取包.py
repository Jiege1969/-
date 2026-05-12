# -*- coding: utf-8 -*-
"""Read-only validator for the final 00 manager acceptance read package."""
from __future__ import annotations

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\杰哥智能化系统\00杰哥系统总管")
PACKAGE_JSON = ROOT / r"03数据\运行状态\最终总体验收读取包_最新.json"
PACKAGE_MD = ROOT / r"03数据\运行状态\最终总体验收读取包_最新.md"
RECYCLE_JSON = ROOT / r"03数据\并行回收\00总管_最终总体验收读取回收报告_最新.json"
RECYCLE_MD = ROOT / r"03数据\并行回收\00总管_最终总体验收读取回收报告_最新.md"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(condition: bool, code: str, failures: list[str]):
    status = "PASS" if condition else "FAIL"
    print(f"{status} {code}")
    if not condition:
        failures.append(code)


def main() -> int:
    failures: list[str] = []
    expected_paths = {
        "PACKAGE_JSON_EXISTS": PACKAGE_JSON,
        "PACKAGE_MD_EXISTS": PACKAGE_MD,
        "RECYCLE_JSON_EXISTS": RECYCLE_JSON,
        "RECYCLE_MD_EXISTS": RECYCLE_MD,
    }
    for code, path in expected_paths.items():
        check(path.exists(), code, failures)
    if not PACKAGE_JSON.exists():
        return 1

    data = load_json(PACKAGE_JSON)
    check(data.get("读取模式") == "read_only_local_files", "READ_ONLY_MODE", failures)
    check(data.get("是否重算进度") is False, "NO_PROGRESS_RECALC", failures)
    check(data.get("是否修改进度口径") is False, "NO_PROGRESS_WORDING_CHANGE", failures)
    check(data.get("是否触发外部服务") is False, "NO_EXTERNAL_SERVICE", failures)
    check(data.get("是否执行真实动作") is False, "NO_REAL_ACTION", failures)

    current = data.get("当前口径", {})
    check(current.get("全盘当前进度") == "88%-93%", "PROGRESS_88_93", failures)
    check(current.get("全盘剩余有效工时") == "5-11小时", "HOURS_5_11", failures)

    zero = data.get("交付阻断归零判定", {})
    check(zero.get("是否归零") is True, "DELIVERY_BLOCKERS_ZERO", failures)
    check(zero.get("交付阻断数量") == 0, "DELIVERY_BLOCKER_COUNT_0", failures)

    coverage = data.get("批次覆盖", {})
    hijk = coverage.get("交付候选HIJK", {})
    defg = coverage.get("最终验收前门禁DEFG", {})
    check(hijk.get("完成任务数量") == hijk.get("任务总数") == 4, "HIJK_4_OF_4", failures)
    check(hijk.get("交付阻断数量") == 0, "HIJK_DELIVERY_BLOCKERS_0", failures)
    check(defg.get("完成任务数量") == defg.get("任务总数") == 4, "DEFG_4_OF_4", failures)
    check(defg.get("交付阻断数量") == 0, "DEFG_DELIVERY_BLOCKERS_0", failures)

    gates = data.get("仍关闭的安全闸门清单", [])
    check(len(gates) >= 8, "CLOSED_GATE_COUNT_GE_8", failures)
    check(all(item.get("状态") in {"关闭", "关闭/暂停"} for item in gates), "ALL_GATES_CLOSED", failures)

    boundary = data.get("真实动作安全边界", {})
    check(boundary and all(value is True for value in boundary.values()), "REAL_ACTION_BOUNDARY_ALL_FORBIDDEN", failures)

    source_files = data.get("源证据文件", [])
    check(len(source_files) >= 16, "SOURCE_FILE_COUNT_GE_16", failures)
    missing = [item.get("路径") for item in source_files if not Path(item.get("路径", "")).exists()]
    check(not missing, "SOURCE_FILES_EXIST", failures)
    if missing:
        for path in missing:
            print(f"MISSING {path}")

    if failures:
        print("RESULT FAIL")
        return 1
    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())