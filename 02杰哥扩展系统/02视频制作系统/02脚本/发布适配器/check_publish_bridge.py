# -*- coding: utf-8 -*-
"""
名称：check_publish_bridge.py
作用：检查轮次012视频发布桥梁是否具备真实发布前置条件。
触发方式：python check_publish_bridge.py [--task-id VF-YYYYMMDD-001]
依赖：Python 标准库；视频发布桥梁配置.json；视频发布放行清单_最新.md。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：只做本地检查和报告输出；不调用真实发布、不上传、不触发企业微信真实发送或n8n。
创建/修改记录：2026-05-08 创建发布桥梁预检工具。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def module_root() -> Path:
    return Path(__file__).resolve().parents[2]


ROOT = module_root()
ROUND_DIR = ROOT / "03数据" / "18轮次012视频工厂总控层"
CONFIG_PATH = ROOT / "01配置" / "视频发布桥梁配置.json"
RELEASE_PATH = ROUND_DIR / "放行清单" / "视频发布放行清单_最新.md"
OUTPUT_DIR = ROUND_DIR / "测试与审核" / "发布桥梁预检"
ARCHIVE_DIR = OUTPUT_DIR / "archive"
LATEST_JSON = OUTPUT_DIR / "发布桥梁预检_最新.json"
LATEST_MD = OUTPUT_DIR / "发布桥梁预检_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_markdown_table(text: str) -> list[dict[str, str]]:
    table_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(table_lines) < 3:
        return []
    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells, strict=True)))
    return rows


def clean_field(value: Any) -> str:
    text = str(value or "").strip()
    return "" if text == "-" else text


def check_command(command: str) -> dict[str, Any]:
    result = {
        "命令": command,
        "路径": shutil.which(command),
        "可用": False,
        "stdout": "",
        "stderr": "",
        "错误": "",
    }
    if not result["路径"]:
        result["错误"] = "未在PATH中找到命令"
        return result
    try:
        completed = subprocess.run(
            [command, "--help"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
        result["可用"] = completed.returncode in {0, 1}
        result["stdout"] = completed.stdout[:2000]
        result["stderr"] = completed.stderr[:2000]
        result["returncode"] = completed.returncode
    except Exception as exc:  # noqa: BLE001
        result["错误"] = str(exc)
        result["traceback"] = traceback.format_exc()
    return result


def check_patchright_runtime() -> dict[str, Any]:
    base = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")) if os.environ.get("PLAYWRIGHT_BROWSERS_PATH") else Path.home() / "AppData" / "Local" / "ms-playwright"
    chromium_dirs = sorted(base.glob("chromium-*")) if base.exists() else []
    headless_dirs = sorted(base.glob("chromium_headless_shell-*")) if base.exists() else []
    ffmpeg_dirs = sorted(base.glob("ffmpeg-*")) if base.exists() else []
    return {
        "浏览器目录": str(base),
        "chromium": [str(path) for path in chromium_dirs],
        "chromium_headless_shell": [str(path) for path in headless_dirs],
        "ffmpeg": [str(path) for path in ffmpeg_dirs],
        "可用": bool(chromium_dirs or headless_dirs),
    }


def row_findings(row: dict[str, str], real_publish_enabled: bool) -> list[str]:
    findings: list[str] = []
    task_id = row.get("任务ID", "未识别")
    if row.get("发布放行状态") != "放行":
        findings.append(f"{task_id}：发布放行状态不是“放行”")
    video_file = clean_field(row.get("视频文件", ""))
    if not video_file:
        findings.append(f"{task_id}：未填写视频文件；阻断真实发布")
    elif not Path(video_file).exists():
        findings.append(f"{task_id}：视频文件不存在：{video_file}")
    if not clean_field(row.get("平台", "")):
        findings.append(f"{task_id}：未填写平台，将使用默认平台")
    if not clean_field(row.get("账号", "")):
        findings.append(f"{task_id}：未填写账号，将使用默认账号")
    return findings


def build_markdown(report: dict[str, Any]) -> str:
    blockers = report.get("阻断项", [])
    warnings = report.get("提醒项", [])
    blocker_text = "\n".join(f"- {item}" for item in blockers) if blockers else "- 无"
    warning_text = "\n".join(f"- {item}" for item in warnings) if warnings else "- 无"
    rows = report.get("发布清单行", [])
    row_text = "\n".join(
        f"| {row.get('任务ID', '')} | {row.get('发布放行状态', '')} | {row.get('平台', '')} | {row.get('视频文件', '')} |"
        for row in rows
    )
    if not row_text:
        row_text = "| - | - | - | - |"
    return "\n".join([
        "# 轮次012 发布桥梁预检报告",
        "",
        f"- 生成时间：{report.get('生成时间')}",
        f"- 总体状态：{report.get('总体状态')}",
        f"- 可进入真实发布：{report.get('可进入真实发布')}",
        f"- 真实发布启用：{report.get('真实发布启用')}",
        f"- 桥梁命令：{report.get('桥梁命令')}",
        f"- 命令可用：{report.get('命令检查', {}).get('可用')}",
        "",
        "## 阻断项",
        "",
        blocker_text,
        "",
        "## 提醒项",
        "",
        warning_text,
        "",
        "## 发布清单行",
        "",
        "| 任务ID | 发布放行状态 | 平台 | 视频文件 |",
        "| --- | --- | --- | --- |",
        row_text,
        "",
        "## 安全结论",
        "",
        "发布桥梁预检只做本地检查，不执行真实发布。未放行、未填写视频文件、未登记发布清单、未完成 AI 标识确认或桥梁配置未启用时，必须阻断真实发布。",
        "",
    ])


def run_check(task_id: str = "") -> dict[str, Any]:
    config = read_json(CONFIG_PATH)
    release_text = read_text(RELEASE_PATH)
    rows = parse_markdown_table(release_text)
    if task_id:
        rows = [row for row in rows if row.get("任务ID") == task_id]
    bridge = config.get("发布桥梁", {})
    command = str(bridge.get("命令", "sau"))
    real_publish_enabled = bool(bridge.get("启用真实发布", False))
    command_check = check_command(command)
    runtime_check = check_patchright_runtime()
    blockers: list[str] = []
    warnings: list[str] = []

    if not CONFIG_PATH.exists():
        blockers.append(f"缺少发布桥梁配置：{CONFIG_PATH}")
    if not RELEASE_PATH.exists():
        blockers.append(f"缺少发布放行清单：{RELEASE_PATH}")
    if not command_check.get("可用"):
        blockers.append(f"发布桥梁命令不可用：{command}；请先安装并验证 social-auto-upload")
    if not runtime_check.get("可用"):
        blockers.append("patchright Chromium 运行时未就绪；请先安装浏览器运行时")
    if not rows:
        blockers.append("未找到匹配的发布清单任务行")
    for row in rows:
        findings = row_findings(row, real_publish_enabled)
        for finding in findings:
            if "视频文件" in finding or "状态不是" in finding:
                blockers.append(finding)
            else:
                warnings.append(finding)
    if not real_publish_enabled:
        warnings.append("真实发布当前关闭；这是默认安全状态。")

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not blockers else "blocked",
        "任务ID过滤": task_id,
        "真实发布启用": real_publish_enabled,
        "可进入真实发布": bool(real_publish_enabled and not blockers),
        "桥梁命令": command,
        "命令检查": command_check,
        "浏览器运行时检查": runtime_check,
        "发布清单行": rows,
        "阻断项": blockers,
        "提醒项": warnings,
        "安全边界": {
            "真实发布": False,
            "执行上传": False,
            "执行发布": False,
            "调用外部账号": False,
            "触发n8n": False,
            "企业微信真实发送": False,
        },
    }
    return report


def save_report(report: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    markdown = build_markdown(report)
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, markdown)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(ARCHIVE_DIR / f"发布桥梁预检_{timestamp}.json", report)
    write_text(ARCHIVE_DIR / f"发布桥梁预检_{timestamp}.md", markdown)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="轮次012发布桥梁预检")
    parser.add_argument("--task-id", default="", help="仅检查指定任务ID")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_check(args.task_id)
    save_report(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
