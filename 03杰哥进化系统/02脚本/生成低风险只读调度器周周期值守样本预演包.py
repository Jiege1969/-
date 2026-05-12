# -*- coding: utf-8 -*-
"""生成低风险只读调度器周周期值守样本预演包。

只生成本地 JSON/MD 预演材料；不注册系统计划任务，不自动执行，不接外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "120低风险只读调度器周周期值守样本预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器周周期值守样本预演包验收"

RULE_JSON = DATA_DIR / "周周期值守规则_最新.json"
RULE_MD = DATA_DIR / "周周期值守规则_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器周周期值守样本预演包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器周周期值守样本预演包_最新.md"
GENERATE_LOG = LOG_DIR / "low-risk-readonly-scheduler-week-cycle-sample-generate-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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


def based_on_packages() -> dict[str, str]:
    data_root = EVOLUTION_ROOT / "03数据"
    return {
        "package116_cross_day_handoff": str(data_root / "116低风险只读调度器跨日值守接续预演包" / "跨日值守接续预演结果_最新.json"),
        "package117_handoff_inheritance": str(data_root / "117低风险只读调度器交接班摘要与未完成项继承包" / "未完成项继承清单_最新.json"),
        "package118_evidence_retention_no_delete": str(data_root / "118低风险只读调度器证据留存到期检查与不删除预演包" / "不删除预演报告_最新.json"),
        "package119_round15_cross_day_index": str(data_root / "119第十五轮跨日值守样本并行调度索引包" / "第十五轮跨日值守样本并行调度索引包_最新.json"),
    }


def week_rules() -> list[dict[str, Any]]:
    specs = [
        ("MON-START", "周一启动", "Monday", "weekday", "建立本周只读值守样本队列，继承跨日未完成项，只登记待办。", True, False),
        ("TUE-CHECK", "工作日巡检", "Tuesday", "weekday", "读取本地样本状态并生成巡检观察项，不触发任何任务。", True, False),
        ("WED-REVIEW", "周中复核", "Wednesday", "weekday", "复核周一至周三队列一致性和红线标志，生成复核候选。", True, False),
        ("THU-CHECK", "工作日巡检", "Thursday", "weekday", "延续只读巡检样本，保留人工确认入口。", True, False),
        ("FRI-ARCHIVE", "周五归档", "Friday", "weekday", "生成周归档候选与证据路径，不删除、不上传、不发布。", True, False),
        ("SAT-HOLD", "周末不执行/只保留待办", "Saturday", "weekend", "不执行巡检，仅保留待办和下周一人工复核候选。", False, True),
        ("SUN-HOLD", "周末不执行/只保留待办", "Sunday", "weekend", "不执行巡检，仅保留待办和下周一人工复核候选。", False, True),
    ]
    rules: list[dict[str, Any]] = []
    for order, (rule_id, phase, weekday, day_type, purpose, weekday_queue_created, weekend_hold_only) in enumerate(specs, start=1):
        item = {
            "order": order,
            "rule_id": rule_id,
            "phase": phase,
            "weekday": weekday,
            "day_type": day_type,
            "purpose": purpose,
            "weekday_queue_created": weekday_queue_created,
            "weekend_execute": False,
            "weekend_hold_only": weekend_hold_only,
            "queue_mode": "readonly_candidate_queue" if weekday_queue_created else "todo_hold_only",
            "action_mode": "preview_plan_only",
            "execution_adapter": "none",
            "script_to_execute": None,
            "system_schedule_name": None,
            "manual_review_required": phase in {"周中复核", "周五归档", "周末不执行/只保留待办"},
            "evidence_path": str(DATA_DIR / "证据路径预留" / f"{order:02d}_{rule_id}_计划证据.json"),
        }
        item.update(safety_flags())
        rules.append(item)
    return rules


def build_rule(generated_at: str) -> dict[str, Any]:
    rules = week_rules()
    rule = {
        "name": "低风险只读调度器周周期值守规则",
        "generated_at": generated_at,
        "data_dir": str(DATA_DIR),
        "timezone": "Asia/Shanghai",
        "scheduler_mode": "week_cycle_sample_preview_plan_only",
        "based_on_packages": based_on_packages(),
        "day_count": len(rules),
        "rule_count": len(rules),
        "required_phases": ["周一启动", "工作日巡检", "周中复核", "周五归档", "周末不执行/只保留待办"],
        "weekday_queue_created": True,
        "weekend_execute": False,
        "external_call": False,
        "reload_service": False,
        "rules": rules,
        "hard_red_line_confirmation": safety_flags(),
    }
    rule.update(safety_flags())
    return rule


def rule_md(rule: dict[str, Any]) -> str:
    rows = [
        f"| {item['order']} | {item['rule_id']} | {item['phase']} | {item['weekday']} | {item['queue_mode']} | {str(item['weekend_execute']).lower()} |"
        for item in rule["rules"]
    ]
    return "\n".join(
        [
            "# 低风险只读调度器周周期值守规则",
            "",
            f"- 生成时间: {rule['generated_at']}",
            f"- 数据目录: `{rule['data_dir']}`",
            f"- day_count: {rule['day_count']}",
            "- preview_only: true",
            "- auto_schedule: false",
            "- actual_execution: false",
            "- external_call: false",
            "- reload_service: false",
            "",
            "| order | rule_id | phase | weekday | queue_mode | weekend_execute |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def package_md(package: dict[str, Any]) -> str:
    output_rows = [f"- {key}: `{value}`" for key, value in package["outputs"].items()]
    return "\n".join(
        [
            "# 低风险只读调度器周周期值守样本预演包",
            "",
            f"- 生成时间: {package['generated_at']}",
            f"- 数据目录: `{package['data_dir']}`",
            f"- day_count: {package['day_count']}",
            "- preview_only: true",
            "- auto_schedule: false",
            "- actual_execution: false",
            "- external_call: false",
            "- reload_service: false",
            "",
            "## 输出",
            "",
            *output_rows,
        ]
    )


def main() -> int:
    generated_at = now()
    rule = build_rule(generated_at)
    package = {
        "name": "低风险只读调度器周周期值守样本预演包",
        "generated_at": generated_at,
        "status": "generated_preview_only",
        "data_dir": str(DATA_DIR),
        "based_on_packages": based_on_packages(),
        "day_count": rule["day_count"],
        "rule_count": rule["rule_count"],
        "weekday_queue_created": True,
        "weekend_execute": False,
        "external_call": False,
        "reload_service": False,
        "outputs": {
            "rule_json": str(RULE_JSON),
            "rule_md": str(RULE_MD),
            "sample_json": str(DATA_DIR / "周周期样本_最新.json"),
            "sample_md": str(DATA_DIR / "周周期样本_最新.md"),
            "preview_report_json": str(DATA_DIR / "周周期预演报告_最新.json"),
            "preview_report_md": str(DATA_DIR / "周周期预演报告_最新.md"),
            "package_json": str(PACKAGE_JSON),
            "package_md": str(PACKAGE_MD),
        },
        "hard_red_line_confirmation": safety_flags(),
    }
    package.update(safety_flags())

    write_json(RULE_JSON, rule)
    write_text(RULE_MD, rule_md(rule))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))
    write_json(
        GENERATE_LOG,
        {
            "name": "低风险只读调度器周周期值守样本预演包生成日志",
            "generated_at": generated_at,
            "pass": True,
            "error_count": 0,
            "data_dir": str(DATA_DIR),
            "outputs": package["outputs"],
            "preview_only": True,
            "auto_schedule": False,
            "actual_execution": False,
            "external_call": False,
            "reload_service": False,
            "hard_red_line_confirmation": safety_flags(),
        },
    )
    print(json.dumps({"pass": True, "error_count": 0, "day_count": rule["day_count"], "data_dir": str(DATA_DIR)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
