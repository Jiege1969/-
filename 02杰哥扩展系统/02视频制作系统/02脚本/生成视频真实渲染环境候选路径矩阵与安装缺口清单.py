# -*- coding: utf-8 -*-
"""
生成视频真实渲染环境候选路径矩阵与安装缺口清单。

只读边界：
- 不调用 MoneyPrinterTurbo。
- 不执行 magick，也不执行 magick -version。
- 仅检查候选目录、入口文件存在性，并用 shutil.which("magick") 做命令名解析。
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
DATA_DIR = ROOT / "03数据" / "20真实渲染环境候选路径矩阵与安装缺口清单"

PACKAGE_LATEST_JSON = DATA_DIR / "视频真实渲染环境候选路径矩阵与安装缺口清单_最新.json"
MATRIX_LATEST_MD = DATA_DIR / "视频真实渲染环境候选路径矩阵_最新.md"
GAP_LATEST_JSON = DATA_DIR / "视频真实渲染环境安装缺口清单_最新.json"
GAP_LATEST_MD = DATA_DIR / "视频真实渲染环境安装缺口清单_最新.md"
CARD_LATEST_JSON = DATA_DIR / "视频真实渲染环境下一步人工安装配置核对卡_最新.json"
CARD_LATEST_MD = DATA_DIR / "视频真实渲染环境下一步人工安装配置核对卡_最新.md"

MONEY_PRINTER_ENTRY_FILES = ["start.bat", "app/main.py", "webui/Main.py"]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def timestamp_text() -> str:
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
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def readonly_flags() -> dict[str, bool]:
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
    }


def money_printer_candidate_dirs() -> list[Path]:
    return unique_paths(
        [
            SYSTEM_ROOT / "MoneyPrinterTurbo",
            ROOT / "MoneyPrinterTurbo",
            ROOT / "05外部工具" / "MoneyPrinterTurbo",
            ROOT / "06渲染工具" / "MoneyPrinterTurbo",
            SYSTEM_ROOT / "02杰哥扩展系统" / "MoneyPrinterTurbo",
            Path(r"D:\MoneyPrinterTurbo"),
            Path(r"C:\MoneyPrinterTurbo"),
            Path.home() / "MoneyPrinterTurbo",
        ]
    )


def image_magick_candidate_dirs() -> list[Path]:
    found = shutil.which("magick")
    paths: list[Path] = []
    if found:
        paths.append(Path(found).parent)

    program_roots = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
        Path(r"C:\ImageMagick"),
        Path(r"D:\ImageMagick"),
        ROOT / "05外部工具" / "ImageMagick",
        ROOT / "06渲染工具" / "ImageMagick",
    ]
    for root in program_roots:
        paths.append(root)
        if root.exists() and root.is_dir() and root.name.lower() in {"program files", "program files (x86)"}:
            paths.extend(sorted(root.glob("ImageMagick*")))
    return unique_paths(paths)


def money_printer_matrix() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, base in enumerate(money_printer_candidate_dirs(), start=1):
        entries: list[dict[str, Any]] = []
        for relative in MONEY_PRINTER_ENTRY_FILES:
            path = base / Path(relative)
            entries.append(
                {
                    "relative_path": relative,
                    "候选入口文件": relative,
                    "absolute_path": str(path),
                    "存在": path.exists(),
                    "是文件": path.is_file() if path.exists() else False,
                }
            )
        exists = base.exists()
        has_any_entry = any(item["存在"] for item in entries)
        missing_entries = [item["候选入口文件"] for item in entries if not item["存在"]]
        rows.append(
            {
                "序号": index,
                "工具": "MoneyPrinterTurbo",
                "候选目录": str(base),
                "目录存在": exists and base.is_dir(),
                "入口文件检查": entries,
                "包含任一入口文件": has_any_entry,
                "缺失入口文件": missing_entries,
                "只读识别方式": "Path.exists/Path.is_file，仅检查 start.bat、app/main.py、webui/Main.py 是否存在",
                "调用MoneyPrinterTurbo": False,
                "不得进入真实渲染原因": build_money_printer_blockers(exists and base.is_dir(), has_any_entry),
            }
        )
    return rows


def image_magick_matrix() -> list[dict[str, Any]]:
    found = shutil.which("magick")
    rows: list[dict[str, Any]] = []
    for index, base in enumerate(image_magick_candidate_dirs(), start=1):
        exe_path = base / "magick.exe"
        rows.append(
            {
                "序号": index,
                "工具": "ImageMagick",
                "候选目录": str(base),
                "目录存在": base.exists() and base.is_dir(),
                "magick.exe候选路径": str(exe_path),
                "包含magick.exe": exe_path.exists() and exe_path.is_file(),
                "shutil.which_magick_path": found or "",
                "PATH命令名可解析": bool(found),
                "只读识别方式": "shutil.which('magick') 与候选目录文件存在性检查；未执行 magick 或 magick -version",
                "执行magick": False,
                "执行magick_version": False,
                "不得进入真实渲染原因": build_image_magick_blockers(bool(found), exe_path.exists() and exe_path.is_file()),
            }
        )
    return rows


def build_money_printer_blockers(dir_exists: bool, has_entry: bool) -> list[str]:
    blockers = [
        "本轮任务仅做候选路径矩阵与安装缺口清单，不包含真实渲染放行授权",
        "未调用 MoneyPrinterTurbo，无法确认工程运行状态、依赖状态或渲染链路可用性",
    ]
    if not dir_exists:
        blockers.append("候选目录不存在，需人工确认 MoneyPrinterTurbo 安装位置")
    if dir_exists and not has_entry:
        blockers.append("候选目录存在但未识别 start.bat、app/main.py、webui/Main.py 任一入口文件")
    return blockers


def build_image_magick_blockers(which_found: bool, exe_exists: bool) -> list[str]:
    blockers = [
        "本轮任务仅做候选路径矩阵与安装缺口清单，不包含真实渲染放行授权",
        "未执行 magick -version，无法确认 ImageMagick 真实版本、策略文件或运行可用性",
    ]
    if not which_found:
        blockers.append("PATH 中未解析到 magick 命令名，需人工安装 ImageMagick 或配置 PATH")
    if not exe_exists:
        blockers.append("该候选目录未识别到 magick.exe 文件")
    return blockers


def build_gap_list(money_rows: list[dict[str, Any]], magick_rows: list[dict[str, Any]]) -> dict[str, Any]:
    money_dir_exists = any(row["目录存在"] for row in money_rows)
    money_has_entry = any(row["包含任一入口文件"] for row in money_rows)
    magick_which_found = any(row["PATH命令名可解析"] for row in magick_rows)
    magick_exe_found = any(row["包含magick.exe"] for row in magick_rows)

    gaps: list[dict[str, Any]] = []
    if not money_dir_exists:
        gaps.append(
            {
                "对象": "MoneyPrinterTurbo",
                "缺口": "未发现候选安装目录存在",
                "人工处理": "确认安装目录，并将目录放入候选路径或后续受控配置",
                "自动动作": "无",
            }
        )
    if not money_has_entry:
        gaps.append(
            {
                "对象": "MoneyPrinterTurbo",
                "缺口": "未发现 start.bat、app/main.py、webui/Main.py 任一入口文件",
                "人工处理": "确认 MoneyPrinterTurbo 工程是否完整，入口文件位置是否符合预期",
                "自动动作": "无",
            }
        )
    if not magick_which_found:
        gaps.append(
            {
                "对象": "ImageMagick",
                "缺口": "shutil.which('magick') 未解析到命令名",
                "人工处理": "安装 ImageMagick 或将安装目录加入 PATH；由人工另行执行版本核对",
                "自动动作": "无",
            }
        )
    if not magick_exe_found:
        gaps.append(
            {
                "对象": "ImageMagick",
                "缺口": "候选目录未识别到 magick.exe",
                "人工处理": "确认 ImageMagick 安装目录，补充受控候选路径",
                "自动动作": "无",
            }
        )

    gaps.append(
        {
            "对象": "真实渲染放行链",
            "缺口": "本包没有真实渲染授权、素材授权、人审回执、发布放行的全链验收",
            "人工处理": "如需真实渲染，必须由总管另行下发明确放行任务",
            "自动动作": "无",
        }
    )

    return {
        "名称": "视频真实渲染环境安装缺口清单",
        "生成时间": now_text(),
        "error_count": 0,
        "缺口数量": len(gaps),
        "缺口清单": gaps,
        "可进入真实渲染": False,
        "readonly_flags": readonly_flags(),
        "readonly_flags_ascii": readonly_flags_ascii(),
    }


def build_manual_card(gap_list: dict[str, Any]) -> dict[str, Any]:
    return {
        "名称": "视频真实渲染环境下一步人工安装配置核对卡",
        "生成时间": now_text(),
        "用途": "供人工在安全窗口核对安装路径、命令 PATH 与放行材料；本卡不替代真实渲染放行",
        "核对项": [
            "人工确认 MoneyPrinterTurbo 实际安装目录，并确认 start.bat、app/main.py、webui/Main.py 中的有效入口",
            "人工确认 ImageMagick 安装目录是否包含 magick.exe",
            "人工确认 PATH 中 magick 命令名是否可解析；版本核对只能在另行授权窗口手工执行",
            "人工补齐素材授权、人审回执、任务单、发布放行链和真实渲染前最终确认记录",
            "总管未另行下发明确放行任务前，不得触发真实渲染、上传发布、n8n、企业微信公共配置或服务重载",
        ],
        "来自缺口数量": gap_list["缺口数量"],
        "可进入真实渲染": False,
        "readonly_flags": readonly_flags(),
        "readonly_flags_ascii": readonly_flags_ascii(),
    }


def build_package() -> dict[str, Any]:
    money_rows = money_printer_matrix()
    magick_rows = image_magick_matrix()
    gap_list = build_gap_list(money_rows, magick_rows)
    manual_card = build_manual_card(gap_list)
    return {
        "名称": "视频真实渲染环境候选路径矩阵与安装缺口清单包",
        "生成时间": now_text(),
        "阶段": "候选路径矩阵与安装缺口只读结构化",
        "error_count": 0,
        "可进入真实渲染": False,
        "can_enter_real_render": False,
        "候选路径矩阵": {
            "MoneyPrinterTurbo": money_rows,
            "ImageMagick": magick_rows,
        },
        "安装缺口清单": gap_list,
        "下一步人工安装配置核对卡": manual_card,
        "readonly_flags": readonly_flags(),
        "readonly_flags_ascii": readonly_flags_ascii(),
        "安全边界": [
            "不真实渲染",
            "不发布",
            "不接 n8n",
            "不改企业微信公共配置",
            "不改总管面板",
            "不改一键接续包",
            "不重载服务",
            "不调用 MoneyPrinterTurbo",
            "不执行 magick",
            "不执行 magick -version",
        ],
    }


def build_matrix_markdown(package: dict[str, Any]) -> str:
    money_lines = [
        (
            f"| {row['序号']} | {row['候选目录']} | {row['目录存在']} | "
            f"{row['包含任一入口文件']} | {'；'.join(row['缺失入口文件']) or '无'} |"
        )
        for row in package["候选路径矩阵"]["MoneyPrinterTurbo"]
    ]
    magick_lines = [
        (
            f"| {row['序号']} | {row['候选目录']} | {row['目录存在']} | "
            f"{row['包含magick.exe']} | {row['PATH命令名可解析']} | {row['shutil.which_magick_path'] or '未解析'} |"
        )
        for row in package["候选路径矩阵"]["ImageMagick"]
    ]
    return "\n".join(
        [
            "# 视频真实渲染环境候选路径矩阵",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 可进入真实渲染：{package['可进入真实渲染']}",
            "- 执行 magick：False",
            "- 执行 magick -version：False",
            "- 调用 MoneyPrinterTurbo：False",
            "",
            "## MoneyPrinterTurbo",
            "",
            "| 序号 | 候选目录 | 目录存在 | 包含任一入口文件 | 缺失入口文件 |",
            "| --- | --- | --- | --- | --- |",
            *money_lines,
            "",
            "## ImageMagick",
            "",
            "| 序号 | 候选目录 | 目录存在 | 包含 magick.exe | PATH 命令名可解析 | which 结果 |",
            "| --- | --- | --- | --- | --- | --- |",
            *magick_lines,
        ]
    )


def build_gap_markdown(gap_list: dict[str, Any]) -> str:
    gap_lines = [
        f"- 【{item['对象']}】{item['缺口']}；人工处理：{item['人工处理']}；自动动作：{item['自动动作']}"
        for item in gap_list["缺口清单"]
    ]
    return "\n".join(
        [
            "# 视频真实渲染环境安装缺口清单",
            "",
            f"- 生成时间：{gap_list['生成时间']}",
            f"- 缺口数量：{gap_list['缺口数量']}",
            f"- error_count：{gap_list['error_count']}",
            f"- 可进入真实渲染：{gap_list['可进入真实渲染']}",
            "",
            *gap_lines,
        ]
    )


def build_card_markdown(card: dict[str, Any]) -> str:
    card_lines = [f"- {item}" for item in card["核对项"]]
    return "\n".join(
        [
            "# 视频真实渲染环境下一步人工安装配置核对卡",
            "",
            f"- 生成时间：{card['生成时间']}",
            f"- 可进入真实渲染：{card['可进入真实渲染']}",
            "",
            *card_lines,
        ]
    )


def main() -> int:
    package = build_package()
    stamp = timestamp_text()
    stamped_package = DATA_DIR / f"视频真实渲染环境候选路径矩阵与安装缺口清单_{stamp}.json"

    write_json(stamped_package, package)
    write_json(PACKAGE_LATEST_JSON, package)
    write_text(MATRIX_LATEST_MD, build_matrix_markdown(package))
    write_json(GAP_LATEST_JSON, package["安装缺口清单"])
    write_text(GAP_LATEST_MD, build_gap_markdown(package["安装缺口清单"]))
    write_json(CARD_LATEST_JSON, package["下一步人工安装配置核对卡"])
    write_text(CARD_LATEST_MD, build_card_markdown(package["下一步人工安装配置核对卡"]))

    print(
        json.dumps(
            {
                "输出": str(PACKAGE_LATEST_JSON),
                "真实渲染": False,
                "生成真实视频": False,
                "上传发布": False,
                "调用MoneyPrinterTurbo": False,
                "执行magick": False,
                "执行magick_version": False,
                "可进入真实渲染": False,
                "error_count": 0,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
