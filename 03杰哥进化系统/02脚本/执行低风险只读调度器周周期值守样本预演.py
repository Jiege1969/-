# -*- coding: utf-8 -*-
"""执行低风险只读调度器周周期值守样本预演。

这里的“执行”只表示生成本地一周样本和预演报告；不自动调度、不真实执行、不接外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "120低风险只读调度器周周期值守样本预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器周周期值守样本预演包验收"

RULE_JSON = DATA_DIR / "周周期值守规则_最新.json"
SAMPLE_JSON = DATA_DIR / "周周期样本_最新.json"
SAMPLE_MD = DATA_DIR / "周周期样本_最新.md"
REPORT_JSON = DATA_DIR / "周周期预演报告_最新.json"
REPORT_MD = DATA_DIR / "周周期预演报告_最新.md"
EXECUTE_LOG = LOG_DIR / "low-risk-readonly-scheduler-week-cycle-sample-execute-最新.json"


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


def week_start() -> datetime:
    today = datetime.now()
    return today - timedelta(days=today.weekday())


def build_sample(rule: dict[str, Any], generated_at: str) -> dict[str, Any]:
    start = week_start()
    days: list[dict[str, Any]] = []
    rule_by_weekday = {item["weekday"]: item for item in rule.get("rules", [])}
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for offset, weekday in enumerate(weekdays):
        day = start + timedelta(days=offset)
        source_rule = rule_by_weekday[weekday]
        item = {
            "day_index": offset + 1,
            "sample_date": day.strftime("%Y-%m-%d"),
            "weekday": weekday,
            "rule_id": source_rule["rule_id"],
            "phase": source_rule["phase"],
            "day_type": source_rule["day_type"],
            "planned_action": source_rule["purpose"],
            "weekday_queue_created": bool(source_rule["weekday_queue_created"]),
            "weekend_execute": False,
            "weekend_hold_only": bool(source_rule["weekend_hold_only"]),
            "queue_mode": source_rule["queue_mode"],
            "sample_status": "preview_sample_only",
            "todo_retained": source_rule["weekend_hold_only"] or source_rule["manual_review_required"],
            "manual_review_required": source_rule["manual_review_required"],
            "evidence_path": source_rule["evidence_path"],
            "script_to_execute": None,
            "execution_adapter": "none",
            "system_schedule_name": None,
        }
        item.update(safety_flags())
        days.append(item)

    sample = {
        "name": "低风险只读调度器周周期样本",
        "generated_at": generated_at,
        "data_dir": str(DATA_DIR),
        "sample_start_date": days[0]["sample_date"],
        "sample_end_date": days[-1]["sample_date"],
        "day_count": len(days),
        "days": days,
        "weekday_queue_created": any(day["weekday_queue_created"] for day in days if day["day_type"] == "weekday"),
        "weekend_execute": any(day["weekend_execute"] for day in days if day["day_type"] == "weekend"),
        "external_call": False,
        "reload_service": False,
        "hard_red_line_confirmation": safety_flags(),
    }
    sample.update(safety_flags())
    return sample


def build_report(rule: dict[str, Any], sample: dict[str, Any], generated_at: str) -> dict[str, Any]:
    errors: list[str] = []
    days = sample.get("days", [])
    if len(days) < 7:
        errors.append("周周期样本自然日不足7个")
    required_phases = {"周一启动", "工作日巡检", "周中复核", "周五归档", "周末不执行/只保留待办"}
    phases = {day.get("phase") for day in days}
    missing = sorted(required_phases - phases)
    if missing:
        errors.append(f"周周期样本缺少阶段: {missing}")
    if not sample.get("weekday_queue_created"):
        errors.append("工作日队列未创建")
    if sample.get("weekend_execute") is not False:
        errors.append("周末不得执行")

    report = {
        "name": "低风险只读调度器周周期预演报告",
        "generated_at": generated_at,
        "data_dir": str(DATA_DIR),
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "day_count": len(days),
        "rule_count": rule.get("rule_count", 0),
        "weekday_queue_created": sample.get("weekday_queue_created") is True,
        "weekend_execute": False,
        "external_call": False,
        "reload_service": False,
        "auto_schedule": False,
        "actual_execution": False,
        "summary": {
            "monday_start": any(day.get("phase") == "周一启动" for day in days),
            "weekday_inspection": sum(1 for day in days if day.get("phase") == "工作日巡检"),
            "midweek_review": any(day.get("phase") == "周中复核" for day in days),
            "friday_archive": any(day.get("phase") == "周五归档" for day in days),
            "weekend_hold_only": sum(1 for day in days if day.get("phase") == "周末不执行/只保留待办"),
        },
        "hard_red_line_confirmation": safety_flags(),
    }
    report.update(safety_flags())
    return report


def sample_md(sample: dict[str, Any]) -> str:
    rows = [
        f"| {day['day_index']} | {day['sample_date']} | {day['weekday']} | {day['phase']} | {day['queue_mode']} | {str(day['weekend_execute']).lower()} |"
        for day in sample["days"]
    ]
    return "\n".join(
        [
            "# 低风险只读调度器周周期样本",
            "",
            f"- 生成时间: {sample['generated_at']}",
            f"- 样本周期: {sample['sample_start_date']} 至 {sample['sample_end_date']}",
            f"- day_count: {sample['day_count']}",
            "- preview_only: true",
            "- auto_schedule: false",
            "- actual_execution: false",
            "",
            "| day | date | weekday | phase | queue_mode | weekend_execute |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def report_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 低风险只读调度器周周期预演报告",
            "",
            f"- 生成时间: {report['generated_at']}",
            f"- pass: {str(report['pass']).lower()}",
            f"- error_count: {report['error_count']}",
            f"- day_count: {report['day_count']}",
            f"- weekday_queue_created: {str(report['weekday_queue_created']).lower()}",
            f"- weekend_execute: {str(report['weekend_execute']).lower()}",
            "- external_call: false",
            "- reload_service: false",
            "- auto_schedule: false",
            "- actual_execution: false",
        ]
    )


def main() -> int:
    generated_at = now()
    if not RULE_JSON.exists():
        raise FileNotFoundError(f"缺少周周期值守规则，请先运行生成脚本: {RULE_JSON}")
    rule = read_json(RULE_JSON)
    sample = build_sample(rule, generated_at)
    report = build_report(rule, sample, generated_at)

    write_json(SAMPLE_JSON, sample)
    write_text(SAMPLE_MD, sample_md(sample))
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, report_md(report))
    write_json(
        EXECUTE_LOG,
        {
            "name": "低风险只读调度器周周期值守样本预演执行日志",
            "generated_at": generated_at,
            "pass": report["pass"],
            "error_count": report["error_count"],
            "day_count": report["day_count"],
            "weekday_queue_created": report["weekday_queue_created"],
            "weekend_execute": report["weekend_execute"],
            "preview_only": True,
            "auto_schedule": False,
            "actual_execution": False,
            "external_call": False,
            "reload_service": False,
            "hard_red_line_confirmation": safety_flags(),
        },
    )
    print(json.dumps({"pass": report["pass"], "error_count": report["error_count"], "day_count": report["day_count"], "log": str(EXECUTE_LOG)}, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
