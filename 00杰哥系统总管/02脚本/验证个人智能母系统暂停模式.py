# -*- coding: utf-8 -*-
"""
名称：验证个人智能母系统暂停模式.py
作用：验证暂停/恢复标志控制脚本与日常调度状态的联动。
触发方式：python 验证个人智能母系统暂停模式.py
依赖：Python标准库；设置个人智能母系统暂停模式.py；生成个人智能母系统日常调度状态.py。
所属系统：00杰哥系统总管。
输出：00杰哥系统总管/04日志/个人智能母系统日常调度/pause-mode-verify-*.json。
安全边界：只临时设置并恢复暂停标志，写总管验证日志；不停止服务、不重启服务、不触发n8n、不发送企业微信、不调用券商接口、不自动交易。
标识：personal-ai-pause-mode-verify；暂停恢复验收；只控标志。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_py(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )


def add(checks: list[dict[str, Any]], name: str, ok: bool, detail: Any) -> None:
    checks.append({"名称": name, "通过": bool(ok), "说明": detail})


def main() -> int:
    manager = manager_root()
    pause_script = manager / "02脚本" / "设置个人智能母系统暂停模式.py"
    state_script = manager / "02脚本" / "生成个人智能母系统日常调度状态.py"
    flag = manager / "03数据" / "运行状态" / "暂停模式.flag"
    state_latest = manager / "03数据" / "运行状态" / "个人智能母系统日常调度状态_最新.json"
    checks: list[dict[str, Any]] = []

    previous = flag.read_text(encoding="utf-8") if flag.exists() else None
    try:
        pause_run = run_py(pause_script, "--pause", "--reason", "pause-mode-verify")
        add(checks, "暂停命令执行成功", pause_run.returncode == 0 and flag.exists(), pause_run.stdout.strip())

        state_run = run_py(state_script, "--now", "2026-05-06 10:00:00", "--ignore-resource-pressure")
        state = load_json(state_latest, {})
        add(checks, "暂停模式被日常调度识别", state_run.returncode == 0 and state.get("当前状态") == "暂停模式", state)

        resume_run = run_py(pause_script, "--resume", "--reason", "pause-mode-verify-finished")
        add(checks, "恢复命令执行成功", resume_run.returncode == 0 and not flag.exists(), resume_run.stdout.strip())

        state_run2 = run_py(state_script, "--now", "2026-05-06 10:00:00", "--ignore-resource-pressure")
        state2 = load_json(state_latest, {})
        add(checks, "恢复后回到时间窗口状态", state_run2.returncode == 0 and state2.get("当前状态") == "开市轻量待命", state2)
    finally:
        if previous is not None:
            flag.parent.mkdir(parents=True, exist_ok=True)
            flag.write_text(previous, encoding="utf-8")
        elif flag.exists():
            flag.unlink()

    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "个人智能母系统暂停模式验证",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "检查项": checks,
        "安全边界": {
            "是否停止服务": False,
            "是否重启服务": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    out_dir = manager / "04日志" / "个人智能母系统日常调度"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = out_dir / f"pause-mode-verify-{stamp}.json"
    latest = out_dir / "pause-mode-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": report["通过"], "失败": report["失败"], "输出": str(latest)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
