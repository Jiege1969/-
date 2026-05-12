"""
名称：验证真实依赖只读联通.py
作用：只读验证本机v3真实基础依赖的联通状态，包括 v3 Ollama、隔离n8n、v3测试大脑、v3 Redis TCP 和 Docker 容器登记情况。
触发方式：python 验证真实依赖只读联通.py
依赖：Python 标准库；Docker CLI 可选。
所属系统：00杰哥系统总管
安全边界：只执行 HTTP GET、TCP connect 和 docker ps 只读命令；不调用 n8n webhook，不写数据库，不发送消息，不接管旧系统。
创建/修改记录：2026-04-26 创建真实依赖只读联通验证脚本；2026-04-30 改为检查新系统v3依赖，不再要求旧系统端口在线。
"""

from __future__ import annotations

import json
import socket
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error, request


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def log_dir() -> Path:
    target = v3_root() / "00杰哥系统总管" / "04日志" / "真实依赖联通验收"
    target.mkdir(parents=True, exist_ok=True)
    return target


def service_registry_path() -> Path:
    return v3_root() / "00杰哥系统总管" / "01配置" / "服务注册表.json"


def load_registry() -> dict[str, Any]:
    return json.loads(service_registry_path().read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {
        "检查项": name,
        "结果": "通过" if condition else "失败",
        "详情": detail,
    }


def http_get(url: str, timeout: int = 5) -> dict[str, Any]:
    try:
        with request.urlopen(url, timeout=timeout) as response:
            body = response.read(2048).decode("utf-8", errors="replace")
            return {
                "可访问": True,
                "状态码": response.status,
                "预览": body[:300],
            }
    except error.HTTPError as exc:
        return {
            "可访问": False,
            "状态码": exc.code,
            "错误": str(exc),
        }
    except Exception as exc:
        return {
            "可访问": False,
            "错误": str(exc),
        }


def tcp_connect(host: str, port: int, timeout: int = 3) -> dict[str, Any]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"可连接": True, "地址": host, "端口": port}
    except Exception as exc:
        return {"可连接": False, "地址": host, "端口": port, "错误": str(exc)}


def docker_ps() -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}|{{.Image}}|{{.Status}}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        containers = []
        for line in (result.stdout or "").splitlines():
            parts = line.split("|")
            if len(parts) == 3:
                containers.append({"容器名": parts[0], "镜像": parts[1], "状态": parts[2]})
        return {"可读取": result.returncode == 0, "容器": containers, "错误": result.stderr.strip()}
    except Exception as exc:
        return {"可读取": False, "容器": [], "错误": str(exc)}


def service_by_name(registry: dict[str, Any], name: str) -> dict[str, Any]:
    for service in registry.get("服务", []):
        if service.get("服务名") == name:
            return service
    return {}


def main() -> int:
    registry = load_registry()
    services = registry.get("服务", [])
    ollama = service_by_name(registry, "v3 Ollama")
    n8n = {"健康检查": "http://127.0.0.1:28679/healthz", "宿主机端口": 28679}
    redis = service_by_name(registry, "v3 Redis")
    v3_brain = service_by_name(registry, "v3智能体大脑测试服务")

    docker_status = docker_ps()
    ollama_status = http_get(ollama.get("健康检查", ""))
    n8n_status = http_get(n8n.get("健康检查", ""))
    v3_status = http_get(v3_brain.get("健康检查", ""))
    redis_status = tcp_connect("127.0.0.1", int(redis.get("宿主机端口", 0)))
    controlled_services = [
        item
        for item in services
        if item.get("接管状态") and "自动接管" not in str(item.get("接管状态"))
    ]

    checks = [
        check("服务注册表存在", service_registry_path().exists() and len(services) >= 1, str(service_registry_path())),
        check("登记服务处于受控状态", len(controlled_services) == len(services), [item.get("接管状态") for item in services]),
        check("Docker容器只读可见", docker_status.get("可读取") is True and len(docker_status.get("容器", [])) >= 1, docker_status),
        check("v3 Ollama只读联通", ollama_status.get("可访问") is True and "models" in ollama_status.get("预览", ""), ollama_status),
        check("v3隔离n8n健康只读联通", n8n_status.get("可访问") is True, n8n_status),
        check("v3测试大脑只读联通", v3_status.get("可访问") is True, v3_status),
        check("v3 Redis TCP联通", redis_status.get("可连接") is True, redis_status),
    ]

    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "real-dependency-readonly-verify",
        "安全边界": "只读联通，不写入、不触发、不接管。",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = log_dir()
    output = output_dir / f"real-dependency-readonly-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "real-dependency-readonly-verify-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
