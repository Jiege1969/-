# -*- coding: utf-8 -*-
"""执行低风险自主任务本地只读调度预演。

这里只做本地排序、依赖和证据字段预演，不执行计划中的任务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "96低风险自主任务本地只读调度预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险自主任务本地只读调度预演包验收"

RULES_JSON = DATA_DIR / "调度预演规则_最新.json"
SCHEDULE_JSON = DATA_DIR / "本地只读调度计划_最新.json"
REPORT_JSON = DATA_DIR / "调度预演报告_最新.json"
REPORT_MD = DATA_DIR / "调度预演报告_最新.md"
RUN_LOG = LOG_DIR / "low-risk-autonomous-local-scheduler-preview-run-最新.json"


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


def validate_task(task: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["scheduled", "auto_execute", "external_call", "real_send", "reload_service", "write_formal_rule", "task_executed"]:
        if task.get(key) is not False:
            errors.append(f"{task.get('id', '<missing>')}.{key} 必须为 false")
    if task.get("dry_run_only") is not True:
        errors.append(f"{task.get('id', '<missing>')}.dry_run_only 必须为 true")
    if task.get("execution_adapter") != "none":
        errors.append(f"{task.get('id', '<missing>')}.execution_adapter 必须为 none")
    return errors


def build_report_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['preview_order']} | {item['id']} | {item['name']} | {item['dependency_ready']} | {item['task_executed']} | {', '.join(item['depends_on']) or '无'} |"
        for item in report["preview_result"]["ordered_tasks"]
    ]
    return "\n".join(
        [
            "# 调度预演报告",
            "",
            f"- 生成时间：{report['generated_at']}",
            f"- pass: {report['pass']}",
            f"- error_count: {report['error_count']}",
            "- 确认：只预演排序和依赖，未执行任务。",
            f"- executed_task_count: {report['executed_task_count']}",
            f"- external_call: {report['external_call']}",
            "",
            "| order | id | name | dependency_ready | task_executed | depends_on |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def main() -> int:
    generated_at = now()
    errors: list[str] = []
    for path in [RULES_JSON, SCHEDULE_JSON]:
        if not path.exists():
            errors.append(f"缺少输入文件：{path}")

    rules = read_json(RULES_JSON) if RULES_JSON.exists() else {}
    schedule = read_json(SCHEDULE_JSON) if SCHEDULE_JSON.exists() else {"tasks": []}
    tasks = sorted(schedule.get("tasks", []), key=lambda item: item.get("preview_order", 9999))
    known_ids = {task.get("id") for task in tasks}

    ordered_tasks: list[dict[str, Any]] = []
    for task in tasks:
        errors.extend(validate_task(task))
        depends_on = list(task.get("depends_on", []))
        missing_dependencies = [dep for dep in depends_on if dep not in known_ids]
        if missing_dependencies:
            errors.append(f"{task.get('id', '<missing>')} 缺少依赖任务：{missing_dependencies}")
        ordered_tasks.append(
            {
                "preview_order": task.get("preview_order"),
                "id": task.get("id"),
                "name": task.get("name"),
                "source_candidate_id": task.get("source_candidate_id"),
                "depends_on": depends_on,
                "dependency_ready": not missing_dependencies,
                "task_executed": False,
                "action_taken": "previewed_order_and_dependencies_only",
            }
        )

    if len(tasks) < 8:
        errors.append("本地只读调度计划任务数不足 8 个")
    for key in ["auto_execute", "external_call", "real_send", "reload_service", "write_formal_rule"]:
        if rules.get("hard_red_line_confirmation", {}).get(key) is not False:
            errors.append(f"rules.hard_red_line_confirmation.{key} 必须为 false")

    report = {
        "name": "低风险自主任务本地只读调度预演报告",
        "generated_at": generated_at,
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "confirmation": "只预演排序和依赖，未执行任务，未调用业务接口。",
        "preview_only": True,
        "sort_preview_only": True,
        "dependency_preview_only": True,
        "tasks_executed": False,
        "executed_task_count": 0,
        "scheduled": False,
        "auto_execute": False,
        "external_call": False,
        "real_send": False,
        "reload_service": False,
        "write_formal_rule": False,
        "preview_result": {
            "task_count": len(tasks),
            "ordered_tasks": ordered_tasks,
            "dependency_edges": [
                {"from": dep, "to": task["id"]}
                for task in ordered_tasks
                for dep in task["depends_on"]
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
