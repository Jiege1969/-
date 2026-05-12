# -*- coding: utf-8 -*-
"""
名称：enable_real_render.py
作用：轮次012真实渲染启用前的最终门禁。
触发方式：python enable_real_render.py --task-id VF-YYYYMMDD-001 --confirm-real-render
安全边界：本脚本只在全部条件满足时打开视频生成桥梁配置中的真实渲染开关；不调用 MoneyPrinterTurbo，不生成媒体，不触发发布。
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
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
CONFIG_PATH = ROOT / "01配置" / "视频生成桥梁配置.json"
TASK_PATH = ROUND_DIR / "视频工厂任务单_最新.json"
GENERATION_RELEASE_PATH = ROUND_DIR / "放行清单" / "视频生成放行清单_最新.md"
OUTPUT_DIR = ROUND_DIR / "测试与审核" / "最终真实渲染启用门禁"
ARCHIVE_DIR = OUTPUT_DIR / "archive"
LATEST_JSON = OUTPUT_DIR / "最终真实渲染启用门禁_最新.json"
LATEST_MD = OUTPUT_DIR / "最终真实渲染启用门禁_最新.md"


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


def path_from_config(value: str) -> Path:
    if not value:
        return Path()
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def find_release_row(task_id: str) -> dict[str, str]:
    for row in parse_markdown_table(read_text(GENERATION_RELEASE_PATH)):
        if row.get("任务ID") == task_id:
            return row
    return {}


def check_moneyprinter(config: dict[str, Any]) -> dict[str, Any]:
    bridge = config.get("生成桥梁", {})
    candidates: list[Path] = []
    root = str(bridge.get("根目录", "")).strip()
    if root:
        candidates.append(path_from_config(root))
    for item in bridge.get("候选根目录", []):
        candidates.append(path_from_config(str(item)))

    checked: list[dict[str, Any]] = []
    for candidate in candidates:
        if not str(candidate):
            continue
        start_bat = candidate / "start.bat"
        app_file = candidate / "app" / "main.py"
        webui_file = candidate / "webui" / "Main.py"
        usable = candidate.exists() and (start_bat.exists() or app_file.exists() or webui_file.exists())
        item = {
            "路径": str(candidate),
            "存在": candidate.exists(),
            "start.bat": start_bat.exists(),
            "app/main.py": app_file.exists(),
            "webui/Main.py": webui_file.exists(),
            "可识别": usable,
        }
        checked.append(item)
        if usable:
            return {"可用": True, "根目录": str(candidate), "候选检查": checked}
    return {"可用": False, "根目录": "", "候选检查": checked}


def check_imagemagick(config: dict[str, Any]) -> dict[str, Any]:
    command = str(config.get("依赖检查", {}).get("ImageMagick命令", "magick"))
    resolved = shutil.which(command) or (command if Path(command).exists() else "")
    report: dict[str, Any] = {"命令": command, "路径": resolved, "可用": False, "错误": ""}
    if not resolved:
        report["错误"] = "未找到 ImageMagick 命令"
        return report
    try:
        completed = subprocess.run(
            [resolved, "-version"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        report["returncode"] = completed.returncode
        report["stdout"] = completed.stdout[:1000]
        report["stderr"] = completed.stderr[:1000]
        report["可用"] = completed.returncode == 0
    except Exception as exc:  # noqa: BLE001
        report["错误"] = str(exc)
    return report


def check_chrome(config: dict[str, Any]) -> dict[str, Any]:
    paths = [str(item) for item in config.get("依赖检查", {}).get("Chrome候选路径", [])]
    checked = []
    for raw in paths:
        path = Path(raw)
        checked.append({"路径": str(path), "存在": path.exists()})
        if path.exists():
            return {"可用": True, "路径": str(path), "候选检查": checked}
    return {"可用": False, "路径": "", "候选检查": checked}


def archive_config(config: dict[str, Any], task_id: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = ARCHIVE_DIR / f"视频生成桥梁配置_before_real_render_{task_id}_{timestamp}.json"
    write_json(path, config)
    return path


def set_real_render_enabled(config: dict[str, Any], task_id: str) -> str:
    backup = archive_config(config, task_id)
    config.setdefault("生成桥梁", {})["启用真实渲染"] = True
    config.setdefault("安全约束", [])
    notice = "真实渲染已通过最终启用门禁后打开；如需暂停，请将生成桥梁.启用真实渲染改回 false。"
    if notice not in config["安全约束"]:
        config["安全约束"].append(notice)
    write_json(CONFIG_PATH, config)
    return str(backup)


def build_markdown(report: dict[str, Any]) -> str:
    blockers = report.get("阻断项", [])
    warnings = report.get("提醒项", [])
    blocker_text = "\n".join(f"- {item}" for item in blockers) if blockers else "- 无"
    warning_text = "\n".join(f"- {item}" for item in warnings) if warnings else "- 无"
    return "\n".join([
        "# 轮次012 最终真实渲染启用门禁报告",
        "",
        f"- 生成时间：{report.get('生成时间')}",
        f"- 任务ID：{report.get('任务ID')}",
        f"- 总体状态：{report.get('总体状态')}",
        f"- 配置是否已启用真实渲染：{report.get('配置已启用真实渲染')}",
        f"- 配置备份：{report.get('配置备份') or '未写入'}",
        "",
        "## 阻断项",
        "",
        blocker_text,
        "",
        "## 提醒项",
        "",
        warning_text,
        "",
        "## 安全结论",
        "",
        "本门禁只在全部条件通过后打开真实渲染配置开关；不会调用 MoneyPrinterTurbo，不会生成媒体，不会触发发布。",
        "",
    ])


def save_report(report: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    markdown = build_markdown(report)
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, markdown)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(ARCHIVE_DIR / f"最终真实渲染启用门禁_{report.get('任务ID', 'UNKNOWN')}_{timestamp}.json", report)
    write_text(ARCHIVE_DIR / f"最终真实渲染启用门禁_{report.get('任务ID', 'UNKNOWN')}_{timestamp}.md", markdown)


def run_gate(task_id: str, confirm_real_render: bool) -> dict[str, Any]:
    config = read_json(CONFIG_PATH)
    task = read_json(TASK_PATH)
    release_row = find_release_row(task_id)
    moneyprinter = check_moneyprinter(config)
    imagemagick = check_imagemagick(config)
    chrome = check_chrome(config)
    blockers: list[str] = []
    warnings: list[str] = []

    if not config:
        blockers.append(f"未找到视频生成桥梁配置：{CONFIG_PATH}")
    if str(task.get("任务ID", "")) != task_id:
        blockers.append(f"当前最新任务不是 {task_id}")
    if task.get("状态") != "生成放行":
        blockers.append(f"任务状态不是“生成放行”：{task.get('状态', '未知')}")
    if task.get("生成控制", {}).get("人工复核状态") != "复核通过-生成放行":
        blockers.append(f"人工复核状态不是“复核通过-生成放行”：{task.get('生成控制', {}).get('人工复核状态', '未知')}")
    if task.get("生成控制", {}).get("允许自动发布") is not False:
        blockers.append("任务单允许自动发布不是 false，需先恢复安全默认值")
    if not release_row:
        blockers.append(f"未在视频生成放行清单中找到任务：{task_id}")
    elif release_row.get("放行状态") != "放行":
        blockers.append(f"生成放行状态不是“放行”：{release_row.get('放行状态')}")
    if not confirm_real_render:
        blockers.append("缺少确认口令：我确认启用真实渲染")
    if not moneyprinter.get("可用"):
        blockers.append("MoneyPrinterTurbo 本地目录或启动入口不可识别")
    if not chrome.get("可用"):
        blockers.append("Chrome 未通过检查")
    if not imagemagick.get("可用"):
        warnings.append("ImageMagick 未通过检查；真实渲染字幕或图片处理可能失败")

    backup_path = ""
    passed = not blockers
    if passed:
        backup_path = set_real_render_enabled(config, task_id)

    refreshed = read_json(CONFIG_PATH)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": task_id,
        "总体状态": "pass" if passed else "blocked",
        "配置已启用真实渲染": bool(refreshed.get("生成桥梁", {}).get("启用真实渲染", False)),
        "确认真实渲染": confirm_real_render,
        "配置备份": backup_path,
        "任务状态": task.get("状态", ""),
        "人工复核状态": task.get("生成控制", {}).get("人工复核状态", ""),
        "生成放行清单行": release_row,
        "MoneyPrinterTurbo检查": moneyprinter,
        "ImageMagick检查": imagemagick,
        "Chrome检查": chrome,
        "阻断项": blockers,
        "提醒项": warnings,
        "安全边界": {
            "调用MoneyPrinterTurbo": False,
            "生成媒体": False,
            "触发发布": False,
            "企业微信真实外发": False,
        },
    }
    save_report(report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="轮次012真实渲染启用前最终门禁")
    parser.add_argument("--task-id", required=True, help="任务ID，例如 VF-20260508-005")
    parser.add_argument("--confirm-real-render", action="store_true", help="确认启用真实渲染配置开关")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_gate(args.task_id, args.confirm_real_render)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("总体状态") == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
