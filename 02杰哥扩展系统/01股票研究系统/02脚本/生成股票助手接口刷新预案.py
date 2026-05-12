# -*- coding: utf-8 -*-
"""
名称：生成股票助手接口刷新预案.py
作用：检查本地股票助手运行进程是否加载了最新接口，并生成刷新预案。
触发方式：python 生成股票助手接口刷新预案.py
依赖：Python标准库；本地股票助手127.0.0.1:19300；启动股票助手.ps1；停止股票助手.ps1。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只做HTTP只读探测和预案生成；不停止进程；不启动进程；不重启服务；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手接口刷新预案脚本。
标识：stock-assistant-endpoint-refresh-plan
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ENDPOINTS = ["/health", "/watchlist", "/report/latest", "/data-health", "/status-summary", "/daily-package"]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def probe(endpoint: str) -> dict[str, Any]:
    url = f"http://127.0.0.1:19300{endpoint}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            body = response.read(300).decode("utf-8", errors="replace")
            return {"接口": endpoint, "状态码": response.status, "可用": 200 <= response.status < 300, "摘要": body[:180]}
    except urllib.error.HTTPError as exc:
        return {"接口": endpoint, "状态码": exc.code, "可用": False, "摘要": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"接口": endpoint, "状态码": None, "可用": False, "摘要": str(exc)}


def build_md(report: dict[str, Any]) -> str:
    endpoint_lines = "\n".join(
        f"- {item['接口']}：{'可用' if item['可用'] else '不可用'}（{item['状态码']}）"
        for item in report["接口探测"]
    )
    missing = "\n".join(f"- {item}" for item in report["缺失接口"]) or "- 无"
    steps = "\n".join(f"- {item}" for item in report["人工确认后刷新步骤"])
    return f"""# 股票助手接口刷新预案

生成时间：{report['生成时间']}

结论：{report['结论']}

## 一、接口探测

{endpoint_lines}

## 二、缺失接口

{missing}

## 三、人工确认后刷新步骤

{steps}

## 四、安全边界

- 本预案没有停止进程。
- 本预案没有启动进程。
- 本预案没有重启服务。
- 本预案没有触发n8n。
- 本预案没有发送企业微信。
- 本预案没有调用券商接口或自动交易。
"""


def main() -> int:
    root = module_root()
    probes = [probe(endpoint) for endpoint in ENDPOINTS]
    missing = [item["接口"] for item in probes if not item["可用"]]
    refresh_needed = bool(missing)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "readonly_probe_and_plan",
        "接口探测": probes,
        "缺失接口": missing,
        "是否需要刷新本地股票助手进程": refresh_needed,
        "结论": "当前运行进程未加载全部新接口，需要人工确认后刷新本地股票助手。" if refresh_needed else "当前运行进程已加载全部目标接口。",
        "人工确认后刷新步骤": [
            "执行停止股票助手.ps1，仅停止新系统本地股票助手进程。",
            "执行启动股票助手.ps1，仅绑定127.0.0.1:19300。",
            "重新探测/data-health、/status-summary、/daily-package。",
            "确认旧系统未受影响、n8n未触发、企业微信未真实发送。",
        ],
        "实际动作": {
            "停止进程": False,
            "启动进程": False,
            "重启服务": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "22助手刷新预案"
    log_dir = root / "04日志" / "助手刷新预案"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / f"股票助手接口刷新预案_{timestamp}.json"
    latest_json = output_dir / "股票助手接口刷新预案_最新.json"
    md_path = output_dir / f"股票助手接口刷新预案_{timestamp}.md"
    latest_md = output_dir / "股票助手接口刷新预案_最新.md"
    log_path = log_dir / f"stock-assistant-endpoint-refresh-plan-{timestamp}.json"
    latest_log_path = log_dir / "stock-assistant-endpoint-refresh-plan-最新.json"
    write_json(json_path, report)
    write_json(latest_json, report)
    markdown = build_md(report)
    write_text(md_path, markdown)
    write_text(latest_md, markdown)
    write_json(log_path, report)
    write_json(latest_log_path, report)
    print(json.dumps({"需要刷新": refresh_needed, "缺失接口": missing, "输出": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
