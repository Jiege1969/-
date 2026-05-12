# -*- coding: utf-8 -*-
"""
生成视频真实渲染白名单材料人工补齐模板与签收预演包。

本脚本只整理人工补齐模板和签收预演单；不自动补齐材料，不让白名单生效，不调用
MoneyPrinterTurbo，不执行 magick，不真实渲染，不生成真实视频，不上传发布，不接 n8n，
不改企业微信公共配置，不改总管面板，不改一键接续包，不重载服务。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
SOURCE_DATA_DIR = ROOT / "03数据" / "26真实渲染白名单申请材料完整度判定包"
DATA_DIR = ROOT / "03数据" / "27真实渲染白名单材料人工补齐模板与签收预演包"

PACKAGE_ID = "VIDEO-REAL-RENDER-WHITELIST-MATERIAL-MANUAL-FILL-SIGNOFF-PREVIEW-20260508-001"

SOURCE_MATERIAL_LIST = SOURCE_DATA_DIR / "视频真实渲染白名单申请材料清单_最新.json"
SOURCE_COMPLETENESS_REPORT = SOURCE_DATA_DIR / "视频真实渲染白名单申请材料完整度判定报告_最新.json"
SOURCE_GAP_TODO = SOURCE_DATA_DIR / "视频真实渲染白名单申请缺口补齐待办_最新.json"
SOURCE_READONLY_CHECK = SOURCE_DATA_DIR / "视频真实渲染白名单申请只读完整度检查_最新.json"

MATERIAL_TEMPLATE_LATEST = DATA_DIR / "视频真实渲染白名单材料人工补齐模板_最新.json"
MATERIAL_TEMPLATE_MD_LATEST = DATA_DIR / "视频真实渲染白名单材料人工补齐模板_最新.md"
SIGNOFF_PREVIEW_LATEST = DATA_DIR / "视频真实渲染白名单材料签收预演单_最新.json"
SIGNOFF_PREVIEW_MD_LATEST = DATA_DIR / "视频真实渲染白名单材料签收预演单_最新.md"
PACKAGE_LATEST = DATA_DIR / "视频真实渲染白名单材料人工补齐模板与签收预演包_最新.json"
PACKAGE_MD_LATEST = DATA_DIR / "视频真实渲染白名单材料人工补齐模板与签收预演包_最新.md"

REQUIRED_ITEMS = [
    {
        "item_id": "environment_identification",
        "name": "环境识别",
        "manual_fill_fields": ["候选环境标识", "机器范围", "账号范围", "依赖路径确认", "风险备注"],
        "acceptance_criteria": "人工确认真实渲染候选环境与当前机器/账号范围一致，且仅作为申请材料，不启用真实渲染。",
    },
    {
        "item_id": "material_authorization",
        "name": "素材授权",
        "manual_fill_fields": ["素材来源", "授权证明编号", "授权边界", "试运行可用范围", "授权人/确认人"],
        "acceptance_criteria": "人工提供或签收素材授权证明，脚本不得代填或推断授权。",
    },
    {
        "item_id": "output_directory_isolation",
        "name": "输出目录隔离",
        "manual_fill_fields": ["试运行输出目录", "生产目录隔离说明", "清理规则", "覆盖保护说明"],
        "acceptance_criteria": "人工确认试运行输出目录与生产/发布目录隔离，且不会覆盖既有产物。",
    },
    {
        "item_id": "failure_rollback",
        "name": "失败回滚",
        "manual_fill_fields": ["失败场景", "回滚动作", "责任人", "禁止删除范围", "复核方式"],
        "acceptance_criteria": "人工确认失败回滚边界；预演只记录回滚方案，不执行删除、重试真实渲染或恢复动作。",
    },
    {
        "item_id": "evidence_retention",
        "name": "证据留存",
        "manual_fill_fields": ["材料快照路径", "检查报告路径", "签收记录路径", "留存期限", "审计索引"],
        "acceptance_criteria": "人工确认留存期限和审计路径；脚本只写入第27包材料快照索引。",
    },
    {
        "item_id": "manual_signoff",
        "name": "人工签收",
        "manual_fill_fields": ["签收人", "签收角色", "签收意见", "签收时间", "总管确认编号"],
        "acceptance_criteria": "默认 signed=false；必须由总管另行确认，且本包不让白名单生效。",
    },
    {
        "item_id": "trial_scope",
        "name": "试运行范围",
        "manual_fill_fields": ["批次编号", "任务范围", "素材范围", "数量上限", "禁入条件"],
        "acceptance_criteria": "人工确认试运行范围，不默认扩展，不进入真实渲染。",
    },
    {
        "item_id": "publish_isolation",
        "name": "发布隔离",
        "manual_fill_fields": ["上传链路状态", "发布链路状态", "n8n链路状态", "企业微信公共配置状态", "总管面板状态"],
        "acceptance_criteria": "人工确认上传、发布、n8n、企业微信公共配置和总管面板链路均保持关闭或隔离。",
    },
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256_or_empty(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8-sig")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8-sig")


def guard_flags(generated_at: str, error_count: int = 0) -> dict[str, Any]:
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


def source_snapshot() -> dict[str, Any]:
    paths = {
        "第26包材料清单": SOURCE_MATERIAL_LIST,
        "第26包完整度判定报告": SOURCE_COMPLETENESS_REPORT,
        "第26包缺口补齐待办": SOURCE_GAP_TODO,
        "第26包只读完整度检查": SOURCE_READONLY_CHECK,
    }
    return {
        name: {"path": str(path), "exists": path.exists(), "sha256": sha256_or_empty(path)}
        for name, path in paths.items()
    }


def source_status_by_item() -> dict[str, dict[str, Any]]:
    report = load_json(SOURCE_COMPLETENESS_REPORT)
    items = report.get("检查结果", [])
    return {item.get("item_id"): item for item in items if item.get("item_id")}


def build_material_template(generated_at: str) -> dict[str, Any]:
    status_by_item = source_status_by_item()
    sections = []
    for item in REQUIRED_ITEMS:
        source_item = status_by_item.get(item["item_id"], {})
        sections.append(
            {
                **item,
                "source_package_26_status": source_item.get("status", "unknown"),
                "source_package_26_note": source_item.get("判定说明", ""),
                "manual_fill_required": True,
                "auto_fill": False,
                "script_may_complete_this_item": False,
                "signed": False,
                "field_values": {field: "" for field in item["manual_fill_fields"]},
                "human_operator_note": "",
                "supervisor_confirmation_note": "",
            }
        )
    result = {
        "名称": "视频真实渲染白名单材料人工补齐模板",
        "package_id": PACKAGE_ID,
        "基于包": "26真实渲染白名单申请材料完整度判定包",
        "模板用途": "供人工补齐或确认白名单申请材料；脚本不得自动补齐，且不得让白名单生效。",
        "覆盖材料": [item["name"] for item in sections],
        "材料补齐模板": sections,
        "source_package_26_snapshot": source_snapshot(),
    }
    result.update(guard_flags(generated_at))
    return result


def build_signoff_preview(generated_at: str, template: dict[str, Any]) -> dict[str, Any]:
    items = []
    for item in template["材料补齐模板"]:
        items.append(
            {
                "item_id": item["item_id"],
                "name": item["name"],
                "preview_status": "waiting_manual_fill",
                "signed": False,
                "signoff_person": "",
                "signoff_time": "",
                "signoff_opinion": "",
                "whitelist_effective_after_this_preview": False,
                "requires_supervisor_confirmation": True,
            }
        )
    result = {
        "名称": "视频真实渲染白名单材料签收预演单",
        "package_id": PACKAGE_ID,
        "预演模式": "readonly_signoff_preview_only",
        "signed": False,
        "whitelist_effective": False,
        "requires_supervisor_confirmation": True,
        "签收预演结论": "默认未签收；本预演单不构成批准，不让白名单生效，不能进入真实渲染。",
        "签收项": items,
        "人工签收总览": {
            "signed": False,
            "signoff_person": "",
            "signoff_time": "",
            "supervisor_confirmation_id": "",
            "whitelist_effective": False,
        },
    }
    result.update(guard_flags(generated_at))
    return result


def build_package(generated_at: str, template: dict[str, Any], signoff: dict[str, Any]) -> dict[str, Any]:
    result = {
        "名称": "视频真实渲染白名单材料人工补齐模板与签收预演包",
        "package_id": PACKAGE_ID,
        "产物": {
            "材料人工补齐模板JSON": str(MATERIAL_TEMPLATE_LATEST),
            "材料人工补齐模板MD": str(MATERIAL_TEMPLATE_MD_LATEST),
            "签收预演单JSON": str(SIGNOFF_PREVIEW_LATEST),
            "签收预演单MD": str(SIGNOFF_PREVIEW_MD_LATEST),
        },
        "覆盖材料": template["覆盖材料"],
        "签收预演摘要": {
            "signed": signoff["signed"],
            "whitelist_effective": signoff["whitelist_effective"],
            "requires_supervisor_confirmation": signoff["requires_supervisor_confirmation"],
        },
        "当前结论": "仅生成模板和签收预演；signed=false，whitelist_effective=false，can_enter_real_render=false。",
    }
    result.update(guard_flags(generated_at))
    return result


def material_template_md(doc: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染白名单材料人工补齐模板",
        "",
        f"- 生成时间：{doc['生成时间']}",
        "- auto_fill：false",
        "- signed：false",
        "- whitelist_effective：false",
        "- can_enter_real_render：false",
        "- requires_supervisor_confirmation：true",
        "",
        "| 材料项 | 第26包状态 | 人工补齐字段 | 验收口径 |",
        "| --- | --- | --- | --- |",
    ]
    for item in doc["材料补齐模板"]:
        fields = "、".join(item["manual_fill_fields"])
        lines.append(f"| {item['name']} | {item['source_package_26_status']} | {fields} | {item['acceptance_criteria']} |")
    return "\n".join(lines) + "\n"


def signoff_preview_md(doc: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染白名单材料签收预演单",
        "",
        f"- 生成时间：{doc['生成时间']}",
        "- signed：false",
        "- whitelist_effective：false",
        "- can_enter_real_render：false",
        "- real_render：false",
        "- publish：false",
        "- requires_supervisor_confirmation：true",
        "",
        "| 签收项 | 预演状态 | signed | whitelist_effective_after_this_preview |",
        "| --- | --- | --- | --- |",
    ]
    for item in doc["签收项"]:
        lines.append(
            f"| {item['name']} | {item['preview_status']} | {str(item['signed']).lower()} | "
            f"{str(item['whitelist_effective_after_this_preview']).lower()} |"
        )
    lines.extend(["", doc["签收预演结论"]])
    return "\n".join(lines) + "\n"


def package_md(doc: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染白名单材料人工补齐模板与签收预演包",
        "",
        f"- 生成时间：{doc['生成时间']}",
        f"- package_id：{doc['package_id']}",
        "- signed：false",
        "- whitelist_effective：false",
        "- can_enter_real_render：false",
        "- real_render：false",
        "- publish：false",
        "- requires_supervisor_confirmation：true",
        "",
        "## 产物",
        "",
    ]
    for name, path in doc["产物"].items():
        lines.append(f"- {name}：{path}")
    lines.extend(["", f"当前结论：{doc['当前结论']}"])
    return "\n".join(lines) + "\n"


def main() -> int:
    generated_at = now_text()
    stamp = stamp_text()
    template = build_material_template(generated_at)
    signoff = build_signoff_preview(generated_at, template)
    package = build_package(generated_at, template, signoff)

    write_json(DATA_DIR / f"视频真实渲染白名单材料人工补齐模板_{stamp}.json", template)
    write_json(MATERIAL_TEMPLATE_LATEST, template)
    write_text(MATERIAL_TEMPLATE_MD_LATEST, material_template_md(template))
    write_json(DATA_DIR / f"视频真实渲染白名单材料签收预演单_{stamp}.json", signoff)
    write_json(SIGNOFF_PREVIEW_LATEST, signoff)
    write_text(SIGNOFF_PREVIEW_MD_LATEST, signoff_preview_md(signoff))
    write_json(DATA_DIR / f"视频真实渲染白名单材料人工补齐模板与签收预演包_{stamp}.json", package)
    write_json(PACKAGE_LATEST, package)
    write_text(PACKAGE_MD_LATEST, package_md(package))

    print(
        json.dumps(
            {
                "package": str(PACKAGE_LATEST),
                "material_template": str(MATERIAL_TEMPLATE_LATEST),
                "signoff_preview": str(SIGNOFF_PREVIEW_LATEST),
                "error_count": package["error_count"],
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
