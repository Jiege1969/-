# -*- coding: utf-8 -*-
"""执行低风险自主任务队列只读准入检查。

只检查本地候选包字段，不执行候选任务，不访问外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "93低风险自主任务队列准入与暂停闸口包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险自主任务队列准入与暂停闸口包验收"

RULES_JSON = DATA_DIR / "低风险任务准入规则_最新.json"
QUEUE_JSON = DATA_DIR / "自主任务队列候选_最新.json"
PAUSE_JSON = DATA_DIR / "暂停闸口_最新.json"
REPORT_JSON = DATA_DIR / "只读准入检查报告_最新.json"
REPORT_MD = DATA_DIR / "只读准入检查报告_最新.md"
CHECK_LOG = LOG_DIR / "low-risk-autonomous-task-queue-admission-check-最新.json"


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


def build_report_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['id']} | {item['name']} | {item['admitted']} | {item['pause_required']} | {', '.join(item['errors']) if item['errors'] else '无'} |"
        for item in report["candidate_checks"]
    ]
    return "\n".join(
        [
            "# 只读准入检查报告",
            "",
            f"- 生成时间：{report['generated_at']}",
            f"- 通过：{report['pass']}",
            f"- error_count：{report['error_count']}",
            f"- auto_execute：{report['safety_confirmation']['auto_execute']}",
            f"- external_call：{report['safety_confirmation']['external_call']}",
            f"- write_formal_rule：{report['safety_confirmation']['write_formal_rule']}",
            f"- reload_service：{report['safety_confirmation']['reload_service']}",
            f"- real_send：{report['safety_confirmation']['real_send']}",
            "",
            "| ID | 名称 | admitted | pause_required | errors |",
            "| --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def check_candidate(candidate: dict[str, Any], allowed_categories: set[str], pause_words: list[str]) -> dict[str, Any]:
    errors: list[str] = []
    if candidate.get("enabled") is not False:
        errors.append("enabled 必须为 false")
    if candidate.get("dry_run_only") is not True:
        errors.append("dry_run_only 必须为 true")
    if candidate.get("requires_supervisor_confirmation") is not False:
        errors.append("requires_supervisor_confirmation 必须为 false")
    if candidate.get("auto_execute") is not False:
        errors.append("auto_execute 必须为 false")
    if candidate.get("external_call") is not False:
        errors.append("external_call 必须为 false")
    if candidate.get("write_formal_rule") is not False:
        errors.append("write_formal_rule 必须为 false")
    if candidate.get("reload_service") is not False:
        errors.append("reload_service 必须为 false")
    if candidate.get("real_send") is not False:
        errors.append("real_send 必须为 false")
    if candidate.get("category") not in allowed_categories:
        errors.append("类别不在低风险准入范围")
    if "readonly" not in str(candidate.get("scope", "")):
        errors.append("scope 必须限定 readonly")

    searchable_text = " ".join(
        str(candidate.get(key, ""))
        for key in ["id", "name", "category", "description", "scope", "allowed_write_scope"]
    )
    hit_words = [word for word in pause_words if word and word in searchable_text]
    pause_required = bool(errors or hit_words)
    return {
        "id": candidate.get("id", ""),
        "name": candidate.get("name", ""),
        "category": candidate.get("category", ""),
        "admitted": not pause_required,
        "pause_required": pause_required,
        "pause_reasons": hit_words,
        "errors": errors,
    }


def main() -> int:
    generated_at = now()
    errors: list[str] = []
    for path in [RULES_JSON, QUEUE_JSON, PAUSE_JSON]:
        if not path.exists():
            errors.append(f"缺少输入文件：{path}")

    rules = read_json(RULES_JSON) if RULES_JSON.exists() else {}
    queue = read_json(QUEUE_JSON) if QUEUE_JSON.exists() else {"candidates": []}
    pause_gate = read_json(PAUSE_JSON) if PAUSE_JSON.exists() else {}

    allowed_categories = {item.get("name", "") for item in rules.get("allowed_categories", [])}
    pause_words = pause_gate.get("red_line_words", [])
    candidates = queue.get("candidates", [])
    candidate_checks = [check_candidate(item, allowed_categories, pause_words) for item in candidates]

    safety_confirmation = {
        "auto_execute": False,
        "external_call": False,
        "write_formal_rule": False,
        "reload_service": False,
        "real_send": False,
    }
    if any(item["pause_required"] for item in candidate_checks):
        errors.append("存在需要暂停的候选项")
    if len(candidates) < 8:
        errors.append("候选项不足 8 条")

    report = {
        "name": "低风险自主任务队列只读准入检查报告",
        "generated_at": generated_at,
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "safety_confirmation": safety_confirmation,
        "candidate_count": len(candidates),
        "admitted_count": sum(1 for item in candidate_checks if item["admitted"]),
        "paused_count": sum(1 for item in candidate_checks if item["pause_required"]),
        "candidate_checks": candidate_checks,
        "scope_statement": "仅限只读候选登记，不执行任务，不调用外部接口，不写正式规则，不重载服务，不真实发送。",
    }
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, build_report_md(report))
    write_json(CHECK_LOG, report)
    print(json.dumps({"pass": report["pass"], "error_count": report["error_count"], "output": str(REPORT_JSON)}, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
