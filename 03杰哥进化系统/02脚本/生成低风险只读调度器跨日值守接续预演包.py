# -*- coding: utf-8 -*-
"""生成低风险只读调度器跨日值守接续预演包。

只生成本地 JSON/MD 预演材料，不注册系统计划任务，不接外部系统，
不真实发送企业微信，不执行调度任务，不重载服务。
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
CONFIG_MD = DATA_DIR / "跨日值守接续配置_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器跨日值守接续预演包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器跨日值守接续预演包_最新.md"
GENERATE_LOG = LOG_DIR / "low-risk-readonly-scheduler-cross-day-handoff-generate-最新.json"


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


def source_packages() -> dict[str, str]:
    return {
        "package108_daily_rhythm_preview": str(
            EVOLUTION_ROOT / "03数据" / "108低风险只读调度器日内值守节拍预演包" / "值守节拍预演结果_最新.json"
        ),
        "package109_local_summary_no_notify": str(
            EVOLUTION_ROOT / "03数据" / "109低风险只读调度器本地值守摘要与不发送通知包" / "本地值守摘要预演结果_最新.json"
        ),
        "package110_exception_escalation_queue": str(
            EVOLUTION_ROOT / "03数据" / "110低风险只读调度器异常升级草案与总管确认队列包" / "总管确认队列_最新.json"
        ),
        "package111_round14_index": str(
            EVOLUTION_ROOT / "03数据" / "111第十四轮只读调度日常值守并行调度索引包" / "第十四轮只读调度日常值守并行调度索引包_最新.json"
        ),
    }


def build_handoff_steps() -> list[dict[str, Any]]:
    specs = [
        (
            "XDAY-001",
            "日终只读收束",
            "T日 20:30",
            "读取108日内节拍结果与109本地摘要，形成跨日接续起点。",
            ["package108_daily_rhythm_preview", "package109_local_summary_no_notify"],
        ),
        (
            "XDAY-002",
            "未完成项继承",
            "T日 20:45",
            "把未完成项登记为次日候选队列，不自动恢复、不自动执行。",
            ["package109_local_summary_no_notify"],
        ),
        (
            "XDAY-003",
            "异常升级草案挂起",
            "T日 21:00",
            "读取110总管确认队列，只生成挂起说明和次日人工确认候选。",
            ["package110_exception_escalation_queue"],
        ),
        (
            "XDAY-004",
            "次日只读开局计划",
            "T+1日 09:00",
            "生成次日只读开局计划，不注册系统计划任务。",
            ["package108_daily_rhythm_preview", "package111_round14_index"],
        ),
        (
            "XDAY-005",
            "跨日一致性复核",
            "T+1日 09:20",
            "核对跨日接续编号、证据路径、红线阻断和人工确认候选。",
            ["package108_daily_rhythm_preview", "package109_local_summary_no_notify", "package110_exception_escalation_queue"],
        ),
    ]
    steps: list[dict[str, Any]] = []
    for order, (step_id, name, planned_at, purpose, dependencies) in enumerate(specs, start=1):
        evidence_path = DATA_DIR / "证据路径预留" / f"{order:02d}_{name}_计划证据.json"
        item = {
            "order": order,
            "handoff_id": step_id,
            "handoff_name": name,
            "planned_at": planned_at,
            "purpose": purpose,
            "dependency_keys": dependencies,
            "evidence_path": str(evidence_path),
            "preview_status": "planned_not_executed",
            "plan_only": True,
            "script_to_execute": None,
            "execution_adapter": "none",
            "system_schedule_name": None,
            "manual_review_required": name in {"未完成项继承", "异常升级草案挂起", "跨日一致性复核"},
        }
        item.update(safety_flags())
        steps.append(item)
    return steps


def build_config(generated_at: str) -> dict[str, Any]:
    steps = build_handoff_steps()
    config = {
        "name": "低风险只读调度器跨日值守接续配置",
        "generated_at": generated_at,
        "data_dir": str(DATA_DIR),
        "based_on_packages": source_packages(),
        "handoff_step_count": len(steps),
        "timezone": "Asia/Shanghai",
        "scheduler_mode": "cross_day_handoff_preview_plan_only",
        "cross_day_boundary": "T日收束到T+1日只读开局",
        "preview_only": True,
        "auto_schedule": False,
        "auto_execute": False,
        "actual_execution": False,
        "external_call": False,
        "reload_service": False,
        "register_system_scheduled_task": False,
        "handoff_steps": steps,
        "hard_red_line_confirmation": safety_flags(),
    }
    config.update(safety_flags())
    return config


def config_md(config: dict[str, Any]) -> str:
    rows = [
        f"| {item['order']} | {item['handoff_id']} | {item['handoff_name']} | {item['planned_at']} | {item['preview_status']} | {item['manual_review_required']} |"
        for item in config["handoff_steps"]
    ]
    return "\n".join(
        [
            "# 低风险只读调度器跨日值守接续配置",
            "",
            f"- 生成时间: {config['generated_at']}",
            f"- 数据目录: `{config['data_dir']}`",
            f"- handoff_step_count: {config['handoff_step_count']}",
            "- preview_only: true",
            "- auto_schedule: false",
            "- actual_execution: false",
            "- external_call: false",
            "- reload_service: false",
            "",
            "| order | handoff_id | handoff_name | planned_at | preview_status | manual_review_required |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def package_md(package: dict[str, Any]) -> str:
    output_rows = [f"- {key}: `{value}`" for key, value in package["outputs"].items()]
    return "\n".join(
        [
            "# 低风险只读调度器跨日值守接续预演包",
            "",
            f"- 生成时间: {package['generated_at']}",
            f"- 数据目录: `{package['data_dir']}`",
            f"- handoff_step_count: {package['handoff_step_count']}",
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
    config = build_config(generated_at)
    package = {
        "name": "低风险只读调度器跨日值守接续预演包",
        "generated_at": generated_at,
        "status": "generated_preview_only",
        "data_dir": str(DATA_DIR),
        "handoff_step_count": config["handoff_step_count"],
        "preview_only": True,
        "auto_schedule": False,
        "auto_execute": False,
        "actual_execution": False,
        "external_call": False,
        "reload_service": False,
        "register_system_scheduled_task": False,
        "outputs": {
            "config_json": str(CONFIG_JSON),
            "config_md": str(CONFIG_MD),
            "preview_result_json": str(DATA_DIR / "跨日值守接续预演结果_最新.json"),
            "preview_result_md": str(DATA_DIR / "跨日值守接续预演结果_最新.md"),
            "next_day_queue_json": str(DATA_DIR / "次日只读候选队列_最新.json"),
            "next_day_queue_md": str(DATA_DIR / "次日只读候选队列_最新.md"),
            "handoff_check_json": str(DATA_DIR / "跨日接续一致性检查_最新.json"),
            "handoff_check_md": str(DATA_DIR / "跨日接续一致性检查_最新.md"),
            "package_json": str(PACKAGE_JSON),
            "package_md": str(PACKAGE_MD),
            "verify_log_json": str(LOG_DIR / "low-risk-readonly-scheduler-cross-day-handoff-verify-最新.json"),
        },
        "hard_red_line_confirmation": safety_flags(),
    }
    package.update(safety_flags())
    write_json(CONFIG_JSON, config)
    write_text(CONFIG_MD, config_md(config))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))
    write_json(GENERATE_LOG, package | {"log_type": "generate"})
    print(json.dumps({"pass": True, "error_count": 0, "handoff_step_count": config["handoff_step_count"], "output": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
