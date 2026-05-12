# -*- coding: utf-8 -*-
"""
执行视频真实渲染环境候选路径只读核对。

只复核候选路径矩阵中的目录/入口文件存在性，不调用 MoneyPrinterTurbo，不执行 ImageMagick。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = ROOT / "03数据" / "真实渲染环境候选路径矩阵与安装缺口清单"

PACKAGE_LATEST_JSON = DATA_DIR / "视频真实渲染环境候选路径矩阵与安装缺口清单_最新.json"
CHECK_LATEST_JSON = DATA_DIR / "视频真实渲染环境候选路径只读核对_最新.json"
CHECK_LATEST_MD = DATA_DIR / "视频真实渲染环境候选路径只读核对_最新.md"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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


def recheck_money_row(row: dict[str, Any]) -> dict[str, Any]:
    path = Path(row["candidate_path"])
    entry_names = list(row.get("候选入口文件存在性", {}).keys())
    entries = {name: (path / name).exists() for name in entry_names}
    return {
        "对象": "MoneyPrinterTurbo",
        "candidate_path": str(path),
        "目录存在_复核": path.exists() and path.is_dir(),
        "候选入口文件存在性_复核": entries,
        "包含任一候选入口文件_复核": any(entries.values()),
        "本轮是否调用": False,
        "本轮是否渲染": False,
    }


def recheck_magick_row(row: dict[str, Any]) -> dict[str, Any]:
    path = Path(row["candidate_path"])
    entry_names = list(row.get("候选入口文件存在性", {}).keys())
    entries = {name: (path / name).exists() for name in entry_names}
    return {
        "对象": "ImageMagick",
        "candidate_path": str(path),
        "目录存在_复核": path.exists() and path.is_dir(),
        "候选入口文件存在性_复核": entries,
        "包含magick.exe_复核": entries.get("magick.exe", False),
        "本轮是否执行magick": False,
        "本轮是否执行magick_version": False,
    }


def build_result(package: dict[str, Any]) -> dict[str, Any]:
    matrix = package.get("候选路径矩阵", {})
    money_rows = [recheck_money_row(row) for row in matrix.get("MoneyPrinterTurbo", [])]
    magick_rows = [recheck_magick_row(row) for row in matrix.get("ImageMagick", [])]

    money_entry_count = sum(1 for row in money_rows if row["包含任一候选入口文件_复核"])
    magick_exe_count = sum(1 for row in magick_rows if row["包含magick.exe_复核"])
    blockers = [
        "MoneyPrinterTurbo 本轮未调用，真实渲染入口、依赖和配置仍未验证。",
        "ImageMagick 本轮未执行，未运行 magick 或 magick -version，版本与可运行性仍未验证。",
        "本轮仅复核目录和入口文件存在性，不构成真实渲染接入。",
        "真实发布链路未放行，仍 blocked。",
    ]
    if money_entry_count == 0:
        blockers.append("MoneyPrinterTurbo 未发现可确认入口文件，需人工补充或确认根目录。")
    if magick_exe_count == 0:
        blockers.append("ImageMagick 未发现 magick.exe，需人工安装或确认路径。")

    return {
        "名称": "视频真实渲染环境候选路径只读核对",
        "generated_at": now_text(),
        "source_package": str(PACKAGE_LATEST_JSON),
        "error_count": 0,
        "真实渲染状态": "blocked",
        "real_render_status": "blocked",
        "真实发布状态": "blocked",
        "real_publish_status": "blocked",
        "当前阶段": "仅候选路径矩阵与安装缺口清单只读核对",
        "current_stage": "candidate_path_gap_readonly_check_only",
        "是否已接入真实渲染": False,
        "is_real_render_integrated": False,
        "是否已接入真实发布": False,
        "is_real_publish_integrated": False,
        "readonly_flags": readonly_flags_cn(),
        "readonly_flags_ascii": readonly_flags_ascii(),
        "复核矩阵": {
            "MoneyPrinterTurbo": money_rows,
            "ImageMagick": magick_rows,
        },
        "readback_summary": {
            "moneyprinter_candidate_count": len(money_rows),
            "moneyprinter_existing_dir_count": sum(1 for row in money_rows if row["目录存在_复核"]),
            "moneyprinter_entry_count": money_entry_count,
            "imagemagick_candidate_count": len(magick_rows),
            "imagemagick_existing_dir_count": sum(1 for row in magick_rows if row["目录存在_复核"]),
            "imagemagick_magick_exe_count": magick_exe_count,
        },
        "当前阻断原因": blockers,
        "核对结论": "只读核对完成；真实渲染仍 blocked，真实发布仍 blocked，当前仅候选路径/缺口清单，不得伪装已接入。",
    }


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染环境候选路径只读核对",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- error_count：{result['error_count']}",
        f"- 真实渲染状态：{result['真实渲染状态']}",
        f"- 真实发布状态：{result['真实发布状态']}",
        "- 声明：当前仅候选路径/缺口清单，不得伪装已接入。",
        "",
        "## 复核摘要",
        "",
    ]
    for key, value in result["readback_summary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## 当前阻断原因", ""])
    for item in result["当前阻断原因"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    package = load_json(PACKAGE_LATEST_JSON)
    result = build_result(package)
    stamp = stamp_text()
    stamped_json = DATA_DIR / f"视频真实渲染环境候选路径只读核对_{stamp}.json"

    write_json(stamped_json, result)
    write_json(CHECK_LATEST_JSON, result)
    write_text(CHECK_LATEST_MD, build_markdown(result))

    print(
        json.dumps(
            {
                "readonly_check": str(CHECK_LATEST_JSON),
                "real_render_status": "blocked",
                "real_publish_status": "blocked",
                "current_stage": "candidate_path_gap_readonly_check_only",
                "called_money_printer_turbo": False,
                "executed_magick": False,
                "executed_magick_version": False,
                "error_count": 0,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
