# -*- coding: utf-8 -*-
"""
名称：生成视频真实渲染环境只读识别增强包.py
作用：只读识别真实渲染环境候选状态，记录 ImageMagick 命令名与 MoneyPrinterTurbo 入口文件存在性。
安全边界：只做路径与命令名识别；不执行 magick；不调用 MoneyPrinterTurbo；不渲染；不生成真实视频；不触发发布、n8n 或企业微信。
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\02视频制作系统")
PROJECT_ROOT = Path(r"D:\杰哥智能化系统")
OUTPUT_DIR = ROOT / "03数据" / "19真实渲染环境只读识别增强包"
LATEST_JSON = OUTPUT_DIR / "视频真实渲染环境只读识别增强包_最新.json"
LATEST_MD = OUTPUT_DIR / "视频真实渲染环境只读识别增强包_最新.md"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def path_record(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "是目录": path.is_dir() if path.exists() else False,
        "是文件": path.is_file() if path.exists() else False,
    }


def detect_magick_command() -> dict[str, Any]:
    found = shutil.which("magick")
    path_entries = [entry for entry in os.environ.get("PATH", "").split(os.pathsep) if entry]
    return {
        "命令名": "magick",
        "PATH命令名可找到": bool(found),
        "解析到的命令路径": found or "",
        "识别方式": "shutil.which，仅做 PATH 级命令名解析；未执行 magick 或 magick -version",
        "PATH条目数": len(path_entries),
    }


def money_printer_candidates() -> list[Path]:
    candidates = [
        PROJECT_ROOT / "MoneyPrinterTurbo",
        PROJECT_ROOT / "02杰哥扩展系统" / "02视频制作系统" / "MoneyPrinterTurbo",
        PROJECT_ROOT / "02杰哥扩展系统" / "02视频制作系统" / "05外部工具" / "MoneyPrinterTurbo",
        PROJECT_ROOT / "02杰哥扩展系统" / "02视频制作系统" / "06渲染工具" / "MoneyPrinterTurbo",
        Path(r"D:\MoneyPrinterTurbo"),
        Path(r"C:\MoneyPrinterTurbo"),
    ]
    seen: set[str] = set()
    unique: list[Path] = []
    for candidate in candidates:
        key = str(candidate).lower()
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def detect_money_printer() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    entry_names = ["start.bat", "app/main.py", "webui/Main.py"]
    for base in money_printer_candidates():
        entries = {
            name: {
                "路径": str(base / Path(name)),
                "存在": (base / Path(name)).exists(),
            }
            for name in entry_names
        }
        records.append(
            {
                "候选目录": str(base),
                "目录存在": base.exists() and base.is_dir(),
                "入口文件只读识别": entries,
                "含任一入口文件": any(item["存在"] for item in entries.values()),
                "是否调用入口": False,
            }
        )
    return records


def build_package() -> dict[str, Any]:
    candidate_paths = [
        ROOT,
        OUTPUT_DIR,
        ROOT / "02脚本",
        ROOT / "03数据",
        ROOT / "04日志",
        PROJECT_ROOT / "00杰哥系统总管",
        PROJECT_ROOT / "01杰哥智能系统",
        PROJECT_ROOT / "02杰哥扩展系统",
        PROJECT_ROOT / "03杰哥进化系统",
    ]
    return {
        "名称": "视频真实渲染环境只读识别增强包",
        "生成时间": now_text(),
        "阶段": "真实渲染环境只读识别",
        "候选路径存在性": [path_record(path) for path in candidate_paths],
        "ImageMagick命令名识别": detect_magick_command(),
        "MoneyPrinterTurbo候选目录识别": detect_money_printer(),
        "当前真实动作": {
            "执行magick": False,
            "执行magick_version": False,
            "调用MoneyPrinterTurbo": False,
            "真实渲染": False,
            "生成真实视频": False,
            "上传发布": False,
            "触发n8n": False,
            "修改企业微信公共配置": False,
            "修改总管面板": False,
            "修改一键接续包": False,
            "重载服务": False,
        },
        "安全结论": "本包仅完成真实渲染环境只读识别，不具备进入真实渲染的放行能力。",
    }


def build_markdown(package: dict[str, Any]) -> str:
    magick = package["ImageMagick命令名识别"]
    money = package["MoneyPrinterTurbo候选目录识别"]
    money_lines = [
        f"- {item['候选目录']}：目录存在={item['目录存在']}，含任一入口文件={item['含任一入口文件']}，是否调用入口={item['是否调用入口']}"
        for item in money
    ]
    return "\n".join(
        [
            "# 视频真实渲染环境只读识别增强包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- magick PATH 命令名可找到：{magick['PATH命令名可找到']}",
            f"- magick 解析路径：{magick['解析到的命令路径'] or '未找到'}",
            "- magick 执行：False",
            "- MoneyPrinterTurbo 入口调用：False",
            "- 真实渲染：False",
            "",
            "## MoneyPrinterTurbo 候选目录",
            "",
            *money_lines,
            "",
            "## 结论",
            "",
            package["安全结论"],
        ]
    )


def main() -> int:
    package = build_package()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stamped_json = OUTPUT_DIR / f"视频真实渲染环境只读识别增强包_{timestamp}.json"
    write_json(stamped_json, package)
    write_json(LATEST_JSON, package)
    write_text(LATEST_MD, build_markdown(package))
    print(json.dumps({"输出": str(LATEST_JSON), "真实渲染": False, "执行magick": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
