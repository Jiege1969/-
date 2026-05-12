# -*- coding: utf-8 -*-
"""
名称：生成个人智能母系统日常调度状态.py
作用：根据交易保护窗口、资源状态、暂停标志和旧口径审计状态，生成个人智能母系统当前运行/施工调度状态。
触发方式：python 生成个人智能母系统日常调度状态.py [--now "YYYY-MM-DD HH:MM:SS"] [--ignore-resource-pressure]
依赖：Python标准库；PowerShell；nvidia-smi可选；交易保护与施工窗口规则；个人智能母系统日常调度规则。
所属系统：00杰哥系统总管。
输出：00杰哥系统总管/04日志/个人智能母系统日常调度/daily-scheduler-state-*.json|md；03数据/运行状态/个人智能母系统日常调度状态_最新.json|md。
安全边界：只读判断并写总管状态/日志；不重启服务、不触发n8n、不发送企业微信、不调用券商接口、不自动交易、不下载模型、不执行备份。
标识：personal-ai-daily-scheduler-state；分时调度；硬件天花板；只读状态。
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, time
from pathlib import Path
from typing import Any


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2))


def parse_hhmm(value: str) -> time:
    hour, minute = value.split(":", 1)
    return time(int(hour), int(minute))


def in_window(current: time, start: str, end: str) -> bool:
    return parse_hhmm(start) <= current <= parse_hhmm(end)


def run_command(args: list[str], timeout: int = 15) -> tuple[int, str]:
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


def run_ps(script: str, timeout: int = 15) -> str:
    return run_command(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        timeout=timeout,
    )[1]


def detect_resources() -> dict[str, Any]:
    script = r"""
$os=Get-CimInstance Win32_OperatingSystem
$cpu=Get-CimInstance Win32_Processor
[ordered]@{
  cpu_percent=$cpu.LoadPercentage
  total_memory_mb=[math]::Round($os.TotalVisibleMemorySize/1024,0)
  free_memory_mb=[math]::Round($os.FreePhysicalMemory/1024,0)
} | ConvertTo-Json -Compress
"""
    try:
        base = json.loads(run_ps(script) or "{}")
    except json.JSONDecodeError:
        base = {}

    gpu = {"可用": False}
    code, out = run_command(
        [
            "nvidia-smi",
            "--query-gpu=memory.total,memory.used,temperature.gpu",
            "--format=csv,noheader,nounits",
        ],
        timeout=10,
    )
    if code == 0 and out:
        first = out.splitlines()[0]
        parts = [item.strip() for item in first.split(",")]
        if len(parts) >= 3:
            total = float(parts[0])
            used = float(parts[1])
            temp = float(parts[2])
            gpu = {
                "可用": True,
                "显存总量MB": total,
                "显存占用MB": used,
                "显存占用百分比": round(used / total * 100, 2) if total else None,
                "温度摄氏度": temp,
            }
    return {"CPU内存": base, "GPU": gpu}


def detect_heavy_processes(keywords: list[str]) -> list[dict[str, Any]]:
    escaped = [keyword.lower() for keyword in keywords]
    script = r"""
Get-Process |
  Select-Object Id,ProcessName,MainWindowTitle |
  ConvertTo-Json -Compress -Depth 3
"""
    try:
        processes = json.loads(run_ps(script, timeout=20) or "[]")
    except json.JSONDecodeError:
        processes = []
    if isinstance(processes, dict):
        processes = [processes]
    hits = []
    for proc in processes:
        haystack = f"{proc.get('ProcessName') or ''} {proc.get('MainWindowTitle') or ''}".lower()
        matched = [keyword for keyword in escaped if keyword.lower() in haystack]
        if matched:
            hits.append({
                "PID": proc.get("Id"),
                "进程名": proc.get("ProcessName"),
                "窗口": proc.get("MainWindowTitle"),
                "命中": matched,
            })
    return hits


def trading_state(manager: Path, now: datetime) -> dict[str, Any]:
    script = manager / "02脚本" / "判断交易保护施工窗口.py"
    code, out = run_command(["python", str(script), "--now", now.strftime("%Y-%m-%d %H:%M:%S")], timeout=20)
    latest = manager / "03数据" / "运行状态" / "交易保护施工窗口_最新.json"
    detail = load_json(latest) if latest.exists() else {}
    return {"返回码": code, "输出": out, "详情": detail}


def old_contract_state(manager: Path) -> dict[str, Any]:
    latest = manager / "04日志" / "旧口径冲突审计" / "old-contract-conflict-audit-最新.json"
    if not latest.exists():
        return {"状态": "未生成", "高等级": None, "中等级": None, "阻断": False}
    data = load_json(latest)
    high = int(data.get("高等级数量") or data.get("高等级") or 0)
    medium = int(data.get("中等级数量") or data.get("中等级") or 0)
    return {"状态": "已生成", "高等级": high, "中等级": medium, "阻断": high > 0 or medium > 0, "文件": str(latest)}


def pause_state(manager: Path) -> dict[str, Any]:
    pause_file = manager / "03数据" / "运行状态" / "暂停模式.flag"
    return {"是否暂停": pause_file.exists(), "标志文件": str(pause_file)}


def classify_state(
    now: datetime,
    schedule_rules: dict[str, Any],
    window_detail: dict[str, Any],
    resources: dict[str, Any],
    heavy_processes: list[dict[str, Any]],
    old_state: dict[str, Any],
    paused: dict[str, Any],
    ignore_resource_pressure: bool = False,
) -> tuple[str, list[str], list[str], list[str]]:
    reasons: list[str] = []
    allowed: list[str] = []
    forbidden: list[str] = list(schedule_rules.get("禁止自动执行", []))

    if paused.get("是否暂停"):
        return "暂停模式", ["检测到暂停模式标志。"], ["只读状态查询", "核心入口健康检查"], forbidden

    if old_state.get("阻断"):
        return "异常保护", ["旧口径审计存在高危或中危残留。"], ["旧口径审计修复", "核心入口健康检查"], forbidden

    thresholds = schedule_rules.get("资源避让阈值", {})
    cpu_mem = resources.get("CPU内存", {})
    gpu = resources.get("GPU", {})
    cpu_high = float(cpu_mem.get("cpu_percent") or 0) >= float(thresholds.get("CPU百分比", 85))
    mem_low = float(cpu_mem.get("free_memory_mb") or 999999) < float(thresholds.get("可用内存MB", 8192))
    gpu_high = gpu.get("可用") and float(gpu.get("显存占用百分比") or 0) >= float(thresholds.get("GPU显存占用百分比", 75))
    gpu_hot = gpu.get("可用") and float(gpu.get("温度摄氏度") or 0) >= float(thresholds.get("GPU温度摄氏度", 78))
    if not ignore_resource_pressure and (cpu_high or mem_low or gpu_high or gpu_hot or heavy_processes):
        reasons.append("检测到资源高负载或用户重负载应用。")
        allowed = ["企业微信问答", "股票入口保活", "只读健康检查", "延后非必要任务"]
        forbidden.extend(["启动视频渲染", "启动模型训练", "批量报告生成", "版本升级"])
        return "用户重负载避让", reasons, allowed, forbidden

    window_state = str(window_detail.get("当前运行状态") or "")
    if window_state in {"交易保护", "施工保护"}:
        reasons.append(f"交易/施工保护窗口：{window_state}。")
        allowed = window_detail.get("保护窗口内允许动作", [])
        forbidden.extend(window_detail.get("保护窗口内禁止动作", []))
        return "开市轻量待命", reasons, allowed, forbidden

    if window_state == "收市分析":
        reasons.append("处于收市后股票分析窗口。")
        allowed = ["股票数据采集", "分层日报生成", "推荐报告生成", "报告质检旁路", "推荐详情验收"]
        forbidden.extend(["大模型训练", "视频渲染", "系统底座升级"])
        return "收市股票分析", reasons, allowed, forbidden

    current_time = now.time()
    if current_time >= time(22, 0) or current_time <= time(6, 0):
        reasons.append("处于夜间低峰窗口。")
        allowed = ["复盘学习", "备份归档", "版本情报只读检查", "影子试验", "低风险维护", "新业务系统模板生成"]
        forbidden.extend(["无回滚升级", "无验收切正式"])
        return "夜间维护进化", reasons, allowed, forbidden

    reasons.append("资源健康且不处于交易保护、收市分析或夜间维护窗口。")
    allowed = ["企业微信问答", "状态查询", "文档整理", "规则草案", "低风险脚本准备", "静态验收"]
    return "日常轻量可用", reasons, allowed, forbidden


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 个人智能母系统日常调度状态",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 判断时间：{report['判断时间']}",
        f"- 当前状态：{report['当前状态']}",
        f"- 结论：{report['结论']}",
        "",
        "## 原因",
    ]
    lines.extend([f"- {item}" for item in report.get("原因", [])])
    lines.extend(["", "## 当前允许"])
    lines.extend([f"- {item}" for item in report.get("当前允许", [])])
    lines.extend(["", "## 当前禁止"])
    lines.extend([f"- {item}" for item in report.get("当前禁止", [])[:30]])
    lines.extend(["", "## 安全边界"])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", help="用于验收的指定时间，格式 YYYY-MM-DD HH:MM:SS；默认当前本机时间。")
    parser.add_argument("--ignore-resource-pressure", action="store_true", help="仅用于验收时间窗口逻辑，忽略当前真实资源压力。")
    args = parser.parse_args()

    now = datetime.strptime(args.now, "%Y-%m-%d %H:%M:%S") if args.now else datetime.now()
    manager = manager_root()
    rules_path = manager / "01配置" / "个人智能母系统日常调度规则.json"
    rules = load_json(rules_path)

    window = trading_state(manager, now)
    resources = detect_resources()
    heavy_processes = detect_heavy_processes(rules.get("用户重负载进程关键词", []))
    old_state = old_contract_state(manager)
    paused = pause_state(manager)
    state, reasons, allowed, forbidden = classify_state(
        now,
        rules,
        window.get("详情", {}),
        resources,
        heavy_processes,
        old_state,
        paused,
        args.ignore_resource_pressure,
    )
    report = {
        "名称": "个人智能母系统日常调度状态",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "判断时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "当前状态": state,
        "结论": "只读判断完成；按当前状态决定后续任务是否允许、延后或降级。",
        "原因": reasons,
        "当前允许": allowed,
        "当前禁止": sorted(set(forbidden)),
        "交易保护判断": window,
        "资源状态": resources,
        "用户重负载进程": heavy_processes,
        "旧口径审计状态": old_state,
        "暂停模式": paused,
        "调度优先级": rules.get("调度优先级", []),
        "安全边界": {
            "是否重启服务": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否下载模型": False,
            "是否执行备份": False,
        },
        "规则文件": str(rules_path),
    }

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = manager / "04日志" / "个人智能母系统日常调度"
    state_dir = manager / "03数据" / "运行状态"
    json_path = log_dir / "daily-scheduler-state-最新.json"
    md_path = log_dir / "daily-scheduler-state-最新.md"
    latest_json = state_dir / "个人智能母系统日常调度状态_最新.json"
    latest_md = state_dir / "个人智能母系统日常调度状态_最新.md"
    write_json(json_path, report)
    write_text(md_path, render_markdown(report))
    write_json(latest_json, report)
    write_text(latest_md, render_markdown(report))

    print(json.dumps({"当前状态": state, "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
