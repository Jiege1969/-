# -*- coding: utf-8 -*-
"""
验证视频真实渲染白名单申请材料完整度判定包。

验证仅检查产物结构、完整度字段和红线状态，并写入固定验收日志。
不会调用真实渲染、发布、n8n、企业微信、总管面板或服务重载链路。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = ROOT / "03数据" / "26真实渲染白名单申请材料完整度判定包"
LOG_DIR = ROOT / "04日志" / "真实渲染白名单申请材料完整度判定包验收"

MATERIAL_LIST_LATEST = DATA_DIR / "视频真实渲染白名单申请材料清单_最新.json"
MATERIAL_LIST_MD_LATEST = DATA_DIR / "视频真实渲染白名单申请材料清单_最新.md"
COMPLETENESS_REPORT_LATEST = DATA_DIR / "视频真实渲染白名单申请材料完整度判定报告_最新.json"
COMPLETENESS_REPORT_MD_LATEST = DATA_DIR / "视频真实渲染白名单申请材料完整度判定报告_最新.md"
GAP_TODO_LATEST = DATA_DIR / "视频真实渲染白名单申请缺口补齐待办_最新.json"
GAP_TODO_MD_LATEST = DATA_DIR / "视频真实渲染白名单申请缺口补齐待办_最新.md"
PACKAGE_LATEST = DATA_DIR / "视频真实渲染白名单申请材料完整度判定包_最新.json"
READONLY_CHECK_LATEST = DATA_DIR / "视频真实渲染白名单申请只读完整度检查_最新.json"
VERIFY_LATEST = LOG_DIR / "video-render-whitelist-application-completeness-verify-最新.json"

REQUIRED_ITEM_NAMES = [
    "环境识别",
    "素材授权",
    "输出目录隔离",
    "失败回滚",
    "证据留存",
    "人工签收",
    "试运行范围",
    "发布隔离",
]
VALID_STATUSES = {"pass", "pending", "block"}


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
        "whitelist_effective": False,
        "can_enter_real_render": False,
        "real_render": False,
        "publish": False,
        "requires_supervisor_confirmation": True,
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
        doc.get("whitelist_effective") is False
        and doc.get("can_enter_real_render") is False
        and doc.get("real_render") is False
        and doc.get("publish") is False
        and doc.get("requires_supervisor_confirmation") is True
        and flags.get("whitelist_effective") is False
        and flags.get("can_enter_real_render") is False
        and flags.get("real_render") is False
        and flags.get("publish") is False
        and flags.get("requires_supervisor_confirmation") is True
    )


def validate() -> dict[str, Any]:
    material_list = load_json(MATERIAL_LIST_LATEST)
    report = load_json(COMPLETENESS_REPORT_LATEST)
    gap_todo = load_json(GAP_TODO_LATEST)
    package = load_json(PACKAGE_LATEST)
    readonly_check = load_json(READONLY_CHECK_LATEST)
    checks: list[dict[str, Any]] = []

    for name, path in {
        "材料清单JSON": MATERIAL_LIST_LATEST,
        "材料清单MD": MATERIAL_LIST_MD_LATEST,
        "完整度判定报告JSON": COMPLETENESS_REPORT_LATEST,
        "完整度判定报告MD": COMPLETENESS_REPORT_MD_LATEST,
        "缺口补齐待办JSON": GAP_TODO_LATEST,
        "缺口补齐待办MD": GAP_TODO_MD_LATEST,
        "总包JSON": PACKAGE_LATEST,
        "只读检查JSON": READONLY_CHECK_LATEST,
    }.items():
        add_check(checks, f"{name}存在", path.exists(), str(path))

    material_items = material_list.get("材料清单", [])
    material_names = [item.get("name") for item in material_items]
    add_check(checks, "材料清单包含八项指定材料", all(name in material_names for name in REQUIRED_ITEM_NAMES), material_names)

    report_items = report.get("检查结果", [])
    report_names = [item.get("name") for item in report_items]
    add_check(checks, "完整度判定报告包含八项指定材料", all(name in report_names for name in REQUIRED_ITEM_NAMES), report_names)
    add_check(checks, "完整度判定报告每项状态为 pass/pending/block", all(item.get("status") in VALID_STATUSES for item in report_items), report_items)
    add_check(checks, "完整度判定报告每项含 pass/pending/block 字段", all({"pass", "pending", "block"}.issubset(item) for item in report_items), report_items)
    add_check(checks, "完整度判定报告显式禁止真实渲染", report.get("decision", {}).get("whitelist_effective") is False and report.get("decision", {}).get("can_enter_real_render") is False, report.get("decision", {}))

    todos = gap_todo.get("待办清单", [])
    add_check(checks, "缺口补齐待办列出人工材料且不自动补齐", gap_todo.get("自动补齐") is False and all(item.get("不得自动补齐") is True and item.get("需要人工提供或确认") for item in todos), todos)

    for label, doc in {
        "材料清单": material_list,
        "完整度判定报告": report,
        "缺口补齐待办": gap_todo,
        "总包": package,
        "只读检查": readonly_check,
    }.items():
        add_check(checks, f"{label} error_count=0", doc.get("error_count") == 0, doc.get("error_count"))
        add_check(checks, f"{label} whitelist_effective=false", doc.get("whitelist_effective") is False, doc.get("whitelist_effective"))
        add_check(checks, f"{label} can_enter_real_render=false", doc.get("can_enter_real_render") is False, doc.get("can_enter_real_render"))
        add_check(checks, f"{label} real_render=false", doc.get("real_render") is False, doc.get("real_render"))
        add_check(checks, f"{label} publish=false", doc.get("publish") is False, doc.get("publish"))
        add_check(checks, f"{label} requires_supervisor_confirmation=true", doc.get("requires_supervisor_confirmation") is True, doc.get("requires_supervisor_confirmation"))
        add_check(checks, f"{label} 红线字段一致", required_guard_state(doc), doc.get("readonly_flags_ascii", {}))

    errors = [item for item in checks if not item["通过"]]
    result = {
        "名称": "视频真实渲染白名单申请材料完整度判定包验收",
        "验收模式": "structure_and_guard_state_only",
        "检查结果": checks,
        "错误项": errors,
        "产物路径": {
            "材料清单": str(MATERIAL_LIST_LATEST),
            "完整度判定报告": str(COMPLETENESS_REPORT_LATEST),
            "缺口补齐待办": str(GAP_TODO_LATEST),
            "只读检查": str(READONLY_CHECK_LATEST),
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
