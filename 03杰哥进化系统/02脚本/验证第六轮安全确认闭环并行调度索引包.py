# -*- coding: utf-8 -*-
"""验证第六轮安全确认闭环并行调度索引包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "82第六轮安全确认闭环并行调度索引包" / "第六轮安全确认闭环并行调度索引包_最新.json"
LOG_DIR = ROOT / "04日志" / "第六轮安全确认闭环并行调度索引包验收"
LATEST_LOG = LOG_DIR / "parallel-round6-safety-confirmation-loop-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def log_passed(path: Path) -> bool:
    if not path.exists():
        return False
    data = read_json(path)
    if data.get("通过") is True and data.get("指标", {}).get("错误数", data.get("错误数", 0)) == 0:
        return True
    if data.get("总体状态") == "pass" and data.get("汇总", {}).get("失败", data.get("错误数", 0)) == 0:
        return True
    if data.get("passed") is True and data.get("error_count", 0) == 0:
        return True
    if data.get("status") == "pass" and data.get("error_count", 0) == 0:
        return True
    if data.get("error_count") == 0:
        checks = data.get("检查结果", data.get("检查项", []))
        if isinstance(checks, list) and checks and all(item.get("通过") is True for item in checks):
            return True
    if data.get("错误数") == 0 and data.get("通过数", 0) > 0:
        checks = data.get("检查项", [])
        if isinstance(checks, list) and all(item.get("通过") is True for item in checks):
            return True
    return False


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    if asset.get("状态") != "parallel_round6_safety_confirmation_loop_ready":
        errors.append("状态不正确")
    if len(asset.get("并行任务", [])) < 3:
        errors.append("并行任务不足")
    for item in asset.get("并行任务", []):
        path = Path(item.get("验收日志", ""))
        if path.exists() and not log_passed(path):
            errors.append(f"验收日志存在但未通过：{path}")
    for path in asset.get("输出文件", {}).values():
        if not Path(path).exists():
            errors.append(f"输出文件不存在：{path}")
    for flag, value in asset.get("安全边界", {}).items():
        if value is not False:
            errors.append(f"安全边界 {flag} 必须为 false")
    report = {
        "名称": "第六轮安全确认闭环并行调度索引包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {"并行任务": len(asset.get("并行任务", [])), "错误数": len(errors)},
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
