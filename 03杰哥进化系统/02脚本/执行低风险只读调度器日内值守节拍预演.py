# -*- coding: utf-8 -*-
"""执行低风险只读调度器日内值守节拍预演。

这里的“执行”只表示生成本地预演结果和冲突检查；每个节拍只记录计划、
依赖和证据路径，不执行脚本，不注册系统计划任务，不调用外部接口。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "108低风险只读调度器日内值守节拍预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器日内值守节拍预演包验收"

CONFIG_JSON = DATA_DIR / "日内值守节拍配置_最新.json"
PREVIEW_RESULT_JSON = DATA_DIR / "值守节拍预演结果_最新.json"
PREVIEW_RESULT_MD = DATA_DIR / "值守节拍预演结果_最新.md"
CONFLICT_JSON = DATA_DIR / "节拍冲突检查_最新.json"
CONFLICT_MD = DATA_DIR / "节拍冲突检查_最新.md"
EXECUTE_LOG = LOG_DIR / "low-risk-readonly-scheduler-daily-rhythm-preview-execute-最新.json"


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
    }


def minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def build_preview_result(config: dict[str, Any], generated_at: str) -> dict[str, Any]:
    preview_items: list[dict[str, Any]] = []
    for rhythm in sorted(config["rhythms"], key=lambda item: (item["order"], item["rhythm_id"])):
        item = {
            "order": rhythm["order"],
            "rhythm_id": rhythm["rhythm_id"],
            "rhythm_name": rhythm["rhythm_name"],
            "planned_window": rhythm["planned_window"],
            "preview_status": "planned_not_executed",
            "plan": {
                "action": "generate_plan_dependency_evidence_path_only",
                "script_execution": False,
                "system_schedule_registration": False,
                "external_delivery": False,
            },
            "dependencies": rhythm["dependencies"],
            "evidence_path": rhythm["evidence_path"],
            "script_to_execute": None,
            "execution_adapter": "none",
        }
        item.update(safety_flags())
        preview_items.append(item)

    result = {
        "name": "低风险只读调度器日内值守节拍预演结果",
        "generated_at": generated_at,
        "pass": True,
        "error_count": 0,
        "rhythm_count": len(preview_items),
        "rhythms": preview_items,
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


def build_conflict_check(config: dict[str, Any], generated_at: str) -> dict[str, Any]:
    intervals = []
    for rhythm in sorted(config["rhythms"], key=lambda item: (item["planned_window"]["start"], item["rhythm_id"])):
        start = minutes(rhythm["planned_window"]["start"])
        end = minutes(rhythm["planned_window"]["end"])
        intervals.append((start, end, rhythm))

    overlaps = []
    for index, (start, end, current) in enumerate(intervals):
        if end <= start:
            overlaps.append(
                {
                    "type": "invalid_window",
                    "rhythm_id": current["rhythm_id"],
                    "start": current["planned_window"]["start"],
                    "end": current["planned_window"]["end"],
                }
            )
        for next_start, next_end, other in intervals[index + 1 :]:
            if start < next_end and next_start < end:
                overlaps.append(
                    {
                        "type": "overlap",
                        "left": current["rhythm_id"],
                        "right": other["rhythm_id"],
                    }
                )

    blocked_actions = [
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
    ]
    check = {
        "name": "低风险只读调度器日内值守节拍冲突检查",
        "generated_at": generated_at,
        "rhythm_count": len(config["rhythms"]),
        "no_overlap": len(overlaps) == 0,
        "overlap_count": len(overlaps),
        "overlaps": overlaps,
        "redline_blocked": True,
        "blocked_actions": blocked_actions,
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
        f"| {item['order']} | {item['rhythm_id']} | {item['rhythm_name']} | {item['planned_window']['start']}-{item['planned_window']['end']} | {item['preview_status']} | {item['evidence_path']} |"
        for item in result["rhythms"]
    ]
    return "\n".join(
        [
            "# 值守节拍预演结果",
            "",
            f"- 生成时间: {result['generated_at']}",
            f"- rhythm_count: {result['rhythm_count']}",
            "- 每个节拍只生成计划、依赖、证据路径，不执行脚本。",
            "- auto_schedule: false",
            "- actual_execution: false",
            "- external_call: false",
            "- reload_service: false",
            "",
            "| order | rhythm_id | rhythm_name | window | preview_status | evidence_path |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def conflict_md(check: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 节拍冲突检查",
            "",
            f"- 生成时间: {check['generated_at']}",
            f"- rhythm_count: {check['rhythm_count']}",
            f"- no_overlap: {str(check['no_overlap']).lower()}",
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
    conflict_check = build_conflict_check(config, generated_at)

    write_json(PREVIEW_RESULT_JSON, preview_result)
    write_text(PREVIEW_RESULT_MD, preview_result_md(preview_result))
    write_json(CONFLICT_JSON, conflict_check)
    write_text(CONFLICT_MD, conflict_md(conflict_check))
    write_json(
        EXECUTE_LOG,
        {
            "pass": conflict_check["no_overlap"],
            "error_count": 0 if conflict_check["no_overlap"] else 1,
            "preview_result": preview_result,
            "conflict_check": conflict_check,
        },
    )
    print(
        json.dumps(
            {
                "pass": conflict_check["no_overlap"],
                "error_count": 0 if conflict_check["no_overlap"] else 1,
                "rhythm_count": preview_result["rhythm_count"],
                "output": str(PREVIEW_RESULT_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if conflict_check["no_overlap"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
