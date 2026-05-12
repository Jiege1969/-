"""
名称：n8n真实环境只读探测.py
作用：只读探测登记目标n8n健康状态、端口连通和本机n8n容器实例，防止后续灰度导入错实例。
触发方式：python n8n真实环境只读探测.py
依赖：Python 标准库、Docker CLI。
所属系统：00杰哥系统总管
安全边界：只访问n8n健康检查端点和读取docker ps；不读取工作流、不读取凭据、不调用n8n写接口、不导入n8n、不启用Webhook。
创建/修改记录：2026-04-27 创建n8n真实环境只读探测脚本；2026-05-06 第十四轮改为 v3 n8n 母样本口径。
"""

from __future__ import annotations

import json
import socket
import subprocess
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def service_registry() -> dict[str, Any]:
    return load_json(v3_root() / "00杰哥系统总管" / "01配置" / "服务注册表.json")


def find_registered_n8n() -> dict[str, Any]:
    for item in service_registry().get("服务", []):
        if item.get("服务名") == "v3隔离n8n" and item.get("容器名") == "jiege_v3_n8n":
            return item
    return {}


def tcp_check(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=5):
            return True
    except OSError:
        return False


def http_get(url: str) -> dict[str, Any]:
    try:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=5) as response:
            return {
                "成功": True,
                "状态码": response.status,
                "内容": response.read(1024).decode("utf-8", errors="replace"),
            }
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"成功": False, "错误": str(exc)}


def docker_containers() -> list[dict[str, str]]:
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
    )
    containers = []
    if result.returncode != 0:
        return containers
    for line in result.stdout.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3 and "n8n" in parts[0].lower():
            containers.append({"容器名": parts[0], "状态": parts[1], "端口": parts[2]})
    return containers


def main() -> int:
    registered = find_registered_n8n()
    host = registered.get("绑定地址", "127.0.0.1")
    port = int(registered.get("宿主机端口", 28679))
    health_url = registered.get("健康检查", f"http://{host}:{port}/healthz")
    containers = docker_containers()
    target_container = registered.get("容器名")
    non_target = [item for item in containers if item.get("容器名") != target_container]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "第2层前置准备-n8n真实环境只读探测",
        "登记目标": registered,
        "TCP连通": tcp_check(host, port),
        "健康检查": http_get(health_url),
        "本机n8n容器": containers,
        "目标容器": target_container,
        "发现非目标n8n容器": len(non_target) > 0,
        "非目标n8n容器": non_target,
        "风险提示": "存在多个n8n实例时，后续只允许对登记目标jiege_v3_n8n执行只读核验；当前母样本全inactive，不做灰度导入。",
        "是否读取工作流": False,
        "是否读取凭据": False,
        "是否调用n8n写接口": False,
        "是否导入n8n": False,
        "是否启用Webhook": False,
        "是否触发真实工作流": False,
    }
    output_dir = v3_root() / "00杰哥系统总管" / "03数据" / "灰度接入"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "n8n真实环境只读探测_最新.json"
    latest = output_dir / "n8n真实环境只读探测_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"TCP连通": report["TCP连通"], "健康检查": report["健康检查"].get("成功"), "n8n容器数": len(containers), "输出": str(output)}, ensure_ascii=True))
    return 0 if report["TCP连通"] and report["健康检查"].get("成功") else 1


if __name__ == "__main__":
    raise SystemExit(main())
