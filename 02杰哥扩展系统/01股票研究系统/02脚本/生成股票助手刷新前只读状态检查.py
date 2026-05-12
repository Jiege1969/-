# -*- coding: utf-8 -*-
"""
名称：生成股票助手刷新前只读状态检查.py
作用：只读探测本地股票助手19300端口的接口加载状态，生成刷新前状态检查报告。
触发方式：python 生成股票助手刷新前只读状态检查.py
依赖：Python标准库；本机127.0.0.1:19300股票助手服务。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只做本地HTTP GET只读探测并写入新系统股票模块03数据目录；不停止服务；不启动服务；不重启服务；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手刷新前只读状态检查脚本。
标识：stock-assistant-prerefresh-readonly-status-check-generate
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def port_open(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def probe(path: str, timeout: float = 3.0) -> dict[str, Any]:
    url = f"http://127.0.0.1:19300{path}"
    try:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(300).decode("utf-8", errors="replace")
            return {"path": path, "url": url, "status": response.status, "ok": 200 <= response.status < 300, "sample": body}
    except urllib.error.HTTPError as exc:
        body = exc.read(300).decode("utf-8", errors="replace")
        return {"path": path, "url": url, "status": exc.code, "ok": False, "sample": body}
    except Exception as exc:
        return {"path": path, "url": url, "status": None, "ok": False, "error": str(exc)}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手刷新前只读状态检查",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 19300端口可连接：{report['端口可连接']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、接口探测",
        "",
    ]
    for item in report["接口探测"]:
        status = item.get("status") if item.get("status") is not None else "连接失败"
        lines.append(f"- {item['path']}：{status}，可用：{item['ok']}")
    lines.extend(["", "## 三、缺失新接口", ""])
    if report["缺失新接口"]:
        for item in report["缺失新接口"]:
            lines.append(f"- {item}")
    else:
        lines.append("- 无")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    paths = [
        "/health",
        "/watchlist",
        "/report/latest",
        "/data-health",
        "/status-summary",
        "/daily-package",
        "/l5/latest",
        "/candidate/latest",
    ]
    probes = [probe(path) for path in paths]
    required_new = ["/data-health", "/status-summary", "/daily-package"]
    missing_new = [item["path"] for item in probes if item["path"] in required_new and not item["ok"]]
    connectable = port_open("127.0.0.1", 19300)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "端口": "127.0.0.1:19300",
        "端口可连接": connectable,
        "接口探测": probes,
        "缺失新接口": missing_new,
        "是否需要刷新": bool(missing_new),
        "当前结论": "当前运行进程尚未加载全部新接口，若要进入真实灰度前需人工确认后刷新本地股票助手进程。" if missing_new else "当前运行进程已加载关键新接口，可进入下一步只读验收。",
        "实际动作": {
            "停止服务": False,
            "启动服务": False,
            "重启服务": False,
            "触发n8n": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写正式库": False,
            "写旧系统": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "37助手刷新前只读状态"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手刷新前只读状态检查_{stamp}.json"
    latest_json = output_dir / "股票助手刷新前只读状态检查_最新.json"
    output_md = output_dir / f"股票助手刷新前只读状态检查_{stamp}.md"
    latest_md = output_dir / "股票助手刷新前只读状态检查_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"端口可连接": connectable, "缺失新接口": missing_new, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
