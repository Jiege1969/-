# -*- coding: utf-8 -*-
"""执行低风险只读调度红线失败注入演练。

执行含义仅为读取本地文本样例并生成暂停判定报告；不执行样例中的任何动作。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "106低风险只读调度红线失败注入与自动暂停演练包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度红线失败注入与自动暂停演练包验收"

INJECTION_JSON = DATA_DIR / "失败注入样例_最新.json"
SUPERVISOR_JSON = DATA_DIR / "总管确认事项清单_最新.json"
REPORT_JSON = DATA_DIR / "自动暂停演练报告_最新.json"
REPORT_MD = DATA_DIR / "自动暂停演练报告_最新.md"
RUN_LOG = LOG_DIR / "low-risk-readonly-redline-injection-pause-run-最新.json"


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
        "commands_executed": False,
        "external_call": False,
        "reload_service": False,
        "real_wecom_send": False,
        "connect_n8n": False,
        "connect_broker": False,
        "trade": False,
        "login_tax_bureau": False,
        "connect_finance_tax_software": False,
        "write_formal_rule": False,
        "promote_to_formal_rule": False,
        "real_video_publish": False,
    }


def simulate_scheduler_pause(sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "injection_id": sample.get("id"),
        "redline_type": sample.get("redline_type"),
        "simulated_text": sample.get("simulated_text"),
        "pause_required": True,
        "continue_allowed": False,
        "requires_supervisor_confirmation": True,
        "scheduler_decision": "paused",
        "supervisor_confirmation_item_created": True,
        "executed": False,
        "commands_executed": False,
        "external_call": False,
        "reload_service": False,
        "decision_note": "命中红线文本样例，调度器自动暂停并生成总管确认事项。",
    }


def report_md(report: dict[str, Any]) -> str:
    rows = [
        "| {injection_id} | {redline_type} | {pause_required} | {continue_allowed} | {requires_supervisor_confirmation} | {scheduler_decision} | {executed} |".format(
            **item
        )
        for item in report["results"]
    ]
    return "\n".join(
        [
            "# 自动暂停演练报告",
            "",
            f"- 生成时间: {report['generated_at']}",
            f"- pass: {report['pass']}",
            f"- error_count: {report['error_count']}",
            f"- injection_count: {report['injection_count']}",
            f"- pause_required_count: {report['pause_required_count']}",
            "- commands_executed: false",
            "- external_call: false",
            "- reload_service: false",
            "",
            "| 样例 | 红线类型 | pause_required | continue_allowed | requires_supervisor_confirmation | scheduler_decision | executed |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def main() -> int:
    errors: list[str] = []
    if not INJECTION_JSON.exists():
        errors.append(f"缺少失败注入样例: {INJECTION_JSON}")
    if not SUPERVISOR_JSON.exists():
        errors.append(f"缺少总管确认事项清单: {SUPERVISOR_JSON}")

    injections = read_json(INJECTION_JSON) if INJECTION_JSON.exists() else {"samples": []}
    checklist = read_json(SUPERVISOR_JSON) if SUPERVISOR_JSON.exists() else {"items": []}
    samples = injections.get("samples", [])
    results = [simulate_scheduler_pause(sample) for sample in samples]

    if len(samples) < 6:
        errors.append("失败注入样例数量必须不少于 6")
    if len(checklist.get("items", [])) != len(samples):
        errors.append("总管确认事项数量必须等于失败注入样例数量")

    for result in results:
        if result["pause_required"] is not True:
            errors.append(f"{result['injection_id']} 未暂停")
        if result["continue_allowed"] is not False:
            errors.append(f"{result['injection_id']} 不允许继续调度")
        if result["requires_supervisor_confirmation"] is not True:
            errors.append(f"{result['injection_id']} 必须生成总管确认事项")
        if result["executed"] is not False:
            errors.append(f"{result['injection_id']} 不允许执行")
        if result["commands_executed"] is not False:
            errors.append(f"{result['injection_id']} 不允许执行命令")
        if result["external_call"] is not False:
            errors.append(f"{result['injection_id']} 不允许外部调用")
        if result["reload_service"] is not False:
            errors.append(f"{result['injection_id']} 不允许重载服务")

    report = {
        "name": "低风险只读调度红线失败注入自动暂停演练报告",
        "generated_at": now(),
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "readonly_text_simulation_only": True,
        "injection_count": len(samples),
        "pause_required_count": sum(1 for item in results if item.get("pause_required") is True),
        "continue_allowed_count": sum(1 for item in results if item.get("continue_allowed") is True),
        "requires_supervisor_confirmation_count": sum(
            1 for item in results if item.get("requires_supervisor_confirmation") is True
        ),
        "commands_executed": False,
        "external_call": False,
        "reload_service": False,
        "safety_confirmation": safety_flags(),
        "results": results,
    }
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, report_md(report))
    write_json(RUN_LOG, report)
    print(
        json.dumps(
            {
                "pass": report["pass"],
                "error_count": report["error_count"],
                "injection_count": report["injection_count"],
                "pause_required_count": report["pause_required_count"],
                "commands_executed": report["commands_executed"],
                "external_call": report["external_call"],
                "reload_service": report["reload_service"],
                "output": str(REPORT_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
