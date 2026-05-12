# -*- coding: utf-8 -*-
"""
验证视频真实渲染白名单材料人工补齐模板与签收预演包。

只验证产物结构、人工补齐模板覆盖范围、签收预演默认状态和红线字段，写入固定验收日志。
不调用真实渲染、发布、n8n、企业微信、总管面板、一键接续包或服务重载链路。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = ROOT / "03数据" / "27真实渲染白名单材料人工补齐模板与签收预演包"
LOG_DIR = ROOT / "04日志" / "真实渲染白名单材料人工补齐模板与签收预演包验收"

MATERIAL_TEMPLATE_LATEST = DATA_DIR / "视频真实渲染白名单材料人工补齐模板_最新.json"
MATERIAL_TEMPLATE_MD_LATEST = DATA_DIR / "视频真实渲染白名单材料人工补齐模板_最新.md"
SIGNOFF_PREVIEW_LATEST = DATA_DIR / "视频真实渲染白名单材料签收预演单_最新.json"
SIGNOFF_PREVIEW_MD_LATEST = DATA_DIR / "视频真实渲染白名单材料签收预演单_最新.md"
PACKAGE_LATEST = DATA_DIR / "视频真实渲染白名单材料人工补齐模板与签收预演包_最新.json"
PACKAGE_MD_LATEST = DATA_DIR / "视频真实渲染白名单材料人工补齐模板与签收预演包_最新.md"
READONLY_PREVIEW_LATEST = DATA_DIR / "视频真实渲染白名单材料只读签收预演报告_最新.json"
READONLY_PREVIEW_MD_LATEST = DATA_DIR / "视频真实渲染白名单材料只读签收预演报告_最新.md"
VERIFY_LATEST = LOG_DIR / "video-render-whitelist-material-signoff-preview-verify-最新.json"

REQUIRED_ITEM_NAMES = ["环境识别", "素材授权", "输出目录隔离", "失败回滚", "证据留存", "人工签收", "试运行范围", "发布隔离"]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8-sig")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"检查项": name, "通过": bool(passed), "详情": detail})


def guard_flags(error_count: int) -> dict[str, Any]:
    ascii_flags = {
        "signed": False,
        "whitelist_effective": False,
        "can_enter_real_render": False,
        "real_render": False,
        "generate_real_video": False,
        "publish": False,
        "upload_publish": False,
        "call_money_printer_turbo": False,
        "execute_magick": False,
        "execute_magick_version": False,
        "trigger_n8n": False,
        "modify_wecom_public_config": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_pack": False,
        "reload_service": False,
        "requires_supervisor_confirmation": True,
    }
    return {
        "生成时间": now_text(),
        "error_count": error_count,
        "signed": False,
        "whitelist_effective": False,
        "can_enter_real_render": False,
        "real_render": False,
        "publish": False,
        "requires_supervisor_confirmation": True,
        "已签收": False,
        "白名单已生效": False,
        "可进入真实渲染": False,
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
        "需要总管人工确认": True,
        "readonly_flags_ascii": ascii_flags,
    }


def required_guard_state(doc: dict[str, Any]) -> bool:
    flags = doc.get("readonly_flags_ascii", {})
    return (
        doc.get("signed") is False
        and doc.get("whitelist_effective") is False
        and doc.get("can_enter_real_render") is False
        and doc.get("real_render") is False
        and doc.get("publish") is False
        and doc.get("requires_supervisor_confirmation") is True
        and flags.get("signed") is False
        and flags.get("whitelist_effective") is False
        and flags.get("can_enter_real_render") is False
        and flags.get("real_render") is False
        and flags.get("publish") is False
        and flags.get("requires_supervisor_confirmation") is True
    )


def validate() -> dict[str, Any]:
    template = load_json(MATERIAL_TEMPLATE_LATEST)
    signoff = load_json(SIGNOFF_PREVIEW_LATEST)
    package = load_json(PACKAGE_LATEST)
    readonly_preview = load_json(READONLY_PREVIEW_LATEST)
    checks: list[dict[str, Any]] = []

    for name, path in {
        "材料人工补齐模板JSON": MATERIAL_TEMPLATE_LATEST,
        "材料人工补齐模板MD": MATERIAL_TEMPLATE_MD_LATEST,
        "签收预演单JSON": SIGNOFF_PREVIEW_LATEST,
        "签收预演单MD": SIGNOFF_PREVIEW_MD_LATEST,
        "总包JSON": PACKAGE_LATEST,
        "总包MD": PACKAGE_MD_LATEST,
        "只读签收预演报告JSON": READONLY_PREVIEW_LATEST,
        "只读签收预演报告MD": READONLY_PREVIEW_MD_LATEST,
    }.items():
        add_check(checks, f"{name}存在", path.exists(), str(path))

    template_items = template.get("材料补齐模板", [])
    template_names = [item.get("name") for item in template_items]
    signoff_items = signoff.get("签收项", [])
    signoff_names = [item.get("name") for item in signoff_items]
    add_check(checks, "材料人工补齐模板覆盖八项指定材料", all(name in template_names for name in REQUIRED_ITEM_NAMES), template_names)
    add_check(checks, "签收预演单覆盖八项指定材料", all(name in signoff_names for name in REQUIRED_ITEM_NAMES), signoff_names)
    add_check(checks, "材料人工补齐模板逐项要求人工补齐且不自动补齐", all(item.get("manual_fill_required") is True and item.get("auto_fill") is False and item.get("script_may_complete_this_item") is False for item in template_items), template_items)
    add_check(checks, "材料人工补齐模板逐项包含字段和值占位", all(item.get("manual_fill_fields") and isinstance(item.get("field_values"), dict) for item in template_items), template_items)
    add_check(checks, "签收预演单默认signed=false", signoff.get("signed") is False and all(item.get("signed") is False for item in signoff_items), signoff_items)
    add_check(checks, "签收预演单默认whitelist_effective=false", signoff.get("whitelist_effective") is False, signoff.get("whitelist_effective"))
    add_check(checks, "签收预演单requires_supervisor_confirmation=true", signoff.get("requires_supervisor_confirmation") is True, signoff.get("requires_supervisor_confirmation"))
    add_check(checks, "只读签收预演报告确认不可进入真实渲染", readonly_preview.get("can_enter_real_render") is False and readonly_preview.get("real_render") is False and readonly_preview.get("publish") is False, readonly_preview.get("签收状态确认", {}))

    for label, doc in {"材料人工补齐模板": template, "签收预演单": signoff, "总包": package, "只读签收预演报告": readonly_preview}.items():
        add_check(checks, f"{label} error_count=0", doc.get("error_count") == 0, doc.get("error_count"))
        add_check(checks, f"{label} signed=false", doc.get("signed") is False, doc.get("signed"))
        add_check(checks, f"{label} whitelist_effective=false", doc.get("whitelist_effective") is False, doc.get("whitelist_effective"))
        add_check(checks, f"{label} can_enter_real_render=false", doc.get("can_enter_real_render") is False, doc.get("can_enter_real_render"))
        add_check(checks, f"{label} real_render=false", doc.get("real_render") is False, doc.get("real_render"))
        add_check(checks, f"{label} publish=false", doc.get("publish") is False, doc.get("publish"))
        add_check(checks, f"{label} requires_supervisor_confirmation=true", doc.get("requires_supervisor_confirmation") is True, doc.get("requires_supervisor_confirmation"))
        add_check(checks, f"{label}红线字段一致", required_guard_state(doc), doc.get("readonly_flags_ascii", {}))

    errors = [item for item in checks if not item["通过"]]
    result = {
        "名称": "视频真实渲染白名单材料人工补齐模板与签收预演包验收",
        "验收模式": "manual_template_and_readonly_signoff_preview_structure_only",
        "检查结果": checks,
        "错误项": errors,
        "产物路径": {
            "材料人工补齐模板": str(MATERIAL_TEMPLATE_LATEST),
            "签收预演单": str(SIGNOFF_PREVIEW_LATEST),
            "只读签收预演报告": str(READONLY_PREVIEW_LATEST),
            "固定验收日志": str(VERIFY_LATEST),
        },
        "红线确认": {
            "不调用MoneyPrinterTurbo": True,
            "不执行magick": True,
            "不真实渲染": True,
            "不生成真实视频": True,
            "不上传发布": True,
            "不接n8n": True,
            "不改企业微信公共配置": True,
            "不改总管面板": True,
            "不改一键接续包": True,
            "不重载服务": True,
            "不自动补齐": True,
            "不让白名单生效": True,
        },
        "验收结论": "通过" if not errors else "不通过",
    }
    result.update(guard_flags(len(errors)))
    return result


def main() -> int:
    result = validate()
    write_json(VERIFY_LATEST, result)
    print(
        json.dumps(
            {
                "verify_log": str(VERIFY_LATEST),
                "error_count": result["error_count"],
                "signed": False,
                "whitelist_effective": False,
                "can_enter_real_render": False,
                "real_render": False,
                "publish": False,
                "requires_supervisor_confirmation": True,
                "验收结论": result["验收结论"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
