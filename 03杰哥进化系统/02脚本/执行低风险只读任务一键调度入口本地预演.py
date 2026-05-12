# -*- coding: utf-8 -*-
"""执行低风险只读任务一键调度入口本地预演。

本脚本只解析入口草案和本地预演配置，并生成禁用态计划预览；不会执行任务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "99低风险只读任务一键调度入口草案包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读任务一键调度入口草案包验收"

ENTRY_JSON = DATA_DIR / "一键调度入口草案_最新.json"
CONFIG_JSON = DATA_DIR / "本地预演配置_最新.json"
REPORT_JSON = DATA_DIR / "一键入口本地预演报告_最新.json"
REPORT_MD = DATA_DIR / "一键入口本地预演报告_最新.md"
RUN_LOG = LOG_DIR / "low-risk-readonly-one-click-scheduler-entry-run-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def require_false(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not False:
        errors.append(f"{scope}.{key} 必须为 false")


def require_true(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not True:
        errors.append(f"{scope}.{key} 必须为 true")


def validate_disabled_task(task: dict[str, Any], errors: list[str]) -> None:
    scope = str(task.get("id", "<missing>"))
    require_false(errors, task, "enabled", scope)
    require_true(errors, task, "preview_only", scope)
    for key in [
        "auto_execute",
        "external_call",
        "real_send",
        "real_wecom_send",
        "trigger_n8n",
        "broker_connection",
        "trade_order",
        "tax_bureau_login",
        "finance_tax_software_connection",
        "write_formal_rule",
        "reload_service",
        "modify_supervisor_panel",
        "modify_one_click_pack",
        "task_executed",
    ]:
        require_false(errors, task, key, scope)
    if task.get("execution_adapter") != "none":
        errors.append(f"{scope}.execution_adapter 必须为 none")


def build_report_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['preview_order']} | {item['id']} | {item['name']} | {item['enabled']} | {item['planned']} | {item['task_executed']} | {item['plan_action']} |"
        for item in report["generated_plan"]["items"]
    ]
    return "\n".join(
        [
            "# 一键入口本地预演报告",
            "",
            f"- 生成时间: {report['generated_at']}",
            f"- pass: {report['pass']}",
            f"- error_count: {report['error_count']}",
            "- 确认: 只做入口解析和计划生成，未执行任务。",
            f"- parsed_entry: {report['parsed_entry']}",
            f"- generated_plan_only: {report['generated_plan_only']}",
            f"- executed_task_count: {report['executed_task_count']}",
            "",
            "| order | id | name | enabled | planned | task_executed | plan_action |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def main() -> int:
    generated_at = now()
    errors: list[str] = []
    for path in [ENTRY_JSON, CONFIG_JSON]:
        if not path.exists():
            errors.append(f"缺少输入文件: {path}")

    entry = read_json(ENTRY_JSON) if ENTRY_JSON.exists() else {}
    config = read_json(CONFIG_JSON) if CONFIG_JSON.exists() else {"tasks": []}
    defaults = config.get("defaults", {})
    require_false(errors, defaults, "enabled", "config.defaults")
    require_true(errors, defaults, "preview_only", "config.defaults")
    require_false(errors, defaults, "auto_execute", "config.defaults")
    require_false(errors, defaults, "external_call", "config.defaults")

    tasks = sorted(config.get("tasks", []), key=lambda item: item.get("preview_order", 9999))
    known_ids = {task.get("id") for task in tasks}
    plan_items: list[dict[str, Any]] = []
    for task in tasks:
        validate_disabled_task(task, errors)
        depends_on = list(task.get("depends_on", []))
        missing_dependencies = [dep for dep in depends_on if dep not in known_ids]
        if missing_dependencies:
            errors.append(f"{task.get('id', '<missing>')} 缺少依赖任务: {missing_dependencies}")
        plan_items.append(
            {
                "preview_order": task.get("preview_order"),
                "id": task.get("id"),
                "name": task.get("name"),
                "enabled": task.get("enabled"),
                "planned": False,
                "depends_on": depends_on,
                "dependency_ready": not missing_dependencies,
                "task_executed": False,
                "plan_action": "not_planned_because_enabled_false",
                "adapter_invoked": False,
            }
        )

    if len(tasks) < 8:
        errors.append("本地预演配置任务数不足 8 个")
    if entry.get("entry_name") != "低风险只读任务一键调度入口草案":
        errors.append("入口名称不符合草案要求")

    report = {
        "name": "低风险只读任务一键调度入口本地预演报告",
        "generated_at": generated_at,
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "confirmation": "只做入口解析和计划生成，未执行任务，未调用外部系统。",
        "parsed_entry": True,
        "generated_plan_only": True,
        "preview_only": True,
        "tasks_executed": False,
        "executed_task_count": 0,
        "adapter_invoked": False,
        "auto_execute": False,
        "external_call": False,
        "real_send": False,
        "reload_service": False,
        "modify_supervisor_panel": False,
        "modify_one_click_pack": False,
        "generated_plan": {
            "planned_task_count": 0,
            "skipped_disabled_count": len(tasks),
            "items": plan_items,
            "dependency_edges": [
                {"from": dep, "to": item["id"]}
                for item in plan_items
                for dep in item["depends_on"]
            ],
        },
    }
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, build_report_md(report))
    write_json(RUN_LOG, report)
    print(json.dumps({"pass": report["pass"], "error_count": report["error_count"], "output": str(REPORT_JSON)}, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
