# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-isolated-n8n-startup-preflight.py
Purpose: Generate a readonly preflight report before any isolated new-system n8n startup for the stock assistant.
Trigger: python 生成股票助手隔离n8n启动前只读核验.py
Dependencies: Python standard library, netstat command, Docker CLI readonly query.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Performs readonly local checks and writes reports only under the new stock module data directory; does not create directories, start, restart, import, enable, trigger, send, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created isolated n8n startup preflight generator.
Marker: stock-assistant-isolated-n8n-startup-preflight-generate
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return module_root().parents[1]


def run_command(args: list[str]) -> tuple[bool, str]:
    completed = subprocess.run(args, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    return completed.returncode == 0, completed.stdout if completed.returncode == 0 else completed.stderr


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手隔离n8n启动前只读核验",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否具备启动前基础条件：{report['是否具备启动前基础条件']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、检查项",
        "",
    ]
    for item in report["检查项"]:
        lines.append(f"- {item['名称']}：{item['通过']}，{item['说明']}")
    lines.extend(["", "## 三、禁止动作", ""])
    for key, value in report["实际动作"].items():
        if value is False:
            lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    v3_root = system_root()
    compose_path = v3_root / "01杰哥智能系统" / "01配置" / "docker-compose.v3草案.yml"
    n8n_data = v3_root / "01杰哥智能系统" / "03数据" / "n8n"
    ok_netstat, netstat_output = run_command(["netstat", "-ano"])
    ok_docker, docker_output = run_command(["docker", "ps", "--format", "{{json .}}"])
    port_occupied = ":28679" in netstat_output
    v3_running = "jiege_v3_n8n" in docker_output or "28679" in docker_output
    checks = [
        {"名称": "compose草案存在", "通过": compose_path.exists(), "说明": str(compose_path)},
        {"名称": "目标数据目录存在", "通过": n8n_data.exists(), "说明": str(n8n_data)},
        {"名称": "28679端口空闲", "通过": ok_netstat and not port_occupied, "说明": "未发现28679占用" if ok_netstat and not port_occupied else "28679已被占用或netstat失败"},
        {"名称": "新系统n8n尚未运行", "通过": ok_docker and not v3_running, "说明": "未发现jiege_v3_n8n运行" if ok_docker and not v3_running else "发现疑似新系统n8n或docker查询失败"},
        {"名称": "旧系统不作为目标", "通过": "jiege_n8n" in docker_output, "说明": "旧系统jiege_n8n仍仅作为保护对象识别，不作为目标"},
    ]
    ready = all(item["通过"] for item in checks)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查项": checks,
        "是否具备启动前基础条件": ready,
        "当前结论": "启动前只读条件齐备；后续若启动服务仍属于高风险施工动作，需要按实施申请边界执行。" if ready else "启动前基础条件未齐备；当前不启动服务，先补齐缺口。",
        "实际动作": {
            "读取netstat": ok_netstat,
            "读取docker_ps": ok_docker,
            "读取本地路径": True,
            "写入新系统股票核验报告": True,
            "创建n8n数据目录": False,
            "启动n8n服务": False,
            "重启服务": False,
            "导入n8n": False,
            "启用n8n工作流": False,
            "触发n8n工作流": False,
            "写旧系统": False,
            "发送企业微信": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False
        }
    }
    output_dir = root / "03数据" / "68隔离n8n启动前只读核验"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手隔离n8n启动前只读核验_{stamp}.json"
    latest_json = output_dir / "股票助手隔离n8n启动前只读核验_最新.json"
    output_md = output_dir / f"股票助手隔离n8n启动前只读核验_{stamp}.md"
    latest_md = output_dir / "股票助手隔离n8n启动前只读核验_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备启动前基础条件": ready, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
