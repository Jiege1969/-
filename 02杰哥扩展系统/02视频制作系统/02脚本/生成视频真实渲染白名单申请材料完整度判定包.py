# -*- coding: utf-8 -*-
"""
生成视频真实渲染白名单申请材料完整度判定包。

本脚本只整理申请材料完整度，不调用 MoneyPrinterTurbo，不执行 magick，
不真实渲染，不生成真实视频，不上传发布，不接 n8n，不修改公共配置或服务。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = ROOT / "03数据" / "26真实渲染白名单申请材料完整度判定包"

PACKAGE_ID = "VIDEO-REAL-RENDER-WHITELIST-APPLICATION-COMPLETENESS-20260508-001"

MATERIAL_LIST_LATEST = DATA_DIR / "视频真实渲染白名单申请材料清单_最新.json"
MATERIAL_LIST_MD_LATEST = DATA_DIR / "视频真实渲染白名单申请材料清单_最新.md"
COMPLETENESS_REPORT_LATEST = DATA_DIR / "视频真实渲染白名单申请材料完整度判定报告_最新.json"
COMPLETENESS_REPORT_MD_LATEST = DATA_DIR / "视频真实渲染白名单申请材料完整度判定报告_最新.md"
GAP_TODO_LATEST = DATA_DIR / "视频真实渲染白名单申请缺口补齐待办_最新.json"
GAP_TODO_MD_LATEST = DATA_DIR / "视频真实渲染白名单申请缺口补齐待办_最新.md"
PACKAGE_LATEST = DATA_DIR / "视频真实渲染白名单申请材料完整度判定包_最新.json"
PACKAGE_MD_LATEST = DATA_DIR / "视频真实渲染白名单申请材料完整度判定包_最新.md"

SOURCE_CANDIDATES = {
    "environment_identification": [
        ROOT / "03数据" / "19真实渲染环境只读识别增强包" / "视频真实渲染环境只读识别增强包_最新.json",
        ROOT / "03数据" / "20真实渲染环境候选路径矩阵与安装缺口清单" / "视频真实渲染环境候选路径矩阵与安装缺口清单包_最新.json",
        ROOT / "03数据" / "21真实渲染启用前总闸口与人工放行申请包" / "视频真实渲染启用前总闸口与人工放行申请包_最新.json",
    ],
    "material_authorization": [
        ROOT / "03数据" / "22真实渲染人工放行材料完整性复核与试运行禁入包" / "视频真实渲染人工放行材料完整性复核_最新.json",
        ROOT / "03数据" / "23真实渲染试运行白名单与回滚预案草案包" / "视频真实渲染试运行白名单申请草案_最新.json",
    ],
    "output_directory_isolation": [
        ROOT / "03数据" / "21真实渲染启用前总闸口与人工放行申请包" / "视频真实渲染启用前总闸口与人工放行申请包_最新.json",
        ROOT / "03数据" / "24真实渲染试运行批次预检与白名单未生效闸口包" / "视频真实渲染试运行批次预检_最新.json",
    ],
    "failure_rollback": [
        ROOT / "03数据" / "25真实渲染试运行批次失败回滚与证据留存包" / "视频真实渲染试运行批次失败回滚动作清单_最新.json",
        ROOT / "03数据" / "23真实渲染试运行白名单与回滚预案草案包" / "视频真实渲染试运行回滚预案草案_最新.json",
    ],
    "evidence_retention": [
        ROOT / "03数据" / "25真实渲染试运行批次失败回滚与证据留存包" / "视频真实渲染试运行批次失败证据留存索引_最新.json",
        ROOT / "03数据" / "24真实渲染试运行批次预检与白名单未生效闸口包" / "视频真实渲染试运行批次只读预检报告_最新.json",
    ],
    "manual_signoff": [
        ROOT / "03数据" / "22真实渲染人工放行材料完整性复核与试运行禁入包" / "视频真实渲染下一步人工补齐卡_最新.json",
        ROOT / "03数据" / "24真实渲染试运行批次预检与白名单未生效闸口包" / "视频真实渲染试运行批次人工签收清单_最新.json",
    ],
    "trial_scope": [
        ROOT / "03数据" / "24真实渲染试运行批次预检与白名单未生效闸口包" / "视频真实渲染试运行批次预检_最新.json",
        ROOT / "03数据" / "23真实渲染试运行白名单与回滚预案草案包" / "视频真实渲染试运行白名单草案_最新.json",
    ],
    "publish_isolation": [
        ROOT / "03数据" / "22真实渲染人工放行材料完整性复核与试运行禁入包" / "视频真实渲染试运行禁入清单_最新.json",
        ROOT / "03数据" / "24真实渲染试运行批次预检与白名单未生效闸口包" / "视频真实渲染白名单未生效闸口_最新.json",
    ],
}

REQUIRED_ITEMS = [
    {
        "item_id": "environment_identification",
        "name": "环境识别",
        "required_evidence": "只读识别真实渲染候选环境、依赖、路径、未启用状态和风险说明。",
        "human_requirement": "人工确认候选环境与当前机器/账号范围一致。",
    },
    {
        "item_id": "material_authorization",
        "name": "素材授权",
        "required_evidence": "素材来源、授权边界、可用于试运行的低风险素材说明。",
        "human_requirement": "人工提供或签收授权证明，不由脚本补齐。",
    },
    {
        "item_id": "output_directory_isolation",
        "name": "输出目录隔离",
        "required_evidence": "试运行输出目录与生产/发布目录隔离，且不覆盖既有产物。",
        "human_requirement": "人工确认隔离目录和清理规则。",
    },
    {
        "item_id": "failure_rollback",
        "name": "失败回滚",
        "required_evidence": "失败场景、只读回滚动作、禁止删除和禁止重试真实渲染说明。",
        "human_requirement": "人工确认回滚边界和责任人。",
    },
    {
        "item_id": "evidence_retention",
        "name": "证据留存",
        "required_evidence": "材料快照、检查报告、签收状态、留存期限和索引。",
        "human_requirement": "人工确认留存期限与审计口径。",
    },
    {
        "item_id": "manual_signoff",
        "name": "人工签收",
        "required_evidence": "审批人、签收动作、拒绝/待补齐状态和不可自动生效说明。",
        "human_requirement": "人工最终签收；当前不得让白名单生效。",
    },
    {
        "item_id": "trial_scope",
        "name": "试运行范围",
        "required_evidence": "试运行批次、任务、素材范围、数量上限和禁入条件。",
        "human_requirement": "人工确认试运行范围，不默认扩展。",
    },
    {
        "item_id": "publish_isolation",
        "name": "发布隔离",
        "required_evidence": "上传、发布、n8n、企业微信公共配置和总管面板均保持隔离关闭。",
        "human_requirement": "人工确认发布链路仍关闭。",
    },
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


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


def source_state(path: Path) -> dict[str, Any]:
    doc = load_json(path)
    return {
        "path": str(path),
        "exists": path.exists(),
        "sha256": sha256_or_empty(path),
        "error_count": doc.get("error_count"),
        "whitelist_effective": doc.get("whitelist_effective"),
        "can_enter_real_render": doc.get("can_enter_real_render"),
        "real_render": doc.get("real_render"),
        "publish": doc.get("publish"),
        "requires_supervisor_confirmation": doc.get("requires_supervisor_confirmation"),
    }


def evidence_score(paths: list[Path]) -> tuple[str, list[dict[str, Any]], str]:
    sources = [source_state(path) for path in paths]
    existing = [item for item in sources if item["exists"]]
    if not existing:
        return "block", sources, "未找到可引用材料，需人工提供。"
    if len(existing) < len(paths):
        return "pending", sources, "已有部分材料，但仍需人工确认或补齐。"
    return "pending", sources, "已有引用材料；仍需人工签收后才能进入下一阶段。"


def build_material_list(generated_at: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for item in REQUIRED_ITEMS:
        status, sources, reason = evidence_score(SOURCE_CANDIDATES[item["item_id"]])
        items.append(
            {
                **item,
                "status": status,
                "completion_status": status,
                "auto_fill": False,
                "human_confirm_required": True,
                "source_candidates": sources,
                "判定说明": reason,
            }
        )
    result = {
        "名称": "视频真实渲染白名单申请材料清单",
        "package_id": PACKAGE_ID,
        "材料项数量": len(items),
        "材料清单": items,
        "用途": "只判定白名单申请材料完整度，为未来人工决定做准备；当前不得让白名单生效。",
    }
    result.update(guard_flags(generated_at))
    return result


def build_report(generated_at: str, material_list: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for item in material_list["材料清单"]:
        checks.append(
            {
                "item_id": item["item_id"],
                "name": item["name"],
                "status": item["status"],
                "pass": item["status"] == "pass",
                "pending": item["status"] == "pending",
                "block": item["status"] == "block",
                "human_confirm_required": item["human_confirm_required"],
                "判定说明": item["判定说明"],
            }
        )
    summary = {
        "pass_count": sum(1 for item in checks if item["status"] == "pass"),
        "pending_count": sum(1 for item in checks if item["status"] == "pending"),
        "block_count": sum(1 for item in checks if item["status"] == "block"),
    }
    result = {
        "名称": "视频真实渲染白名单申请材料完整度判定报告",
        "package_id": PACKAGE_ID,
        "判定模式": "readonly_completeness_only",
        "完整度结论": "待人工补齐或确认；白名单未生效，不能进入真实渲染。",
        "检查结果": checks,
        "统计": summary,
        "decision": {
            "whitelist_effective": False,
            "can_enter_real_render": False,
            "reason": "本包只做申请材料完整度判定，不代表批准，不自动补齐材料，不启用白名单。",
        },
    }
    result.update(guard_flags(generated_at))
    return result


def build_gap_todo(generated_at: str, report: dict[str, Any], material_list: dict[str, Any]) -> dict[str, Any]:
    item_by_id = {item["item_id"]: item for item in material_list["材料清单"]}
    todos: list[dict[str, Any]] = []
    for check in report["检查结果"]:
        if check["status"] in {"pending", "block"}:
            item = item_by_id[check["item_id"]]
            todos.append(
                {
                    "todo_id": f"TODO-{len(todos) + 1:02d}",
                    "item_id": item["item_id"],
                    "name": item["name"],
                    "status": check["status"],
                    "需要人工提供或确认": item["human_requirement"],
                    "不得自动补齐": True,
                    "补齐后动作": "重新运行只读完整度检查；仍需总管人工确认，且不得自动生效白名单。",
                }
            )
    result = {
        "名称": "视频真实渲染白名单申请缺口补齐待办",
        "package_id": PACKAGE_ID,
        "待办数量": len(todos),
        "待办清单": todos,
        "自动补齐": False,
    }
    result.update(guard_flags(generated_at))
    return result


def build_package(generated_at: str, material_list: dict[str, Any], report: dict[str, Any], gap_todo: dict[str, Any]) -> dict[str, Any]:
    result = {
        "名称": "视频真实渲染白名单申请材料完整度判定包",
        "package_id": PACKAGE_ID,
        "产物": {
            "材料清单JSON": str(MATERIAL_LIST_LATEST),
            "材料清单MD": str(MATERIAL_LIST_MD_LATEST),
            "完整度判定报告JSON": str(COMPLETENESS_REPORT_LATEST),
            "完整度判定报告MD": str(COMPLETENESS_REPORT_MD_LATEST),
            "缺口补齐待办JSON": str(GAP_TODO_LATEST),
            "缺口补齐待办MD": str(GAP_TODO_MD_LATEST),
        },
        "材料清单摘要": {
            "材料项数量": material_list["材料项数量"],
            "状态": {item["name"]: item["status"] for item in material_list["材料清单"]},
        },
        "完整度统计": report["统计"],
        "待办数量": gap_todo["待办数量"],
        "当前结论": "whitelist_effective=false，can_enter_real_render=false；等待人工补齐和总管确认。",
    }
    result.update(guard_flags(generated_at))
    return result


def material_list_md(doc: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染白名单申请材料清单",
        "",
        f"- 生成时间：{doc['生成时间']}",
        "- whitelist_effective：false",
        "- can_enter_real_render：false",
        "- requires_supervisor_confirmation：true",
        "",
        "| 材料项 | 状态 | 人工要求 |",
        "| --- | --- | --- |",
    ]
    for item in doc["材料清单"]:
        lines.append(f"| {item['name']} | {item['status']} | {item['human_requirement']} |")
    return "\n".join(lines) + "\n"


def report_md(doc: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染白名单申请材料完整度判定报告",
        "",
        f"- 生成时间：{doc['生成时间']}",
        f"- error_count：{doc['error_count']}",
        "- whitelist_effective：false",
        "- can_enter_real_render：false",
        "- real_render：false",
        "- publish：false",
        "",
        "| 材料项 | pass | pending | block |",
        "| --- | --- | --- | --- |",
    ]
    for item in doc["检查结果"]:
        lines.append(f"| {item['name']} | {str(item['pass']).lower()} | {str(item['pending']).lower()} | {str(item['block']).lower()} |")
    lines.extend(["", f"结论：{doc['完整度结论']}"])
    return "\n".join(lines) + "\n"


def todo_md(doc: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染白名单申请缺口补齐待办",
        "",
        f"- 生成时间：{doc['生成时间']}",
        "- 自动补齐：false",
        "- whitelist_effective：false",
        "- can_enter_real_render：false",
        "",
    ]
    for item in doc["待办清单"]:
        lines.append(f"- {item['todo_id']}｜{item['name']}｜{item['status']}｜{item['需要人工提供或确认']}")
    return "\n".join(lines) + "\n"


def package_md(doc: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染白名单申请材料完整度判定包",
        "",
        f"- 生成时间：{doc['生成时间']}",
        f"- package_id：{doc['package_id']}",
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
    material_list = build_material_list(generated_at)
    report = build_report(generated_at, material_list)
    gap_todo = build_gap_todo(generated_at, report, material_list)
    package = build_package(generated_at, material_list, report, gap_todo)
    stamp = stamp_text()

    write_json(DATA_DIR / f"视频真实渲染白名单申请材料清单_{stamp}.json", material_list)
    write_json(MATERIAL_LIST_LATEST, material_list)
    write_text(MATERIAL_LIST_MD_LATEST, material_list_md(material_list))
    write_json(DATA_DIR / f"视频真实渲染白名单申请材料完整度判定报告_{stamp}.json", report)
    write_json(COMPLETENESS_REPORT_LATEST, report)
    write_text(COMPLETENESS_REPORT_MD_LATEST, report_md(report))
    write_json(DATA_DIR / f"视频真实渲染白名单申请缺口补齐待办_{stamp}.json", gap_todo)
    write_json(GAP_TODO_LATEST, gap_todo)
    write_text(GAP_TODO_MD_LATEST, todo_md(gap_todo))
    write_json(DATA_DIR / f"视频真实渲染白名单申请材料完整度判定包_{stamp}.json", package)
    write_json(PACKAGE_LATEST, package)
    write_text(PACKAGE_MD_LATEST, package_md(package))

    print(
        json.dumps(
            {
                "package": str(PACKAGE_LATEST),
                "material_list": str(MATERIAL_LIST_LATEST),
                "completeness_report": str(COMPLETENESS_REPORT_LATEST),
                "gap_todo": str(GAP_TODO_LATEST),
                "error_count": package["error_count"],
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
