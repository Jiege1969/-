# -*- coding: utf-8 -*-
"""
名称：补齐服务注册实时状态字段.py
作用：按当前监听端口和 Docker 只读状态，补齐 service_registry.json 与 port_registry.json 的实时状态类字段，并生成可复现报告。
触发方式：python 补齐服务注册实时状态字段.py
依赖：Python 标准库；PowerShell Get-NetTCPConnection；Docker CLI 可选；service_registry.json；port_registry.json。
所属系统：00杰哥系统总管。
输出：03数据/运行状态/服务注册实时状态字段补齐报告_最新.json|md；04日志/服务注册实时状态字段补齐/runtime-field-completion-*.json|md。
安全边界：只补齐登记状态、实时状态、状态来源、验收入口、是否允许自动操作等治理字段；不启动服务、不停止服务、不重启服务、不清理容器、不触发 n8n、不发送企业微信、不调用券商接口、不自动交易。
标识：service-registry-runtime-field-completion；低负载治理；只读采集；受控写回。
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


CONFIRM_ACTIONS = [
    "真实发送企业微信",
    "触发Webhook",
    "触发n8n",
    "写正式业务库",
    "调用券商接口",
    "自动交易",
    "停止或重启生产服务",
    "清理旧容器",
    "开放公网入口",
]


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S +08:00")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


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
    code, output = run_command(["powershell", "-NoProfile", "-Command", script], timeout=20)
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
        try:
            port = int(item.get("LocalPort", 0))
        except (TypeError, ValueError):
            continue
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
    port_listeners = listeners.get(int(port), []) if isinstance(port, int) else []
    docker_status = docker.get(container, {}) if container else {}
    raw_container = str(docker_status.get("状态") or "")

    if port_listeners:
        runtime_status = "监听中"
    elif raw_container.lower().startswith("up"):
        runtime_status = "容器运行中但未发现登记端口监听"
    elif raw_container:
        runtime_status = f"容器未运行：{raw_container}"
    else:
        runtime_status = "未监听"

    registered = service.get("登记状态") or service.get("接管状态") or service.get("状态") or "未登记"
    return {
        "登记状态": registered,
        "实时状态": runtime_status,
        "状态更新时间": now_text(),
        "实时状态来源": "Get-NetTCPConnection + Docker CLI",
        "验收入口": service.get("验收入口") or service.get("健康检查") or "",
        "允许自动操作": bool(service.get("允许自动操作", False)),
        "需要确认动作": service.get("需要确认动作") or CONFIRM_ACTIONS,
        "监听": port_listeners,
        "容器状态": raw_container,
    }


def apply_service_fields(service: dict[str, Any], status: dict[str, Any]) -> dict[str, Any]:
    service["登记状态"] = status["登记状态"]
    service["实时状态"] = status["实时状态"]
    service["状态更新时间"] = status["状态更新时间"]
    service["实时状态来源"] = status["实时状态来源"]
    service["验收入口"] = status["验收入口"]
    service["允许自动操作"] = status["允许自动操作"]
    service["需要确认动作"] = status["需要确认动作"]
    if status.get("容器状态"):
        service["容器实时状态"] = status["容器状态"]
    return service


def apply_port_fields(port_item: dict[str, Any], service_status_by_port: dict[int, dict[str, Any]], timestamp: str) -> dict[str, Any]:
    port = port_item.get("端口")
    status = service_status_by_port.get(port) if isinstance(port, int) else None
    if status:
        port_item["登记状态"] = port_item.get("登记状态") or port_item.get("状态") or "未登记"
        port_item["实时状态"] = status["实时状态"]
        port_item["状态更新时间"] = timestamp
        port_item["实时状态来源"] = status["实时状态来源"]
        port_item["允许自动操作"] = bool(port_item.get("允许自动操作", False))
        port_item["验收入口"] = status.get("验收入口", "")
    else:
        port_item["登记状态"] = port_item.get("登记状态") or port_item.get("状态") or "未登记"
        port_item["状态更新时间"] = timestamp
        port_item["实时状态来源"] = port_item.get("实时状态来源") or "未纳入服务注册表，仅保留端口登记"
        port_item["允许自动操作"] = bool(port_item.get("允许自动操作", False))
    return port_item


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# 服务注册实时状态字段补齐报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 服务数量：{report['汇总']['服务数量']}",
        f"- 端口数量：{report['汇总']['端口数量']}",
        f"- 监听中服务：{report['汇总']['监听中服务']}",
        f"- 默认允许自动操作：false",
        "",
        "## 服务补齐结果",
        "",
        "| 服务 | 端口 | 登记状态 | 实时状态 | 允许自动操作 | 验收入口 |",
        "|---|---:|---|---|---|---|",
    ]
    for item in report["服务"]:
        lines.append(
            f"| {item['服务名']} | {item.get('端口') or ''} | {item['登记状态']} | {item['实时状态']} | {str(item['允许自动操作']).lower()} | {item.get('验收入口') or ''} |"
        )
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 本步骤只补齐治理字段和生成报告。",
            "- 未启动、停止、重启、清理任何服务或容器。",
            "- 未触发 n8n、未发送企业微信、未调用券商接口、未自动交易。",
            "- 后续如需把任一服务改为允许自动操作，必须单独确认并验收。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    manager = manager_root()
    machine = manager / "01配置" / "machine"
    service_path = machine / "service_registry.json"
    port_path = machine / "port_registry.json"
    service_registry = load_json(service_path, {})
    port_registry = load_json(port_path, {})

    services = service_registry.get("服务", [])
    ports = [item.get("宿主机端口") for item in services if isinstance(item.get("宿主机端口"), int)]
    ports.extend(item.get("端口") for item in port_registry.get("端口", []) if isinstance(item.get("端口"), int))
    listeners = collect_listeners([int(port) for port in ports if isinstance(port, int)])
    docker = collect_docker_status()

    service_rows = []
    service_status_by_port: dict[int, dict[str, Any]] = {}
    timestamp = now_text()
    for service in services:
        status = infer_runtime_status(service, listeners, docker)
        status["状态更新时间"] = timestamp
        apply_service_fields(service, status)
        port = service.get("宿主机端口")
        if isinstance(port, int):
            service_status_by_port[port] = status
        service_rows.append(
            {
                "服务名": service.get("服务名"),
                "端口": port,
                "登记状态": status["登记状态"],
                "实时状态": status["实时状态"],
                "允许自动操作": status["允许自动操作"],
                "验收入口": status["验收入口"],
            }
        )

    for port_item in port_registry.get("端口", []):
        apply_port_fields(port_item, service_status_by_port, timestamp)

    write_json(service_path, service_registry)
    write_json(port_path, port_registry)

    report = {
        "名称": "服务注册实时状态字段补齐报告",
        "生成时间": timestamp,
        "汇总": {
            "服务数量": len(services),
            "端口数量": len(port_registry.get("端口", [])),
            "监听中服务": sum(1 for item in service_rows if item["实时状态"] == "监听中"),
            "允许自动操作为true": sum(1 for item in service_rows if item["允许自动操作"] is True),
        },
        "服务": service_rows,
        "安全边界": {
            "是否启动服务": False,
            "是否停止服务": False,
            "是否重启服务": False,
            "是否清理容器": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    stamp = stamp_text()
    log_dir = manager / "04日志" / "服务注册实时状态字段补齐"
    data_dir = manager / "03数据" / "运行状态"
    for path in [
        log_dir / f"runtime-field-completion-{stamp}.json",
        log_dir / "runtime-field-completion-最新.json",
        data_dir / "服务注册实时状态字段补齐报告_最新.json",
    ]:
        write_json(path, report)
    md = render_md(report)
    for path in [
        log_dir / f"runtime-field-completion-{stamp}.md",
        log_dir / "runtime-field-completion-最新.md",
        data_dir / "服务注册实时状态字段补齐报告_最新.md",
    ]:
        write_text(path, md)

    print(json.dumps({"汇总": report["汇总"], "输出": str(data_dir / "服务注册实时状态字段补齐报告_最新.json")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
