# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-delivery-runtime-patrol-package.py
Purpose: Generate a read-only runtime patrol package for stock assistant delivery readiness.
Trigger: python 生成股票助手交付运行巡检包.py
Dependencies: Python standard library; Docker CLI if available; local stock assistant and isolated n8n endpoints.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Read-only patrol only; does not restart, enable, trigger Webhook, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created stock assistant delivery runtime patrol package generator.
Marker: stock-assistant-delivery-runtime-patrol-package-generate
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return module_root().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_command(args: list[str], timeout: int = 30) -> dict[str, Any]:
    completed = subprocess.run(args, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {
        "命令": args,
        "返回码": completed.returncode,
        "标准输出": completed.stdout.strip(),
        "标准错误": completed.stderr.strip(),
    }


def probe_url(url: str, timeout: int = 5) -> dict[str, Any]:
    try:
        request = Request(url, method="GET", headers={"User-Agent": "jiege-stock-runtime-patrol"})
        with urlopen(request, timeout=timeout) as response:
            body = response.read(300).decode("utf-8", errors="replace")
            return {"地址": url, "可访问": True, "状态码": response.status, "片段": body}
    except HTTPError as exc:
        return {"地址": url, "可访问": False, "状态码": exc.code, "片段": str(exc)}
    except URLError as exc:
        return {"地址": url, "可访问": False, "状态码": None, "片段": str(exc.reason)}
    except Exception as exc:
        return {"地址": url, "可访问": False, "状态码": None, "片段": str(exc)}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手交付运行巡检包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、巡检结论",
        "",
        f"- 是否适合继续交付施工：{report['是否适合继续交付施工']}",
        f"- 本地股票助手：{report['端点探测']['本地股票助手']}",
        f"- 隔离n8n：{report['端点探测']['隔离n8n']}",
        "",
        "## 二、安全闸口",
        "",
    ]
    for key, value in report["安全闸口"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、容器状态", ""])
    for key, value in report["容器状态"].items():
        lines.append(f"### {key}")
        lines.append("```text")
        lines.append(value.get("标准输出") or value.get("标准错误") or "")
        lines.append("```")
    lines.extend(["", "## 四、实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    v3_root = system_root()
    rule_path = root / "01配置" / "股票助手交付运行巡检规则.json"
    delivery_package = root / "03数据" / "79股票助手交付使用包" / "股票助手交付使用包_最新.json"
    send_gate_config = v3_root / "02杰哥扩展系统" / "00公共组件" / "01配置" / "企业微信受控发送配置模板.json"
    send_gate = load_json(send_gate_config)
    endpoints = {
        "本地股票助手": probe_url("http://127.0.0.1:19300/"),
        "隔离n8n": probe_url("http://127.0.0.1:28679/")
    }
    containers = {
        "jiege_v3_n8n": run_command(["docker", "ps", "-a", "--filter", "name=jiege_v3_n8n", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}"], 60),
        "jiege_n8n保护对象": run_command(["docker", "ps", "-a", "--filter", "name=jiege_n8n", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}"], 60)
    }
    ready = (
        delivery_package.exists()
        and send_gate.get("真实发送启用", False) is False
        and "jiege_v3_n8n" in containers["jiege_v3_n8n"].get("标准输出", "")
        and "jiege_n8n" in containers["jiege_n8n保护对象"].get("标准输出", "")
    )
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "交付使用包": str(delivery_package),
        "端点探测": endpoints,
        "容器状态": containers,
        "安全闸口": {
            "企业微信真实发送": send_gate.get("真实发送启用", False),
            "OpenClaw真实桥接": False,
            "交易接口": False,
            "旧系统写入": False
        },
        "是否适合继续交付施工": ready,
        "实际动作": {
            "生成巡检包": True,
            "重启服务": False,
            "启用Webhook": False,
            "触发Webhook": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False
        }
    }
    output_dir = root / "03数据" / "80股票助手交付运行巡检包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手交付运行巡检包_{stamp}.json"
    latest_json = output_dir / "股票助手交付运行巡检包_最新.json"
    output_md = output_dir / f"股票助手交付运行巡检包_{stamp}.md"
    latest_md = output_dir / "股票助手交付运行巡检包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否适合继续交付施工": ready, "输出": str(output_json)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
