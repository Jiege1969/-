# -*- coding: utf-8 -*-
"""
名称：apply_render_bridge_suggestion.py
作用：安全应用轮次012视频生成桥梁建议配置中的可验证路径。
触发方式：python apply_render_bridge_suggestion.py
安全边界：只更新 MoneyPrinterTurbo 根目录和 ImageMagick 命令等本地路径配置；强制保持真实渲染关闭，不调用 MoneyPrinterTurbo，不生成媒体。
"""

from __future__ import annotations

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
SUGGESTION_DIR = ROUND_DIR / "测试与审核" / "视频生成环境修复清单"
SUGGESTED_CONFIG_PATH = SUGGESTION_DIR / "视频生成桥梁配置_建议更新.json"
OUTPUT_DIR = ROUND_DIR / "测试与审核" / "视频生成桥梁配置应用"
ARCHIVE_DIR = OUTPUT_DIR / "archive"
LATEST_JSON = OUTPUT_DIR / "视频生成桥梁配置应用_最新.json"
LATEST_MD = OUTPUT_DIR / "视频生成桥梁配置应用_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def is_moneyprinter_root(raw_path: str) -> bool:
    if not raw_path:
        return False
    path = Path(raw_path)
    return (
        path.exists()
        and (
            (path / "start.bat").exists()
            or (path / "app" / "main.py").exists()
            or (path / "webui" / "Main.py").exists()
        )
    )


def check_imagemagick_command(command: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "命令": command,
        "可用": False,
        "解析路径": "",
        "returncode": None,
        "stdout": "",
        "stderr": "",
    }
    if not command:
        result["错误"] = "命令为空"
        return result
    resolved = shutil.which(command) or (command if Path(command).exists() else "")
    result["解析路径"] = resolved
    if not resolved:
        result["错误"] = "未找到 ImageMagick 命令"
        return result
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
        result["returncode"] = completed.returncode
        result["stdout"] = completed.stdout[:1000]
        result["stderr"] = completed.stderr[:1000]
        result["可用"] = completed.returncode == 0
    except Exception as exc:  # noqa: BLE001
        result["错误"] = str(exc)
    return result


def archive_current_config(config: dict[str, Any]) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = ARCHIVE_DIR / f"视频生成桥梁配置_before_apply_{timestamp}.json"
    write_json(archive_path, config)
    return archive_path


def build_markdown(report: dict[str, Any]) -> str:
    changes = report.get("已应用变更", [])
    blockers = report.get("阻断项", [])
    changes_text = "\n".join(f"- {item}" for item in changes) if changes else "- 无"
    blockers_text = "\n".join(f"- {item}" for item in blockers) if blockers else "- 无"
    return "\n".join([
        "# 轮次012 视频生成桥梁配置应用报告",
        "",
        f"- 生成时间：{report.get('生成时间')}",
        f"- 总体状态：{report.get('总体状态')}",
        f"- 原配置：{CONFIG_PATH}",
        f"- 建议配置：{SUGGESTED_CONFIG_PATH}",
        f"- 配置备份：{report.get('配置备份') or '未写入'}",
        f"- 真实渲染开关：{report.get('真实渲染开关')}",
        "",
        "## 已应用变更",
        "",
        changes_text,
        "",
        "## 阻断项",
        "",
        blockers_text,
        "",
        "## 安全结论",
        "",
        "本步骤只应用可验证的本地路径配置，并强制保持真实渲染关闭；不会调用 MoneyPrinterTurbo，不会生成媒体，不会触发发布。",
        "",
    ])


def save_report(report: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    markdown = build_markdown(report)
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, markdown)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(ARCHIVE_DIR / f"视频生成桥梁配置应用_{timestamp}.json", report)
    write_text(ARCHIVE_DIR / f"视频生成桥梁配置应用_{timestamp}.md", markdown)


def run_apply() -> dict[str, Any]:
    current = read_json(CONFIG_PATH)
    suggested = read_json(SUGGESTED_CONFIG_PATH)
    blockers: list[str] = []
    changes: list[str] = []
    checks: dict[str, Any] = {}

    if not current:
        blockers.append(f"原配置不存在或为空：{CONFIG_PATH}")
    if not suggested:
        blockers.append(f"建议配置不存在或为空：{SUGGESTED_CONFIG_PATH}")

    updated = json.loads(json.dumps(current, ensure_ascii=False)) if current else {}
    suggested_bridge = suggested.get("生成桥梁", {})
    suggested_dependency = suggested.get("依赖检查", {})
    backup_path = ""

    suggested_root = str(suggested_bridge.get("根目录", "")).strip()
    checks["MoneyPrinterTurbo根目录"] = {
        "建议值": suggested_root,
        "可用": is_moneyprinter_root(suggested_root),
    }
    if suggested_root:
        if checks["MoneyPrinterTurbo根目录"]["可用"]:
            old = str(updated.setdefault("生成桥梁", {}).get("根目录", ""))
            if old != suggested_root:
                updated["生成桥梁"]["根目录"] = suggested_root
                changes.append(f"生成桥梁.根目录：{old or '空'} -> {suggested_root}")
        else:
            blockers.append(f"建议 MoneyPrinterTurbo 根目录不可识别：{suggested_root}")

    suggested_imagemagick = str(suggested_dependency.get("ImageMagick命令", "")).strip()
    imagemagick_check = check_imagemagick_command(suggested_imagemagick)
    checks["ImageMagick命令"] = imagemagick_check
    if suggested_imagemagick:
        if imagemagick_check.get("可用"):
            old = str(updated.setdefault("依赖检查", {}).get("ImageMagick命令", ""))
            if old != suggested_imagemagick:
                updated["依赖检查"]["ImageMagick命令"] = suggested_imagemagick
                changes.append(f"依赖检查.ImageMagick命令：{old or '空'} -> {suggested_imagemagick}")
        elif suggested_imagemagick != str(current.get("依赖检查", {}).get("ImageMagick命令", "")):
            blockers.append(f"建议 ImageMagick 命令不可用：{suggested_imagemagick}")

    if updated:
        # 安全规则：应用建议配置时绝不打开真实渲染开关。
        updated.setdefault("生成桥梁", {})["启用真实渲染"] = False

    if changes and not blockers:
        backup_path = str(archive_current_config(current))
        write_json(CONFIG_PATH, updated)
    elif not changes and not blockers:
        blockers.append("建议配置中没有可应用的新变更")

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "applied" if changes and not blockers else "blocked",
        "原配置": str(CONFIG_PATH),
        "建议配置": str(SUGGESTED_CONFIG_PATH),
        "配置备份": backup_path,
        "已应用变更": changes,
        "检查结果": checks,
        "阻断项": blockers,
        "真实渲染开关": False,
        "安全边界": {
            "启用真实渲染": False,
            "调用MoneyPrinterTurbo": False,
            "生成媒体": False,
            "触发发布": False,
            "企业微信真实外发": False,
        },
    }
    save_report(report)
    return report


def main() -> int:
    report = run_apply()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("总体状态") == "applied" else 2


if __name__ == "__main__":
    raise SystemExit(main())
