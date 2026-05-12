# -*- coding: utf-8 -*-
"""只读验收多对话框并行施工冲突扫描包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "110多对话框并行施工冲突扫描包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "多对话框并行施工冲突扫描包验收"

PACKAGE_JSON = DATA_DIR / "多对话框并行施工冲突扫描包_最新.json"
PACKAGE_MD = DATA_DIR / "多对话框并行施工冲突扫描包_最新.md"
RECENT_MD = DATA_DIR / "最近施工文件扫描_最新.md"
RISK_MD = DATA_DIR / "高风险冲突扫描_最新.md"
PORT_MD = DATA_DIR / "端口状态只读记录_最新.md"
GEN_LOG = LOG_DIR / "生成多对话框并行施工冲突扫描包_最新.json"
VERIFY_LOG = LOG_DIR / "parallel-dialogue-construction-conflict-scan-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, RECENT_MD, RISK_MD, PORT_MD, GEN_LOG]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"名称": name, "通过": passed, "详情": detail})


def main() -> int:
    checks: list[dict[str, Any]] = []
    package = read_json(PACKAGE_JSON)

    missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
    add_check(checks, "必需文件存在", not missing, "缺失: " + "；".join(missing) if missing else "全部存在")

    add_check(checks, "总包状态合法", package.get("状态") in {"pass", "blocked"}, str(package.get("状态")))
    add_check(checks, "扫描窗口存在", package.get("扫描窗口小时") == 2, str(package.get("扫描窗口小时")))

    metrics = package.get("指标", {})
    add_check(checks, "指标完整", all(key in metrics for key in ["最近文件数", "高风险命中数", "同名最新产物重复组", "红线词命中数", "问题数"]), json.dumps(metrics, ensure_ascii=False))

    ports = package.get("端口状态只读记录", [])
    port_set = {item.get("端口") for item in ports if isinstance(item, dict)}
    add_check(checks, "端口状态记录覆盖19310和19302", {19310, 19302}.issubset(port_set), json.dumps(ports, ensure_ascii=False)[:500])

    safety = package.get("安全边界", {})
    safety_ok = bool(safety) and all(value is False for value in safety.values())
    add_check(checks, "安全边界保持关闭", safety_ok, f"边界项={len(safety)}")

    # 验收脚本不要求扫描结果必须 pass；如果扫描 blocked，也应保留证据供总管判断。
    scan_passed = package.get("状态") == "pass"
    add_check(checks, "扫描已形成总管可判定结果", True, f"扫描状态={package.get('状态')}，问题={len(package.get('问题', []))}")

    passed = sum(1 for item in checks if item["通过"])
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "多对话框并行施工冲突扫描包验收",
        "验收时间": now_text(),
        "通过": not failed,
        "扫描结论通过": scan_passed,
        "指标": {"检查项": len(checks), "通过项": passed, "错误数": len(failed)},
        "检查明细": checks,
        "扫描摘要": {
            "状态": package.get("状态"),
            "指标": metrics,
            "问题": package.get("问题", []),
        },
        "输出文件": {
            "验收日志": str(VERIFY_LOG),
            "总包": str(PACKAGE_JSON),
            "最近施工文件扫描": str(RECENT_MD),
            "高风险冲突扫描": str(RISK_MD),
            "端口状态只读记录": str(PORT_MD),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_LOG.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": result["通过"], "扫描结论通过": scan_passed, "检查项": len(checks), "错误数": len(failed), "日志": str(VERIFY_LOG)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
