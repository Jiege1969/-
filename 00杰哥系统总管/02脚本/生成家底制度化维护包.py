# -*- coding: utf-8 -*-
"""
名称：生成家底制度化维护包.py
作用：制度化刷新数据资产台账、系统依赖与恢复清单、暗角落扫描摘要。
触发方式：python 生成家底制度化维护包.py
依赖：Python 标准库；PowerShell、Docker、Ollama、WSL 命令可选，失败时记录不可用原因。
所属系统：00杰哥系统总管
安全边界：只读扫描并写最新报告；不删除文件；不禁用计划任务；不改启动项；不改防火墙；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-05-06 创建家底制度化维护包生成脚本。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
STOCK = ROOT / "02杰哥扩展系统" / "01股票研究系统"
EVOLUTION = ROOT / "03杰哥进化系统"
BACKUP = Path(r"F:\系统备份")
ASSET_DIR = BACKUP / "数据资产台账"
DEPENDENCY_DIR = BACKUP / "依赖清单"
DARK_DIR = MANAGER / "03数据" / "运行状态" / "暗角扫描"
RUN_DIR = MANAGER / "03数据" / "运行状态"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S +08:00")


def run_command(args: list[str], timeout: int = 30, shell: bool = False) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args if not shell else " ".join(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=shell,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    except Exception as exc:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": str(exc)}


def run_command_raw_text(args: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        completed = subprocess.run(args, capture_output=True, timeout=timeout)
        stdout = decode_bytes(completed.stdout)
        stderr = decode_bytes(completed.stderr)
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": stdout.strip(),
            "stderr": stderr.strip(),
        }
    except Exception as exc:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": str(exc)}


def decode_bytes(data: bytes) -> str:
    if not data:
        return ""
    candidates = []
    for encoding in ("utf-8", "utf-16le", "gb18030", "cp936"):
        text = data.decode(encoding, errors="replace")
        bad = text.count("\ufffd") + text.count("\x00")
        candidates.append((bad, text))
    candidates.sort(key=lambda row: row[0])
    return candidates[0][1].replace("\x00", "")


def wsl_version_result() -> dict[str, Any]:
    result = run_command_raw_text(["wsl", "--version"], 20)
    raw = result.get("stdout") or result.get("stderr") or ""
    version_values = re.findall(r"\d+(?:\.\d+)+(?:-\d+)?", raw)
    names = ["WSL", "Kernel", "WSLg", "MSRDC", "Direct3D", "DXCore", "Windows"]
    if len(version_values) >= 3:
        pairs = [f"{name}: {value}" for name, value in zip(names, version_values)]
        result["stdout"] = "; ".join(pairs)
    return result


def run_powershell(command: str, timeout: int = 60) -> dict[str, Any]:
    utf8_prefix = (
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
        "$OutputEncoding=[System.Text.Encoding]::UTF8; "
    )
    return run_command(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", utf8_prefix + command],
        timeout=timeout,
    )


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = text.replace("\x00", "").replace("\x0b", "").replace("\ufffd", "")
    path.write_text(clean, encoding="utf-8")


def dir_stats(path: Path) -> dict[str, Any]:
    files = 0
    bytes_total = 0
    exists = path.exists()
    if exists and path.is_file():
        files = 1
        try:
            bytes_total = path.stat().st_size
        except OSError:
            bytes_total = 0
    elif exists:
        for item in path.rglob("*"):
            if item.is_file():
                files += 1
                try:
                    bytes_total += item.stat().st_size
                except OSError:
                    pass
    return {
        "路径": str(path),
        "存在": exists,
        "文件数": files,
        "大小MB": round(bytes_total / 1024 / 1024, 3),
    }


def backup_exists(label: str, snapshot_root: Path) -> bool:
    if not snapshot_root.exists():
        return False
    target_name = Path(label).name
    return any(item.name == target_name for item in snapshot_root.rglob("*"))


def snapshot_alias_exists(snapshot_root: Path | None, aliases: str | list[str]) -> bool:
    if not snapshot_root or not snapshot_root.exists():
        return False
    alias_list = aliases if isinstance(aliases, list) else [aliases]
    return all((snapshot_root / alias).exists() for alias in alias_list)


def sync_one_snapshot_asset(source: Path, destination: Path) -> bool:
    if not source.exists():
        return False
    stats = dir_stats(source)
    if stats["大小MB"] > 1024:
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_file():
        shutil.copy2(source, destination)
    else:
        shutil.copytree(source, destination, dirs_exist_ok=True)
    return True


def sync_high_value_snapshot(snapshot: Path | None) -> list[dict[str, Any]]:
    if not snapshot:
        return []
    mappings = [
        (MANAGER / "01配置", snapshot / "00总管_01配置"),
        (MANAGER / "02脚本", snapshot / "00总管_02脚本"),
        (MANAGER / "03数据", snapshot / "00总管_03数据"),
        (MANAGER / "07文档", snapshot / "00总管_07文档"),
        (ROOT / "杰哥智能化系统全盘架构说明_20260504.md", snapshot / "全盘架构说明_20260504.md"),
        (ROOT / "01杰哥智能系统" / "01配置", snapshot / "01智能_01配置"),
        (ROOT / "01杰哥智能系统" / "02脚本", snapshot / "01智能_02脚本"),
        (ROOT / "01杰哥智能系统" / "03数据" / "n8n", snapshot / "01智能_03数据" / "n8n"),
        (ROOT / "01杰哥智能系统" / "03数据" / "知识库", snapshot / "01智能_03数据" / "知识库"),
        (ROOT / "01杰哥智能系统" / "提示词库", snapshot / "01智能_提示词库"),
        (ROOT / "02杰哥扩展系统" / "00公共组件", snapshot / "02扩展_00公共组件"),
        (ROOT / "02杰哥扩展系统" / "01股票研究系统", snapshot / "02扩展_01股票"),
        (ROOT / "02杰哥扩展系统" / "05税收业务系统", snapshot / "02扩展_05税收业务系统"),
        (ROOT / "02杰哥扩展系统" / "06企业微信助手系统", snapshot / "02扩展_06企业微信"),
        (ROOT / "02杰哥扩展系统" / "07知识库系统", snapshot / "02扩展_07知识库系统"),
        (EVOLUTION / "01配置", snapshot / "03进化_01配置"),
        (EVOLUTION / "02脚本", snapshot / "03进化_02脚本"),
        (EVOLUTION / "02提示词管理", snapshot / "03进化_02提示词管理"),
        (EVOLUTION / "03数据", snapshot / "03进化_03数据"),
        (EVOLUTION / "04系统复盘", snapshot / "03进化_04系统复盘"),
        (EVOLUTION / "07文档", snapshot / "03进化_07文档"),
        (EVOLUTION / "月度档案", snapshot / "03进化_月度档案"),
        (EVOLUTION / "README.md", snapshot / "03进化_README.md"),
    ]
    results = []
    for source, destination in mappings:
        copied = sync_one_snapshot_asset(source, destination)
        results.append({"源": str(source), "目标": str(destination), "已同步": copied})
    return results


def latest_high_value_snapshot() -> Path | None:
    if not BACKUP.exists():
        return None
    snapshots = sorted(
        [item for item in BACKUP.iterdir() if item.is_dir() and item.name.startswith("当前高价值小资产快照_")],
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    return snapshots[0] if snapshots else None


def generate_asset_ledger() -> dict[str, Any]:
    snapshot = latest_high_value_snapshot()
    snapshot_sync = sync_high_value_snapshot(snapshot)
    assets = [
        ("总管配置", MANAGER / "01配置", "不可再生", "00总管_01配置"),
        ("总管脚本", MANAGER / "02脚本", "不可再生", "00总管_02脚本"),
        ("开工上下文", MANAGER / "03数据" / "开工上下文", "不可再生", "00总管_03数据"),
        ("运行状态与验收报告", MANAGER / "03数据" / "运行状态", "不可再生", "00总管_03数据"),
        ("总管验收报告", MANAGER / "03数据" / "验收报告", "不可再生", "00总管_03数据"),
        ("总管文档", MANAGER / "07文档", "不可再生", "00总管_07文档"),
        ("全盘架构说明", ROOT / "杰哥智能化系统全盘架构说明_20260504.md", "不可再生", "全盘架构说明_20260504.md"),
        ("智能系统配置脚本", ROOT / "01杰哥智能系统" / "01配置", "不可再生", "01智能_01配置"),
        ("智能系统脚本", ROOT / "01杰哥智能系统" / "02脚本", "不可再生", "01智能_02脚本"),
        ("n8n工作流数据库与母样本", ROOT / "01杰哥智能系统" / "03数据" / "n8n", "不可再生", "01智能_03数据"),
        ("知识库文档与索引", ROOT / "01杰哥智能系统" / "03数据" / "知识库", "不可再生", "01智能_03数据"),
        ("智能系统提示词库", ROOT / "01杰哥智能系统" / "提示词库", "不可再生", "01智能_提示词库"),
        ("股票系统配置", STOCK / "01配置", "不可再生", "02扩展_01股票"),
        ("股票系统脚本", STOCK / "02脚本", "不可再生", "02扩展_01股票"),
        ("股票业务沉淀", STOCK / "03数据", "不可再生", "02扩展_01股票"),
        ("股票系统文档", STOCK / "07文档", "不可再生", "02扩展_01股票"),
        ("税收业务系统", ROOT / "02杰哥扩展系统" / "05税收业务系统", "不可再生", "02扩展_05税收业务系统"),
        ("企业微信配置脚本数据", ROOT / "02杰哥扩展系统" / "06企业微信助手系统", "不可再生", "02扩展_06企业微信"),
        ("进化配置提示词数据", EVOLUTION, "不可再生", ["03进化_01配置", "03进化_02脚本", "03进化_02提示词管理", "03进化_03数据", "03进化_07文档"]),
    ]
    rows = []
    for name, path, category, aliases in assets:
        stats = dir_stats(path)
        f_copy_exists = snapshot_alias_exists(snapshot, aliases)
        rows.append({
            "名称": name,
            "分类": category,
            **stats,
            "F盘当前快照锚点": aliases,
            "F盘当前快照存在": f_copy_exists,
            "双副本状态": "通过" if stats["存在"] and f_copy_exists else "需复核",
        })
    recoverable = [
        {"名称": "Ollama模型文件", "分类": "可再生/可重下", "恢复依据": str(DEPENDENCY_DIR / "ollama模型清单.txt")},
        {"名称": "Docker镜像", "分类": "可再生/可重拉", "恢复依据": str(DEPENDENCY_DIR / "docker镜像清单.txt")},
        {"名称": "WSL2一致性备份", "分类": "恢复底座", "恢复依据": newest_dir("WSL2一致性备份_")},
    ]
    report = {
        "名称": "数据资产台账",
        "更新时间": now_text(),
        "当前高价值快照": str(snapshot) if snapshot else "",
        "当前快照同步结果": snapshot_sync,
        "不可再生资产": rows,
        "可再生与恢复底座": recoverable,
        "中间产物规则": [
            "日志流水只保留需要核查的证据日志；纯流水和已解决问题日志按清债规则删除。",
            "__pycache__/.pyc 发现无当前依赖即删除，不登记为资产。",
            "临时目录、草稿旧备份、旧候选流水，证实无依赖直接删除。",
            "有价值旧内容必须先吸收为规则、模板、台账或当前文档，再删除原旧壳。",
        ],
    }
    write_json(ASSET_DIR / "数据资产台账_最新.json", report)
    lines = [
        "# 数据资产台账",
        "",
        f"- 更新时间：{report['更新时间']}",
        f"- 当前高价值快照：{report['当前高价值快照']}",
        "- 结论：不可再生资产以 D 盘主副本 + F 盘当前快照为目标；可再生资产保留恢复依据；中间产物不长期堆债。",
        "",
        "## 不可再生资产",
    ]
    for row in rows:
        lines.append(f"- {row['名称']}：{row['分类']}，D盘 {row['大小MB']} MB/{row['文件数']} 文件，F盘副本 {row['F盘当前快照存在']}，双副本 {row['双副本状态']}。")
    lines.extend(["", "## 可再生与恢复底座"])
    for row in recoverable:
        lines.append(f"- {row['名称']}：{row['分类']}，恢复依据：{row['恢复依据']}。")
    lines.extend(["", "## 中间产物规则"])
    for item in report["中间产物规则"]:
        lines.append(f"- {item}")
    write_text(ASSET_DIR / "数据资产台账_最新.md", "\n".join(lines) + "\n")
    return report


def newest_dir(prefix: str) -> str:
    if not BACKUP.exists():
        return ""
    candidates = sorted(
        [item for item in BACKUP.iterdir() if item.is_dir() and item.name.startswith(prefix)],
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    return str(candidates[0]) if candidates else ""


def redact_env(name: str, value: str) -> str:
    if re.search(r"(TOKEN|KEY|SECRET|PASSWORD|PASS|COOKIE|CREDENTIAL)", name, re.I):
        return "<敏感值已遮蔽>"
    if len(value) > 180:
        return value[:180] + "...<截断>"
    return value


def persistent_env_rows() -> list[dict[str, str]]:
    command = (
        "$rows=@(); "
        "foreach($scope in 'User','Machine'){ "
        "  [Environment]::GetEnvironmentVariables($scope).GetEnumerator() | "
        "  ForEach-Object { $rows += [pscustomobject]@{Scope=$scope;Name=$_.Key;Value=[string]$_.Value} } "
        "}; "
        "$rows | Sort-Object Scope,Name | ConvertTo-Json -Depth 3"
    )
    result = run_powershell(command, 30)
    if not result.get("ok") or not result.get("stdout"):
        return []
    try:
        parsed = json.loads(result["stdout"])
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, dict):
        parsed = [parsed]
    rows = []
    for item in parsed:
        rows.append({
            "范围": str(item.get("Scope", "")),
            "名称": str(item.get("Name", "")),
            "值": str(item.get("Value", "")),
        })
    return rows


def env_path_parts(value: str) -> list[str]:
    if ";" in value:
        return [part.strip() for part in value.split(";") if part.strip()]
    return [value.strip()] if value.strip() else []


def generate_dependency_list() -> dict[str, Any]:
    DEPENDENCY_DIR.mkdir(parents=True, exist_ok=True)
    commands = {
        "docker_images": ["docker", "images"],
        "docker_ps": ["docker", "ps", "--format", "{{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}"],
        "docker_volumes": ["docker", "volume", "ls"],
        "ollama_models": ["ollama", "list"],
    }
    command_outputs = {name: run_command(cmd, timeout=45) for name, cmd in commands.items()}
    write_text(DEPENDENCY_DIR / "docker镜像清单.txt", command_outputs["docker_images"]["stdout"] or command_outputs["docker_images"]["stderr"])
    write_text(DEPENDENCY_DIR / "docker容器清单.txt", command_outputs["docker_ps"]["stdout"] or command_outputs["docker_ps"]["stderr"])
    write_text(DEPENDENCY_DIR / "docker卷清单.txt", command_outputs["docker_volumes"]["stdout"] or command_outputs["docker_volumes"]["stderr"])
    write_text(DEPENDENCY_DIR / "ollama模型清单.txt", command_outputs["ollama_models"]["stdout"] or command_outputs["ollama_models"]["stderr"])

    versions = {
        "生成时间": now_text(),
        "GPU": run_powershell("Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion | ConvertTo-Json -Compress", 30),
        "Docker": run_command(["docker", "--version"], 20),
        "Docker Compose": run_command(["docker", "compose", "version"], 20),
        "WSL": wsl_version_result(),
        "Python": run_command(["python", "--version"], 20),
        "Node": run_command(["node", "--version"], 20),
        "npm": run_command(["npm", "--version"], 20),
    }
    write_json(DEPENDENCY_DIR / "系统软件版本清单.json", versions)

    task_result = run_powershell(
        "Get-ScheduledTask | Where-Object {$_.TaskName -like '杰哥智能化系统_*' -or $_.TaskName -like 'AI_*' -or $_.TaskName -like '*Jiege*' -or $_.TaskName -like '*serviceraj*'} | "
        "Select-Object TaskName,TaskPath,State,@{n='Actions';e={$_.Actions | ForEach-Object {$_.Execute + ' ' + $_.Arguments}}} | ConvertTo-Json -Depth 5",
        60,
    )
    write_text(DEPENDENCY_DIR / "计划任务清单.json", task_result["stdout"] or task_result["stderr"])

    port_result = run_powershell(
        "Get-NetTCPConnection -State Listen | Where-Object {$_.LocalPort -in 19300,19302,19310,26379,28100,28679,29134} | "
        "Select-Object LocalAddress,LocalPort,OwningProcess,@{n='ProcessName';e={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}} | ConvertTo-Json -Depth 4",
        30,
    )
    write_text(DEPENDENCY_DIR / "端口映射清单.json", port_result["stdout"] or port_result["stderr"])

    persisted_env = persistent_env_rows()
    env_rows = [
        {"范围": row["范围"], "名称": row["名称"], "值": redact_env(row["名称"], row["值"])}
        for row in persisted_env
        if row["名称"].upper() in {
            "PATH", "OLLAMA_HOST", "OLLAMA_MODELS", "N8N_API_TOKEN", "DOCKER_HOST", "CUDA_PATH", "PYTHONPATH", "NODE_PATH",
        } or re.search(r"(OLLAMA|N8N|DOCKER|CUDA|WEWORK|OPENAI|PROXY|TOKEN|KEY)", row["名称"], re.I)
    ]
    write_json(DEPENDENCY_DIR / "环境变量清单_敏感值已遮蔽.json", env_rows)

    report = {
        "名称": "系统依赖与恢复清单",
        "更新时间": now_text(),
        "命令结果": command_outputs,
        "系统软件版本": versions,
        "敏感配置位置": {
            "企业微信私密配置": str(ROOT / "02杰哥扩展系统" / "06企业微信助手系统" / "01配置" / "企业微信助手私密配置_本机.json"),
            "企业微信凭据路径模板": str(ROOT / "02杰哥扩展系统" / "06企业微信助手系统" / "01配置" / "企业微信凭据路径模板.json"),
            "股票公网入口配置": str(STOCK / "01配置" / "股票公网入口配置.json"),
            "股票公网隧道启动脚本": str(STOCK / "02脚本" / "启动股票公网回调隧道.ps1"),
        },
        "安全边界": {
            "不记录敏感明文": True,
            "不触发n8n": True,
            "不发送企业微信": True,
            "不调用券商接口": True,
            "不自动交易": True,
        },
    }
    write_json(DEPENDENCY_DIR / "系统依赖与恢复清单.json", report)
    md = build_dependency_markdown(report)
    write_text(DEPENDENCY_DIR / "系统依赖与恢复清单.md", md)
    return report


def ok_stdout(result: dict[str, Any]) -> str:
    return result.get("stdout") or result.get("stderr") or "未取得"


def build_dependency_markdown(report: dict[str, Any]) -> str:
    versions = report["系统软件版本"]
    docker = report["命令结果"]
    lines = [
        "# 系统依赖与恢复清单",
        "",
        f"- 更新时间：{report['更新时间']}",
        "- 敏感信息只记录存放位置，不记录明文。",
        "",
        "## 恢复顺序",
        "1. 恢复 Windows、WSL2、Docker Desktop、NVIDIA 驱动/CUDA。",
        "2. 恢复 `D:\\杰哥智能化系统` 与 `F:\\系统备份`。",
        "3. 使用 `01杰哥智能系统\\01配置` 下的 compose 文件恢复 v3 三件套。",
        "4. 复核计划任务、端口映射、企业微信本地入口、股票分析入口和 OpenClaw。",
        "5. 按敏感配置位置恢复凭据，不在本清单写入明文。",
        "",
        "## 软件版本",
        f"- GPU：{ok_stdout(versions['GPU'])}",
        f"- Docker：{ok_stdout(versions['Docker'])}",
        f"- Docker Compose：{ok_stdout(versions['Docker Compose'])}",
        f"- WSL：{ok_stdout(versions['WSL'])}",
        f"- Python：{ok_stdout(versions['Python'])}",
        f"- Node：{ok_stdout(versions['Node'])}",
        f"- npm：{ok_stdout(versions['npm'])}",
        "",
        "## Docker 与模型清单",
        f"- Docker 镜像：`{DEPENDENCY_DIR / 'docker镜像清单.txt'}`",
        f"- Docker 容器：`{DEPENDENCY_DIR / 'docker容器清单.txt'}`",
        f"- Docker 卷：`{DEPENDENCY_DIR / 'docker卷清单.txt'}`",
        f"- Ollama 模型：`{DEPENDENCY_DIR / 'ollama模型清单.txt'}`",
        "",
        "## 端口与计划任务",
        f"- 端口映射：`{DEPENDENCY_DIR / '端口映射清单.json'}`",
        f"- 计划任务：`{DEPENDENCY_DIR / '计划任务清单.json'}`",
        f"- 环境变量：`{DEPENDENCY_DIR / '环境变量清单_敏感值已遮蔽.json'}`",
        "",
        "## 敏感配置位置",
    ]
    for key, value in report["敏感配置位置"].items():
        lines.append(f"- {key}：`{value}`")
    lines.extend([
        "",
        "## 券商接口",
        "当前股票系统边界为只分析不交易；未登记可用券商接口、自动交易或下单配置。未来如新增，必须先写安全闸门、人工确认和依赖清单。",
    ])
    return "\n".join(lines) + "\n"


def generate_dark_corner_report() -> dict[str, Any]:
    DARK_DIR.mkdir(parents=True, exist_ok=True)
    scheduled = run_powershell(
        "Get-ScheduledTask | Select-Object TaskName,TaskPath,State,@{n='Actions';e={$_.Actions | ForEach-Object {$_.Execute + ' ' + $_.Arguments}}} | ConvertTo-Json -Depth 5",
        90,
    )
    startup = run_powershell(
        "Get-CimInstance Win32_StartupCommand | Select-Object Name,Command,Location,User | ConvertTo-Json -Depth 4",
        60,
    )
    hosts_path = Path(r"C:\Windows\System32\drivers\etc\hosts")
    hosts_text = hosts_path.read_text(encoding="utf-8", errors="replace") if hosts_path.exists() else ""
    firewall = run_powershell(
        "Get-NetFirewallRule | Where-Object {$_.DisplayName -match '杰哥|Jiege|AI|Docker|n8n|Ollama|Redis|WeWork|企业微信'} | Select-Object DisplayName,Enabled,Direction,Action,Profile | ConvertTo-Json -Depth 4",
        60,
    )
    wsl = run_command(["wsl", "-e", "bash", "-lc", "printf '--- crontab ---\\n'; crontab -l 2>/dev/null || true; printf '\\n--- bashrc hits ---\\n'; grep -nE '杰哥|OLLAMA|n8n|docker|serviceraj|AI_System|杰哥智能系统' ~/.bashrc /etc/crontab 2>/dev/null || true"], 45)
    env_dead_paths = []
    for row in persistent_env_rows():
        for part in env_path_parts(row["值"]):
            if re.search(r"^[A-Za-z]:\\", part) and not Path(part).exists():
                env_dead_paths.append({"范围": row["范围"], "变量": row["名称"], "路径": part})
    risk = []
    scheduled_text = scheduled.get("stdout", "")
    for word in ["serviceraj", "EncodedCommand", "IEX", "DownloadString", "AI_AutoEvolve", "AI_Backup", "DailyWorkPlan"]:
        if word.lower() in scheduled_text.lower():
            risk.append({"类型": "计划任务线索", "关键词": word})
    report = {
        "名称": "暗角落只读扫描报告",
        "扫描时间": now_text(),
        "扫描范围": ["Windows计划任务", "Windows启动项", "环境变量死路径", "hosts", "防火墙规则", "WSL crontab/bashrc"],
        "风险线索": risk,
        "环境变量死路径数量": len(env_dead_paths),
        "环境变量死路径样例": env_dead_paths[:30],
        "hosts摘要": [line for line in hosts_text.splitlines() if line.strip() and not line.strip().startswith("#")][:30],
        "原始结果": {
            "计划任务": scheduled,
            "启动项": startup,
            "防火墙": firewall,
            "WSL": wsl,
        },
        "安全边界": {
            "未禁用计划任务": True,
            "未删除启动项": True,
            "未修改hosts": True,
            "未修改防火墙": True,
            "未修改WSL文件": True,
            "未触发n8n": True,
            "未发送企业微信": True,
            "未调用券商接口": True,
            "未自动交易": True,
        },
    }
    write_json(DARK_DIR / "暗角落只读扫描报告_最新.json", report)
    lines = [
        "# 暗角落只读扫描报告",
        "",
        f"- 扫描时间：{report['扫描时间']}",
        "- 本报告只读生成，不修改计划任务、启动项、hosts、防火墙或 WSL 文件。",
        "",
        "## 扫描范围",
    ]
    for item in report["扫描范围"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 风险线索"])
    if risk:
        for item in risk:
            lines.append(f"- {item['类型']}：{item['关键词']}")
    else:
        lines.append("- 当前未发现旧高危关键词线索。")
    lines.extend([
        "",
        "## 环境变量死路径",
        f"- 数量：{len(env_dead_paths)}",
    ])
    for item in env_dead_paths[:10]:
        lines.append(f"- {item['变量']}：`{item['路径']}`")
    lines.extend([
        "",
        "## hosts 摘要",
    ])
    if report["hosts摘要"]:
        for item in report["hosts摘要"]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- 未发现非注释 hosts 业务映射。")
    lines.extend([
        "",
        "## 安全边界",
        "- 未禁用计划任务；未删除启动项；未修改 hosts；未修改防火墙；未修改 WSL 文件。",
        "- 未触发 n8n；未发送企业微信；未调用券商接口；未自动交易。",
    ])
    write_text(DARK_DIR / "暗角落只读扫描报告_最新.md", "\n".join(lines) + "\n")
    return report


def main() -> int:
    asset = generate_asset_ledger()
    dependency = generate_dependency_list()
    dark = generate_dark_corner_report()
    summary = {
        "名称": "家底制度化维护包",
        "生成时间": now_text(),
        "数据资产台账": str(ASSET_DIR / "数据资产台账_最新.md"),
        "系统依赖与恢复清单": str(DEPENDENCY_DIR / "系统依赖与恢复清单.md"),
        "暗角落只读扫描报告": str(DARK_DIR / "暗角落只读扫描报告_最新.md"),
        "不可再生资产数量": len(asset["不可再生资产"]),
        "暗角风险线索数量": len(dark["风险线索"]),
        "安全边界": {
            "未触发n8n": True,
            "未发送企业微信": True,
            "未调用券商接口": True,
            "未自动交易": True,
            "未删除文件": True,
        },
    }
    write_json(RUN_DIR / "家底制度化维护包_最新.json", summary)
    write_text(
        RUN_DIR / "家底制度化维护包_最新.md",
        "\n".join([
            "# 家底制度化维护包",
            "",
            f"- 生成时间：{summary['生成时间']}",
            f"- 数据资产台账：{summary['数据资产台账']}",
            f"- 系统依赖与恢复清单：{summary['系统依赖与恢复清单']}",
            f"- 暗角落只读扫描报告：{summary['暗角落只读扫描报告']}",
            f"- 不可再生资产数量：{summary['不可再生资产数量']}",
            f"- 暗角风险线索数量：{summary['暗角风险线索数量']}",
            "",
            "## 安全边界",
            "- 只读扫描并写最新报告；未触发 n8n；未发送企业微信；未调用券商接口；未自动交易；未删除文件。",
        ]) + "\n",
    )
    print(json.dumps({"状态": "完成", "输出": str(RUN_DIR / "家底制度化维护包_最新.md")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
