# -*- coding: utf-8 -*-
"""
名称：生成服务注册实时状态校准报告.py
作用：读取服务注册表和端口分配表，对照当前监听端口与 Docker 容器状态，生成登记状态与实时状态的只读校准报告。
触发方式：python 生成服务注册实时状态校准报告.py
依赖：Python 标准库；PowerShell Get-NetTCPConnection；Docker CLI 可选；service_registry.json；port_registry.json。
所属系统：00杰哥系统总管。
输出：00杰哥系统总管/03数据/运行状态/服务注册实时状态校准报告_最新.json|md；04日志/服务注册实时状态校准/service-registry-runtime-calibration-*.json|md。
安全边界：只读采集并写总管状态/日志；不启动服务、不停止服务、不重启服务、不清理容器、不修改服务注册表、不修改端口分配表、不触发 n8n、不发送企业微信、不调用券商接口、不自动交易。
标识：service-registry-runtime-calibration；登记状态；实时状态；只读校准。
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2))


def run_command(args: list[str], timeout: int = 20) -> tuple[int, str]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return result.returncode, (result.stdout or result.stderr or "").strip()
    except Exception as exc:  # noqa: BLE001
        return 99, str(exc)


def collect_listeners(ports: list[int]) -> dict[int, list[dict[str, Any]]]:
    if not ports:
        return {}
    port_csv = ",".join(str(port) for port in sorted(set(ports)))
    script = f"""
$ports=@({port_csv})
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
  Where-Object {{ $ports -contains $_.LocalPort }} |
  Select-Object LocalAddress,LocalPort,OwningProcess |
  ConvertTo-Json -Compress
"""
    code, output = run_command(["powershell", "-NoProfile", "-Command", script])
    if code != 0 or not output:
        return {}
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return {}
    if isinstance(data, dict):
        data = [data]
    listeners: dict[int, list[dict[str, Any]]] = {}
    for item in data:
        port = int(item.get("LocalPort", 0))
        listeners.setdefault(port, []).append(item)
    return listeners


def collect_docker_status() -> dict[str, dict[str, str]]:
    code, output = run_command(
        ["docker", "ps", "-a", "--format", "{{.Names}}|{{.Image}}|{{.Status}}"],
        timeout=20,
    )
    if code != 0:
        return {}
    statuses: dict[str, dict[str, str]] = {}
    for line in output.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            statuses[parts[0]] = {"镜像": parts[1], "状态": parts[2]}
    return statuses


def infer_runtime_status(service: dict[str, Any], listeners: dict[int, list[dict[str, Any]]], docker: dict[str, dict[str, str]]) -> dict[str, Any]:
    port = service.get("宿主机端口")
    container = service.get("容器名")
    process_name = service.get("进程名")
    port_listeners = listeners.get(int(port), []) if isinstance(port, int) else []
    docker_status = docker.get(container, {}) if container else {}

    if port_listeners:
        status = "监听中"
    elif docker_status:
        raw = docker_status.get("状态", "")
        status = "容器运行中但未发现登记端口监听" if raw.lower().startswith("up") else f"容器未运行：{raw}"
    else:
        status = "未监听"

    return {
        "服务名": service.get("服务名"),
        "登记状态": service.get("接管状态") or service.get("状态") or "未登记",
        "实时状态": status,
        "端口": port,
        "绑定地址": service.get("绑定地址"),
        "监听": port_listeners,
        "容器名": container,
        "容器状态": docker_status.get("状态"),
        "进程名": process_name,
        "健康检查": service.get("健康检查"),
        "是否一致": bool(port_listeners) if "运行" in str(service.get("接管状态") or service.get("状态") or "") else True,
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# 服务注册实时状态校准报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 服务数量：{report['汇总']['服务数量']}",
        f"- 监听中：{report['汇总']['监听中']}",
        f"- 未监听：{report['汇总']['未监听']}",
        f"- 容器未运行：{report['汇总']['容器未运行']}",
        "",
        "## 服务状态",
        "",
        "| 服务 | 端口 | 登记状态 | 实时状态 | 容器 | 容器状态 |",
        "|---|---:|---|---|---|---|",
    ]
    for item in report.get("服务状态", []):
        lines.append(
            f"| {item.get('服务名')} | {item.get('端口') or ''} | {item.get('登记状态')} | {item.get('实时状态')} | {item.get('容器名') or ''} | {item.get('容器状态') or ''} |"
        )
    lines.extend(
        [
            "",
            "## 建议",
            "",
            "- 后续应在服务注册表和端口分配表中区分登记状态与实时状态。",
            "- 本报告只读生成，不写回 machine 配置。",
            "- 股票主入口 `19300`、`19302` 的实时状态不得被旧股票容器覆盖。",
            "- 任何启动、停止、重启、清理、注册表写回都必须先验收并同步总架构说明。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    manager = manager_root()
    machine = manager / "01配置" / "machine"
    service_registry = load_json(machine / "service_registry.json", {})
    port_registry = load_json(machine / "port_registry.json", {})
    services = service_registry.get("服务", [])
    ports = [item.get("宿主机端口") for item in services if isinstance(item.get("宿主机端口"), int)]
    ports.extend(item.get("端口") for item in port_registry.get("端口", []) if isinstance(item.get("端口"), int))
    listeners = collect_listeners([int(port) for port in ports if isinstance(port, int)])
    docker = collect_docker_status()
    statuses = [infer_runtime_status(item, listeners, docker) for item in services]
    summary = {
        "服务数量": len(statuses),
        "监听中": sum(1 for item in statuses if item["实时状态"] == "监听中"),
        "未监听": sum(1 for item in statuses if item["实时状态"] == "未监听"),
        "容器未运行": sum(1 for item in statuses if str(item["实时状态"]).startswith("容器未运行")),
    }
    report = {
        "名称": "服务注册实时状态校准报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "汇总": summary,
        "服务状态": statuses,
        "安全边界": {
            "是否启动服务": False,
            "是否停止服务": False,
            "是否重启服务": False,
            "是否清理容器": False,
            "是否修改服务注册表": False,
            "是否修改端口分配表": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = manager / "04日志" / "服务注册实时状态校准"
    data_dir = manager / "03数据" / "运行状态"
    for path in [
        log_dir / f"service-registry-runtime-calibration-{stamp}.json",
        log_dir / "service-registry-runtime-calibration-最新.json",
        data_dir / "服务注册实时状态校准报告_最新.json",
    ]:
        write_json(path, report)
    md = render_md(report)
    for path in [
        log_dir / f"service-registry-runtime-calibration-{stamp}.md",
        log_dir / "service-registry-runtime-calibration-最新.md",
        data_dir / "服务注册实时状态校准报告_最新.md",
    ]:
        write_text(path, md)
    print(json.dumps({"汇总": summary, "输出": str(data_dir / "服务注册实时状态校准报告_最新.json")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
