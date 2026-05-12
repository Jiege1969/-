# -*- coding: utf-8 -*-
"""
验证视频真实渲染人工放行材料完整性复核与试运行禁入包。

验证只检查产物结构与红线状态，并写入固定验收日志：
video-render-approval-materials-no-trial-verify-最新.json
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = ROOT / "03数据" / "22真实渲染人工放行材料完整性复核与试运行禁入包"
LOG_DIR = ROOT / "04日志" / "真实渲染人工放行材料完整性复核与试运行禁入包验收"

PACKAGE_LATEST = DATA_DIR / "视频真实渲染人工放行材料完整性复核与试运行禁入包_最新.json"
MATERIAL_REVIEW_LATEST = DATA_DIR / "视频真实渲染人工放行材料完整性复核_最新.json"
TRIAL_BAN_LATEST = DATA_DIR / "视频真实渲染试运行禁入清单_最新.json"
NEXT_CARD_LATEST = DATA_DIR / "视频真实渲染下一步人工补齐卡_最新.json"
CHECK_LATEST = DATA_DIR / "视频真实渲染人工放行材料只读复核_最新.json"
VERIFY_LATEST = LOG_DIR / "video-render-approval-materials-no-trial-verify-最新.json"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"检查项": name, "通过": bool(passed), "详情": detail})


def required_status(doc: dict[str, Any]) -> bool:
    return (
        doc.get("试运行禁入") is True
        and doc.get("可进入真实渲染") is False
        and doc.get("真实渲染") is False
        and doc.get("生成真实视频") is False
        and doc.get("上传发布") is False
        and doc.get("调用MoneyPrinterTurbo") is False
        and doc.get("执行magick") is False
        and doc.get("执行magick_version") is False
        and doc.get("error_count") == 0
    )


def required_ascii_status(doc: dict[str, Any]) -> bool:
    flags = doc.get("readonly_flags_ascii", {})
    return (
        flags.get("trial_run_forbidden") is True
        and flags.get("can_enter_real_render") is False
        and flags.get("real_render") is False
        and flags.get("generate_real_video") is False
        and flags.get("upload_publish") is False
        and flags.get("call_money_printer_turbo") is False
        and flags.get("execute_magick") is False
        and flags.get("execute_magick_version") is False
    )


def validate() -> dict[str, Any]:
    package = load_json(PACKAGE_LATEST)
    material_review = load_json(MATERIAL_REVIEW_LATEST)
    trial_ban = load_json(TRIAL_BAN_LATEST)
    next_card = load_json(NEXT_CARD_LATEST)
    check = load_json(CHECK_LATEST)
    checks: list[dict[str, Any]] = []

    add_check(checks, "总包存在", PACKAGE_LATEST.exists(), str(PACKAGE_LATEST))
    add_check(checks, "材料完整性复核 JSON 存在", MATERIAL_REVIEW_LATEST.exists(), str(MATERIAL_REVIEW_LATEST))
    add_check(checks, "材料完整性复核 MD 存在", (DATA_DIR / "视频真实渲染人工放行材料完整性复核_最新.md").exists(), str(DATA_DIR / "视频真实渲染人工放行材料完整性复核_最新.md"))
    add_check(checks, "试运行禁入清单 JSON 存在", TRIAL_BAN_LATEST.exists(), str(TRIAL_BAN_LATEST))
    add_check(checks, "试运行禁入清单 MD 存在", (DATA_DIR / "视频真实渲染试运行禁入清单_最新.md").exists(), str(DATA_DIR / "视频真实渲染试运行禁入清单_最新.md"))
    add_check(checks, "下一步人工补齐卡存在", NEXT_CARD_LATEST.exists(), str(NEXT_CARD_LATEST))
    add_check(checks, "只读复核结果存在", CHECK_LATEST.exists(), str(CHECK_LATEST))

    docs = {
        "package": package,
        "material_review": material_review,
        "trial_ban": trial_ban,
        "next_card": next_card,
        "check": check,
    }
    for name, doc in docs.items():
        add_check(
            checks,
            f"{name}: 试运行禁入=true 且真实动作全 false 且 error_count=0",
            required_status(doc),
            {
                "试运行禁入": doc.get("试运行禁入"),
                "可进入真实渲染": doc.get("可进入真实渲染"),
                "真实渲染": doc.get("真实渲染"),
                "生成真实视频": doc.get("生成真实视频"),
                "上传发布": doc.get("上传发布"),
                "调用MoneyPrinterTurbo": doc.get("调用MoneyPrinterTurbo"),
                "执行magick": doc.get("执行magick"),
                "执行magick_version": doc.get("执行magick_version"),
                "error_count": doc.get("error_count"),
            },
        )
        add_check(checks, f"{name}: 英文红线字段一致", required_ascii_status(doc), doc.get("readonly_flags_ascii", {}))

    material_names = [item.get("材料项") for item in material_review.get("材料复核项", [])]
    required_materials = ["MoneyPrinterTurbo入口", "ImageMagick可用性", "测试素材", "输出目录", "生成放行清单", "发布阻断保持", "回滚方案", "人工确认签收"]
    add_check(checks, "材料完整性复核覆盖指定材料项", all(item in material_names for item in required_materials), material_names)
    ban_actions = [item.get("动作") for item in trial_ban.get("禁入项", [])]
    add_check(checks, "试运行禁入清单覆盖调用/执行/生成/发布动作", all(item in ban_actions for item in ["试运行真实渲染", "调用MoneyPrinterTurbo", "执行magick", "执行magick -version", "生成真实视频", "上传发布"]), ban_actions)

    errors = [item for item in checks if not item["通过"]]
    result = {
        "名称": "视频真实渲染人工放行材料完整性复核与试运行禁入包验收",
        "生成时间": now_text(),
        "error_count": len(errors),
        "试运行禁入": True,
        "trial_run_forbidden": True,
        "可进入真实渲染": False,
        "can_enter_real_render": False,
        "真实渲染": False,
        "生成真实视频": False,
        "上传发布": False,
        "调用MoneyPrinterTurbo": False,
        "执行magick": False,
        "执行magick_version": False,
        "检查结果": checks,
        "错误项": errors,
        "产物路径": {
            "总包": str(PACKAGE_LATEST),
            "材料完整性复核": str(MATERIAL_REVIEW_LATEST),
            "试运行禁入清单": str(TRIAL_BAN_LATEST),
            "下一步人工补齐卡": str(NEXT_CARD_LATEST),
            "只读复核": str(CHECK_LATEST),
            "验收日志": str(VERIFY_LATEST),
        },
        "红线确认": {
            "不调用MoneyPrinterTurbo": True,
            "不执行magick": True,
            "不执行magick_version": True,
            "不真实渲染": True,
            "不生成真实视频": True,
            "不上传发布": True,
            "不接n8n": True,
            "不改企业微信公共配置": True,
            "不改总管面板": True,
            "不改一键接续包": True,
            "不重载服务": True,
        },
        "验收结论": "通过" if not errors else "不通过",
    }
    return result


def main() -> int:
    result = validate()
    write_json(VERIFY_LATEST, result)
    print(
        json.dumps(
            {
                "verify_log": str(VERIFY_LATEST),
                "试运行禁入": True,
                "可进入真实渲染": False,
                "真实渲染": False,
                "生成真实视频": False,
                "上传发布": False,
                "调用MoneyPrinterTurbo": False,
                "执行magick": False,
                "执行magick_version": False,
                "error_count": result["error_count"],
                "验收结论": result["验收结论"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
