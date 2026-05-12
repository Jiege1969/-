# -*- coding: utf-8 -*-
"""
名称：prepare_render_bridge_environment.py
作用：生成轮次012真实渲染前置环境修复清单。
触发方式：python prepare_render_bridge_environment.py
安全边界：只读取本地配置和依赖状态，只生成建议清单；不启用真实渲染，不调用 MoneyPrinterTurbo，不联网下载。
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
OUTPUT_DIR = ROUND_DIR / "测试与审核" / "视频生成环境修复清单"
ARCHIVE_DIR = OUTPUT_DIR / "archive"
LATEST_JSON = OUTPUT_DIR / "视频生成环境修复清单_最新.json"
LATEST_MD = OUTPUT_DIR / "视频生成环境修复清单_最新.md"
SUGGESTED_CONFIG_PATH = OUTPUT_DIR / "视频生成桥梁配置_建议更新.json"


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


def path_from_config(value: str) -> Path:
    if not value:
        return Path()
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def is_moneyprinter_root(path: Path) -> bool:
    return (
        path.exists()
        and (
            (path / "start.bat").exists()
            or (path / "app" / "main.py").exists()
            or (path / "webui" / "Main.py").exists()
        )
    )


def inspect_moneyprinter_candidates(config: dict[str, Any]) -> dict[str, Any]:
    bridge = config.get("生成桥梁", {})
    candidates: list[Path] = []
    configured_root = str(bridge.get("根目录", "")).strip()
    if configured_root:
        candidates.append(path_from_config(configured_root))
    for item in bridge.get("候选根目录", []):
        candidates.append(path_from_config(str(item)))

    extra_search_roots = [
        ROOT / "06临时",
        ROOT.parent,
        Path.cwd(),
    ]
    for search_root in extra_search_roots:
        if not search_root.exists():
            continue
        for name in ["MoneyPrinterTurbo", "moneyprinterturbo", "MoneyPrinterTurbo-main"]:
            candidates.append(search_root / name)

    seen: set[str] = set()
    checked: list[dict[str, Any]] = []
    found = ""
    for candidate in candidates:
        if not str(candidate):
            continue
        normalized = str(candidate.resolve()) if candidate.exists() else str(candidate)
        if normalized in seen:
            continue
        seen.add(normalized)
        item = {
            "路径": str(candidate),
            "存在": candidate.exists(),
            "start.bat": (candidate / "start.bat").exists(),
            "app/main.py": (candidate / "app" / "main.py").exists(),
            "webui/Main.py": (candidate / "webui" / "Main.py").exists(),
            "可识别": is_moneyprinter_root(candidate),
        }
        checked.append(item)
        if item["可识别"] and not found:
            found = str(candidate)
    return {"已找到": bool(found), "推荐根目录": found, "候选检查": checked}


def inspect_imagemagick(config: dict[str, Any]) -> dict[str, Any]:
    command = str(config.get("依赖检查", {}).get("ImageMagick命令", "magick"))
    which_path = shutil.which(command) or ""
    common_matches: list[str] = []
    for base in [Path("C:/Program Files"), Path("C:/Program Files (x86)")]:
        if not base.exists():
            continue
        common_matches.extend(str(path) for path in base.glob("ImageMagick*/magick.exe"))

    result: dict[str, Any] = {
        "配置命令": command,
        "PATH可识别路径": which_path,
        "常见安装路径候选": common_matches,
        "可用": False,
        "版本摘要": "",
    }
    executable = which_path or (common_matches[0] if common_matches else "")
    if executable:
        try:
            completed = subprocess.run(
                [executable, "-version"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
            result["returncode"] = completed.returncode
            result["版本摘要"] = (completed.stdout or completed.stderr)[:500]
            result["可用"] = completed.returncode == 0
            result["建议命令"] = executable
        except Exception as exc:  # noqa: BLE001
            result["错误"] = str(exc)
    return result


def build_suggested_config(config: dict[str, Any], moneyprinter: dict[str, Any], imagemagick: dict[str, Any]) -> dict[str, Any]:
    suggested = json.loads(json.dumps(config, ensure_ascii=False))
    bridge = suggested.setdefault("生成桥梁", {})
    dependency = suggested.setdefault("依赖检查", {})
    if moneyprinter.get("推荐根目录"):
        bridge["根目录"] = moneyprinter["推荐根目录"]
    if imagemagick.get("建议命令"):
        dependency["ImageMagick命令"] = imagemagick["建议命令"]
    # 安全规则：这里只生成建议配置，绝不自动打开真实渲染开关。
    bridge["启用真实渲染"] = False
    return suggested


def build_steps(moneyprinter: dict[str, Any], imagemagick: dict[str, Any]) -> list[str]:
    steps: list[str] = []
    if not moneyprinter.get("已找到"):
        steps.append("将 MoneyPrinterTurbo Windows 一键启动包解压到不含中文和空格的目录，建议同步放一份到 `02视频制作系统\\06临时\\MoneyPrinterTurbo`。")
        steps.append("解压后确认目录内存在 `start.bat`，或存在 `app\\main.py` / `webui\\Main.py`。")
        steps.append("把真实根目录写入 `01配置\\视频生成桥梁配置.json` 的 `生成桥梁.根目录`。")
    else:
        steps.append(f"MoneyPrinterTurbo 已找到，建议根目录：`{moneyprinter.get('推荐根目录')}`。")

    if not imagemagick.get("可用"):
        if imagemagick.get("常见安装路径候选"):
            steps.append("ImageMagick 似乎已安装但未加入 PATH，可把 `依赖检查.ImageMagick命令` 改为检测到的 `magick.exe` 绝对路径。")
        else:
            steps.append("安装 ImageMagick，并确保 `magick -version` 在 PowerShell 中可正常返回。")
        steps.append("安装 ImageMagick 时建议勾选 legacy utilities / Add application directory to PATH 相关选项。")
    else:
        steps.append("ImageMagick 已可用。")

    steps.append("完成以上修复后，在企业微信发送：`生成预检 VF-YYYYMMDD-001`。")
    steps.append("即使预检通过，真实渲染仍需人工复核、生成放行和最终真实渲染启用门禁。")
    return steps


def build_markdown(report: dict[str, Any]) -> str:
    steps = "\n".join(f"{index}. {item}" for index, item in enumerate(report.get("建议步骤", []), start=1))
    moneyprinter_rows = "\n".join(
        f"| {item.get('路径')} | {item.get('存在')} | {item.get('可识别')} |"
        for item in report.get("MoneyPrinterTurbo检查", {}).get("候选检查", [])
    )
    return "\n".join([
        "# 轮次012 视频生成环境修复清单",
        "",
        f"- 生成时间：{report.get('生成时间')}",
        f"- 总体状态：{report.get('总体状态')}",
        f"- 建议配置：{SUGGESTED_CONFIG_PATH}",
        "",
        "## 建议步骤",
        "",
        steps,
        "",
        "## MoneyPrinterTurbo候选检查",
        "",
        "| 路径 | 存在 | 可识别 |",
        "| --- | --- | --- |",
        moneyprinter_rows or "| - | - | - |",
        "",
        "## ImageMagick检查",
        "",
        f"- 配置命令：{report.get('ImageMagick检查', {}).get('配置命令')}",
        f"- PATH可识别路径：{report.get('ImageMagick检查', {}).get('PATH可识别路径') or '未找到'}",
        f"- 建议命令：{report.get('ImageMagick检查', {}).get('建议命令', '无')}",
        "",
        "## 安全结论",
        "",
        "本清单只生成修复建议和建议配置，不启用真实渲染，不调用外部工具，不触发发布。",
        "",
    ])


def run_prepare() -> dict[str, Any]:
    config = read_json(CONFIG_PATH)
    moneyprinter = inspect_moneyprinter_candidates(config)
    imagemagick = inspect_imagemagick(config)
    steps = build_steps(moneyprinter, imagemagick)
    blockers = []
    if not moneyprinter.get("已找到"):
        blockers.append("MoneyPrinterTurbo根目录未识别")
    if not imagemagick.get("可用"):
        blockers.append("ImageMagick不可用")
    return {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "ready_for_precheck" if not blockers else "need_fix",
        "配置文件": str(CONFIG_PATH),
        "建议配置文件": str(SUGGESTED_CONFIG_PATH),
        "MoneyPrinterTurbo检查": moneyprinter,
        "ImageMagick检查": imagemagick,
        "阻断项": blockers,
        "建议步骤": steps,
        "安全边界": {
            "启用真实渲染": False,
            "调用MoneyPrinterTurbo": False,
            "触发发布": False,
            "企业微信真实外发": False,
        },
    }


def save_report(report: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    config = read_json(CONFIG_PATH)
    suggested = build_suggested_config(config, report["MoneyPrinterTurbo检查"], report["ImageMagick检查"])
    write_json(SUGGESTED_CONFIG_PATH, suggested)
    markdown = build_markdown(report)
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, markdown)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(ARCHIVE_DIR / f"视频生成环境修复清单_{timestamp}.json", report)
    write_text(ARCHIVE_DIR / f"视频生成环境修复清单_{timestamp}.md", markdown)


def main() -> int:
    report = run_prepare()
    save_report(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("总体状态") == "ready_for_precheck" else 2


if __name__ == "__main__":
    raise SystemExit(main())
