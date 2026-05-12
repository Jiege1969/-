# -*- coding: utf-8 -*-
"""
验证视频真实渲染环境候选路径矩阵与安装缺口清单。

验收目标：
- 真实渲染=false、生成真实视频=false、上传发布=false。
- 调用MoneyPrinterTurbo=false、执行magick=false、执行magick_version=false。
- 可进入真实渲染=false、error_count=0。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = ROOT / "03数据" / "20真实渲染环境候选路径矩阵与安装缺口清单"
LOG_DIR = ROOT / "04日志" / "真实渲染环境候选路径矩阵与安装缺口清单验收"

PACKAGE_JSON = DATA_DIR / "视频真实渲染环境候选路径矩阵与安装缺口清单_最新.json"
GAP_JSON = DATA_DIR / "视频真实渲染环境安装缺口清单_最新.json"
CARD_JSON = DATA_DIR / "视频真实渲染环境下一步人工安装配置核对卡_最新.json"
CHECK_JSON = DATA_DIR / "视频真实渲染环境候选路径只读核对_最新.json"
LATEST_LOG = LOG_DIR / "video-render-env-candidate-path-gap-verify-最新.json"

REQUIRED_FALSE_KEYS = [
    "真实渲染",
    "生成真实视频",
    "上传发布",
    "调用MoneyPrinterTurbo",
    "执行magick",
    "执行magick_version",
]

REQUIRED_FALSE_ASCII_KEYS = [
    "real_render",
    "generate_real_video",
    "upload_publish",
    "call_money_printer_turbo",
    "execute_magick",
    "execute_magick_version",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def flags_are_false(data: dict[str, Any], key: str, required_keys: list[str]) -> tuple[bool, dict[str, Any]]:
    flags = data.get(key, {})
    observed = {item: flags.get(item) for item in required_keys}
    return all(value is False for value in observed.values()), observed


def main() -> int:
    package = load_json(PACKAGE_JSON)
    gap_list = load_json(GAP_JSON)
    card = load_json(CARD_JSON)
    check_result = load_json(CHECK_JSON)
    checks: list[dict[str, Any]] = []

    add_check(checks, "候选路径矩阵包存在", PACKAGE_JSON.exists(), str(PACKAGE_JSON))
    add_check(checks, "安装缺口清单存在", GAP_JSON.exists(), str(GAP_JSON))
    add_check(checks, "人工安装配置核对卡存在", CARD_JSON.exists(), str(CARD_JSON))
    add_check(checks, "只读核对结果存在", CHECK_JSON.exists(), str(CHECK_JSON))

    for source_name, source in [("矩阵包", package), ("缺口清单", gap_list), ("核对卡", card), ("只读核对结果", check_result)]:
        ok, detail = flags_are_false(source, "readonly_flags", REQUIRED_FALSE_KEYS)
        add_check(checks, f"{source_name}六个中文禁用标志均为false", ok, detail)
        ok_ascii, detail_ascii = flags_are_false(source, "readonly_flags_ascii", REQUIRED_FALSE_ASCII_KEYS)
        add_check(checks, f"{source_name}六个英文禁用标志均为false", ok_ascii, detail_ascii)

    add_check(checks, "矩阵包真实渲染=false", package.get("readonly_flags", {}).get("真实渲染") is False, package.get("readonly_flags", {}))
    add_check(checks, "矩阵包生成真实视频=false", package.get("readonly_flags", {}).get("生成真实视频") is False, package.get("readonly_flags", {}))
    add_check(checks, "矩阵包上传发布=false", package.get("readonly_flags", {}).get("上传发布") is False, package.get("readonly_flags", {}))
    add_check(checks, "矩阵包调用MoneyPrinterTurbo=false", package.get("readonly_flags", {}).get("调用MoneyPrinterTurbo") is False, package.get("readonly_flags", {}))
    add_check(checks, "矩阵包执行magick=false", package.get("readonly_flags", {}).get("执行magick") is False, package.get("readonly_flags", {}))
    add_check(checks, "矩阵包执行magick_version=false", package.get("readonly_flags", {}).get("执行magick_version") is False, package.get("readonly_flags", {}))
    add_check(checks, "矩阵包可进入真实渲染=false", package.get("可进入真实渲染") is False, package.get("可进入真实渲染"))
    add_check(checks, "只读核对可进入真实渲染=false", check_result.get("可进入真实渲染") is False, check_result.get("可进入真实渲染"))
    add_check(checks, "矩阵包error_count=0", package.get("error_count") == 0, package.get("error_count"))
    add_check(checks, "只读核对error_count=0", check_result.get("error_count") == 0, check_result.get("error_count"))
    add_check(
        checks,
        "包含MoneyPrinterTurbo候选路径矩阵",
        len(package.get("候选路径矩阵", {}).get("MoneyPrinterTurbo", [])) > 0,
        package.get("候选路径矩阵", {}).get("MoneyPrinterTurbo", []),
    )
    add_check(
        checks,
        "包含ImageMagick候选路径矩阵",
        len(package.get("候选路径矩阵", {}).get("ImageMagick", [])) > 0,
        package.get("候选路径矩阵", {}).get("ImageMagick", []),
    )
    add_check(
        checks,
        "包含安装缺口清单",
        len(gap_list.get("缺口清单", [])) > 0,
        gap_list.get("缺口清单", []),
    )
    add_check(
        checks,
        "包含下一步人工安装配置核对卡",
        len(card.get("核对项", [])) > 0,
        card.get("核对项", []),
    )

    errors = [item for item in checks if not item["通过"]]
    report = {
        "名称": "视频真实渲染环境候选路径矩阵与安装缺口清单验收",
        "生成时间": now_text(),
        "error_count": len(errors),
        "错误数": len(errors),
        "通过数": len(checks) - len(errors),
        "检查项": checks,
        "真实渲染": False,
        "生成真实视频": False,
        "上传发布": False,
        "调用MoneyPrinterTurbo": False,
        "执行magick": False,
        "执行magick_version": False,
        "可进入真实渲染": False,
        "readonly_flags": {
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
        },
        "readonly_flags_ascii": {
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
        },
        "结论": "通过" if not errors else "未通过",
        "验收日志文件名": LATEST_LOG.name,
    }
    write_json(LATEST_LOG, report)
    print(
        json.dumps(
            {
                "输出": str(LATEST_LOG),
                "error_count": report["error_count"],
                "通过数": report["通过数"],
                "真实渲染": False,
                "生成真实视频": False,
                "上传发布": False,
                "调用MoneyPrinterTurbo": False,
                "执行magick": False,
                "执行magick_version": False,
                "可进入真实渲染": False,
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
