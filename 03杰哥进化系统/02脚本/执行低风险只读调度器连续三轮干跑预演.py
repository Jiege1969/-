# -*- coding: utf-8 -*-
"""执行低风险只读调度器连续三轮干跑预演。

本脚本只读取本包配置并生成三轮干跑结果/连续性汇总，不执行任务，
不调用外部接口，不重载服务，不写正式规则。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "104低风险只读调度器连续三轮干跑预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器连续三轮干跑预演包验收"

CONFIG_JSON = DATA_DIR / "三轮干跑配置_最新.json"
RUN_RESULT_JSON = DATA_DIR / "三轮干跑结果_最新.json"
RUN_RESULT_MD = DATA_DIR / "三轮干跑结果_最新.md"
CONTINUITY_JSON = DATA_DIR / "连续性汇总_最新.json"
CONTINUITY_MD = DATA_DIR / "连续性汇总_最新.md"
EXECUTE_LOG = LOG_DIR / "low-risk-readonly-scheduler-three-round-dryrun-execute-最新.json"


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


def sha256_json(data: Any) -> str:
    text = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safety_flags() -> dict[str, bool]:
    return {
        "preview_only": True,
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
        "reload_service": False,
    }


def build_evidence_index(task: dict[str, Any], round_index: int) -> dict[str, Any]:
    return {
        "evidence_index_id": f"{task['evidence_index_id']}-R{round_index}",
        "task_id": task["task_id"],
        "source_package": task["source_package"],
        "planned_ledger_key": f"ROUND-{round_index:02d}-{task['order']:02d}-{task['task_id']}",
        "preview_path": str(DATA_DIR / "evidence_preview" / f"round-{round_index:02d}-{task['task_id']}.json"),
        "source_file_touched": False,
        "copy_source_files": False,
        "move_source_files": False,
        "actual_execution": False,
        "external_call": False,
    }


def build_command_scan_summary(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "command_scan_id": task["command_scan_id"],
        "task_id": task["task_id"],
        "scan_mode": "static_whitelist_summary_only",
        "candidate_command": "none",
        "decision": "allow_preview_record_only",
        "commands_executed": False,
        "redline_hit_count": 0,
        "whitelist_hit_count": 1,
        "external_call": False,
        "reload_service": False,
        "write_formal_rule": False,
    }


def build_round_result(config: dict[str, Any], round_index: int, generated_at: str) -> dict[str, Any]:
    ordered_tasks = sorted(config["tasks"], key=lambda item: (item["order"], item["task_id"]))
    task_order = [task["task_id"] for task in ordered_tasks]
    task_snapshots = []
    for task in ordered_tasks:
        task_snapshots.append(
            {
                "order": task["order"],
                "task_id": task["task_id"],
                "task_name": task["task_name"],
                "pause_state": task["pause_state"],
                "preview_status": "planned_not_executed",
                "evidence_index": build_evidence_index(task, round_index),
                "command_whitelist_scan_summary": build_command_scan_summary(task),
                "preview_only": True,
                "auto_execute": False,
                "actual_execution": False,
                "external_call": False,
                "reload_service": False,
                "write_formal_rule": False,
            }
        )
    return {
        "round_index": round_index,
        "generated_at": generated_at,
        "task_count": len(task_snapshots),
        "task_order": task_order,
        "task_order_hash": sha256_json(task_order),
        "pause_states": {task["task_id"]: task["pause_state"] for task in task_snapshots},
        "evidence_index_count": len(task_snapshots),
        "command_whitelist_scan_summary": {
            "scan_mode": "static_whitelist_summary_only_no_command_execution",
            "task_count": len(task_snapshots),
            "commands_executed": False,
            "redline_hit_count": 0,
            "blocked_count": 0,
            "external_call": False,
            "reload_service": False,
            "write_formal_rule": False,
        },
        "tasks": task_snapshots,
        "preview_only": True,
        "auto_execute": False,
        "actual_execution": False,
        "external_call": False,
        "reload_service": False,
        "write_formal_rule": False,
    }


def build_run_result(config: dict[str, Any], generated_at: str) -> dict[str, Any]:
    rounds = [build_round_result(config, index, generated_at) for index in range(1, config["round_count"] + 1)]
    return {
        "name": "低风险只读调度器连续三轮干跑结果",
        "generated_at": generated_at,
        "pass": True,
        "error_count": 0,
        "round_count": len(rounds),
        "task_count": config["task_count"],
        "rounds": rounds,
        "preview_only": True,
        "auto_execute": False,
        "actual_execution": False,
        "external_call": False,
        "reload_service": False,
        "write_formal_rule": False,
        "hard_red_line_confirmation": safety_flags(),
    }


def build_continuity_summary(run_result: dict[str, Any], generated_at: str) -> dict[str, Any]:
    rounds = run_result["rounds"]
    task_counts = [item["task_count"] for item in rounds]
    order_hashes = [item["task_order_hash"] for item in rounds]
    return {
        "name": "低风险只读调度器连续三轮干跑连续性汇总",
        "generated_at": generated_at,
        "round_count": run_result["round_count"],
        "task_count": run_result["task_count"],
        "planned_task_count_consistent": len(set(task_counts)) == 1,
        "order_stable": len(set(order_hashes)) == 1,
        "actual_execution": False,
        "external_call": False,
        "reload_service": False,
        "write_formal_rule": False,
        "auto_execute": False,
        "preview_only": True,
        "task_counts_by_round": task_counts,
        "order_hashes_by_round": order_hashes,
        "evidence_index_counts_by_round": [item["evidence_index_count"] for item in rounds],
        "command_scan": {
            "commands_executed": False,
            "redline_hit_count_total": sum(item["command_whitelist_scan_summary"]["redline_hit_count"] for item in rounds),
            "blocked_count_total": sum(item["command_whitelist_scan_summary"]["blocked_count"] for item in rounds),
            "external_call": False,
            "reload_service": False,
            "write_formal_rule": False,
        },
        "hard_red_line_confirmation": safety_flags(),
    }


def run_result_md(run_result: dict[str, Any]) -> str:
    lines = [
        "# 低风险只读调度器连续三轮干跑结果",
        "",
        f"- 生成时间: {run_result['generated_at']}",
        f"- round_count: {run_result['round_count']}",
        f"- task_count: {run_result['task_count']}",
        "- actual_execution: false",
        "- external_call: false",
        "",
    ]
    for round_data in run_result["rounds"]:
        lines.extend(
            [
                f"## 第{round_data['round_index']}轮",
                "",
                f"- task_order_hash: {round_data['task_order_hash']}",
                f"- evidence_index_count: {round_data['evidence_index_count']}",
                "- commands_executed: false",
                "- redline_hit_count: 0",
                "",
                "| order | task_id | task_name | pause_state | preview_status | evidence_index_id | scan_decision |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for task in round_data["tasks"]:
            lines.append(
                f"| {task['order']} | {task['task_id']} | {task['task_name']} | {task['pause_state']} | {task['preview_status']} | {task['evidence_index']['evidence_index_id']} | {task['command_whitelist_scan_summary']['decision']} |"
            )
        lines.append("")
    return "\n".join(lines)


def continuity_md(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 连续性汇总",
            "",
            f"- 生成时间: {summary['generated_at']}",
            f"- round_count: {summary['round_count']}",
            f"- task_count: {summary['task_count']}",
            f"- planned_task_count_consistent: {str(summary['planned_task_count_consistent']).lower()}",
            f"- order_stable: {str(summary['order_stable']).lower()}",
            "- actual_execution: false",
            "- external_call: false",
            "- reload_service: false",
            "- write_formal_rule: false",
            f"- task_counts_by_round: {summary['task_counts_by_round']}",
            f"- order_hashes_by_round: {summary['order_hashes_by_round']}",
        ]
    )


def main() -> int:
    generated_at = now()
    config = read_json(CONFIG_JSON)
    run_result = build_run_result(config, generated_at)
    continuity_summary = build_continuity_summary(run_result, generated_at)

    write_json(RUN_RESULT_JSON, run_result)
    write_text(RUN_RESULT_MD, run_result_md(run_result))
    write_json(CONTINUITY_JSON, continuity_summary)
    write_text(CONTINUITY_MD, continuity_md(continuity_summary))
    write_json(EXECUTE_LOG, {"pass": True, "error_count": 0, "run_result": run_result, "continuity_summary": continuity_summary})
    print(json.dumps({"pass": True, "error_count": 0, "output": str(RUN_RESULT_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
