# -*- coding: utf-8 -*-
"""验证低风险只读调度器连续三轮干跑预演包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "104低风险只读调度器连续三轮干跑预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器连续三轮干跑预演包验收"

CONFIG_JSON = DATA_DIR / "三轮干跑配置_最新.json"
CONFIG_MD = DATA_DIR / "三轮干跑配置_最新.md"
RUN_RESULT_JSON = DATA_DIR / "三轮干跑结果_最新.json"
RUN_RESULT_MD = DATA_DIR / "三轮干跑结果_最新.md"
CONTINUITY_JSON = DATA_DIR / "连续性汇总_最新.json"
CONTINUITY_MD = DATA_DIR / "连续性汇总_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器连续三轮干跑预演包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器连续三轮干跑预演包_最新.md"
VERIFY_JSON = LOG_DIR / "low-risk-readonly-scheduler-three-round-dryrun-verify-最新.json"


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


def main() -> int:
    generated_at = now()
    errors: list[str] = []
    required_files = [
        CONFIG_JSON,
        CONFIG_MD,
        RUN_RESULT_JSON,
        RUN_RESULT_MD,
        CONTINUITY_JSON,
        CONTINUITY_MD,
        PACKAGE_JSON,
        PACKAGE_MD,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件: {path}")

    config = read_json(CONFIG_JSON) if CONFIG_JSON.exists() else {}
    run_result = read_json(RUN_RESULT_JSON) if RUN_RESULT_JSON.exists() else {"rounds": []}
    continuity = read_json(CONTINUITY_JSON) if CONTINUITY_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}

    if config.get("round_count") != 3:
        errors.append("config.round_count 必须为 3")
    if config.get("task_count", 0) < 8:
        errors.append("config.task_count 必须不少于 8")
    require_true(errors, config, "preview_only", "config")
    require_false(errors, config, "auto_execute", "config")
    require_false(errors, config, "actual_execution", "config")
    require_false(errors, config, "external_call", "config")

    tasks = config.get("tasks", [])
    if len(tasks) != config.get("task_count"):
        errors.append("config.tasks 数量必须等于 task_count")
    task_ids = [task.get("task_id") for task in sorted(tasks, key=lambda item: (item.get("order", 0), item.get("task_id", "")))]
    if len(task_ids) != len(set(task_ids)):
        errors.append("config.tasks task_id 不得重复")
    for task in tasks:
        scope = task.get("task_id", "<missing_task>")
        require_true(errors, task, "preview_only", scope)
        require_false(errors, task, "auto_execute", scope)
        require_false(errors, task, "actual_execution", scope)
        require_false(errors, task, "external_call", scope)
        require_false(errors, task, "reload_service", scope)
        require_false(errors, task, "write_formal_rule", scope)
        if task.get("execution_adapter") != "none":
            errors.append(f"{scope}.execution_adapter 必须为 none")

    rounds = run_result.get("rounds", [])
    if run_result.get("round_count") != 3 or len(rounds) != 3:
        errors.append("run_result.round_count 与 rounds 数量必须为 3")
    require_true(errors, run_result, "preview_only", "run_result")
    require_false(errors, run_result, "auto_execute", "run_result")
    require_false(errors, run_result, "actual_execution", "run_result")
    require_false(errors, run_result, "external_call", "run_result")
    require_false(errors, run_result, "reload_service", "run_result")
    require_false(errors, run_result, "write_formal_rule", "run_result")

    order_hashes: list[str] = []
    task_counts: list[int] = []
    for round_data in rounds:
        scope = f"round_{round_data.get('round_index')}"
        if round_data.get("task_count") != config.get("task_count"):
            errors.append(f"{scope}.task_count 必须等于 config.task_count")
        if round_data.get("task_order") != task_ids:
            errors.append(f"{scope}.task_order 必须与配置排序一致")
        if round_data.get("evidence_index_count") != round_data.get("task_count"):
            errors.append(f"{scope}.evidence_index_count 必须等于 task_count")
        order_hashes.append(str(round_data.get("task_order_hash")))
        task_counts.append(int(round_data.get("task_count", -1)))
        require_true(errors, round_data, "preview_only", scope)
        require_false(errors, round_data, "auto_execute", scope)
        require_false(errors, round_data, "actual_execution", scope)
        require_false(errors, round_data, "external_call", scope)
        require_false(errors, round_data, "reload_service", scope)
        require_false(errors, round_data, "write_formal_rule", scope)
        scan_summary = round_data.get("command_whitelist_scan_summary", {})
        if scan_summary.get("commands_executed") is not False:
            errors.append(f"{scope}.command_whitelist_scan_summary.commands_executed 必须为 false")
        if scan_summary.get("redline_hit_count") != 0:
            errors.append(f"{scope}.command_whitelist_scan_summary.redline_hit_count 必须为 0")
        for task in round_data.get("tasks", []):
            task_scope = f"{scope}.{task.get('task_id', '<missing_task>')}"
            if not task.get("evidence_index"):
                errors.append(f"{task_scope} 缺少 evidence_index")
            if not task.get("command_whitelist_scan_summary"):
                errors.append(f"{task_scope} 缺少 command_whitelist_scan_summary")
            require_true(errors, task, "preview_only", task_scope)
            require_false(errors, task, "auto_execute", task_scope)
            require_false(errors, task, "actual_execution", task_scope)
            require_false(errors, task, "external_call", task_scope)
            require_false(errors, task, "reload_service", task_scope)
            require_false(errors, task, "write_formal_rule", task_scope)

    if len(set(task_counts)) > 1:
        errors.append("三轮 planned task_count 必须一致")
    if len(set(order_hashes)) > 1:
        errors.append("三轮 task_order_hash 必须一致")

    require_true(errors, continuity, "planned_task_count_consistent", "continuity")
    require_true(errors, continuity, "order_stable", "continuity")
    require_true(errors, continuity, "preview_only", "continuity")
    require_false(errors, continuity, "auto_execute", "continuity")
    require_false(errors, continuity, "actual_execution", "continuity")
    require_false(errors, continuity, "external_call", "continuity")
    require_false(errors, continuity, "reload_service", "continuity")
    require_false(errors, continuity, "write_formal_rule", "continuity")

    for scope, data in [("package", package)]:
        if data.get("round_count") != 3:
            errors.append(f"{scope}.round_count 必须为 3")
        if data.get("task_count", 0) < 8:
            errors.append(f"{scope}.task_count 必须不少于 8")
        require_true(errors, data, "preview_only", scope)
        require_false(errors, data, "auto_execute", scope)
        require_false(errors, data, "actual_execution", scope)
        require_false(errors, data, "external_call", scope)
        require_false(errors, data, "reload_service", scope)
        require_false(errors, data, "write_formal_rule", scope)

    verification = {
        "name": "低风险只读调度器连续三轮干跑预演包验收",
        "generated_at": generated_at,
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "fixed_log_path": str(VERIFY_JSON),
        "required_file_count": len(required_files),
        "existing_file_count": sum(1 for path in required_files if path.exists()),
        "round_count": 3,
        "task_count": config.get("task_count", 0),
        "planned_task_count_consistent": continuity.get("planned_task_count_consistent") is True,
        "order_stable": continuity.get("order_stable") is True,
        "preview_only": True,
        "auto_execute": False,
        "actual_execution": False,
        "external_call": False,
        "reload_service": False,
        "write_formal_rule": False,
        "hard_red_line_confirmation": {
            "real_wecom_send": False,
            "connect_n8n": False,
            "trigger_n8n": False,
            "broker_connection": False,
            "trade_order": False,
            "tax_bureau_login": False,
            "finance_tax_software_connection": False,
            "modify_supervisor_panel": False,
            "modify_one_click_continuation_package": False,
            "reload_service": False,
            "write_formal_rule": False,
        },
        "scope_statement": "连续三轮只读调度干跑，只验证计划生成、排序稳定、台账预演稳定；不真实执行任务。",
    }
    write_json(VERIFY_JSON, verification)
    print(json.dumps({"pass": verification["pass"], "error_count": verification["error_count"], "log": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if verification["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
