# -*- coding: utf-8 -*-
"""
生成视频真实渲染环境候选路径矩阵与安装缺口清单包。

红线：
- 不调用 MoneyPrinterTurbo。
- 不调用 ImageMagick，不执行 magick，也不执行 magick -version。
- 不真实渲染，不上传发布，不接 n8n，不修改公共配置，不重载服务。

本脚本只读取 PATH、候选目录存在性、候选入口文件存在性，并写入候选路径/缺口清单产物。
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
SCRIPT_DIR = ROOT / "02脚本"
DATA_DIR = ROOT / "03数据" / "真实渲染环境候选路径矩阵与安装缺口清单"

PACKAGE_LATEST_JSON = DATA_DIR / "视频真实渲染环境候选路径矩阵与安装缺口清单_最新.json"
PACKAGE_LATEST_MD = DATA_DIR / "视频真实渲染环境候选路径矩阵与安装缺口清单_最新.md"
GAP_LATEST_JSON = DATA_DIR / "视频真实渲染环境安装缺口清单_最新.json"
GAP_LATEST_MD = DATA_DIR / "视频真实渲染环境安装缺口清单_最新.md"
MANUAL_LATEST_JSON = DATA_DIR / "视频真实渲染环境下一步人工确认清单_最新.json"
MANUAL_LATEST_MD = DATA_DIR / "视频真实渲染环境下一步人工确认清单_最新.md"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        if not str(path):
            continue
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def env_path_entries() -> list[Path]:
    entries: list[Path] = []
    for item in os.environ.get("PATH", "").split(os.pathsep):
        item = item.strip().strip('"')
        if item:
            entries.append(Path(item))
    return unique_paths(entries)


def readonly_flags_cn() -> dict[str, bool]:
    return {
        "真实渲染": False,
        "生成真实视频": False,
        "上传发布": False,
        "调用MoneyPrinterTurbo": False,
        "执行magick": False,
        "执行magick_version": False,
        "触发n8n": False,
        "修改企业微信公共配置": False,
        "修改总管面板": False,
        "修改一键接续包": False,
        "重载服务": False,
        "安装软件": False,
        "写入系统环境变量": False,
    }


def readonly_flags_ascii() -> dict[str, bool]:
    return {
        "real_render": False,
        "generate_real_video": False,
        "upload_publish": False,
        "call_money_printer_turbo": False,
        "execute_magick": False,
        "execute_magick_version": False,
        "trigger_n8n": False,
        "modify_wecom_public_config": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_pack": False,
        "reload_service": False,
        "install_software": False,
        "write_system_environment": False,
    }


def moneyprinter_candidates() -> list[Path]:
    env_names = ["MONEYPRINTERTURBO_HOME", "MONEY_PRINTER_TURBO_HOME", "MPT_HOME"]
    env_candidates = [Path(os.environ[name]) for name in env_names if os.environ.get(name)]
    path_candidates = [entry for entry in env_path_entries() if "moneyprinterturbo" in str(entry).lower()]
    static_candidates = [
        ROOT / "MoneyPrinterTurbo",
        ROOT / "02脚本" / "MoneyPrinterTurbo",
        ROOT / "01工具" / "MoneyPrinterTurbo",
        SYSTEM_ROOT / "MoneyPrinterTurbo",
        Path(r"D:\MoneyPrinterTurbo"),
        Path(r"C:\MoneyPrinterTurbo"),
    ]
    return unique_paths(env_candidates + path_candidates + static_candidates)


def imagemagick_candidates() -> list[Path]:
    env_names = ["IMAGEMAGICK_HOME", "MAGICK_HOME"]
    env_candidates = [Path(os.environ[name]) for name in env_names if os.environ.get(name)]
    path_candidates: list[Path] = []
    for entry in env_path_entries():
        text = str(entry).lower()
        if "imagemagick" in text or (entry / "magick.exe").exists():
            path_candidates.append(entry)

    program_files = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
    ]
    version_names = [
        "ImageMagick",
        "ImageMagick-7.1.2-Q16-HDRI",
        "ImageMagick-7.1.1-Q16-HDRI",
        "ImageMagick-7.1.0-Q16-HDRI",
        "ImageMagick-7.0.11-Q16-HDRI",
        "ImageMagick-6.9.13-Q16",
    ]
    static_candidates = [base / name for base in program_files for name in version_names]
    static_candidates.extend([Path(r"D:\ImageMagick"), ROOT / "ImageMagick", ROOT / "01工具" / "ImageMagick"])

    which_magick = shutil.which("magick")
    which_candidates = [Path(which_magick).parent] if which_magick else []
    return unique_paths(env_candidates + path_candidates + which_candidates + static_candidates)


def moneyprinter_row(path: Path) -> dict[str, Any]:
    entry_files = [
        "app.py",
        "main.py",
        "webui.py",
        "start.py",
        "requirements.txt",
        "pyproject.toml",
        "config.toml",
        "MoneyPrinterTurbo.py",
    ]
    checks = {name: (path / name).exists() for name in entry_files}
    return {
        "对象": "MoneyPrinterTurbo",
        "candidate_path": str(path),
        "来源": "环境变量/PATH/常见安装目录候选",
        "目录存在": path.exists() and path.is_dir(),
        "候选入口文件存在性": checks,
        "包含任一候选入口文件": any(checks.values()),
        "本轮是否调用": False,
        "本轮是否渲染": False,
        "阻断说明": "仅确认候选路径和入口文件存在性；未调用项目、未安装依赖、未执行真实渲染。",
    }


def imagemagick_row(path: Path) -> dict[str, Any]:
    exe_checks = {
        "magick.exe": (path / "magick.exe").exists(),
        "convert.exe": (path / "convert.exe").exists(),
    }
    return {
        "对象": "ImageMagick",
        "candidate_path": str(path),
        "来源": "环境变量/PATH/常见安装目录候选",
        "目录存在": path.exists() and path.is_dir(),
        "候选入口文件存在性": exe_checks,
        "包含magick.exe": exe_checks["magick.exe"],
        "PATH命令名可解析": bool(shutil.which("magick")) and Path(shutil.which("magick") or "").parent == path,
        "本轮是否执行magick": False,
        "本轮是否执行magick_version": False,
        "阻断说明": "仅确认 magick.exe 文件存在性；未执行 magick 或 magick -version，版本与可运行性未确认。",
    }


def build_matrix() -> dict[str, Any]:
    money_rows = [moneyprinter_row(path) for path in moneyprinter_candidates()]
    magick_rows = [imagemagick_row(path) for path in imagemagick_candidates()]
    return {
        "MoneyPrinterTurbo": money_rows,
        "ImageMagick": magick_rows,
    }


def build_gap_list(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    money_rows = matrix["MoneyPrinterTurbo"]
    magick_rows = matrix["ImageMagick"]
    money_dirs = [row for row in money_rows if row["目录存在"]]
    money_entries = [row for row in money_rows if row["包含任一候选入口文件"]]
    magick_dirs = [row for row in magick_rows if row["目录存在"]]
    magick_exes = [row for row in magick_rows if row["包含magick.exe"]]

    gaps: list[dict[str, Any]] = []
    gaps.append(
        {
            "对象": "MoneyPrinterTurbo",
            "状态": "blocked",
            "缺口": "未调用 MoneyPrinterTurbo，项目依赖、配置、素材链路和真实渲染入口未验证。",
            "只读发现": {
                "候选目录数量": len(money_rows),
                "存在目录数量": len(money_dirs),
                "包含候选入口文件目录数量": len(money_entries),
            },
            "下一步": "人工确认 MoneyPrinterTurbo 根目录、Python 环境、依赖安装状态、项目配置和真实渲染授权后，再由后续受控任务放行。",
        }
    )
    if not money_dirs:
        gaps.append(
            {
                "对象": "MoneyPrinterTurbo",
                "状态": "blocked",
                "缺口": "只读候选路径中未发现 MoneyPrinterTurbo 目录存在。",
                "下一步": "人工提供或安装 MoneyPrinterTurbo 的实际根目录；本任务不安装、不修改 PATH。",
            }
        )
    elif not money_entries:
        gaps.append(
            {
                "对象": "MoneyPrinterTurbo",
                "状态": "blocked",
                "缺口": "发现候选目录，但未发现 app.py/main.py/webui.py/start.py/requirements.txt 等候选入口或依赖清单。",
                "下一步": "人工确认该目录是否为 MoneyPrinterTurbo 根目录，或补充正确路径。",
            }
        )

    gaps.append(
        {
            "对象": "ImageMagick",
            "状态": "blocked",
            "缺口": "未执行 magick 或 magick -version，ImageMagick 版本、PATH 可运行性、MoviePy/Pillow 调用链未验证。",
            "只读发现": {
                "候选目录数量": len(magick_rows),
                "存在目录数量": len(magick_dirs),
                "包含magick.exe目录数量": len(magick_exes),
            },
            "下一步": "人工确认 ImageMagick 安装目录、magick.exe、PATH、策略文件和字体/编码支持后，再由后续受控任务放行。",
        }
    )
    if not magick_dirs:
        gaps.append(
            {
                "对象": "ImageMagick",
                "状态": "blocked",
                "缺口": "只读候选路径中未发现 ImageMagick 目录存在。",
                "下一步": "人工安装或提供 ImageMagick 目录；本任务不安装、不写系统环境变量。",
            }
        )
    elif not magick_exes:
        gaps.append(
            {
                "对象": "ImageMagick",
                "状态": "blocked",
                "缺口": "发现候选目录，但未发现 magick.exe。",
                "下一步": "人工确认 ImageMagick 安装完整性和 magick.exe 所在目录。",
            }
        )
    return gaps


def build_manual_checklist(matrix: dict[str, Any], gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "序号": 1,
            "对象": "MoneyPrinterTurbo",
            "人工确认项": "确认 MoneyPrinterTurbo 实际根目录和入口文件。",
            "完成条件": "目录、入口文件、依赖清单和项目配置由人工确认；后续任务才可调用。",
            "当前状态": "blocked",
        },
        {
            "序号": 2,
            "对象": "MoneyPrinterTurbo",
            "人工确认项": "确认 Python 环境、依赖安装、素材输入、输出目录和真实渲染授权。",
            "完成条件": "形成可追溯确认记录；本任务不做安装和渲染。",
            "当前状态": "blocked",
        },
        {
            "序号": 3,
            "对象": "ImageMagick",
            "人工确认项": "确认 ImageMagick 安装目录、magick.exe 和 PATH。",
            "完成条件": "人工确认后，后续受控任务才可执行 magick -version。",
            "当前状态": "blocked",
        },
        {
            "序号": 4,
            "对象": "发布链路",
            "人工确认项": "确认真实渲染、人工审核、发布授权、n8n/企业微信/总管面板接入边界。",
            "完成条件": "全部授权前，真实发布仍 blocked。",
            "当前状态": "blocked",
        },
        {
            "序号": 5,
            "对象": "验收红线",
            "人工确认项": "确认本包仅为候选路径矩阵与安装缺口清单，不伪装已接入。",
            "完成条件": "真实渲染仍 blocked，真实发布仍 blocked。",
            "当前状态": "blocked",
        },
    ]


def build_package() -> dict[str, Any]:
    matrix = build_matrix()
    gaps = build_gap_list(matrix)
    manual = build_manual_checklist(matrix, gaps)
    return {
        "名称": "视频真实渲染环境候选路径矩阵与安装缺口清单包",
        "generated_at": now_text(),
        "scope": {
            "data_dir": str(DATA_DIR),
            "script_dir": str(SCRIPT_DIR),
            "mode": "readonly_candidate_path_and_gap_inventory",
        },
        "当前阶段": "仅候选路径矩阵与安装缺口清单",
        "current_stage": "candidate_path_gap_inventory_only",
        "真实渲染状态": "blocked",
        "real_render_status": "blocked",
        "真实发布状态": "blocked",
        "real_publish_status": "blocked",
        "是否已接入真实渲染": False,
        "is_real_render_integrated": False,
        "是否已接入真实发布": False,
        "is_real_publish_integrated": False,
        "readonly_flags": readonly_flags_cn(),
        "readonly_flags_ascii": readonly_flags_ascii(),
        "候选路径矩阵": matrix,
        "candidate_path_matrix": matrix,
        "安装缺口清单": gaps,
        "installation_gap_list": gaps,
        "下一步人工确认清单": manual,
        "manual_confirmation_checklist": manual,
        "当前阻断原因": [
            "MoneyPrinterTurbo 未被调用，依赖、配置、素材、输出和真实渲染链路未验证。",
            "ImageMagick 未被调用，未执行 magick 或 magick -version，版本与 PATH 可运行性未验证。",
            "本任务只读识别候选路径和安装缺口，不安装软件、不写系统环境变量、不放行真实渲染。",
            "真实发布链路未接 n8n、未改企业微信公共配置、未改总管面板、未改一键接续包，真实发布仍 blocked。",
        ],
    }


def build_gap_document(package: dict[str, Any]) -> dict[str, Any]:
    return {
        "名称": "视频真实渲染环境安装缺口清单",
        "generated_at": package["generated_at"],
        "真实渲染状态": package["真实渲染状态"],
        "真实发布状态": package["真实发布状态"],
        "安装缺口清单": package["安装缺口清单"],
        "readonly_flags": package["readonly_flags"],
        "readonly_flags_ascii": package["readonly_flags_ascii"],
    }


def build_manual_document(package: dict[str, Any]) -> dict[str, Any]:
    return {
        "名称": "视频真实渲染环境下一步人工确认清单",
        "generated_at": package["generated_at"],
        "真实渲染状态": package["真实渲染状态"],
        "真实发布状态": package["真实发布状态"],
        "下一步人工确认清单": package["下一步人工确认清单"],
        "readonly_flags": package["readonly_flags"],
        "readonly_flags_ascii": package["readonly_flags_ascii"],
    }


def matrix_markdown(package: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染环境候选路径矩阵与安装缺口清单",
        "",
        f"- 生成时间：{package['generated_at']}",
        f"- 当前阶段：{package['当前阶段']}",
        f"- 真实渲染状态：{package['真实渲染状态']}",
        f"- 真实发布状态：{package['真实发布状态']}",
        "- 声明：当前仅候选路径/缺口清单，不得伪装已接入。",
        "",
        "## MoneyPrinterTurbo 候选路径",
        "",
    ]
    for row in package["候选路径矩阵"]["MoneyPrinterTurbo"]:
        lines.append(
            f"- {row['candidate_path']} | 目录存在={row['目录存在']} | 含入口={row['包含任一候选入口文件']} | 本轮调用=False"
        )
    lines.extend(["", "## ImageMagick 候选路径", ""])
    for row in package["候选路径矩阵"]["ImageMagick"]:
        lines.append(
            f"- {row['candidate_path']} | 目录存在={row['目录存在']} | 含magick.exe={row['包含magick.exe']} | 执行magick=False"
        )
    lines.extend(["", "## 安装缺口", ""])
    for gap in package["安装缺口清单"]:
        lines.append(f"- {gap['对象']}：{gap['缺口']}（{gap['状态']}）")
    lines.extend(["", "## 下一步人工确认", ""])
    for item in package["下一步人工确认清单"]:
        lines.append(f"- {item['序号']}. {item['对象']}：{item['人工确认项']}（{item['当前状态']}）")
    return "\n".join(lines) + "\n"


def simple_list_markdown(title: str, generated_at: str, items: list[dict[str, Any]], item_key: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- 生成时间：{generated_at}",
        "- 真实渲染状态：blocked",
        "- 真实发布状态：blocked",
        "- 声明：当前仅候选路径/缺口清单，不得伪装已接入。",
        "",
    ]
    for item in items:
        lines.append(f"- {item.get('对象', '未分类')}：{item.get(item_key, '')}（{item.get('状态', item.get('当前状态', 'blocked'))}）")
    return "\n".join(lines) + "\n"


def main() -> int:
    package = build_package()
    gaps_doc = build_gap_document(package)
    manual_doc = build_manual_document(package)
    stamp = stamp_text()

    package_stamped = DATA_DIR / f"视频真实渲染环境候选路径矩阵与安装缺口清单_{stamp}.json"
    gap_stamped = DATA_DIR / f"视频真实渲染环境安装缺口清单_{stamp}.json"
    manual_stamped = DATA_DIR / f"视频真实渲染环境下一步人工确认清单_{stamp}.json"

    write_json(PACKAGE_LATEST_JSON, package)
    write_json(package_stamped, package)
    write_text(PACKAGE_LATEST_MD, matrix_markdown(package))

    write_json(GAP_LATEST_JSON, gaps_doc)
    write_json(gap_stamped, gaps_doc)
    write_text(GAP_LATEST_MD, simple_list_markdown("视频真实渲染环境安装缺口清单", package["generated_at"], gaps_doc["安装缺口清单"], "缺口"))

    write_json(MANUAL_LATEST_JSON, manual_doc)
    write_json(manual_stamped, manual_doc)
    write_text(
        MANUAL_LATEST_MD,
        simple_list_markdown("视频真实渲染环境下一步人工确认清单", package["generated_at"], manual_doc["下一步人工确认清单"], "人工确认项"),
    )

    print(
        json.dumps(
            {
                "package": str(PACKAGE_LATEST_JSON),
                "gap_list": str(GAP_LATEST_JSON),
                "manual_checklist": str(MANUAL_LATEST_JSON),
                "real_render_status": "blocked",
                "real_publish_status": "blocked",
                "current_stage": "candidate_path_gap_inventory_only",
                "called_money_printer_turbo": False,
                "executed_magick": False,
                "executed_magick_version": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
