#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
名称：验证股票四系统闭环完成观察记录.py
作用：验证股票四系统闭环完成观察记录存在、关键验收全部通过且安全边界未越界。
输入：生成股票四系统闭环完成观察记录.py 输出的最新 JSON/Markdown。
输出：00杰哥系统总管/04日志/四系统小闭环/stock-four-system-closed-loop-completion-observation-verify-最新.json。
安全边界：只运行生成脚本并读取本地观察记录；不触发n8n，不发送企业微信，不重启服务，不写股票业务库，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建，用于闭环完成态验收。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
SCRIPT = MANAGER / "02脚本" / "生成股票四系统闭环完成观察记录.py"
LATEST_JSON = MANAGER / "03数据" / "四系统小闭环" / "股票四系统闭环完成观察记录_最新.json"
LATEST_MD = MANAGER / "03数据" / "四系统小闭环" / "股票四系统闭环完成观察记录_最新.md"


def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default
    return default


def check(name: str, passed: bool, note: Any = "") -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "说明": note}


def main() -> int:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=str(MANAGER),
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    report = load_json(LATEST_JSON, {})
    boundary = report.get("安全边界", {}) if isinstance(report.get("安全边界"), dict) else {}
    key_checks = report.get("关键验收", []) if isinstance(report.get("关键验收"), list) else []
    completed = report.get("已完成链路", []) if isinstance(report.get("已完成链路"), list) else []
    followups = report.get("后续观察事项", []) if isinstance(report.get("后续观察事项"), list) else []

    checks = [
        check("生成脚本存在", SCRIPT.exists(), str(SCRIPT)),
        check("生成脚本执行成功", proc.returncode == 0, {"stdout": proc.stdout[-500:], "stderr": proc.stderr[-500:]}),
        check("最新JSON存在", LATEST_JSON.exists() and LATEST_JSON.stat().st_size > 500, str(LATEST_JSON)),
        check("最新Markdown存在", LATEST_MD.exists() and LATEST_MD.stat().st_size > 300, str(LATEST_MD)),
        check("总结论进入完成观察态", "完成观察态" in str(report.get("总结论", "")), report.get("总结论")),
        check("关键验收全部通过", bool(key_checks) and all(item.get("通过") is True for item in key_checks), key_checks),
        check("194写入结果已纳入", any(item.get("名称") == "194模板同步执行" and item.get("通过") is True for item in key_checks), key_checks),
        check("已完成链路包含205到194", all(any(token in item for item in completed) for token in ["205", "191 CSV", "197", "193", "194"]), completed),
        check("观察期事项存在", any("24小时" in item or "完整业务周期" in item for item in followups), followups),
        check("安全边界全部关闭", bool(boundary) and all(value is False for value in boundary.values()), boundary),
        check("明确不更新施工接续包", boundary.get("更新施工接续包") is False, boundary),
    ]

    ok = all(item["通过"] for item in checks)
    log_dir = MANAGER / "04日志" / "四系统小闭环"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": sum(1 for item in checks if item["通过"]),
        "失败": sum(1 for item in checks if not item["通过"]),
        "检查项": checks,
        "报告": str(LATEST_JSON),
    }
    latest = log_dir / "stock-four-system-closed-loop-completion-observation-verify-最新.json"
    stamped = log_dir / f"stock-four-system-closed-loop-completion-observation-verify-{stamp}.json"
    latest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    stamped.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(latest)}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
