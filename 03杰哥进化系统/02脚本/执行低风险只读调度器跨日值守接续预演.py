# -*- coding: utf-8 -*-
"""执行低风险只读调度器跨日值守接续预演。

这里的“执行”只表示生成本地预演结果、次日候选队列和一致性检查；
不执行脚本，不注册系统计划任务，不调用外部接口。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "116低风险只读调度器跨日值守接续预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器跨日值守接续预演包验收"

CONFIG_JSON = DATA_DIR / "跨日值守接续配置_最新.json"
PREVIEW_RESULT_JSON = DATA_DIR / "跨日值守接续预演结果_最新.json"
PREVIEW_RESULT_MD = DATA_DIR / "跨日值守接续预演结果_最新.md"
NEXT_DAY_QUEUE_JSON = DATA_DIR / "次日只读候选队列_最新.json"
NEXT_DAY_QUEUE_MD = DATA_DIR / "次日只读候选队列_最新.md"
HANDOFF_CHECK_JSON = DATA_DIR / "跨日接续一致性检查_最新.json"
HANDOFF_CHECK_MD = DATA_DIR / "跨日接续一致性检查_最新.md"
EXECUTE_LOG = LOG_DIR / "low-risk-readonly-scheduler-cross-day-handoff-execute-最新.json"


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


def safety_flags() -> dict[str, bool]:
    return {
        "preview_only": True,
        "auto_schedule": False,
        "auto_execute": False,
        "actual_execution": False,
        "external_call": False,
        "real_wecom_send": False,
        "connect_n8n": False,
        "trigger_n8n": False,
        "broker_connection": False,
        "trade_order": False,
        "tax_bureau_login": False,
        "finance_tax_software_connection": False,
        "write_formal_rule": False,
        "auto_promote_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
        "register_system_scheduled_task": False,
        "reload_service": False,
        "delete_business_artifact": False,
    }


def build_preview_result(config: dict[str, Any], generated_at: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for step in sorted(config["handoff_steps"], key=lambda item: (item["order"], item["handoff_id"])):
        item = {
            "order": step["order"],
            "handoff_id": step["handoff_id"],
            "handoff_name": step["handoff_name"],
            "planned_at": step["planned_at"],
            "purpose": step["purpose"],
            "preview_status": "planned_not_executed",
            "plan": {
                "action": "generate_cross_day_handoff_evidence_path_only",
                "script_execution": False,
                "system_schedule_registration": False,
                "external_delivery": False,
                "resume_task_execution": False,
            },
            "dependency_keys": step["dependency_keys"],
            "evidence_path": step["evidence_path"],
            "script_to_execute": None,
            "execution_adapter": "none",
            "manual_review_required": step["manual_review_required"],
        }
        item.update(safety_flags())
        items.append(item)

    result = {
        "name": "低风险只读调度器跨日值守接续预演结果",
        "generated_at": generated_at,
        "data_dir": str(DATA_DIR),
        "pass": True,
        "error_count": 0,
        "handoff_step_count": len(items),
        "handoff_steps": items,
        "preview_only": True,
        "auto_schedule": False,
        "auto_execute": False,
        "actual_execution": False,
        "external_call": False,
        "reload_service": False,
        "register_system_scheduled_task": False,
        "hard_red_line_confirmation": safety_flags(),
    }
    result.update(safety_flags())
    return result


def build_next_day_queue(preview: dict[str, Any], generated_at: str) -> dict[str, Any]:
    queue_items = []
    for step in preview["handoff_steps"]:
        queue_items.append(
            {
                "queue_id": f"NEXT-{step['order']:03d}",
                "source_handoff_id": step["handoff_id"],
                "title": step["handoff_name"],
                "next_day_action": "read_only_review_candidate",
                "auto_resume": False,
                "auto_execute": False,
                "manual_review_required": step["manual_review_required"],
                "evidence_path": step["evidence_path"],
                "status": "candidate_only",
            }
            | safety_flags()
        )
    queue = {
        "name": "低风险只读调度器次日只读候选队列",
        "generated_at": generated_at,
        "data_dir": str(DATA_DIR),
        "queue_count": len(queue_items),
        "items": queue_items,
        "preview_only": True,
        "auto_schedule": False,
        "auto_execute": False,
        "actual_execution": False,
        "external_call": False,
        "reload_service": False,
        "register_system_scheduled_task": False,
        "hard_red_line_confirmation": safety_flags(),
    }
    queue.update(safety_flags())
    return queue


def build_handoff_check(config: dict[str, Any], preview: dict[str, Any], queue: dict[str, Any], generated_at: str) -> dict[str, Any]:
    errors: list[str] = []
    if "116低风险只读调度器跨日值守接续预演包" not in str(DATA_DIR):
        errors.append("数据目录未指向116")
    if "112" in str(DATA_DIR):
        errors.append("数据目录误指向112")
    if preview.get("handoff_step_count") != config.get("handoff_step_count"):
        errors.append("预演步骤数与配置不一致")
    if queue.get("queue_count") != preview.get("handoff_step_count"):
        errors.append("次日队列数量与预演步骤数不一致")
    blocked = [
        "real_wecom_send",
        "connect_n8n",
        "trigger_n8n",
        "broker_connection",
        "trade_order",
        "tax_bureau_login",
        "finance_tax_software_connection",
        "write_formal_rule",
        "auto_promote_formal_rule",
        "modify_supervisor_panel",
        "modify_one_click_continuation_package",
        "register_system_scheduled_task",
        "reload_service",
        "delete_business_artifact",
    ]
    check = {
        "name": "低风险只读调度器跨日接续一致性检查",
        "generated_at": generated_at,
        "data_dir": str(DATA_DIR),
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "handoff_step_count": preview.get("handoff_step_count", 0),
        "queue_count": queue.get("queue_count", 0),
        "data_dir_is_116": "116低风险只读调度器跨日值守接续预演包" in str(DATA_DIR),
        "data_dir_is_not_112": "112" not in str(DATA_DIR),
        "redline_blocked": True,
        "blocked_actions": blocked,
        "service_reload_required": False,
        "preview_only": True,
        "auto_schedule": False,
        "auto_execute": False,
        "actual_execution": False,
        "external_call": False,
        "reload_service": False,
        "register_system_scheduled_task": False,
        "hard_red_line_confirmation": safety_flags(),
    }
    check.update(safety_flags())
    return check


def preview_result_md(result: dict[str, Any]) -> str:
    rows = [
        f"| {item['order']} | {item['handoff_id']} | {item['handoff_name']} | {item['planned_at']} | {item['preview_status']} | {item['evidence_path']} |"
        for item in result["handoff_steps"]
    ]
    return "\n".join(
        [
            "# 跨日值守接续预演结果",
            "",
            f"- 生成时间: {result['generated_at']}",
            f"- 数据目录: `{result['data_dir']}`",
            f"- handoff_step_count: {result['handoff_step_count']}",
            "- 每个步骤只生成计划、依赖、证据路径，不执行脚本。",
            "- auto_schedule: false",
            "- actual_execution: false",
            "- external_call: false",
            "- reload_service: false",
            "",
            "| order | handoff_id | handoff_name | planned_at | preview_status | evidence_path |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def queue_md(queue: dict[str, Any]) -> str:
    rows = [
        f"| {item['queue_id']} | {item['source_handoff_id']} | {item['title']} | {item['next_day_action']} | {item['manual_review_required']} | {item['auto_execute']} |"
        for item in queue["items"]
    ]
    return "\n".join(
        [
            "# 次日只读候选队列",
            "",
            f"- 生成时间: {queue['generated_at']}",
            f"- queue_count: {queue['queue_count']}",
            "- auto_resume: false",
            "- auto_execute: false",
            "- external_call: false",
            "",
            "| queue_id | source_handoff_id | title | next_day_action | manual_review_required | auto_execute |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def handoff_check_md(check: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 跨日接续一致性检查",
            "",
            f"- 生成时间: {check['generated_at']}",
            f"- data_dir_is_116: {str(check['data_dir_is_116']).lower()}",
            f"- data_dir_is_not_112: {str(check['data_dir_is_not_112']).lower()}",
            f"- error_count: {check['error_count']}",
            f"- redline_blocked: {str(check['redline_blocked']).lower()}",
            f"- service_reload_required: {str(check['service_reload_required']).lower()}",
            "- auto_schedule: false",
            "- actual_execution: false",
            "- external_call: false",
            "",
            "## blocked_actions",
            "",
            *[f"- {item}" for item in check["blocked_actions"]],
        ]
    )


def main() -> int:
    generated_at = now()
    config = read_json(CONFIG_JSON)
    preview_result = build_preview_result(config, generated_at)
    queue = build_next_day_queue(preview_result, generated_at)
    handoff_check = build_handoff_check(config, preview_result, queue, generated_at)

    write_json(PREVIEW_RESULT_JSON, preview_result)
    write_text(PREVIEW_RESULT_MD, preview_result_md(preview_result))
    write_json(NEXT_DAY_QUEUE_JSON, queue)
    write_text(NEXT_DAY_QUEUE_MD, queue_md(queue))
    write_json(HANDOFF_CHECK_JSON, handoff_check)
    write_text(HANDOFF_CHECK_MD, handoff_check_md(handoff_check))
    write_json(
        EXECUTE_LOG,
        {
            "pass": handoff_check["pass"],
            "error_count": handoff_check["error_count"],
            "preview_result": preview_result,
            "next_day_queue": queue,
            "handoff_check": handoff_check,
        },
    )
    print(
        json.dumps(
            {
                "pass": handoff_check["pass"],
                "error_count": handoff_check["error_count"],
                "handoff_step_count": preview_result["handoff_step_count"],
                "output": str(PREVIEW_RESULT_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if handoff_check["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
