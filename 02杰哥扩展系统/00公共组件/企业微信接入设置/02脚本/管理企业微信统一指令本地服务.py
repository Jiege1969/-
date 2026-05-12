# -*- coding: utf-8 -*-
"""
名称：管理企业微信统一指令本地服务.py
作用：统一管理 127.0.0.1:19310 企业微信统一指令本地服务的启动、停止、重启和状态检查。
触发方式：
  python 管理企业微信统一指令本地服务.py status
  python 管理企业微信统一指令本地服务.py restart
安全边界：只管理本机 19310 本地服务进程；不真实发送企业微信、不触发Webhook、不触发n8n、不调用业务执行器。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


HOST = "127.0.0.1"
PORT = 19310


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
SERVICE_SCRIPT = ROOT / "02脚本" / "企业微信统一指令本地服务入口.py"
LOG_DIR = ROOT / "04日志" / "统一指令本地服务"
PID_PATH = LOG_DIR / "wecom-unified-local-service.pid"
STDOUT_PATH = LOG_DIR / "wecom-unified-local-service.stdout.log"
STDERR_PATH = LOG_DIR / "wecom-unified-local-service.stderr.log"
STATUS_JSON = LOG_DIR / "wecom-unified-local-service-manager-最新.json"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_pid_file() -> int | None:
    if not PID_PATH.exists():
        return None
    try:
        return int(PID_PATH.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def run_powershell_json(command: str) -> Any:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    text = completed.stdout.strip()
    if not text:
        return None
    return json.loads(text)


def listener_info() -> dict[str, Any]:
    command = (
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
        f"$conn=Get-NetTCPConnection -LocalPort {PORT} -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1; "
        "if($conn){$p=Get-Process -Id $conn.OwningProcess; "
        "[pscustomobject]@{pid=$conn.OwningProcess;process=$p.ProcessName;path=$p.Path;startTime=$p.StartTime.ToString('yyyy-MM-dd HH:mm:ss')}|ConvertTo-Json -Compress} "
        "else {'{}'}"
    )
    try:
        data = run_powershell_json(command) or {}
        return data if isinstance(data, dict) else {}
    except Exception as exc:  # noqa: BLE001
        return {"错误": str(exc)}


def stop_pid(pid: int) -> None:
    command = f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue"
    subprocess.run(["powershell", "-NoProfile", "-Command", command], check=False, capture_output=True, text=True, timeout=10)


def health_check() -> dict[str, Any]:
    try:
        with urllib.request.urlopen(f"http://{HOST}:{PORT}/health", timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"状态": "异常", "错误": str(exc)}


def stop_service() -> dict[str, Any]:
    before = listener_info()
    pid_file_pid = read_pid_file()
    stopped: list[int] = []
    listen_pid = before.get("pid")
    if isinstance(listen_pid, int):
        stop_pid(listen_pid)
        stopped.append(listen_pid)
    if isinstance(pid_file_pid, int) and pid_file_pid not in stopped:
        stop_pid(pid_file_pid)
        stopped.append(pid_file_pid)
    time.sleep(1.5)
    after = listener_info()
    if not after.get("pid"):
        PID_PATH.unlink(missing_ok=True)
    result = {
        "动作": "stop",
        "执行时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "停止PID": stopped,
        "停止前监听": before,
        "停止后监听": after,
    }
    write_json(STATUS_JSON, result)
    return result


def start_service() -> dict[str, Any]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    before = listener_info()
    if before.get("pid"):
        PID_PATH.write_text(str(before["pid"]), encoding="ascii")
        result = {
            "动作": "start",
            "执行时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "状态": "already_running",
            "监听进程": before,
            "health": health_check(),
        }
        write_json(STATUS_JSON, result)
        return result

    stdout_handle = STDOUT_PATH.open("a", encoding="utf-8")
    stderr_handle = STDERR_PATH.open("a", encoding="utf-8")
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(
        [sys.executable, str(SERVICE_SCRIPT)],
        cwd=str(ROOT),
        stdout=stdout_handle,
        stderr=stderr_handle,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
        close_fds=False,
    )

    listener: dict[str, Any] = {}
    for _ in range(20):
        time.sleep(0.5)
        listener = listener_info()
        if listener.get("pid"):
            break
    if listener.get("pid"):
        PID_PATH.write_text(str(listener["pid"]), encoding="ascii")
    else:
        PID_PATH.write_text(str(process.pid), encoding="ascii")

    result = {
        "动作": "start",
        "执行时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "启动进程PID": process.pid,
        "监听进程": listener,
        "pid文件": str(PID_PATH),
        "health": health_check(),
    }
    write_json(STATUS_JSON, result)
    return result


def restart_service() -> dict[str, Any]:
    stopped = stop_service()
    started = start_service()
    result = {
        "动作": "restart",
        "执行时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stop": stopped,
        "start": started,
        "状态": "pass" if started.get("监听进程", {}).get("pid") and started.get("health", {}).get("状态") == "正常" else "blocked",
    }
    write_json(STATUS_JSON, result)
    return result


def status_service() -> dict[str, Any]:
    listener = listener_info()
    pid_file_pid = read_pid_file()
    health = health_check()
    pid_match = bool(listener.get("pid")) and pid_file_pid == listener.get("pid")
    result = {
        "动作": "status",
        "执行时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pid文件PID": pid_file_pid,
        "监听进程": listener,
        "pid文件与监听进程一致": pid_match,
        "health": health,
        "状态": "pass" if pid_match and health.get("状态") == "正常" else "blocked",
    }
    write_json(STATUS_JSON, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="企业微信统一指令本地服务管理器")
    parser.add_argument("action", choices=["start", "stop", "restart", "status"], help="服务管理动作")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    actions = {
        "start": start_service,
        "stop": stop_service,
        "restart": restart_service,
        "status": status_service,
    }
    result = actions[args.action]()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("状态", "pass") in {"pass", "already_running"} or args.action == "stop" else 2


if __name__ == "__main__":
    raise SystemExit(main())
