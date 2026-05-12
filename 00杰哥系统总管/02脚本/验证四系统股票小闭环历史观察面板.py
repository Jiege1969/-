#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
名称：验证四系统股票小闭环历史观察面板.py
作用：验证历史观察面板已纳入主闭环总验收、完成观察记录、关键文件和安全边界，避免只生成不验收。
输入：生成四系统股票小闭环历史观察面板.py 输出的最新 JSON/Markdown。
输出：00杰哥系统总管/04日志/四系统小闭环/four-system-stock-loop-history-panel-verify-最新.json。
安全边界：只运行生成脚本并读取本地观察面板；不触发n8n，不发送企业微信，不重启服务，不写股票业务库，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建，用于完成观察态纳入历史观察面板后的配套验收。
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
SCRIPT = MANAGER / "02脚本" / "生成四系统股票小闭环历史观察面板.py"
LATEST_JSON = MANAGER / "03数据" / "四系统小闭环" / "四系统股票小闭环历史观察面板_最新.json"
LATEST_MD = MANAGER / "03数据" / "四系统小闭环" / "四系统股票小闭环历史观察面板_最新.md"
LOG_DIR = MANAGER / "04日志" / "四系统小闭环"


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
    md_text = LATEST_MD.read_text(encoding="utf-8-sig") if LATEST_MD.exists() else ""
    main_acceptance = report.get("主闭环总验收", {}) if isinstance(report.get("主闭环总验收"), dict) else {}
    observation = report.get("完成观察记录", {}) if isinstance(report.get("完成观察记录"), dict) else {}
    observation_verify = report.get("完成观察记录验证", {}) if isinstance(report.get("完成观察记录验证"), dict) else {}
    key_files = report.get("关键文件", {}) if isinstance(report.get("关键文件"), dict) else {}
    boundary = report.get("安全边界", {}) if isinstance(report.get("安全边界"), dict) else {}

    checks = [
        check("生成脚本存在", SCRIPT.exists(), str(SCRIPT)),
        check("生成脚本执行成功", proc.returncode == 0, {"stdout": proc.stdout[-500:], "stderr": proc.stderr[-500:]}),
        check("最新JSON存在", LATEST_JSON.exists() and LATEST_JSON.stat().st_size > 1000, str(LATEST_JSON)),
        check("最新Markdown存在", LATEST_MD.exists() and LATEST_MD.stat().st_size > 800, str(LATEST_MD)),
        check("主闭环总验收已纳入", ("完成观察" in str(main_acceptance.get("总验收结论", "")) or "观察期" in str(main_acceptance.get("总验收结论", ""))) and main_acceptance.get("失败数量") == 0, main_acceptance.get("总验收结论")),
        check("完成观察记录已纳入", "完成观察态" in str(observation.get("总结论", "")), observation.get("总结论")),
        check("完成观察记录验证已纳入", observation_verify.get("失败") == 0, observation_verify),
        check("历史执行记录存在", int(report.get("覆盖执行次数") or 0) > 0, report.get("覆盖执行次数")),
        check("关键文件全部存在", bool(key_files) and all(item.get("存在") is True for item in key_files.values()), key_files),
        check("Markdown包含完成观察态章节", "## 二、完成观察态" in md_text and "观察期状态" in md_text, ""),
        check("下一步观察包含24小时或完整业务周期", any("24小时" in item or "完整业务周期" in item for item in report.get("下一步观察", [])), report.get("下一步观察", [])),
        check("安全边界全部关闭", bool(boundary) and all(value is False for value in boundary.values()), boundary),
        check("明确不更新施工接续包", boundary.get("是否更新施工接续包") is False, boundary),
    ]

    ok = all(item["通过"] for item in checks)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": sum(1 for item in checks if item["通过"]),
        "失败": sum(1 for item in checks if not item["通过"]),
        "检查项": checks,
        "报告": str(LATEST_JSON),
    }
    latest = LOG_DIR / "four-system-stock-loop-history-panel-verify-最新.json"
    latest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(latest)}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
