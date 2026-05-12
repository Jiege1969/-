# -*- coding: utf-8 -*-
"""
名称：enable_real_publish.py
作用：轮次012真实发布启用前的最终门禁。只有账号、成品视频、发布清单、AI标识确认
和发布桥梁全部通过后，才允许把“视频发布桥梁配置.json”中的真实发布开关改为 true。
触发方式：python enable_real_publish.py --task-id VF-YYYYMMDD-001 --ai-label-confirmed
安全边界：本脚本只启用或保持关闭发布桥梁配置，不执行上传、不执行发布、不触发企业微信真实外发。
"""

from __future__ import annotations

import argparse
import json
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
OUTPUT_DIR = ROUND_DIR / "测试与审核" / "最终发布启用门禁"
ARCHIVE_DIR = OUTPUT_DIR / "archive"
LATEST_JSON = OUTPUT_DIR / "最终发布启用门禁_最新.json"
LATEST_MD = OUTPUT_DIR / "最终发布启用门禁_最新.md"

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
MIN_VIDEO_BYTES = 1_000_000


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


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


def normalize_platform(platform: str, config: dict[str, Any]) -> str:
    platform_map = config.get("平台映射", {})
    return platform_map.get(platform.strip(), platform.strip())


def find_release_row(task_id: str) -> dict[str, str]:
    rows = parse_markdown_table(read_text(RELEASE_PATH))
    for row in rows:
        if row.get("任务ID") == task_id:
            return row
    return {}


def check_command(command: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "命令": command,
        "可用": False,
        "路径": "",
        "错误": "",
    }
    resolved = shutil.which(command)
    if not resolved and Path(command).exists():
        resolved = command
    result["路径"] = resolved or ""
    if not resolved:
        result["错误"] = "未找到发布桥梁命令"
        return result
    try:
        completed = subprocess.run(
            [resolved, "--help"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
        result["returncode"] = completed.returncode
        result["stdout"] = completed.stdout[-1000:]
        result["stderr"] = completed.stderr[-1000:]
        result["可用"] = completed.returncode in {0, 1}
    except Exception as exc:  # noqa: BLE001
        result["错误"] = str(exc)
        result["traceback"] = traceback.format_exc()
    return result


def check_account(config: dict[str, Any], platform: str, account: str) -> dict[str, Any]:
    bridge = config.get("发布桥梁", {})
    command = str(bridge.get("命令", "sau"))
    normalized_platform = normalize_platform(platform, config)
    account_name = account or str(bridge.get("默认账号", "creator"))
    resolved = shutil.which(command) or (command if Path(command).exists() else command)
    cmd = [resolved, normalized_platform, "check", "--account", account_name]
    report: dict[str, Any] = {
        "平台": normalized_platform,
        "账号": account_name,
        "命令": cmd,
        "总体状态": "blocked",
        "returncode": None,
        "stdout": "",
        "stderr": "",
    }
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
        )
        report["returncode"] = completed.returncode
        report["stdout"] = completed.stdout[-2000:]
        report["stderr"] = completed.stderr[-2000:]
        report["总体状态"] = "pass" if completed.returncode == 0 else "blocked"
    except Exception as exc:  # noqa: BLE001
        report["错误"] = str(exc)
        report["traceback"] = traceback.format_exc()
    return report


def check_video_file(video_file: str) -> dict[str, Any]:
    path = Path(video_file)
    report: dict[str, Any] = {
        "视频文件": video_file,
        "存在": path.exists(),
        "扩展名": path.suffix.lower(),
        "文件大小": 0,
        "有效": False,
        "阻断原因": [],
    }
    blockers: list[str] = []
    if not video_file:
        blockers.append("未填写视频文件路径")
    elif not path.exists():
        blockers.append("视频文件不存在")
    else:
        report["文件大小"] = path.stat().st_size
        if path.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
            blockers.append(f"视频扩展名不在允许范围：{path.suffix}")
        if path.stat().st_size < MIN_VIDEO_BYTES:
            blockers.append(f"视频文件小于 {MIN_VIDEO_BYTES} 字节，疑似占位文件或非真实成品")
    report["阻断原因"] = blockers
    report["有效"] = not blockers
    return report


def archive_config(config: dict[str, Any], task_id: str) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(ARCHIVE_DIR / f"视频发布桥梁配置_before_{task_id}_{timestamp}.json", config)


def set_real_publish_enabled(config: dict[str, Any], task_id: str) -> None:
    archive_config(config, task_id)
    config.setdefault("发布桥梁", {})["启用真实发布"] = True
    config.setdefault("安全约束", [])
    if "真实发布已通过最终启用门禁后打开；如需暂停，请将发布桥梁.启用真实发布改回 false。" not in config["安全约束"]:
        config["安全约束"].append("真实发布已通过最终启用门禁后打开；如需暂停，请将发布桥梁.启用真实发布改回 false。")
    write_json(CONFIG_PATH, config)


def build_markdown(report: dict[str, Any]) -> str:
    blockers = report.get("阻断项", [])
    blocker_text = "\n".join(f"- {item}" for item in blockers) if blockers else "- 无"
    return "\n".join([
        "# 轮次012 最终发布启用门禁报告",
        "",
        f"- 生成时间：{report.get('生成时间')}",
        f"- 任务ID：{report.get('任务ID')}",
        f"- 总体状态：{report.get('总体状态')}",
        f"- 配置是否已启用真实发布：{report.get('配置已启用真实发布')}",
        f"- 平台：{report.get('平台')}",
        f"- 账号：{report.get('账号')}",
        f"- 视频文件：{report.get('视频文件')}",
        "",
        "## 阻断项",
        "",
        blocker_text,
        "",
        "## 安全结论",
        "",
        "本门禁只在全部条件通过后打开真实发布配置开关；不会上传视频，不会绕过发布放行清单，也不会触发企业微信真实外发。",
        "",
    ])


def save_report(report: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    markdown = build_markdown(report)
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, markdown)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(ARCHIVE_DIR / f"最终发布启用门禁_{report.get('任务ID', 'UNKNOWN')}_{timestamp}.json", report)
    write_text(ARCHIVE_DIR / f"最终发布启用门禁_{report.get('任务ID', 'UNKNOWN')}_{timestamp}.md", markdown)


def run_gate(task_id: str, ai_label_confirmed: bool) -> dict[str, Any]:
    config = read_json(CONFIG_PATH)
    bridge = config.get("发布桥梁", {})
    row = find_release_row(task_id)
    blockers: list[str] = []

    if not config:
        blockers.append(f"未找到发布桥梁配置：{CONFIG_PATH}")
    if not row:
        blockers.append(f"未在发布放行清单中找到任务：{task_id}")

    release_status = row.get("发布放行状态", "") if row else ""
    if release_status != "放行":
        blockers.append(f"发布放行状态不是“放行”：{release_status or '未填写'}")

    if not ai_label_confirmed:
        blockers.append("缺少 AI已标识 确认，不能启用真实发布")

    platform = clean_field(row.get("平台", "")) if row else ""
    account = clean_field(row.get("账号", "")) if row else ""
    video_file = clean_field(row.get("视频文件", "")) if row else ""
    title = clean_field(row.get("标题", "")) if row else ""
    desc = clean_field(row.get("简介", "")) if row else ""

    if not platform:
        platform = str((bridge.get("默认平台") or ["bilibili"])[0])
    if not account:
        account = str(bridge.get("默认账号", "creator"))
    if not title:
        blockers.append("发布清单缺少标题")
    if not desc:
        blockers.append("发布清单缺少简介")

    command_report = check_command(str(bridge.get("命令", "sau")))
    if not command_report.get("可用"):
        blockers.append(f"发布桥梁命令不可用：{command_report.get('错误') or command_report.get('命令')}")

    video_report = check_video_file(video_file)
    blockers.extend(video_report.get("阻断原因", []))

    account_report = check_account(config, platform, account) if command_report.get("可用") else {"总体状态": "blocked"}
    if account_report.get("总体状态") != "pass":
        blockers.append(f"发布账号未通过登录检查：{platform}/{account}")

    passed = not blockers
    if passed:
        set_real_publish_enabled(config, task_id)

    refreshed_config = read_json(CONFIG_PATH)
    report: dict[str, Any] = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": task_id,
        "总体状态": "pass" if passed else "blocked",
        "配置已启用真实发布": bool(refreshed_config.get("发布桥梁", {}).get("启用真实发布", False)),
        "AI标识已确认": ai_label_confirmed,
        "发布清单行": row,
        "发布放行状态": release_status,
        "平台": platform,
        "账号": account,
        "视频文件": video_file,
        "标题": title,
        "简介": desc,
        "命令检查": command_report,
        "视频文件检查": video_report,
        "账号检查": account_report,
        "阻断项": blockers,
        "安全边界": {
            "执行上传": False,
            "执行发布": False,
            "触发n8n": False,
            "企业微信真实外发": False,
        },
    }
    save_report(report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="轮次012真实发布启用前最终门禁")
    parser.add_argument("--task-id", required=True, help="任务ID，例如 VF-20260508-003")
    parser.add_argument("--ai-label-confirmed", action="store_true", help="确认发布平台已勾选或标识 AI 生成内容")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_gate(args.task_id, args.ai_label_confirmed)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("总体状态") == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
