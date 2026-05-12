# -*- coding: utf-8 -*-
"""
执行视频真实渲染白名单材料只读签收预演。

只读取第27包材料人工补齐模板和签收预演单，生成只读签收预演报告；不自动补齐，
不签收，不让白名单生效，不真实渲染，不发布。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = ROOT / "03数据" / "27真实渲染白名单材料人工补齐模板与签收预演包"

MATERIAL_TEMPLATE_LATEST = DATA_DIR / "视频真实渲染白名单材料人工补齐模板_最新.json"
SIGNOFF_PREVIEW_LATEST = DATA_DIR / "视频真实渲染白名单材料签收预演单_最新.json"
PACKAGE_LATEST = DATA_DIR / "视频真实渲染白名单材料人工补齐模板与签收预演包_最新.json"
READONLY_PREVIEW_LATEST = DATA_DIR / "视频真实渲染白名单材料只读签收预演报告_最新.json"
READONLY_PREVIEW_MD_LATEST = DATA_DIR / "视频真实渲染白名单材料只读签收预演报告_最新.md"

REQUIRED_ITEM_NAMES = ["环境识别", "素材授权", "输出目录隔离", "失败回滚", "证据留存", "人工签收", "试运行范围", "发布隔离"]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8-sig")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8-sig")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"检查项": name, "通过": bool(passed), "详情": detail})


def guard_flags(generated_at: str, error_count: int) -> dict[str, Any]:
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
        "生成时间": generated_at,
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


def build_readonly_preview() -> dict[str, Any]:
    generated_at = now_text()
    template = load_json(MATERIAL_TEMPLATE_LATEST)
    signoff = load_json(SIGNOFF_PREVIEW_LATEST)
    package = load_json(PACKAGE_LATEST)
    checks: list[dict[str, Any]] = []

    for name, path in {
        "材料人工补齐模板JSON": MATERIAL_TEMPLATE_LATEST,
        "签收预演单JSON": SIGNOFF_PREVIEW_LATEST,
        "总包JSON": PACKAGE_LATEST,
    }.items():
        add_check(checks, f"{name}存在", path.exists(), str(path))

    template_names = [item.get("name") for item in template.get("材料补齐模板", [])]
    signoff_names = [item.get("name") for item in signoff.get("签收项", [])]
    add_check(checks, "材料人工补齐模板覆盖八项材料", all(name in template_names for name in REQUIRED_ITEM_NAMES), template_names)
    add_check(checks, "签收预演单覆盖八项材料", all(name in signoff_names for name in REQUIRED_ITEM_NAMES), signoff_names)
    add_check(checks, "材料模板不自动补齐", all(item.get("auto_fill") is False and item.get("script_may_complete_this_item") is False for item in template.get("材料补齐模板", [])), template.get("材料补齐模板", []))
    add_check(checks, "签收预演单默认未签收", signoff.get("signed") is False and all(item.get("signed") is False for item in signoff.get("签收项", [])), signoff.get("签收项", []))
    add_check(checks, "签收预演单不让白名单生效", signoff.get("whitelist_effective") is False, signoff.get("whitelist_effective"))

    for label, doc in {"材料人工补齐模板": template, "签收预演单": signoff, "总包": package}.items():
        add_check(checks, f"{label}红线字段关闭", required_guard_state(doc), doc.get("readonly_flags_ascii", {}))
        add_check(checks, f"{label}error_count=0", doc.get("error_count") == 0, doc.get("error_count"))

    errors = [item for item in checks if not item["通过"]]
    result = {
        "名称": "视频真实渲染白名单材料只读签收预演报告",
        "预演模式": "readonly_signoff_preview_only",
        "检查结果": checks,
        "错误项": errors,
        "预演结论": "通过；can_enter_real_render=false，real_render=false，publish=false，白名单未生效。" if not errors else "不通过；仍保持真实渲染和发布关闭。",
        "签收状态确认": {
            "signed": False,
            "whitelist_effective": False,
            "requires_supervisor_confirmation": True,
            "can_enter_real_render": False,
            "real_render": False,
            "publish": False,
        },
        "产物路径": {
            "材料人工补齐模板": str(MATERIAL_TEMPLATE_LATEST),
            "签收预演单": str(SIGNOFF_PREVIEW_LATEST),
            "只读签收预演报告": str(READONLY_PREVIEW_LATEST),
        },
    }
    result.update(guard_flags(generated_at, len(errors)))
    return result


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染白名单材料只读签收预演报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- error_count：{report['error_count']}",
        "- signed：false",
        "- whitelist_effective：false",
        "- can_enter_real_render：false",
        "- real_render：false",
        "- publish：false",
        "- requires_supervisor_confirmation：true",
        "",
        "## 检查项",
        "",
    ]
    for item in report["检查结果"]:
        lines.append(f"- {item['检查项']}：{str(item['通过']).lower()}")
    lines.extend(["", f"结论：{report['预演结论']}"])
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_readonly_preview()
    stamp = stamp_text()
    write_json(DATA_DIR / f"视频真实渲染白名单材料只读签收预演报告_{stamp}.json", report)
    write_json(READONLY_PREVIEW_LATEST, report)
    write_text(READONLY_PREVIEW_MD_LATEST, build_markdown(report))
    print(
        json.dumps(
            {
                "readonly_preview": str(READONLY_PREVIEW_LATEST),
                "error_count": report["error_count"],
                "signed": False,
                "whitelist_effective": False,
                "can_enter_real_render": False,
                "real_render": False,
                "publish": False,
                "requires_supervisor_confirmation": True,
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
