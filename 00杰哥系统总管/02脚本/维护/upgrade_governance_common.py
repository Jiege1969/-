# -*- coding: utf-8 -*-
"""
名称：upgrade_governance_common.py
作用：版本升级治理脚本共享工具，提供路径、读写、时间戳、HTTP只读请求和当前版本采集函数。
触发方式：由版本治理脚本 import 调用，不单独作为业务入口。
依赖：Python标准库；可选本机版本命令。
所属系统：00杰哥系统总管/版本升级治理
输出：无直接业务输出；由调用脚本写入治理日志。
安全边界：共享工具只支持只读状态采集和治理报告写入；不下载、不安装、不升级、不停止服务、不触发 n8n、不发送企业微信、不写业务库、不调用券商接口、不自动交易。
创建/修改记录：2026-05-03 创建版本治理 V1.1 共享工具；2026-05-03 补齐标准标头。
标识：upgrade-governance-common
"""

from __future__ import annotations

import json
import re
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
CONFIG_DIR = MANAGER / "01配置"
SCRIPT_DIR = MANAGER / "02脚本"
MAINT_DIR = SCRIPT_DIR / "维护"
LOG_DIR = MANAGER / "04日志" / "版本升级治理"
BACKUP_DIR = MANAGER / "05备份"
RULES = CONFIG_DIR / "upgrade_rules.json"
LEDGER = CONFIG_DIR / "version_ledger.json"


NO_ACTION_BOUNDARY = {
    "下载": False,
    "安装": False,
    "升级正式环境": False,
    "停止正式服务": False,
    "启动影子容器": False,
    "触发n8n": False,
    "发送企业微信": False,
    "写正式业务库": False,
    "调用券商接口": False,
    "自动交易": False,
}


def now_stamp() -> tuple[datetime, str]:
    now = datetime.now()
    return now, now.strftime("%Y%m%d_%H%M%S")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_jsonl(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False) + "\n")


def run_command(args: list[str], timeout: int = 10) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": (completed.stdout or "").strip(),
            "stderr": (completed.stderr or "").strip(),
        }
    except Exception as exc:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": str(exc)}


def command_text(args: list[str], timeout: int = 10) -> str:
    result = run_command(args, timeout=timeout)
    return ((result.get("stdout") or "") + "\n" + (result.get("stderr") or "")).strip()


def first_version(text: str) -> str:
    text = text.replace("\x00", "").strip()
    match = re.search(r"v?\d+(?:\.\d+){1,3}", text)
    return match.group(0) if match else text


def http_json(url: str, timeout: int = 8) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "jiege-upgrade-governance-readonly/1.1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8", errors="replace")
            return {"ok": True, "url": url, "data": json.loads(payload), "error": ""}
    except Exception as exc:
        return {"ok": False, "url": url, "data": None, "error": str(exc)}


def docker_containers() -> list[dict[str, str]]:
    output = command_text(["docker", "ps", "--format", "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}"], timeout=15)
    rows: list[dict[str, str]] = []
    for line in output.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            rows.append({"名称": parts[0], "镜像": parts[1], "状态": parts[2], "端口": parts[3]})
    return rows


def ollama_models() -> list[dict[str, Any]]:
    # Current deployment exposes Ollama through the container port mapping.
    payload = http_json("http://127.0.0.1:29134/api/tags", timeout=5)
    data = payload.get("data") if payload.get("ok") else {}
    models: list[dict[str, Any]] = []
    if isinstance(data, dict) and isinstance(data.get("models"), list):
        for item in data["models"]:
            models.append({
                "名称": item.get("name", ""),
                "digest": item.get("digest", ""),
                "大小": item.get("size", 0),
                "修改时间": item.get("modified_at", ""),
            })
    return models


def current_version_snapshot() -> dict[str, Any]:
    nvidia = command_text(
        ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader,nounits"],
        timeout=10,
    )
    return {
        "PowerShell": command_text(["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]),
        "Python": first_version(command_text(["python", "--version"])),
        "pip": first_version(command_text(["python", "-m", "pip", "--version"])),
        "Node.js": command_text(["node", "--version"]),
        "npm": command_text(["npm.cmd", "--version"]),
        "Git": first_version(command_text(["git", "--version"])),
        "Docker": first_version(command_text(["docker", "--version"])),
        "Docker Compose": first_version(command_text(["docker", "compose", "version"])),
        "WSL": first_version(command_text(["wsl", "--version"])),
        "NVIDIA": nvidia,
        "核心容器": docker_containers(),
        "Ollama模型": ollama_models(),
    }


def safe_filename_component(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "item"
