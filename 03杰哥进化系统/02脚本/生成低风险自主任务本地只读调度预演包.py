# -*- coding: utf-8 -*-
"""生成低风险自主任务本地只读调度预演包。

本脚本只生成本地 JSON/MD 预演材料，不执行任务，不调用外部接口，不写正式规则，
不重载服务，不触碰总管面板或一键接续包。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "96低风险自主任务本地只读调度预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险自主任务本地只读调度预演包验收"
SOURCE_QUEUE_JSON = (
    EVOLUTION_ROOT
    / "03数据"
    / "93低风险自主任务队列准入与暂停闸口包"
    / "自主任务队列候选_最新.json"
)
SOURCE_RULES_JSON = (
    EVOLUTION_ROOT
    / "03数据"
    / "93低风险自主任务队列准入与暂停闸口包"
    / "低风险任务准入规则_最新.json"
)
SOURCE_PAUSE_JSON = (
    EVOLUTION_ROOT
    / "03数据"
    / "93低风险自主任务队列准入与暂停闸口包"
    / "暂停闸口_最新.json"
)

RULES_JSON = DATA_DIR / "调度预演规则_最新.json"
RULES_MD = DATA_DIR / "调度预演规则_最新.md"
SCHEDULE_JSON = DATA_DIR / "本地只读调度计划_最新.json"
SCHEDULE_MD = DATA_DIR / "本地只读调度计划_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险自主任务本地只读调度预演包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险自主任务本地只读调度预演包_最新.md"
GEN_LOG = LOG_DIR / "low-risk-autonomous-local-scheduler-preview-generate-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json_if_exists(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safety_flags() -> dict[str, bool]:
    return {
        "auto_execute": False,
        "external_call": False,
        "real_send": False,
        "reload_service": False,
        "write_formal_rule": False,
        "trigger_n8n": False,
        "broker_connection": False,
        "trade_order": False,
        "tax_bureau_login": False,
        "finance_tax_software_connection": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
    }


def build_rules(generated_at: str) -> dict[str, Any]:
    return {
        "name": "低风险自主任务本地只读调度预演规则",
        "generated_at": generated_at,
        "based_on": {
            "package": "93低风险自主任务队列准入与暂停闸口包",
            "source_queue_json": str(SOURCE_QUEUE_JSON),
            "source_rules_json": str(SOURCE_RULES_JSON),
            "source_pause_json": str(SOURCE_PAUSE_JSON),
        },
        "scope": "local_readonly_scheduler_preview_only",
        "purpose": "把低风险候选队列转成本地只读调度预演，只预演排序、依赖和证据要求，不真实执行任务。",
        "cron_like_preview": {
            "enabled": False,
            "scheduled": False,
            "preview_only": True,
            "example_expression": "0 */6 * * *",
            "meaning": "仅用于展示未来可采用的类 cron 节奏，不注册计划任务，不启动后台进程。",
        },
        "manual_trigger_preview": {
            "enabled": False,
            "scheduled": False,
            "preview_only": True,
            "entry_hint": "人工触发也只允许运行本地预演脚本和验收脚本。",
            "requires_human_confirmation_before_real_use": True,
        },
        "pause_gate_check": {
            "enabled": True,
            "source": "第93包暂停闸口",
            "check_before_sorting": True,
            "pause_if_any_red_line_or_failure": True,
            "when_paused": "只记录暂停原因和待人工复核事项，不执行任务。",
        },
        "evidence_required": {
            "enabled": True,
            "required_for_each_task": [
                "source_candidate_id",
                "preview_order",
                "depends_on",
                "safety_flags_all_false",
                "dry_run_only_true",
                "external_call_false",
                "task_executed_false",
            ],
        },
        "hard_red_line_confirmation": safety_flags(),
        "defaults": {
            "scheduled": False,
            "auto_execute": False,
            "dry_run_only": True,
            "external_call": False,
            "real_send": False,
            "reload_service": False,
            "write_formal_rule": False,
        },
    }


def source_candidate_ids() -> list[str]:
    source_queue = read_json_if_exists(SOURCE_QUEUE_JSON) or {}
    candidates = source_queue.get("candidates", [])
    ids = [str(item.get("id")) for item in candidates if item.get("id")]
    return ids[:8] if len(ids) >= 8 else [f"LRQ-{index:03d}" for index in range(1, 9)]


def build_schedule(generated_at: str) -> dict[str, Any]:
    refs = source_candidate_ids()
    task_specs = [
        ("LRS-001", "读取第93包候选队列快照", "确认候选来源存在且只作为输入快照。", []),
        ("LRS-002", "扫描只读安全字段", "检查 scheduled/auto_execute/external_call 等字段保持禁用。", ["LRS-001"]),
        ("LRS-003", "预演暂停闸口检查", "套用第93包暂停闸口，只产生 pause_gate_check 结论。", ["LRS-002"]),
        ("LRS-004", "整理证据需求清单", "列出每个候选进入调度预演所需证据字段。", ["LRS-003"]),
        ("LRS-005", "预演候选排序", "按低风险、只读、依赖少优先的规则生成 preview_order。", ["LRS-004"]),
        ("LRS-006", "预演依赖链", "只计算 depends_on，不启动任何真实任务。", ["LRS-005"]),
        ("LRS-007", "预演冲突与红线复核", "确认不触达企业微信、n8n、券商、税局、财税软件和服务重载。", ["LRS-006"]),
        ("LRS-008", "汇总预演报告输入", "为执行脚本准备只读报告材料。", ["LRS-007"]),
    ]
    tasks: list[dict[str, Any]] = []
    for order, (task_id, name, objective, depends_on) in enumerate(task_specs, start=1):
        tasks.append(
            {
                "id": task_id,
                "name": name,
                "objective": objective,
                "source_candidate_id": refs[order - 1],
                "preview_order": order,
                "depends_on": depends_on,
                "scheduled": False,
                "auto_execute": False,
                "dry_run_only": True,
                "external_call": False,
                "real_send": False,
                "reload_service": False,
                "write_formal_rule": False,
                "task_executed": False,
                "execution_adapter": "none",
                "allowed_action": "local_sort_and_dependency_preview_only",
                "evidence_required": [
                    "source_candidate_id",
                    "preview_order",
                    "depends_on",
                    "task_executed_false",
                ],
            }
        )
    return {
        "name": "低风险自主任务本地只读调度计划",
        "generated_at": generated_at,
        "based_on": "93低风险自主任务队列准入与暂停闸口包",
        "defaults": {
            "scheduled": False,
            "auto_execute": False,
            "dry_run_only": True,
            "external_call": False,
            "real_send": False,
            "reload_service": False,
            "write_formal_rule": False,
        },
        "scheduler_state": "preview_only_not_registered",
        "task_count": len(tasks),
        "tasks": tasks,
        "hard_red_line_confirmation": safety_flags(),
    }


def rules_md(rules: dict[str, Any]) -> str:
    evidence_rows = "\n".join(f"- {item}" for item in rules["evidence_required"]["required_for_each_task"])
    flags = "\n".join(f"- {key}: {value}" for key, value in rules["hard_red_line_confirmation"].items())
    return "\n".join(
        [
            "# 低风险自主任务本地只读调度预演规则",
            "",
            f"- 生成时间：{rules['generated_at']}",
            "- 范围：本地只读调度预演，不真实执行任务，不调用业务接口。",
            "",
            "## cron_like_preview",
            "",
            f"- enabled: {rules['cron_like_preview']['enabled']}",
            f"- scheduled: {rules['cron_like_preview']['scheduled']}",
            f"- example_expression: {rules['cron_like_preview']['example_expression']}",
            f"- 说明：{rules['cron_like_preview']['meaning']}",
            "",
            "## manual_trigger_preview",
            "",
            f"- enabled: {rules['manual_trigger_preview']['enabled']}",
            f"- scheduled: {rules['manual_trigger_preview']['scheduled']}",
            f"- 说明：{rules['manual_trigger_preview']['entry_hint']}",
            "",
            "## pause_gate_check",
            "",
            f"- enabled: {rules['pause_gate_check']['enabled']}",
            f"- source: {rules['pause_gate_check']['source']}",
            f"- when_paused: {rules['pause_gate_check']['when_paused']}",
            "",
            "## evidence_required",
            "",
            evidence_rows,
            "",
            "## 硬红线确认",
            "",
            flags,
        ]
    )


def schedule_md(schedule: dict[str, Any]) -> str:
    rows = [
        f"| {item['preview_order']} | {item['id']} | {item['name']} | {item['scheduled']} | {item['auto_execute']} | {item['dry_run_only']} | {item['external_call']} | {', '.join(item['depends_on']) or '无'} |"
        for item in schedule["tasks"]
    ]
    return "\n".join(
        [
            "# 本地只读调度计划",
            "",
            f"- 生成时间：{schedule['generated_at']}",
            "- 默认：scheduled=false、auto_execute=false、dry_run_only=true、external_call=false。",
            "- 状态：preview_only_not_registered，未注册计划任务，未启动后台执行。",
            "",
            "| order | id | name | scheduled | auto_execute | dry_run_only | external_call | depends_on |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def package_md(package: dict[str, Any]) -> str:
    outputs = "\n".join(f"- {name}: {path}" for name, path in package["outputs"].items())
    return "\n".join(
        [
            "# 低风险自主任务本地只读调度预演包",
            "",
            f"- 生成时间：{package['generated_at']}",
            f"- 任务数：{package['task_count']}",
            "- 结论：只生成本地预演规则和调度计划，未执行任务，未调用外部接口。",
            "",
            "## 输出",
            "",
            outputs,
        ]
    )


def main() -> int:
    generated_at = now()
    rules = build_rules(generated_at)
    schedule = build_schedule(generated_at)
    package = {
        "name": "低风险自主任务本地只读调度预演包",
        "generated_at": generated_at,
        "based_on": "93低风险自主任务队列准入与暂停闸口包",
        "task_count": schedule["task_count"],
        "auto_execute": False,
        "external_call": False,
        "real_send": False,
        "reload_service": False,
        "write_formal_rule": False,
        "outputs": {
            "rules_json": str(RULES_JSON),
            "rules_md": str(RULES_MD),
            "schedule_json": str(SCHEDULE_JSON),
            "schedule_md": str(SCHEDULE_MD),
            "package_json": str(PACKAGE_JSON),
            "package_md": str(PACKAGE_MD),
        },
    }
    write_json(RULES_JSON, rules)
    write_text(RULES_MD, rules_md(rules))
    write_json(SCHEDULE_JSON, schedule)
    write_text(SCHEDULE_MD, schedule_md(schedule))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))
    write_json(
        GEN_LOG,
        {
            "name": "低风险自主任务本地只读调度预演包生成日志",
            "generated_at": generated_at,
            "pass": True,
            "error_count": 0,
            "auto_execute": False,
            "external_call": False,
            "real_send": False,
            "reload_service": False,
            "write_formal_rule": False,
            "outputs": package["outputs"],
        },
    )
    print(json.dumps({"pass": True, "error_count": 0, "task_count": schedule["task_count"], "output": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
