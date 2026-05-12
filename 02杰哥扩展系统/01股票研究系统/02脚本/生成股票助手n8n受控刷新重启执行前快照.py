# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-n8n-controlled-refresh-restart-preexecution-snapshot.py
Purpose: Generate a read-only pre-execution snapshot before isolated n8n controlled refresh/restart.
Trigger: python 生成股票助手n8n受控刷新重启执行前快照.py
Dependencies: Python standard library; Docker CLI if available; isolated n8n container jiege_v3_n8n.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Read-only snapshot only; does not restart, stop, enable, trigger, import, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created controlled refresh/restart pre-execution snapshot generator.
Marker: stock-assistant-n8n-controlled-refresh-restart-preexecution-snapshot-generate
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


def run_command(args: list[str], timeout: int = 60) -> dict[str, Any]:
    completed = subprocess.run(args, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {
        "命令": args,
        "返回码": completed.returncode,
        "标准输出": completed.stdout.strip(),
        "标准错误": completed.stderr.strip(),
    }


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


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手n8n受控刷新重启执行前快照",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否适合进入受控刷新/重启申请复核：{report['是否适合进入受控刷新重启申请复核']}",
        f"- 是否已执行重启：{report['实际动作']['重启n8n']}",
        f"- 是否已发送企业微信：{report['实际动作']['发送企业微信']}",
        f"- 是否触碰旧系统：{report['实际动作']['写旧系统']}",
        "",
        "## 二、状态摘要",
        "",
    ]
    for key, value in report["状态摘要"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、只读命令结果", ""])
    for key, value in report["只读命令结果"].items():
        lines.append(f"### {key}")
        lines.append("```text")
        lines.append(value.get("标准输出") or value.get("标准错误") or "")
        lines.append("```")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    v3_root = system_root()
    rule_path = root / "01配置" / "股票助手n8n受控刷新重启执行前快照规则.json"
    request_verify_latest = root / "04日志" / "n8n受控刷新重启申请" / "stock-assistant-n8n-controlled-refresh-restart-request-package-verify-最新.json"
    send_gate_config = v3_root / "02杰哥扩展系统" / "00公共组件" / "01配置" / "企业微信受控发送配置模板.json"
    commands = {
        "docker_ps_jiege_v3_n8n": run_command(["docker", "ps", "-a", "--filter", "name=jiege_v3_n8n", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}"], 60),
        "docker_ps_jiege_n8n_protected": run_command(["docker", "ps", "-a", "--filter", "name=jiege_n8n", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}"], 60),
        "n8n_inactive_workflows": run_command(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=false"], 120),
        "n8n_active_workflows": run_command(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=true"], 120),
    }
    request_verify = load_json(request_verify_latest)
    send_gate = load_json(send_gate_config)
    v3_line = commands["docker_ps_jiege_v3_n8n"].get("标准输出", "")
    old_line = commands["docker_ps_jiege_n8n_protected"].get("标准输出", "")
    ready = (
        commands["docker_ps_jiege_v3_n8n"]["返回码"] == 0
        and "jiege_v3_n8n" in v3_line
        and "127.0.0.1:28679" in v3_line
        and commands["docker_ps_jiege_n8n_protected"]["返回码"] == 0
        and "jiege_n8n" in old_line
        and request_verify.get("失败", 1) == 0
    )
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "申请包验收日志": str(request_verify_latest),
        "企业微信受控发送配置": str(send_gate_config),
        "状态摘要": {
            "隔离n8n容器": v3_line or "未读取到",
            "旧系统保护容器": old_line or "未读取到",
            "申请包验收是否通过": request_verify.get("失败") == 0,
            "真实企业微信发送闸口": send_gate.get("真实发送启用", False),
            "OpenClaw真实桥接": False,
            "交易接口": False,
        },
        "只读命令结果": commands,
        "是否适合进入受控刷新重启申请复核": ready,
        "实际动作": {
            "生成快照": True,
            "重启n8n": False,
            "停止容器": False,
            "启用Webhook": False,
            "触发Webhook": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "77n8n受控刷新重启执行前快照"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手n8n受控刷新重启执行前快照_{stamp}.json"
    latest_json = output_dir / "股票助手n8n受控刷新重启执行前快照_最新.json"
    output_md = output_dir / f"股票助手n8n受控刷新重启执行前快照_{stamp}.md"
    latest_md = output_dir / "股票助手n8n受控刷新重启执行前快照_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否适合进入受控刷新重启申请复核": ready, "输出": str(output_json)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
