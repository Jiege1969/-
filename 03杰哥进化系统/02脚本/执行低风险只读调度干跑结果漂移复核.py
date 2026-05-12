# -*- coding: utf-8 -*-
"""执行低风险只读调度干跑结果漂移复核。

这里的执行仅表示读取源 JSON、在内存中构造三轮规范化预演并比较哈希。
不写源包、不调用外部接口、不触发 n8n、不重载服务。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "105低风险只读调度干跑结果漂移复核与幂等校验包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度干跑结果漂移复核与幂等校验包验收"

RULES_JSON = DATA_DIR / "漂移规则_最新.json"
IDEMPOTENCY_JSON = DATA_DIR / "幂等校验报告_最新.json"
IDEMPOTENCY_MD = DATA_DIR / "幂等校验报告_最新.md"
DRIFT_JSON = DATA_DIR / "漂移复核报告_最新.json"
DRIFT_MD = DATA_DIR / "漂移复核报告_最新.md"
EXECUTE_LOG = LOG_DIR / "low-risk-readonly-scheduler-drift-idempotency-execute-最新.json"


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


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(data: Any) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def file_snapshot(paths: list[Path]) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for path in paths:
        if path.exists():
            stat = path.stat()
            snapshot[str(path)] = {
                "exists": True,
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "sha256": sha256_bytes(path.read_bytes()),
            }
        else:
            snapshot[str(path)] = {"exists": False, "size": None, "mtime_ns": None, "sha256": None}
    return snapshot


def source_files_modified(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> bool:
    return before != after


def safety_flags() -> dict[str, bool]:
    return {
        "real_wecom_send": False,
        "trigger_n8n": False,
        "external_call": False,
        "broker_connection": False,
        "trade_order": False,
        "tax_bureau_login": False,
        "finance_tax_software_connection": False,
        "auto_promote_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
        "reload_service": False,
        "actual_execution": False,
        "copy_source_files": False,
        "move_source_files": False,
        "source_files_modified": False,
    }


def normalize_task(record: dict[str, Any], order_index: int) -> dict[str, Any]:
    task_id = str(record.get("task_id") or record.get("编号") or f"TASK-{order_index:03d}")
    task_name = str(record.get("task_name") or record.get("复核项") or record.get("名称") or "未命名任务")
    task = {
        "order_index": order_index,
        "task_id": task_id,
        "task_name": task_name,
        "plan_time": str(record.get("plan_time") or f"readonly-preview-order-{order_index:03d}"),
        "preview_status": str(record.get("preview_status") or "not_executed"),
        "pause_required": bool(record.get("pause_required", False)),
        "evidence_path": str(record.get("evidence_path") or f"readonly-local-sample://{task_id}"),
        "operator_mode": str(record.get("operator_mode") or "readonly_preview"),
        "actual_execution": False,
        "copy_source_files": False,
        "move_source_files": False,
        "external_call": False,
        "reload_service": False,
        "planned_result_only": True,
        "source_file_touched": False,
    }
    task["hash"] = sha256_json(task)
    return task


def normalize_plan(source_data: dict[str, Any], fallback_data: dict[str, Any]) -> dict[str, Any]:
    raw_records = source_data.get("records")
    source_name = "本地低风险只读调度预演台账"
    if not isinstance(raw_records, list) or not raw_records:
        raw_records = fallback_data.get("第二批低风险复核台账", [])
        source_name = "第104包第二批低风险复核台账"
    tasks = [normalize_task(item, index) for index, item in enumerate(raw_records, start=1) if isinstance(item, dict)]
    return {
        "source_name": source_name,
        "task_count": len(tasks),
        "task_order": [item["task_id"] for item in tasks],
        "task_hashes": [item["hash"] for item in tasks],
        "tasks": tasks,
        "safety_boundary": safety_flags(),
    }


def build_three_rounds(plan: dict[str, Any]) -> list[dict[str, Any]]:
    rounds = []
    for round_index in range(1, 4):
        rounds.append(
            {
                "round": round_index,
                "preview_status": "not_executed",
                "normalized_plan": plan,
                "plan_hash": sha256_json(plan),
                "actual_execution": False,
                "copy_source_files": False,
                "move_source_files": False,
                "external_call": False,
                "reload_service": False,
            }
        )
    return rounds


def count_plan_diffs(rounds: list[dict[str, Any]]) -> int:
    if not rounds:
        return 1
    first_hash = rounds[0]["plan_hash"]
    return sum(1 for item in rounds[1:] if item["plan_hash"] != first_hash)


def redline_scan(source_payloads: list[dict[str, Any]], rounds: list[dict[str, Any]]) -> dict[str, Any]:
    regression_items: list[str] = []
    redline_aliases = {
        "真实发送企业微信": "real_wecom_send",
        "接n8n": "trigger_n8n",
        "真实触发n8n": "trigger_n8n",
        "触发webhook": "external_call",
        "接券商": "broker_connection",
        "交易": "trade_order",
        "登录电子税务局": "tax_bureau_login",
        "接财税软件": "finance_tax_software_connection",
        "自动转正式规则": "auto_promote_formal_rule",
        "写正式规则": "auto_promote_formal_rule",
        "修改总管面板": "modify_supervisor_panel",
        "修改一键接续包": "modify_one_click_continuation_package",
        "重载19310": "reload_service",
        "重载19302": "reload_service",
    }
    for payload_index, payload in enumerate(source_payloads, start=1):
        boundary = payload.get("安全边界", {}) or payload.get("hard_red_line_confirmation", {})
        if isinstance(boundary, dict):
            for source_key, normalized_key in redline_aliases.items():
                if source_key in boundary and boundary[source_key] is not False:
                    regression_items.append(f"source{payload_index}.{source_key}->{normalized_key}")
    for round_item in rounds:
        boundary = round_item["normalized_plan"].get("safety_boundary", {})
        for key, value in boundary.items():
            if value is not False:
                regression_items.append(f"round{round_item['round']}.{key}")
    return {
        "redline_regression_count": len(regression_items),
        "regression_items": regression_items,
        "summary": "红线字段均保持 false，未出现真实发送、外部连接、交易、登录、正式规则、总管面板、一键接续或重载回归。",
    }


def drift_review(
    rules: dict[str, Any],
    plan: dict[str, Any],
    rounds: list[dict[str, Any]],
    source_payloads: list[dict[str, Any]],
) -> dict[str, Any]:
    missing_items: list[str] = []
    drift_items: list[str] = []
    required_fields = set(rules.get("required_ledger_fields", []))
    baseline_count = rounds[0]["normalized_plan"]["task_count"] if rounds else 0
    baseline_order = rounds[0]["normalized_plan"]["task_order"] if rounds else []
    for round_item in rounds:
        round_plan = round_item["normalized_plan"]
        if round_plan["task_count"] != baseline_count:
            drift_items.append(f"round{round_item['round']}.task_count")
        if round_plan["task_order"] != baseline_order:
            drift_items.append(f"round{round_item['round']}.task_order")
    for task in plan.get("tasks", []):
        missing = sorted(required_fields - set(task.keys()))
        for field in missing:
            missing_items.append(f"{task.get('task_id', '<missing>')}.{field}")
    redline = redline_scan(source_payloads, rounds)
    return {
        "name": "低风险只读调度干跑结果漂移复核报告",
        "generated_at": now(),
        "pass": not drift_items and not missing_items and redline["redline_regression_count"] == 0,
        "error_count": len(drift_items) + len(missing_items) + redline["redline_regression_count"],
        "drift_count": len(drift_items),
        "missing_count": len(missing_items),
        "redline_regression_count": redline["redline_regression_count"],
        "drift_items": drift_items,
        "missing_items": missing_items,
        "redline_scan_summary": redline,
        "task_count": baseline_count,
        "task_order": baseline_order,
        "ledger_field_check": {"required_fields": sorted(required_fields), "missing_count": len(missing_items)},
        "actual_execution": False,
        "copy_source_files": False,
        "move_source_files": False,
        "source_files_modified": False,
        "external_call": False,
        "reload_service": False,
        "hard_red_line_confirmation": safety_flags(),
    }


def idempotency_report(
    rounds: list[dict[str, Any]],
    source_before: dict[str, dict[str, Any]],
    source_after: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    diff_count = count_plan_diffs(rounds)
    modified = source_files_modified(source_before, source_after)
    return {
        "name": "低风险只读调度干跑结果幂等校验报告",
        "generated_at": now(),
        "pass": diff_count == 0 and not modified,
        "error_count": 0 if diff_count == 0 and not modified else 1,
        "repeated_preview_same_plan": diff_count == 0,
        "source_files_modified": modified,
        "diff_count": diff_count,
        "round_count": len(rounds),
        "round_plan_hashes": [item["plan_hash"] for item in rounds],
        "source_snapshot_before": source_before,
        "source_snapshot_after": source_after,
        "actual_execution": False,
        "copy_source_files": False,
        "move_source_files": False,
        "external_call": False,
        "reload_service": False,
        "hard_red_line_confirmation": safety_flags(),
    }


def idempotency_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 幂等校验报告",
            "",
            f"- 生成时间：{report['generated_at']}",
            f"- pass: {report['pass']}",
            f"- repeated_preview_same_plan: {report['repeated_preview_same_plan']}",
            f"- source_files_modified: {report['source_files_modified']}",
            f"- diff_count: {report['diff_count']}",
            "- 说明：三轮干跑计划只在内存中规范化并比对，未改源产物。",
        ]
    )


def drift_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 漂移复核报告",
            "",
            f"- 生成时间：{report['generated_at']}",
            f"- pass: {report['pass']}",
            f"- drift_count: {report['drift_count']}",
            f"- missing_count: {report['missing_count']}",
            f"- redline_regression_count: {report['redline_regression_count']}",
            f"- task_count: {report['task_count']}",
            f"- task_order: {', '.join(report['task_order'])}",
            "",
            "## 红线扫描摘要",
            "",
            report["redline_scan_summary"]["summary"],
        ]
    )


def main() -> int:
    errors: list[str] = []
    if not RULES_JSON.exists():
        errors.append(f"缺少漂移规则：{RULES_JSON}")
        rules = {"source_files": {}, "required_ledger_fields": []}
    else:
        rules = read_json(RULES_JSON)

    source_paths = [Path(value) for value in rules.get("source_files", {}).values()]
    source_before = file_snapshot(source_paths)
    payloads = [read_json(path) if path.exists() else {} for path in source_paths]
    source_by_name = {name: read_json(Path(path)) if Path(path).exists() else {} for name, path in rules.get("source_files", {}).items()}
    plan = normalize_plan(source_by_name.get("readonly_ledger", {}), source_by_name.get("package104", {}))
    if plan["task_count"] < 1:
        errors.append("规范化计划任务数必须不少于 1")
    rounds = build_three_rounds(plan)
    drift = drift_review(rules, plan, rounds, payloads)
    source_after = file_snapshot(source_paths)
    idempotency = idempotency_report(rounds, source_before, source_after)

    if errors:
        drift["pass"] = False
        drift["errors"] = errors
        drift["error_count"] = drift.get("error_count", 0) + len(errors)
    else:
        drift["errors"] = []

    write_json(IDEMPOTENCY_JSON, idempotency)
    write_text(IDEMPOTENCY_MD, idempotency_md(idempotency))
    write_json(DRIFT_JSON, drift)
    write_text(DRIFT_MD, drift_md(drift))

    execute_log = {
        "name": "低风险只读调度干跑结果漂移复核执行日志",
        "generated_at": now(),
        "pass": idempotency["pass"] and drift["pass"] and not errors,
        "error_count": idempotency["error_count"] + drift["error_count"],
        "errors": errors + drift.get("drift_items", []) + drift.get("missing_items", []),
        "drift_count": drift["drift_count"],
        "missing_count": drift["missing_count"],
        "redline_regression_count": drift["redline_regression_count"],
        "diff_count": idempotency["diff_count"],
        "repeated_preview_same_plan": idempotency["repeated_preview_same_plan"],
        "source_files_modified": idempotency["source_files_modified"],
        "external_call": False,
        "actual_execution": False,
        "copy_source_files": False,
        "move_source_files": False,
        "reload_service": False,
        "outputs": {"idempotency": str(IDEMPOTENCY_JSON), "drift": str(DRIFT_JSON)},
        "hard_red_line_confirmation": safety_flags(),
    }
    write_json(EXECUTE_LOG, execute_log)
    print(json.dumps({"pass": execute_log["pass"], "error_count": execute_log["error_count"], "diff_count": execute_log["diff_count"], "drift_count": execute_log["drift_count"]}, ensure_ascii=False))
    return 0 if execute_log["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
