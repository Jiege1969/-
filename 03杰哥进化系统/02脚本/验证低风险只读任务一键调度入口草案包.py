# -*- coding: utf-8 -*-
"""验证低风险只读任务一键调度入口草案包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "99低风险只读任务一键调度入口草案包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读任务一键调度入口草案包验收"

ENTRY_JSON = DATA_DIR / "一键调度入口草案_最新.json"
ENTRY_MD = DATA_DIR / "一键调度入口草案_最新.md"
CONFIG_JSON = DATA_DIR / "本地预演配置_最新.json"
CONFIG_MD = DATA_DIR / "本地预演配置_最新.md"
REPORT_JSON = DATA_DIR / "一键入口本地预演报告_最新.json"
REPORT_MD = DATA_DIR / "一键入口本地预演报告_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读任务一键调度入口草案包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读任务一键调度入口草案包_最新.md"

VERIFY_JSON = LOG_DIR / "low-risk-readonly-one-click-scheduler-entry-verify-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def require_false(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not False:
        errors.append(f"{scope}.{key} 必须为 false")


def require_true(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not True:
        errors.append(f"{scope}.{key} 必须为 true")


def verify_safety_flags(errors: list[str], data: dict[str, Any], scope: str) -> None:
    for key in [
        "auto_execute",
        "external_call",
        "real_send",
        "reload_service",
        "modify_supervisor_panel",
        "modify_one_click_pack",
    ]:
        require_false(errors, data, key, scope)


def verify_task(errors: list[str], task: dict[str, Any]) -> None:
    scope = str(task.get("id", "<missing>"))
    require_false(errors, task, "enabled", scope)
    require_true(errors, task, "preview_only", scope)
    verify_safety_flags(errors, task, scope)
    for key in [
        "real_wecom_send",
        "trigger_n8n",
        "broker_connection",
        "trade_order",
        "tax_bureau_login",
        "finance_tax_software_connection",
        "write_formal_rule",
        "task_executed",
    ]:
        require_false(errors, task, key, scope)
    if task.get("execution_adapter") != "none":
        errors.append(f"{scope}.execution_adapter 必须为 none")
    if not isinstance(task.get("depends_on", []), list):
        errors.append(f"{scope}.depends_on 必须为列表")


def main() -> int:
    generated_at = now()
    errors: list[str] = []
    required_files = [
        ENTRY_JSON,
        ENTRY_MD,
        CONFIG_JSON,
        CONFIG_MD,
        REPORT_JSON,
        REPORT_MD,
        PACKAGE_JSON,
        PACKAGE_MD,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件: {path}")

    entry = read_json(ENTRY_JSON) if ENTRY_JSON.exists() else {}
    config = read_json(CONFIG_JSON) if CONFIG_JSON.exists() else {"tasks": []}
    report = read_json(REPORT_JSON) if REPORT_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}

    if entry.get("entry_name") != "低风险只读任务一键调度入口草案":
        errors.append("一键调度入口草案缺少正确入口名称")
    for field in ["allowed_task_list", "pre_execution_checks", "pause_conditions", "output_paths"]:
        if field not in entry:
            errors.append(f"一键调度入口草案缺少字段: {field}")
    if len(entry.get("allowed_task_list", [])) < 8:
        errors.append("一键调度入口草案允许任务列表不足 8 个")
    verify_safety_flags(errors, entry, "entry")

    defaults = config.get("defaults", {})
    require_false(errors, defaults, "enabled", "config.defaults")
    require_true(errors, defaults, "preview_only", "config.defaults")
    require_false(errors, defaults, "auto_execute", "config.defaults")
    require_false(errors, defaults, "external_call", "config.defaults")
    verify_safety_flags(errors, config, "config")

    tasks = config.get("tasks", [])
    if len(tasks) < 8:
        errors.append("本地预演配置任务数不足 8 个")
    seen_ids = set()
    for task in tasks:
        task_id = task.get("id")
        if not task_id:
            errors.append("存在缺少 id 的任务")
        elif task_id in seen_ids:
            errors.append(f"{task_id} 重复")
        seen_ids.add(task_id)
        verify_task(errors, task)

    if report.get("pass") is not True:
        errors.append("一键入口本地预演报告必须 pass=true")
    if report.get("error_count") != 0:
        errors.append("一键入口本地预演报告 error_count 必须为 0")
    require_true(errors, report, "parsed_entry", "report")
    require_true(errors, report, "generated_plan_only", "report")
    require_true(errors, report, "preview_only", "report")
    require_false(errors, report, "tasks_executed", "report")
    if report.get("executed_task_count") != 0:
        errors.append("report.executed_task_count 必须为 0")
    generated_plan = report.get("generated_plan", {})
    if generated_plan.get("planned_task_count") != 0:
        errors.append("report.generated_plan.planned_task_count 必须为 0")
    verify_safety_flags(errors, report, "report")
    verify_safety_flags(errors, package, "package")

    verification = {
        "name": "低风险只读任务一键调度入口草案包验收",
        "generated_at": generated_at,
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "fixed_log_path": str(VERIFY_JSON),
        "required_file_count": len(required_files),
        "existing_file_count": sum(1 for path in required_files if path.exists()),
        "entry_name": entry.get("entry_name"),
        "task_count": len(tasks),
        "report_confirms_parse_and_plan_only": report.get("parsed_entry") is True and report.get("generated_plan_only") is True,
        "executed_task_count": report.get("executed_task_count", -1),
        "auto_execute": False,
        "external_call": False,
        "real_send": False,
        "reload_service": False,
        "modify_supervisor_panel": False,
        "modify_one_click_pack": False,
        "hard_red_line_confirmation": {
            "real_wecom_send": False,
            "trigger_n8n": False,
            "broker_connection": False,
            "trade_order": False,
            "tax_bureau_login": False,
            "finance_tax_software_connection": False,
            "write_formal_rule": False,
            "reload_service": False,
            "modify_supervisor_panel": False,
            "modify_one_click_pack": False,
        },
        "scope_statement": "只做入口草案、本地入口解析和禁用态计划生成；未执行任务，未接入总管面板，未写一键接续包。",
    }
    write_json(VERIFY_JSON, verification)
    print(json.dumps({"pass": verification["pass"], "error_count": verification["error_count"], "log": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if verification["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
