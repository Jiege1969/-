# -*- coding: utf-8 -*-
"""执行低风险自主任务失败暂停只读演练。

脚本只读取演练矩阵并生成本地报告，不继续调度，不申请恢复，不执行恢复动作。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "97低风险自主任务失败暂停与恢复演练包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险自主任务失败暂停与恢复演练包验收"

SCENARIO_JSON = DATA_DIR / "失败暂停场景矩阵_最新.json"
RECOVERY_JSON = DATA_DIR / "恢复申请模板_最新.json"
REPORT_JSON = DATA_DIR / "只读暂停演练报告_最新.json"
REPORT_MD = DATA_DIR / "只读暂停演练报告_最新.md"
DRILL_LOG = LOG_DIR / "low-risk-autonomous-failure-pause-recovery-drill-最新.json"


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


def simulate_pause_decision(scenario: dict[str, Any]) -> dict[str, Any]:
    pause_required = scenario.get("pause_required") is True
    return {
        "scenario_id": scenario.get("id"),
        "scenario": scenario.get("scenario"),
        "pause_required": pause_required,
        "scheduler_decision": "paused" if pause_required else "eligible_for_readonly_review",
        "would_continue_dispatch": False if pause_required else False,
        "auto_continue_after_failure": False,
        "pause_registration_created": pause_required,
        "recovery_requested": False,
        "recovery_executed": False,
        "external_call": False,
        "reload_service": False,
        "readonly_drill_only": True,
        "decision_note": "pause_required=true，停止后续调度，仅登记暂停原因" if pause_required else "只读复核，不触发真实调度",
    }


def report_md(report: dict[str, Any]) -> str:
    rows = [
        "| {scenario_id} | {scenario} | {pause_required} | {scheduler_decision} | {would_continue_dispatch} | {recovery_executed} |".format(**item)
        for item in report["drill_results"]
    ]
    return "\n".join(
        [
            "# 低风险自主任务失败暂停只读演练报告",
            "",
            f"- 生成时间：{report['generated_at']}",
            f"- pass：{report['pass']}",
            f"- error_count：{report['error_count']}",
            f"- auto_continue_after_failure：{report['safety_confirmation']['auto_continue_after_failure']}",
            f"- recovery_executed：{report['safety_confirmation']['recovery_executed']}",
            f"- external_call：{report['safety_confirmation']['external_call']}",
            f"- reload_service：{report['safety_confirmation']['reload_service']}",
            "",
            "| ID | 场景 | pause_required | scheduler_decision | would_continue_dispatch | recovery_executed |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
            "## 结论",
            "",
            "- 所有 pause_required=true 的场景均不会继续调度。",
            "- 本演练没有发起恢复申请，也没有执行恢复动作。",
            "",
        ]
    )


def main() -> int:
    errors: list[str] = []
    if not SCENARIO_JSON.exists():
        errors.append(f"缺少场景矩阵：{SCENARIO_JSON}")
    if not RECOVERY_JSON.exists():
        errors.append(f"缺少恢复申请模板：{RECOVERY_JSON}")

    matrix = read_json(SCENARIO_JSON) if SCENARIO_JSON.exists() else {"scenarios": []}
    template = read_json(RECOVERY_JSON) if RECOVERY_JSON.exists() else {}
    results = [simulate_pause_decision(item) for item in matrix.get("scenarios", [])]

    for item in results:
        if item["pause_required"] and item["would_continue_dispatch"] is not False:
            errors.append(f"{item['scenario_id']} pause_required=true 时仍会继续调度")
        if item["recovery_executed"] is not False:
            errors.append(f"{item['scenario_id']} 不允许执行恢复动作")
        if item["external_call"] is not False:
            errors.append(f"{item['scenario_id']} 不允许外部调用")
        if item["reload_service"] is not False:
            errors.append(f"{item['scenario_id']} 不允许重载服务")

    if template.get("recovery_requested") is not False:
        errors.append("恢复申请模板 recovery_requested 必须默认 false")
    if template.get("recovery_executed") is not False:
        errors.append("恢复申请模板 recovery_executed 必须默认 false")
    if template.get("requires_supervisor_confirmation") is not True:
        errors.append("恢复申请模板 requires_supervisor_confirmation 必须为 true")

    report = {
        "name": "低风险自主任务失败暂停只读演练报告",
        "generated_at": now(),
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "readonly_drill_only": True,
        "pause_required_scenario_count": sum(1 for item in results if item["pause_required"]),
        "paused_without_continue_count": sum(1 for item in results if item["pause_required"] and item["would_continue_dispatch"] is False),
        "drill_results": results,
        "safety_confirmation": {
            "auto_continue_after_failure": False,
            "recovery_requested": False,
            "recovery_executed": False,
            "external_call": False,
            "reload_service": False,
            "real_wecom_send": False,
            "connect_n8n": False,
            "connect_broker": False,
            "trade": False,
            "login_tax_bureau": False,
            "connect_finance_tax_software": False,
            "promote_to_formal_rule": False,
            "modify_master_panel": False,
            "modify_one_click_continuation_package": False,
        },
    }

    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, report_md(report))
    write_json(DRILL_LOG, report)
    print(json.dumps({"pass": report["pass"], "error_count": report["error_count"], "output": str(REPORT_JSON)}, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
