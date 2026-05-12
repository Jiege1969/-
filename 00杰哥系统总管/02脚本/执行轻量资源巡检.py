# -*- coding: utf-8 -*-
"""
名称：执行轻量资源巡检.py
作用：快速检查本机资源、重复旧容器、失控脚本和股票系统关键端口，生成施工前后轻量资源状态报告。
触发方式：python 执行轻量资源巡检.py
依赖：Python标准库；PowerShell；Docker CLI可选。
所属系统：00杰哥系统总管
安全边界：只读检查并写入新系统日志；不停止进程；不停止容器；不删除文件；不写旧系统；不真实发送企业微信；不触发交易接口。
创建/修改记录：2026-04-29 创建轻量资源巡检脚本。
标识：lightweight-resource-check
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_ps(script: str, timeout: int = 20) -> str:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return (result.stdout or result.stderr or "").strip()


def run_cmd(args: list[str], timeout: int = 20) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return (result.stdout or result.stderr or "").strip()
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: {exc}"


def check(name: str, ok: bool, detail: Any, level: str = "info") -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "异常", "级别": level if not ok else "info", "详情": detail}


def private_memory_limit(process_name: str, thresholds: dict[str, Any]) -> float:
    default_limit = float(thresholds.get("单进程私有内存警戒MB", 4096))
    exception_limits = thresholds.get("进程私有内存例外阈值MB", {})
    if not isinstance(exception_limits, dict):
        return default_limit
    return float(exception_limits.get(process_name, default_limit))


def main() -> int:
    manager = root()
    config = load_json(manager / "01配置" / "轻量资源巡检规则.json")
    thresholds = config.get("资源阈值", {})

    mem_script = r"""
$os=Get-CimInstance Win32_OperatingSystem
$cpu=Get-CimInstance Win32_Processor
$commit=Get-Counter '\Memory\Committed Bytes','\Memory\Commit Limit' | Select-Object -ExpandProperty CounterSamples
$committed=($commit | Where-Object {$_.Path -like '*committed bytes'}).CookedValue
$limit=($commit | Where-Object {$_.Path -like '*commit limit'}).CookedValue
[ordered]@{
  time=(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
  cpu_load_percent=$cpu.LoadPercentage
  total_memory_mb=[math]::Round($os.TotalVisibleMemorySize/1024,0)
  free_memory_mb=[math]::Round($os.FreePhysicalMemory/1024,0)
  committed_mb=[math]::Round($committed/1MB,0)
  commit_limit_mb=[math]::Round($limit/1MB,0)
  commit_ratio=[math]::Round($committed/$limit,4)
} | ConvertTo-Json -Compress
"""
    memory = json.loads(run_ps(mem_script) or "{}")

    proc_script = r"""
Get-Process |
  Sort-Object PrivateMemorySize64 -Descending |
  Select-Object -First 10 Id,ProcessName,@{Name='PrivateMB';Expression={[math]::Round($_.PrivateMemorySize64/1MB,1)}},@{Name='WorkingSetMB';Expression={[math]::Round($_.WorkingSet64/1MB,1)}},CPU |
  ConvertTo-Json -Compress -Depth 4
"""
    process_top = json.loads(run_ps(proc_script) or "[]")
    if isinstance(process_top, dict):
        process_top = [process_top]

    process_query = "Get-CimInstance Win32_Process | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress -Depth 4"
    processes_raw = json.loads(run_ps(process_query, timeout=30) or "[]")
    if isinstance(processes_raw, dict):
        processes_raw = [processes_raw]

    port_script = r"""
$ports=@(19300,19302)
Get-NetTCPConnection -LocalAddress 127.0.0.1 -State Listen -ErrorAction SilentlyContinue |
  Where-Object { $ports -contains $_.LocalPort } |
  Select-Object LocalPort,OwningProcess |
  ConvertTo-Json -Compress -Depth 4
"""
    ports = json.loads(run_ps(port_script) or "[]")
    if isinstance(ports, dict):
        ports = [ports]

    docker_lines = run_cmd(["docker", "ps", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}"], timeout=30).splitlines()
    docker_running = []
    for line in docker_lines:
        parts = line.split("|", 2)
        if len(parts) == 3:
            docker_running.append({"名称": parts[0], "状态": parts[1], "端口": parts[2]})

    old_candidates = set(config.get("禁止复发容器名", config.get("重复旧容器候选", [])))
    allowed_containers = set(config.get("允许运行容器", []))
    old_running = [item for item in docker_running if item["名称"] in old_candidates]
    unexpected_running = [item for item in docker_running if item["名称"] not in allowed_containers and item["名称"] not in old_candidates]

    high_risk_keywords = config.get("高风险脚本关键字", [])
    risky_processes = []
    for proc in processes_raw:
        cmd = str(proc.get("CommandLine") or "")
        if any(keyword in cmd for keyword in high_risk_keywords):
            if "执行轻量资源巡检.py" not in cmd:
                risky_processes.append(proc)

    required_ports = config.get("必需端口", [])
    listening_ports = {int(item.get("LocalPort")) for item in ports if item.get("LocalPort") is not None}
    missing_ports = [item for item in required_ports if int(item["端口"]) not in listening_ports]

    high_memory_processes = [
        item for item in process_top
        if float(item.get("PrivateMB") or 0) >= private_memory_limit(str(item.get("ProcessName") or ""), thresholds)
    ]

    checks = [
        check("可用内存不低于阈值", float(memory.get("free_memory_mb", 0)) >= float(thresholds.get("最低可用内存MB", 8192)), memory, "warning"),
        check("提交内存占比未超警戒", float(memory.get("commit_ratio", 1)) < float(thresholds.get("提交内存占比警戒", 0.85)), memory, "warning"),
        check("CPU未超警戒", float(memory.get("cpu_load_percent", 100)) < float(thresholds.get("CPU警戒百分比", 85)), memory, "warning"),
        check("无单进程私有内存超阈值", not high_memory_processes, high_memory_processes, "critical"),
        check("股票关键端口正常监听", not missing_ports, {"监听端口": sorted(listening_ports), "缺失端口": missing_ports}, "critical"),
        check("无旧容器复发运行", not old_running, old_running, "warning"),
        check("无非白名单容器运行", not unexpected_running, unexpected_running, "warning"),
        check("无已知高风险脚本运行", not risky_processes, risky_processes, "critical"),
    ]
    failed = [item for item in checks if item["结果"] != "通过"]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "lightweight-resource-check",
        "配置": str(manager / "01配置" / "轻量资源巡检规则.json"),
        "汇总": {
            "通过": len(checks) - len(failed),
            "异常": len(failed),
            "状态": "healthy" if not failed else "attention_required",
        },
        "资源": memory,
        "进程内存前十": process_top,
        "Docker运行容器": docker_running,
        "股票关键端口": ports,
        "检查结果": checks,
        "安全边界": config.get("安全边界", {}),
    }
    output_dir = manager / "04日志" / "轻量资源巡检"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = output_dir / f"lightweight-resource-check-{stamp}.json"
    latest = output_dir / "lightweight-resource-check-latest.json"
    zh_latest = output_dir / "lightweight-resource-check-最新.json"
    write_json(output, report)
    write_json(latest, report)
    write_json(zh_latest, report)
    print(json.dumps({"汇总": report["汇总"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
