# -*- coding: utf-8 -*-
"""
名称：check_render_bridge.py
作用：检查轮次012视频生成桥梁是否具备真实渲染前置条件。
触发方式：python check_render_bridge.py [--task-id VF-YYYYMMDD-001]
安全边界：只做本地配置、依赖、放行清单检查，不调用 MoneyPrinterTurbo，不读取外部素材，不生成媒体。
"""

from __future__ import annotations

import argparse
import json
import shutil
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
CONFIG_PATH = ROOT / "01配置" / "视频生成桥梁配置.json"
RELEASE_PATH = ROUND_DIR / "放行清单" / "视频生成放行清单_最新.md"
OUTPUT_DIR = ROUND_DIR / "测试与审核" / "视频生成桥梁预检"
ARCHIVE_DIR = OUTPUT_DIR / "archive"
LATEST_JSON = OUTPUT_DIR / "视频生成桥梁预检_最新.json"
LATEST_MD = OUTPUT_DIR / "视频生成桥梁预检_最新.md"


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


def find_release_rows(task_id: str) -> list[dict[str, str]]:
    rows = parse_markdown_table(read_text(RELEASE_PATH))
    if task_id:
        return [row for row in rows if row.get("任务ID") == task_id]
    return rows


def path_from_config(value: str) -> Path:
    if not value:
        return Path()
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def find_moneyprinter_root(config: dict[str, Any]) -> dict[str, Any]:
    bridge = config.get("生成桥梁", {})
    candidates: list[Path] = []
    configured_root = str(bridge.get("根目录", "")).strip()
    if configured_root:
        candidates.append(path_from_config(configured_root))
    for item in bridge.get("候选根目录", []):
        candidates.append(path_from_config(str(item)))

    checked: list[dict[str, Any]] = []
    for candidate in candidates:
        if not str(candidate):
            continue
        start_bat = candidate / "start.bat"
        app_file = candidate / "app" / "main.py"
        webui_file = candidate / "webui" / "Main.py"
        exists = candidate.exists()
        entry_candidates = [
            {
                "入口类型": "Windows批处理",
                "入口路径": str(start_bat),
                "启动方式": f"cmd /c \"{start_bat}\"",
                "存在": start_bat.exists(),
            },
            {
                "入口类型": "Python应用入口",
                "入口路径": str(app_file),
                "启动方式": f"python \"{app_file}\"",
                "存在": app_file.exists(),
            },
            {
                "入口类型": "WebUI入口",
                "入口路径": str(webui_file),
                "启动方式": f"python \"{webui_file}\"",
                "存在": webui_file.exists(),
            },
        ]
        usable = exists and any(item["存在"] for item in entry_candidates)
        check_item = {
            "路径": str(candidate),
            "存在": exists,
            "入口候选": entry_candidates,
            "依赖条件": [
                "需要先人工确认 MoneyPrinterTurbo 根目录和启动入口。",
                "需要人工确认 Python/虚拟环境、项目依赖、模型或素材配置。",
                "需要生成放行、真实渲染放行和最终启用门禁全部独立通过。",
            ],
            "可识别": usable,
            "识别说明": "已识别可调用入口" if usable else ("目录存在但未识别入口" if exists else "目录不存在"),
        }
        checked.append(check_item)
        if usable:
            first_entry = next(item for item in entry_candidates if item["存在"])
            return {
                "可识别": True,
                "可用": True,
                "环境状态": "需人工配置",
                "根目录": str(candidate),
                "可调用入口路径": first_entry["入口路径"],
                "启动方式": first_entry["启动方式"],
                "依赖条件": check_item["依赖条件"],
                "候选检查": checked,
                "识别结论": "识别到入口，但本预检不启动、不调用，仍需人工配置和最终门禁。",
            }
    return {
        "可识别": False,
        "可用": False,
        "环境状态": "环境不可用",
        "根目录": "",
        "可调用入口路径": "",
        "启动方式": "",
        "依赖条件": [
            "未识别 MoneyPrinterTurbo 本地入口，不得伪造已接入。",
            "需人工提供正确根目录、启动入口和依赖安装方式。",
        ],
        "候选检查": checked,
        "识别结论": "未识别，不得伪造已接入",
    }


def check_imagemagick(command: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "命令": command,
        "检查方式": "只做 PATH 识别，不执行 ImageMagick 命令",
        "可识别": False,
        "可用": False,
        "环境状态": "环境不可用",
        "路径": shutil.which(command) or "",
        "版本": "",
        "错误": "",
        "缺失原因": "",
    }
    if not result["路径"]:
        result["错误"] = "未在 PATH 中找到 ImageMagick magick 命令"
        result["缺失原因"] = "PATH 中无可识别 magick 命令；本轮按红线要求未调用 ImageMagick。"
        return result
    result["可识别"] = True
    result["环境状态"] = "需人工配置"
    result["版本"] = "未执行版本命令；因本轮红线禁止调用 ImageMagick"
    result["错误"] = "命令路径存在，但未执行 magick -version，需人工确认版本和可用性。"
    return result


def check_chrome(paths: list[str]) -> dict[str, Any]:
    checked = []
    for raw in paths:
        path = Path(raw)
        checked.append({"路径": str(path), "存在": path.exists()})
        if path.exists():
            return {"可用": True, "路径": str(path), "候选检查": checked}
    return {"可用": False, "路径": "", "候选检查": checked}


def build_markdown(report: dict[str, Any]) -> str:
    blockers = report.get("阻断项", [])
    warnings = report.get("提醒项", [])
    blocker_text = "\n".join(f"- {item}" for item in blockers) if blockers else "- 无"
    warning_text = "\n".join(f"- {item}" for item in warnings) if warnings else "- 无"
    return "\n".join([
        "# 轮次012 视频生成桥梁预检报告",
        "",
        f"- 生成时间：{report.get('生成时间')}",
        f"- 任务ID过滤：{report.get('任务ID过滤') or '未指定'}",
        f"- 总体状态：{report.get('总体状态')}",
        f"- 环境状态：{report.get('环境状态')}",
        f"- 可进入真实渲染：{report.get('可进入真实渲染')}",
        f"- 真实渲染启用：{report.get('真实渲染启用')}",
        f"- MoneyPrinterTurbo根目录：{report.get('MoneyPrinterTurbo检查', {}).get('根目录') or '未找到'}",
        f"- MoneyPrinterTurbo入口：{report.get('MoneyPrinterTurbo检查', {}).get('可调用入口路径') or '未识别'}",
        f"- ImageMagick命令：{report.get('ImageMagick检查', {}).get('命令')}",
        f"- ImageMagick路径：{report.get('ImageMagick检查', {}).get('路径') or '未找到'}",
        f"- ImageMagick版本：{report.get('ImageMagick检查', {}).get('版本') or '未获取'}",
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
        "本预检只确认本地依赖和放行条件，不执行真实渲染。环境不可用或需人工配置时，必须保持阻断，不得伪造已接入或误判为可渲染。",
        "",
    ])


def derive_environment_status(
    moneyprinter_check: dict[str, Any],
    imagemagick_check: dict[str, Any],
    chrome_check: dict[str, Any],
    real_render_enabled: bool,
) -> tuple[str, list[str], bool]:
    required_actions: list[str] = []
    if not moneyprinter_check.get("可识别"):
        required_actions.append("需人工提供可识别的 MoneyPrinterTurbo 根目录和启动入口。")
    if imagemagick_check.get("环境状态") == "环境不可用":
        required_actions.append("需人工安装 ImageMagick 并让 magick 命令进入 PATH。")
    elif imagemagick_check.get("环境状态") == "需人工配置":
        required_actions.append("需人工执行 ImageMagick 版本与功能确认；本预检未调用 magick。")
    if not chrome_check.get("可用"):
        required_actions.append("需人工确认 Chrome 安装路径。")
    if not real_render_enabled:
        required_actions.append("真实渲染配置仍为 false；如未来启用需走最终启用门禁。")

    if not moneyprinter_check.get("可识别") or imagemagick_check.get("环境状态") == "环境不可用":
        return "环境不可用", required_actions, False
    if required_actions:
        return "需人工配置", required_actions, False
    return "环境可用", required_actions, True


def run_check(task_id: str = "") -> dict[str, Any]:
    config = read_json(CONFIG_PATH)
    bridge = config.get("生成桥梁", {})
    dependency = config.get("依赖检查", {})
    real_render_enabled = bool(bridge.get("启用真实渲染", False))
    moneyprinter_check = find_moneyprinter_root(config)
    imagemagick_check = check_imagemagick(str(dependency.get("ImageMagick命令", "magick")))
    chrome_check = check_chrome([str(item) for item in dependency.get("Chrome候选路径", [])])
    environment_status, required_actions, environment_ready = derive_environment_status(
        moneyprinter_check,
        imagemagick_check,
        chrome_check,
        real_render_enabled,
    )
    rows = find_release_rows(task_id)
    blockers: list[str] = []
    warnings: list[str] = []

    if not CONFIG_PATH.exists():
        blockers.append(f"缺少视频生成桥梁配置：{CONFIG_PATH}")
    if not RELEASE_PATH.exists():
        blockers.append(f"缺少视频生成放行清单：{RELEASE_PATH}")
    if not rows:
        blockers.append("未找到匹配的视频生成放行任务")
    for row in rows:
        if row.get("放行状态") != "放行":
            blockers.append(f"{row.get('任务ID', '未知任务')}：生成放行状态不是“放行”")
    if not moneyprinter_check.get("可用"):
        blockers.append("未找到可识别的 MoneyPrinterTurbo 本地目录或启动入口")
    if not imagemagick_check.get("可用"):
        blockers.append("ImageMagick 不可用或未完成人工版本确认；不得进入真实渲染")
    if not chrome_check.get("可用"):
        warnings.append("Chrome 未通过检查；依赖浏览器的流程可能失败")
    if not real_render_enabled:
        warnings.append("真实渲染当前关闭，这是默认安全状态")
    if required_actions:
        warnings.extend(required_actions)

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID过滤": task_id,
        "总体状态": "pass" if not blockers else "blocked",
        "环境状态": environment_status,
        "可进入真实渲染": bool(environment_ready and real_render_enabled and not blockers),
        "真实渲染启用": real_render_enabled,
        "MoneyPrinterTurbo检查": moneyprinter_check,
        "ImageMagick检查": imagemagick_check,
        "Chrome检查": chrome_check,
        "生成放行清单行": rows,
        "阻断项": blockers,
        "提醒项": warnings,
        "需人工配置": required_actions,
        "安全边界": {
            "执行渲染": False,
            "调用外部素材API": False,
            "触发发布": False,
            "企业微信真实外发": False
        }
    }
    return report


def save_report(report: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    markdown = build_markdown(report)
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, markdown)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(ARCHIVE_DIR / f"视频生成桥梁预检_{timestamp}.json", report)
    write_text(ARCHIVE_DIR / f"视频生成桥梁预检_{timestamp}.md", markdown)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="轮次012视频生成桥梁预检")
    parser.add_argument("--task-id", default="", help="仅检查指定任务ID")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_check(args.task_id)
    save_report(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("总体状态") == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
