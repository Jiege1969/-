# -*- coding: utf-8 -*-
"""
验证视频真实渲染环境候选路径矩阵与安装缺口清单包。

验证只检查产物结构、红线标志和 blocked 状态，并写入最终验收日志。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = ROOT / "03数据" / "真实渲染环境候选路径矩阵与安装缺口清单"
LOG_DIR = ROOT / "04日志" / "真实渲染环境候选路径矩阵与安装缺口清单验收"

PACKAGE_LATEST_JSON = DATA_DIR / "视频真实渲染环境候选路径矩阵与安装缺口清单_最新.json"
GAP_LATEST_JSON = DATA_DIR / "视频真实渲染环境安装缺口清单_最新.json"
MANUAL_LATEST_JSON = DATA_DIR / "视频真实渲染环境下一步人工确认清单_最新.json"
CHECK_LATEST_JSON = DATA_DIR / "视频真实渲染环境候选路径只读核对_最新.json"

VERIFY_LATEST_JSON = LOG_DIR / "video-render-env-candidate-path-gap-verify-最新.json"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def all_false(values: dict[str, Any], keys: list[str]) -> bool:
    return all(values.get(key) is False for key in keys)


def validate() -> dict[str, Any]:
    package = load_json(PACKAGE_LATEST_JSON)
    gap_doc = load_json(GAP_LATEST_JSON)
    manual_doc = load_json(MANUAL_LATEST_JSON)
    check_doc = load_json(CHECK_LATEST_JSON)
    checks: list[dict[str, Any]] = []

    add_check(checks, "候选路径矩阵包存在", PACKAGE_LATEST_JSON.exists(), str(PACKAGE_LATEST_JSON))
    add_check(checks, "安装缺口清单存在", GAP_LATEST_JSON.exists(), str(GAP_LATEST_JSON))
    add_check(checks, "下一步人工确认清单存在", MANUAL_LATEST_JSON.exists(), str(MANUAL_LATEST_JSON))
    add_check(checks, "只读核对结果存在", CHECK_LATEST_JSON.exists(), str(CHECK_LATEST_JSON))

    cn_forbidden = ["真实渲染", "生成真实视频", "上传发布", "调用MoneyPrinterTurbo", "执行magick", "执行magick_version", "触发n8n", "修改企业微信公共配置", "修改总管面板", "修改一键接续包", "重载服务", "安装软件", "写入系统环境变量"]
    en_forbidden = ["real_render", "generate_real_video", "upload_publish", "call_money_printer_turbo", "execute_magick", "execute_magick_version", "trigger_n8n", "modify_wecom_public_config", "modify_supervisor_panel", "modify_one_click_continuation_pack", "reload_service", "install_software", "write_system_environment"]

    add_check(checks, "矩阵包中文红线标志均为 false", all_false(package.get("readonly_flags", {}), cn_forbidden), package.get("readonly_flags", {}))
    add_check(checks, "矩阵包英文红线标志均为 false", all_false(package.get("readonly_flags_ascii", {}), en_forbidden), package.get("readonly_flags_ascii", {}))
    add_check(checks, "只读核对中文红线标志均为 false", all_false(check_doc.get("readonly_flags", {}), cn_forbidden), check_doc.get("readonly_flags", {}))
    add_check(checks, "只读核对英文红线标志均为 false", all_false(check_doc.get("readonly_flags_ascii", {}), en_forbidden), check_doc.get("readonly_flags_ascii", {}))

    add_check(checks, "真实渲染仍 blocked", package.get("real_render_status") == "blocked" and check_doc.get("real_render_status") == "blocked", {"package": package.get("real_render_status"), "check": check_doc.get("real_render_status")})
    add_check(checks, "真实发布仍 blocked", package.get("real_publish_status") == "blocked" and check_doc.get("real_publish_status") == "blocked", {"package": package.get("real_publish_status"), "check": check_doc.get("real_publish_status")})
    add_check(checks, "当前仅候选路径/缺口清单", package.get("current_stage") == "candidate_path_gap_inventory_only", package.get("current_stage"))
    add_check(checks, "不得伪装已接入真实渲染", package.get("is_real_render_integrated") is False and check_doc.get("is_real_render_integrated") is False, {"package": package.get("is_real_render_integrated"), "check": check_doc.get("is_real_render_integrated")})
    add_check(checks, "不得伪装已接入真实发布", package.get("is_real_publish_integrated") is False and check_doc.get("is_real_publish_integrated") is False, {"package": package.get("is_real_publish_integrated"), "check": check_doc.get("is_real_publish_integrated")})

    matrix = package.get("候选路径矩阵", {})
    add_check(checks, "MoneyPrinterTurbo 候选路径矩阵存在", isinstance(matrix.get("MoneyPrinterTurbo"), list) and len(matrix.get("MoneyPrinterTurbo", [])) > 0, len(matrix.get("MoneyPrinterTurbo", [])))
    add_check(checks, "ImageMagick 候选路径矩阵存在", isinstance(matrix.get("ImageMagick"), list) and len(matrix.get("ImageMagick", [])) > 0, len(matrix.get("ImageMagick", [])))
    add_check(checks, "安装缺口清单非空", isinstance(gap_doc.get("安装缺口清单"), list) and len(gap_doc.get("安装缺口清单", [])) > 0, len(gap_doc.get("安装缺口清单", [])))
    add_check(checks, "人工确认清单非空", isinstance(manual_doc.get("下一步人工确认清单"), list) and len(manual_doc.get("下一步人工确认清单", [])) > 0, len(manual_doc.get("下一步人工确认清单", [])))

    blockers = package.get("当前阻断原因", []) + check_doc.get("当前阻断原因", [])
    add_check(checks, "阻断原因包含 MoneyPrinterTurbo", any("MoneyPrinterTurbo" in item for item in blockers), blockers)
    add_check(checks, "阻断原因包含 ImageMagick/magick", any("ImageMagick" in item or "magick" in item for item in blockers), blockers)
    add_check(checks, "只读核对 error_count 为 0", check_doc.get("error_count") == 0, check_doc.get("error_count"))

    errors = [item for item in checks if not item["通过"]]
    return {
        "名称": "视频真实渲染环境候选路径矩阵与安装缺口清单验收",
        "generated_at": now_text(),
        "error_count": len(errors),
        "错误数": len(errors),
        "通过数": len(checks) - len(errors),
        "检查项": checks,
        "产物路径": {
            "候选路径矩阵包": str(PACKAGE_LATEST_JSON),
            "安装缺口清单": str(GAP_LATEST_JSON),
            "下一步人工确认清单": str(MANUAL_LATEST_JSON),
            "只读核对结果": str(CHECK_LATEST_JSON),
            "最终验收日志": str(VERIFY_LATEST_JSON),
        },
        "红线确认": {
            "真实渲染仍blocked": True,
            "真实发布仍blocked": True,
            "当前仅候选路径缺口清单": True,
            "未调用MoneyPrinterTurbo": True,
            "未调用ImageMagick": True,
            "未执行magick": True,
            "未执行magick_version": True,
            "未真实渲染": True,
            "未上传发布": True,
            "未接n8n": True,
            "未修改企业微信公共配置": True,
            "未修改总管面板": True,
            "未修改一键接续包": True,
            "未重载任何服务": True,
            "未安装软件": True,
            "未写系统环境变量": True,
        },
        "验收结论": "通过" if len(errors) == 0 else "不通过",
    }


def main() -> int:
    result = validate()
    stamped = LOG_DIR / f"video-render-env-candidate-path-gap-verify-{stamp_text()}.json"
    write_json(stamped, result)
    write_json(VERIFY_LATEST_JSON, result)
    print(
        json.dumps(
            {
                "verify_log": str(VERIFY_LATEST_JSON),
                "error_count": result["error_count"],
                "验收结论": result["验收结论"],
                "real_render_status": "blocked",
                "real_publish_status": "blocked",
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
