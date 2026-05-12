# -*- coding: utf-8 -*-
"""
名称：验证开机施工准备任务.py
作用：验证开机施工准备自检脚本、计划任务登记和最新施工准备快照可用。
触发方式：python 验证开机施工准备任务.py
依赖：Python标准库；PowerShell；执行开机施工准备自检.ps1；注册开机施工准备任务.ps1。
所属系统：00杰哥系统总管
安全边界：只读计划任务状态并检查本地快照；不创建计划任务；不重启服务；不触发n8n；不发送企业微信；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建开机施工准备任务验收脚本；2026-04-30 计划任务验证改为基于ASCII描述，规避PowerShell 5中文任务名输出编码问题。
标识：startup-construction-preflight-verify
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = system_root()
    manager = root / "00杰哥系统总管"
    preflight = manager / "02脚本" / "执行开机施工准备自检.ps1"
    register = manager / "02脚本" / "注册开机施工准备任务.ps1"
    snapshot_dir = manager / "03数据" / "开机施工准备"
    snapshot_json = snapshot_dir / "startup_construction_preflight_latest.json"
    snapshot_md = snapshot_dir / "startup_construction_preflight_latest.md"
    task_query = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-ScheduledTask -TaskName '杰哥智能化系统_开机施工准备自检' -ErrorAction SilentlyContinue | Select-Object TaskName,State,Description | ConvertTo-Json -Compress",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    task_text = task_query.stdout.strip()
    snapshot = load_json(snapshot_json) if snapshot_json.exists() else {}
    construction = snapshot.get("construction", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "开机施工准备脚本存在", preflight.exists(), str(preflight))
    add_check(checks, "计划任务注册脚本存在", register.exists(), str(register))
    add_check(checks, "计划任务已登记", bool(task_text) and "Jiege intelligent system" in task_text, task_text or task_query.stderr.strip())
    add_check(checks, "最新JSON快照存在", snapshot_json.exists() and snapshot.get("mode") == "construction-preflight", str(snapshot_json))
    add_check(checks, "最新Markdown摘要存在", snapshot_md.exists() and "Startup Construction Preflight" in (snapshot_md.read_text(encoding="utf-8") if snapshot_md.exists() else ""), str(snapshot_md))
    add_check(checks, "开机准备包含进度报告", construction.get("current_progress_report", {}).get("ok") is True, construction.get("current_progress_report", {}))
    add_check(checks, "安全边界关闭真实动作", all(item is False for item in snapshot.get("safety_boundary", {}).values()), snapshot.get("safety_boundary", {}))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "开机施工准备任务已可用于下次登录后的施工准备。" if failed == 0 else "开机施工准备任务仍有失败项。",
    }
    output_dir = manager / "04日志" / "开机施工准备"
    output = output_dir / "startup-construction-preflight-verify-最新.json"
    latest = output_dir / "startup-construction-preflight-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
