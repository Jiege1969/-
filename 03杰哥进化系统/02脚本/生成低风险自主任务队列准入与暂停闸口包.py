# -*- coding: utf-8 -*-
"""生成低风险自主任务队列准入与暂停闸口包。

本脚本只生成本地候选材料和闸口说明，不调用外部接口，不写正式规则，
不触发服务重载，不执行任何候选任务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "93低风险自主任务队列准入与暂停闸口包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险自主任务队列准入与暂停闸口包验收"

RULES_JSON = DATA_DIR / "低风险任务准入规则_最新.json"
RULES_MD = DATA_DIR / "低风险任务准入规则_最新.md"
QUEUE_JSON = DATA_DIR / "自主任务队列候选_最新.json"
QUEUE_MD = DATA_DIR / "自主任务队列候选_最新.md"
PAUSE_JSON = DATA_DIR / "暂停闸口_最新.json"
PAUSE_MD = DATA_DIR / "暂停闸口_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险自主任务队列准入与暂停闸口包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险自主任务队列准入与暂停闸口包_最新.md"
GEN_LOG = LOG_DIR / "low-risk-autonomous-task-queue-gate-generate-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_rules(generated_at: str) -> dict[str, Any]:
    allowed_categories = [
        {
            "id": "readonly_inspection",
            "name": "只读巡检",
            "admission": "只读取本地既有产物、脚本清单、日志摘要或状态文件，不访问外部系统。",
        },
        {
            "id": "artifact_integrity_check",
            "name": "产物完整性检查",
            "admission": "检查指定 JSON/MD/日志文件是否存在、字段是否齐全、格式是否可解析。",
        },
        {
            "id": "regression_acceptance",
            "name": "回归验收",
            "admission": "运行本地只读验收脚本或静态校验，禁止触发真实业务动作。",
        },
        {
            "id": "evidence_archive",
            "name": "证据归档",
            "admission": "整理本地证据索引、摘要和验收记录，只写入本包数据/日志目录。",
        },
        {
            "id": "status_package_refresh",
            "name": "状态包刷新",
            "admission": "刷新候选状态包或只读状态摘要，不改正式规则和运行中配置。",
        },
    ]
    excluded_actions = [
        "真实发企微",
        "n8n触发",
        "券商交易",
        "税局登录",
        "财税软件",
        "正式规则生效",
        "视频真实发布",
    ]
    return {
        "name": "低风险任务准入规则",
        "generated_at": generated_at,
        "purpose": "仅登记未来可自主执行的低风险候选任务，当前不执行任务。",
        "auto_execute": False,
        "default_enabled": False,
        "dry_run_only": True,
        "allowed_categories": allowed_categories,
        "excluded_actions": excluded_actions,
        "hard_red_lines": {
            "real_wecom_send": False,
            "trigger_n8n": False,
            "broker_connection": False,
            "trade_order": False,
            "tax_bureau_login": False,
            "finance_tax_software_connection": False,
            "write_formal_rule": False,
            "formal_rule_effective": False,
            "modify_supervisor_panel": False,
            "modify_one_click_continuation_package": False,
            "reload_service": False,
            "real_video_publish": False,
            "external_call": False,
        },
        "admission_must_all_true": [
            "candidate_only",
            "enabled_is_false",
            "dry_run_only_is_true",
            "no_external_call",
            "no_formal_rule_write",
            "no_service_reload",
            "no_real_send",
            "scope_is_readonly",
        ],
    }


def build_candidates(generated_at: str) -> list[dict[str, Any]]:
    base = {
        "enabled": False,
        "dry_run_only": True,
        "requires_supervisor_confirmation": False,
        "scope": "readonly_candidate_registration_only",
        "auto_execute": False,
        "external_call": False,
        "write_formal_rule": False,
        "reload_service": False,
        "real_send": False,
        "generated_at": generated_at,
    }
    candidates = [
        ("LRQ-001", "本地脚本清单只读巡检", "只读巡检", "扫描脚本目录文件名和存在性，输出候选巡检摘要。"),
        ("LRQ-002", "数据产物完整性检查", "产物完整性检查", "检查指定数据包 JSON/MD 是否存在且 JSON 可解析。"),
        ("LRQ-003", "验收日志完整性检查", "产物完整性检查", "检查验收日志目录中的最新日志是否包含 pass/error_count 字段。"),
        ("LRQ-004", "本地回归验收只读复核", "回归验收", "登记可运行的本地验收脚本候选，不自动执行真实业务动作。"),
        ("LRQ-005", "证据索引归档候选", "证据归档", "把已有本地证据文件路径登记为索引候选。"),
        ("LRQ-006", "状态包刷新候选", "状态包刷新", "生成只读状态摘要候选，不覆盖正式状态包。"),
        ("LRQ-007", "暂停词静态扫描候选", "只读巡检", "只读扫描候选文本是否包含暂停闸口词，命中时只登记待复核原因。"),
        ("LRQ-008", "候选队列字段一致性检查", "产物完整性检查", "检查候选项 enabled=false、dry_run_only=true 等准入字段。"),
        ("LRQ-009", "本地 Markdown 摘要刷新候选", "证据归档", "刷新本包内 Markdown 摘要，不触达外部系统。"),
    ]
    return [
        {
            **base,
            "id": item_id,
            "name": name,
            "category": category,
            "description": description,
            "allowed_write_scope": "仅允许写入本包数据目录和验收日志目录",
        }
        for item_id, name, category, description in candidates
    ]


def build_pause_gate(generated_at: str) -> dict[str, Any]:
    triggers = [
        {"id": "failure_detected", "name": "出现失败", "pause_required": True},
        {"id": "red_line_word_detected", "name": "红线词", "pause_required": True},
        {"id": "requires_reload", "name": "需重载", "pause_required": True},
        {"id": "formal_rule_impact", "name": "正式规则影响", "pause_required": True},
        {"id": "external_interface_required", "name": "外部接口需求", "pause_required": True},
    ]
    red_line_words = [
        "真实发企微",
        "企业微信真实发送",
        "n8n触发",
        "券商",
        "交易",
        "下单",
        "税局登录",
        "财税软件",
        "正式规则生效",
        "写正式规则",
        "重载",
        "reload",
        "外部接口",
        "视频真实发布",
    ]
    return {
        "name": "低风险自主任务队列暂停闸口",
        "generated_at": generated_at,
        "default": {"pause_required": False, "reason": "仅登记只读候选且未触发暂停条件"},
        "triggers": triggers,
        "red_line_words": red_line_words,
        "pause_decision": {
            "on_failure": True,
            "on_red_line_word": True,
            "on_requires_reload": True,
            "on_formal_rule_impact": True,
            "on_external_interface_required": True,
        },
        "when_paused": [
            "停止候选登记之外的动作",
            "不执行任务",
            "不调用外部接口",
            "不写正式规则",
            "不重载服务",
            "仅输出待人工复核说明",
        ],
    }


def rules_md(rules: dict[str, Any]) -> str:
    rows = [
        f"| {item['id']} | {item['name']} | {item['admission']} |"
        for item in rules["allowed_categories"]
    ]
    exclusions = "\n".join(f"- {item}" for item in rules["excluded_actions"])
    return "\n".join(
        [
            "# 低风险任务准入规则",
            "",
            f"- 生成时间：{rules['generated_at']}",
            "- 当前状态：只登记候选，不自动执行。",
            "- 默认：enabled=false，dry_run_only=true。",
            "",
            "## 允许类别",
            "",
            "| ID | 类别 | 准入说明 |",
            "| --- | --- | --- |",
            *rows,
            "",
            "## 明确排除",
            "",
            exclusions,
            "",
            "## 硬边界",
            "",
            "- 不真实发送企业微信，不触发 n8n，不接券商，不交易，不登录税局，不接财税软件。",
            "- 不自动转正式规则，不改总管面板，不改一键接续包，不重载服务。",
        ]
    )


def queue_md(candidates: list[dict[str, Any]]) -> str:
    rows = [
        f"| {item['id']} | {item['name']} | {item['category']} | {item['enabled']} | {item['dry_run_only']} | {item['requires_supervisor_confirmation']} |"
        for item in candidates
    ]
    return "\n".join(
        [
            "# 自主任务队列候选",
            "",
            "- 说明：本队列只登记未来可自主执行的低风险候选，当前不执行。",
            "- 全部候选默认 enabled=false、dry_run_only=true、requires_supervisor_confirmation=false，仅限只读。",
            "",
            "| ID | 名称 | 类别 | enabled | dry_run_only | requires_supervisor_confirmation |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def pause_md(pause_gate: dict[str, Any]) -> str:
    rows = [
        f"| {item['id']} | {item['name']} | {item['pause_required']} |"
        for item in pause_gate["triggers"]
    ]
    words = "、".join(pause_gate["red_line_words"])
    return "\n".join(
        [
            "# 暂停闸口",
            "",
            f"- 生成时间：{pause_gate['generated_at']}",
            "- 判定：出现失败、红线词、需重载、正式规则影响、外部接口需求时 pause_required=true。",
            "",
            "| ID | 触发条件 | pause_required |",
            "| --- | --- | --- |",
            *rows,
            "",
            f"- 红线词：{words}",
        ]
    )


def package_md(package: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 低风险自主任务队列准入与暂停闸口包",
            "",
            f"- 生成时间：{package['generated_at']}",
            f"- 候选数：{package['candidate_count']}",
            "- 结论：只登记候选，不真实执行，不调用外部接口，不写正式规则，不重载服务。",
            "",
            "## 输出",
            "",
            *[f"- {name}: {path}" for name, path in package["outputs"].items()],
        ]
    )


def main() -> int:
    generated_at = now()
    rules = build_rules(generated_at)
    candidates = build_candidates(generated_at)
    pause_gate = build_pause_gate(generated_at)
    package = {
        "name": "低风险自主任务队列准入与暂停闸口包",
        "generated_at": generated_at,
        "status": "candidate_registration_only",
        "auto_execute": False,
        "external_call": False,
        "write_formal_rule": False,
        "reload_service": False,
        "real_send": False,
        "candidate_count": len(candidates),
        "outputs": {
            "rules_json": str(RULES_JSON),
            "rules_md": str(RULES_MD),
            "queue_json": str(QUEUE_JSON),
            "queue_md": str(QUEUE_MD),
            "pause_json": str(PAUSE_JSON),
            "pause_md": str(PAUSE_MD),
            "package_json": str(PACKAGE_JSON),
            "package_md": str(PACKAGE_MD),
        },
    }

    write_json(RULES_JSON, rules)
    write_text(RULES_MD, rules_md(rules))
    write_json(QUEUE_JSON, {"name": "自主任务队列候选", "generated_at": generated_at, "candidates": candidates})
    write_text(QUEUE_MD, queue_md(candidates))
    write_json(PAUSE_JSON, pause_gate)
    write_text(PAUSE_MD, pause_md(pause_gate))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))
    write_json(
        GEN_LOG,
        {
            "name": "低风险自主任务队列准入与暂停闸口包生成日志",
            "generated_at": generated_at,
            "pass": True,
            "error_count": 0,
            "outputs": package["outputs"],
        },
    )
    print(json.dumps({"status": "ready", "candidate_count": len(candidates), "output": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
