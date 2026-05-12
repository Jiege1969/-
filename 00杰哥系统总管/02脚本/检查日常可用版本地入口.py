"""
名称：检查日常可用版本地入口.py
作用：按日常可用版入口注册表检查本机服务入口是否可访问，并生成入口状态报告。
触发方式：python 检查日常可用版本地入口.py
依赖：Python 标准库；Docker CLI；PowerShell；日常可用版入口注册表.json。
所属系统：00杰哥系统总管
安全边界：只读探测本地 HTTP、Ollama、Redis、PostgreSQL 状态；不触发业务工作流、不发送企业微信、不写旧系统。
创建/修改记录：2026-04-27 创建日常可用版本地入口检查脚本；2026-04-29 增加script_json入口类型以纳入轻量资源巡检和股票交付验收；2026-05-01 script_json支持参数、超时秒数和允许返回码。
"""

from __future__ import annotations

import json
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


def http_get(url: str, timeout: int = 8) -> dict[str, Any]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "jiege-daily-entry-check/1.0"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(2048)
            return {"可用": 200 <= response.status < 400, "状态码": response.status, "摘要": body.decode("utf-8", errors="replace")[:160]}
    except urllib.error.HTTPError as exc:
        return {"可用": False, "状态码": exc.code, "错误": str(exc)}
    except Exception as exc:
        return {"可用": False, "状态码": 0, "错误": str(exc)}


def run_command(command: list[str], timeout: int = 15) -> dict[str, Any]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return {
            "可用": result.returncode == 0,
            "退出码": result.returncode,
            "标准输出": result.stdout.strip(),
            "标准错误": result.stderr.strip(),
        }
    except Exception as exc:
        return {"可用": False, "退出码": 1, "标准输出": "", "标准错误": str(exc)}


def run_script_json(script_path: str, timeout: int = 120, args: list[str] | None = None, allowed_return_codes: list[int] | None = None) -> dict[str, Any]:
    path = Path(script_path)
    if not path.exists():
        return {"可用": False, "退出码": 127, "错误": f"脚本不存在：{script_path}"}
    if path.suffix.lower() == ".ps1":
        command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(path), *(args or [])]
    else:
        command = ["python", str(path), *(args or [])]
    result = run_command(command, timeout=timeout)
    allowed = allowed_return_codes or [0]
    result["可用"] = result.get("退出码") in allowed
    result["允许返回码"] = allowed
    result["执行参数"] = args or []
    result["超时秒数"] = timeout
    summary: Any = {}
    text = result.get("标准输出") or ""
    try:
        summary = json.loads(text.splitlines()[-1]) if text.strip() else {}
    except Exception:
        summary = text[-500:]
    result["摘要"] = summary
    return result


def inspect_openapi(url: str) -> dict[str, Any]:
    result = http_get(url)
    if not result.get("可用"):
        return result
    try:
        data = json.loads(result.get("摘要", "") + "")
    except Exception:
        full = urllib.request.urlopen(url, timeout=8).read().decode("utf-8", errors="replace")
        data = json.loads(full)
    paths = list(data.get("paths", {}).keys())
    return {
        "可用": True,
        "标题": data.get("info", {}).get("title", ""),
        "版本": data.get("info", {}).get("version", ""),
        "接口数量": len(paths),
        "接口": paths,
    }


def check_entry(entry: dict[str, Any]) -> dict[str, Any]:
    entry_type = entry.get("类型")
    detail: dict[str, Any]
    if entry_type == "http_openapi":
        docs = http_get(entry["检查URL"])
        openapi = inspect_openapi(entry["OpenAPI"])
        ok = docs.get("可用") is True and openapi.get("可用") is True
        detail = {"docs": docs, "openapi": openapi}
    elif entry_type in {"http", "ollama"}:
        detail = http_get(entry["检查URL"])
        ok = detail.get("可用") is True
        if entry_type == "ollama" and ok:
            try:
                data = json.loads(detail.get("摘要", "{}"))
                detail["模型数量"] = len(data.get("models", []))
            except Exception:
                detail["模型数量"] = None
    elif entry_type == "docker_redis":
        detail = run_command(["docker", "exec", entry["容器"], "redis-cli", "ping"])
        ok = detail.get("可用") is True and "PONG" in detail.get("标准输出", "")
    elif entry_type == "docker_postgres":
        detail = run_command(["docker", "exec", entry["容器"], "pg_isready"])
        ok = detail.get("可用") is True and "accepting connections" in detail.get("标准输出", "")
    elif entry_type == "script_json":
        detail = run_script_json(
            entry["脚本"],
            timeout=int(entry.get("超时秒数") or 120),
            args=list(entry.get("参数") or []),
            allowed_return_codes=list(entry.get("允许返回码") or [0]),
        )
        ok = detail.get("可用") is True
    else:
        detail = {"错误": f"未知入口类型：{entry_type}"}
        ok = False
    return {
        "名称": entry.get("名称"),
        "归属": entry.get("归属"),
        "类型": entry_type,
        "用途": entry.get("用途"),
        "是否必检": entry.get("是否必检") is True,
        "可用": ok,
        "详情": detail,
    }


def main() -> int:
    root = v3_root()
    config_path = root / "00杰哥系统总管" / "01配置" / "日常可用版入口注册表.json"
    config = load_json(config_path)
    results = [check_entry(entry) for entry in config.get("入口", [])]
    required = [item for item in results if item.get("是否必检")]
    report = {
        "检查时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "daily-usable-entry-check",
        "配置文件": str(config_path),
        "汇总": {
            "入口总数": len(results),
            "必检入口数": len(required),
            "可用": sum(1 for item in required if item.get("可用") is True),
            "不可用": sum(1 for item in required if item.get("可用") is not True),
        },
        "入口状态": results,
        "安全边界": {
            "是否触发n8n工作流": False,
            "是否发送企业微信": False,
            "是否写入旧系统": False,
            "是否接入税收业务": False
        },
    }
    output_dir = root / "00杰哥系统总管" / "04日志" / "日常可用版"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "daily-usable-entry-check-最新.json"
    latest = output_dir / "daily-usable-entry-check-最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"可用": report["汇总"]["可用"], "不可用": report["汇总"]["不可用"], "输出": str(output)}, ensure_ascii=False))
    return 0 if report["汇总"]["不可用"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
