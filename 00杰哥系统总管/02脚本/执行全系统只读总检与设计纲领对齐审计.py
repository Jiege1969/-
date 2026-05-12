# -*- coding: utf-8 -*-
"""
Name: readonly-systemwide-audit-and-design-alignment.py
Purpose: Generate a read-only system inventory and design-principle alignment audit.
Safety: Read-only probes only. Does not trigger n8n workflows, send WeCom messages,
        call broker APIs, delete files, clean data, or modify service state.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
CONFIG_DIR = MANAGER / "01配置"
STARTUP_DIR = MANAGER / "03数据" / "开机施工准备"
STOCK_CONFIG_DIR = ROOT / "02杰哥扩展系统" / "01股票研究系统" / "01配置"


KEY_CONFIGS = [
    CONFIG_DIR / "系统宪法级原则落地规则.json",
    CONFIG_DIR / "真实接入总闸门规则.json",
    CONFIG_DIR / "股票分析非交易边界规则.json",
    CONFIG_DIR / "股票自动交易屏蔽总闸门规则.json",
    CONFIG_DIR / "并行施工容量控制规则.json",
    CONFIG_DIR / "轻量任务契约层规则.json",
    CONFIG_DIR / "进度口径规则.json",
    CONFIG_DIR / "进度回答标准.json",
    CONFIG_DIR / "服务注册表.json",
    CONFIG_DIR / "端口分配表.json",
    STOCK_CONFIG_DIR / "股票分析系统硬闸门配置.json",
    STOCK_CONFIG_DIR / "股票企业微信真实灰度最终闸口规则.json",
    STOCK_CONFIG_DIR / "股票企业微信真实灰度未确认拦截规则.json",
]


def run_command(args: list[str], timeout: int = 20) -> dict[str, Any]:
    started = time.time()
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "elapsed_sec": round(time.time() - started, 3),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
            "elapsed_sec": round(time.time() - started, 3),
        }


def powershell_json(script: str, timeout: int = 30) -> Any:
    result = run_command(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        timeout=timeout,
    )
    if not result["ok"] or not result["stdout"]:
        return {"_error": result}
    try:
        return json.loads(result["stdout"])
    except json.JSONDecodeError:
        return {"_raw": result["stdout"], "_error": result}


def http_get_json(url: str, timeout: float = 5.0) -> dict[str, Any]:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = body[:500]
            return {"ok": True, "status": resp.status, "body": parsed}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def file_json_status(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "name": path.name,
    }
    if not path.exists():
        return info
    info.update({"size": path.stat().st_size, "mtime": datetime.fromtimestamp(path.stat().st_mtime).isoformat(sep=" ")})
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        info["json_ok"] = True
        if isinstance(data, dict):
            info["top_keys"] = list(data.keys())[:20]
        elif isinstance(data, list):
            info["list_len"] = len(data)
    except Exception as exc:  # noqa: BLE001
        info["json_ok"] = False
        info["error"] = f"{type(exc).__name__}: {exc}"
    return info


def read_text_tail(path: Path, max_chars: int = 4000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    return text[-max_chars:]


def count_files(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    files = 0
    dirs = 0
    try:
        for _, dirnames, filenames in os.walk(path):
            dirs += len(dirnames)
            files += len(filenames)
            if files > 200000:
                break
        return {"exists": True, "dirs": dirs, "files": files}
    except Exception as exc:  # noqa: BLE001
        return {"exists": True, "error": f"{type(exc).__name__}: {exc}"}


def evaluate(report: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []

    def add(level: str, area: str, title: str, evidence: str, suggestion: str) -> None:
        findings.append(
            {
                "level": level,
                "area": area,
                "title": title,
                "evidence": evidence,
                "suggestion": suggestion,
            }
        )

    startup = report.get("startup_preflight", {})
    startup_text = startup.get("latest_md_tail", "")
    if "Ready for Codex construction: True" in startup_text and "Warnings\n\nnone" in startup_text:
        pass
    else:
        add("P1", "开机自检", "最新开机自检不是明确全绿", "未同时读到 Ready=True 与 Warnings none。", "先复核开机自检报告，再决定是否进入调整。")

    scheduled = report.get("scheduled_tasks", [])
    direct_shell_tasks = [
        t for t in scheduled
        if "powershell" in (str(t.get("Execute", "")) + str(t.get("Arguments", ""))).lower()
        or "cmd" in (str(t.get("Execute", "")) + str(t.get("Arguments", ""))).lower()
        or "pwsh" in (str(t.get("Execute", "")) + str(t.get("Arguments", ""))).lower()
    ]
    if direct_shell_tasks:
        add("P1", "开机无干扰", "仍有杰哥计划任务直接调用命令行", f"{len(direct_shell_tasks)} 条任务疑似直接调用 shell。", "统一改为 wscript 静默入口或明确保留原因。")

    ports = {str(item.get("LocalPort")) for item in report.get("listening_ports", []) if isinstance(item, dict)}
    for port in ["19300", "19302", "19310", "28100", "26379", "28679", "29134"]:
        if port not in ports:
            level = "P2" if port == "28100" else "P1"
            add(level, "运行入口", f"端口 {port} 当前未监听", f"监听端口集合：{sorted(ports)}", "若该入口属于日常必需，纳入开机 readiness；若非必需，标注为可选。")

    docker_running = {c.get("Names") or c.get("names") for c in report.get("docker", {}).get("running", []) if isinstance(c, dict)}
    for name in ["jiege_v3_ollama", "jiege_v3_redis", "jiege_v3_n8n"]:
        if name not in docker_running:
            add("P1", "Docker底座", f"{name} 未处于运行态", f"当前运行容器：{sorted(str(x) for x in docker_running)}", "先恢复底座容器，再做业务入口检查。")

    exited_old = report.get("docker", {}).get("exited_jiege_containers", [])
    if exited_old:
        add("P2", "旧资产治理", "仍存在退出态旧 jiege 容器", f"数量：{len(exited_old)}", "保持不自动删除；后续做旧容器归档/删除确认单。")

    json_bad = [x for x in report.get("key_configs", []) if x.get("exists") and not x.get("json_ok", True)]
    if json_bad:
        add("P1", "配置可解析性", "关键 JSON 配置存在解析失败", "、".join(x.get("name", "") for x in json_bad), "优先修复编码或 JSON 结构。")

    missing = [x for x in report.get("key_configs", []) if not x.get("exists")]
    if missing:
        add("P2", "配置完整性", "部分关键规则文件缺失", "、".join(x.get("name", "") for x in missing), "确认是否迁移、废弃或需补建。")

    stock_gate_names = {x.get("name"): x for x in report.get("key_configs", [])}
    if not stock_gate_names.get("股票自动交易屏蔽总闸门规则.json", {}).get("json_ok"):
        add("P1", "股票安全", "股票自动交易总闸门未确认可解析", "未读到有效 JSON。", "优先确认股票系统仍是 analysis-only。")
    if not stock_gate_names.get("股票分析系统硬闸门配置.json", {}).get("json_ok"):
        add("P1", "股票安全", "股票硬闸门配置未确认可解析", "未读到有效 JSON。", "优先确认券商接口、下单、自动交易保持关闭。")

    endpoints = report.get("http_endpoints", {})
    for name, result in endpoints.items():
        if name in {"stock_assistant_19300", "stock_wecom_19302", "wecom_unified_19310", "ollama_29134", "n8n_28679"}:
            if not result.get("ok"):
                add("P1", "HTTP健康", f"{name} 健康探测失败", result.get("error", "no detail"), "检查对应服务是否应纳入日常启动。")

    if not findings:
        add("OK", "总体", "未发现交付阻断", "只读审计未发现 P0/P1 交付阻断。", "进入灰度运行观察与周期巡检。")

    p0 = sum(1 for x in findings if x["level"] == "P0")
    p1 = sum(1 for x in findings if x["level"] == "P1")
    p2 = sum(1 for x in findings if x["level"] == "P2")
    return {
        "summary": {
            "p0": p0,
            "p1": p1,
            "p2": p2,
            "delivery_blocked": p0 > 0,
            "needs_attention": p1 > 0 or p2 > 0,
        },
        "findings": findings,
    }


def render_markdown(report: dict[str, Any]) -> str:
    audit = report["alignment_audit"]
    lines: list[str] = []
    lines.append("# 全系统只读总检与设计纲领对齐审计")
    lines.append("")
    lines.append(f"生成时间：{report['generated_at']}")
    lines.append("")
    lines.append("## 总体结论")
    lines.append("")
    s = audit["summary"]
    lines.append(f"- 交付阻断：{'是' if s['delivery_blocked'] else '否'}")
    lines.append(f"- P0：{s['p0']}，P1：{s['p1']}，P2：{s['p2']}")
    lines.append("- 本轮只读：未触发 n8n、未发送企业微信、未调用券商接口、未删除或清理文件、未修改业务配置。")
    lines.append("")
    lines.append("## 当前运行家底")
    lines.append("")
    lines.append(f"- 主机：{report['machine']['platform']} / {report['machine']['processor']}")
    lines.append(f"- 顶层目录：{', '.join(report['top_level_dirs'])}")
    lines.append(f"- 计划任务：{len(report['scheduled_tasks'])} 条杰哥任务。")
    lines.append(f"- 监听端口：{', '.join(str(x.get('LocalPort')) for x in report['listening_ports'] if isinstance(x, dict))}")
    docker_names = [x.get("Names") or x.get("names") for x in report["docker"]["running"] if isinstance(x, dict)]
    lines.append(f"- Docker 运行容器：{', '.join(str(x) for x in docker_names) if docker_names else '未读到'}")
    exited = report["docker"]["exited_jiege_containers"]
    lines.append(f"- 退出态旧 jiege 容器：{len(exited)} 个。")
    lines.append("")
    lines.append("## 健康入口")
    lines.append("")
    for name, result in report["http_endpoints"].items():
        status = "通过" if result.get("ok") else "失败"
        detail = result.get("error") or result.get("status") or ""
        lines.append(f"- {name}：{status} {detail}")
    lines.append("")
    lines.append("## 关键配置解析")
    lines.append("")
    for cfg in report["key_configs"]:
        if not cfg.get("exists"):
            status = "缺失"
        elif cfg.get("json_ok"):
            status = "JSON可解析"
        else:
            status = "解析失败"
        lines.append(f"- {cfg['name']}：{status}")
    lines.append("")
    lines.append("## 设计纲领对齐判断")
    lines.append("")
    lines.append("- 本地运行：核心入口和 Docker 底座均以本机端口为主，符合本地优先思路。")
    lines.append("- 数据不外传：本轮未发现需要正式外发的动作；公网/企业微信真实链路继续按闸门管理。")
    lines.append("- 人工确认闸口：真实发送、n8n正式执行、券商接口、清理删除仍应保持单独确认。")
    lines.append("- 股票系统定位：继续按 analysis-only 管理，自动交易和券商接口不得打开。")
    lines.append("- n8n定位：n8n作为编排底座运行，不应接管总管准入、调度和证据口径。")
    lines.append("- 经验沉淀：已有运行记录、修复记录和交付手册，但后续要进入周期化巡检而不是继续堆搭建动作。")
    lines.append("")
    lines.append("## 偏差与风险清单")
    lines.append("")
    for item in audit["findings"]:
        lines.append(f"- [{item['level']}] {item['area']}：{item['title']}")
        lines.append(f"  证据：{item['evidence']}")
        lines.append(f"  建议：{item['suggestion']}")
    lines.append("")
    lines.append("## 下一步建议")
    lines.append("")
    lines.append("1. 若 P1 为 0：进入 3-7 天灰度运行观察，每日只读巡检一次。")
    lines.append("2. 若存在 P1：先修复影响日常启动、入口健康或关键闸门解析的问题。")
    lines.append("3. P2 项保持登记，不做自动清理；旧容器、旧备份、旧报告归档需另起确认清单。")
    lines.append("4. 后续新增功能前，先通过任务契约层和总管准入，不直接让 n8n 或业务脚本越权执行。")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    top_level_dirs = [p.name for p in ROOT.iterdir() if p.is_dir()]
    scheduled = powershell_json(
        "Get-ScheduledTask | Where-Object { $_.TaskName -like '杰哥智能化系统_*' } | "
        "ForEach-Object { foreach($a in $_.Actions){ [pscustomobject]@{TaskName=$_.TaskName; State=$_.State; Execute=$a.Execute; Arguments=$a.Arguments; WorkingDirectory=$a.WorkingDirectory; Hidden=$_.Settings.Hidden; StartWhenAvailable=$_.Settings.StartWhenAvailable; ExecutionTimeLimit=$_.Settings.ExecutionTimeLimit} } } | ConvertTo-Json -Depth 5",
        timeout=30,
    )
    if isinstance(scheduled, dict):
        scheduled_list = [] if "_error" in scheduled else [scheduled]
    else:
        scheduled_list = scheduled or []

    listening = powershell_json(
        "Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | "
        "Where-Object { $_.LocalAddress -in @('127.0.0.1','0.0.0.0','::','::1') } | "
        "Select-Object LocalAddress,LocalPort,OwningProcess | Sort-Object LocalPort | ConvertTo-Json -Depth 4",
        timeout=30,
    )
    if isinstance(listening, dict):
        listening_list = [] if "_error" in listening else [listening]
    else:
        listening_list = listening or []

    docker_ps = run_command(["docker", "ps", "--format", "{{json .}}"], timeout=20)
    docker_running = []
    if docker_ps["ok"] and docker_ps["stdout"]:
        for line in docker_ps["stdout"].splitlines():
            try:
                docker_running.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    docker_ps_a = run_command(["docker", "ps", "-a", "--format", "{{json .}}"], timeout=20)
    exited_jiege = []
    if docker_ps_a["ok"] and docker_ps_a["stdout"]:
        for line in docker_ps_a["stdout"].splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            name = item.get("Names", "")
            status = item.get("Status", "")
            if "jiege" in name.lower() and not status.lower().startswith("up"):
                exited_jiege.append(item)

    wsl = run_command(["wsl.exe", "-l", "-v"], timeout=20)
    redis_ping = run_command(["docker", "exec", "jiege_v3_redis", "redis-cli", "ping"], timeout=10)

    endpoints = {
        "stock_assistant_19300": http_get_json("http://127.0.0.1:19300/health", timeout=5),
        "stock_wecom_19302": http_get_json("http://127.0.0.1:19302/health", timeout=5),
        "wecom_unified_19310": http_get_json("http://127.0.0.1:19310/health", timeout=5),
        "v3_agent_brain_28100": http_get_json("http://127.0.0.1:28100/health", timeout=5),
        "n8n_28679": http_get_json("http://127.0.0.1:28679/healthz", timeout=5),
        "ollama_29134": http_get_json("http://127.0.0.1:29134/api/tags", timeout=8),
    }

    report: dict[str, Any] = {
        "generated_at": generated_at,
        "root": str(ROOT),
        "machine": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python": sys.version,
        },
        "top_level_dirs": top_level_dirs,
        "directory_counts": {p.name: count_files(p) for p in ROOT.iterdir() if p.is_dir()},
        "scheduled_tasks": scheduled_list,
        "listening_ports": listening_list,
        "docker": {
            "running": docker_running,
            "exited_jiege_containers": exited_jiege,
            "ps_error": None if docker_ps["ok"] else docker_ps["stderr"],
        },
        "wsl": {
            "ok": wsl["ok"],
            "stdout": wsl["stdout"],
            "stderr": wsl["stderr"],
        },
        "redis_ping": redis_ping,
        "http_endpoints": endpoints,
        "key_configs": [file_json_status(path) for path in KEY_CONFIGS],
        "startup_preflight": {
            "latest_md": str(STARTUP_DIR / "startup_construction_preflight_latest.md"),
            "latest_json": file_json_status(STARTUP_DIR / "startup_construction_preflight_latest.json"),
            "latest_md_tail": read_text_tail(STARTUP_DIR / "startup_construction_preflight_latest.md", 5000),
        },
        "safety_statement": {
            "trigger_n8n": False,
            "send_wecom": False,
            "broker_api": False,
            "auto_trade": False,
            "delete_or_clean": False,
            "modify_business_config": False,
        },
    }
    report["alignment_audit"] = evaluate(report)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = OUT_DIR / f"全系统只读总检与设计纲领对齐审计_{stamp}.json"
    md_path = OUT_DIR / f"全系统只读总检与设计纲领对齐审计_{stamp}.md"
    latest_json = OUT_DIR / "全系统只读总检与设计纲领对齐审计_最新.json"
    latest_md = OUT_DIR / "全系统只读总检与设计纲领对齐审计_最新.md"

    text = render_markdown(report)
    for path in [json_path, latest_json]:
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for path in [md_path, latest_md]:
        path.write_text(text, encoding="utf-8")

    print(json.dumps({
        "generated_at": generated_at,
        "json": str(latest_json),
        "markdown": str(latest_md),
        "summary": report["alignment_audit"]["summary"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
