# -*- coding: utf-8 -*-
"""验证 n8n 离线闸口失败演练与回滚剧本包。"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
SCRIPT_DIR = ROOT / "02脚本"
DATA_DIR = ROOT / "03数据" / "81n8n离线闸口失败演练与回滚剧本包"
LOG_DIR = ROOT / "04日志" / "n8n离线闸口失败演练与回滚剧本包验收"

PACKAGE_JSON = DATA_DIR / "n8n离线闸口失败演练与回滚剧本包_最新.json"
PACKAGE_MD = DATA_DIR / "n8n离线闸口失败演练与回滚剧本包_最新.md"
SCENARIOS_JSON = DATA_DIR / "n8n离线闸口失败演练场景_最新.json"
ROLLBACK_JSON = DATA_DIR / "n8n离线闸口失败演练回滚剧本_最新.json"
ROLLBACK_MD = DATA_DIR / "n8n离线闸口失败演练回滚剧本_最新.md"
REPORT_JSON = DATA_DIR / "n8n离线闸口失败演练报告_最新.json"
REPORT_MD = DATA_DIR / "n8n离线闸口失败演练报告_最新.md"
LOG_JSON = LOG_DIR / "n8n-offline-gate-failure-drill-rollback-verify-最新.json"

SCRIPT_FILES = [
    SCRIPT_DIR / "生成n8n离线闸口失败演练与回滚剧本包.py",
    SCRIPT_DIR / "执行n8n离线闸口失败演练.py",
    SCRIPT_DIR / "验证n8n离线闸口失败演练与回滚剧本包.py",
]

ACCEPTED_MODES = {"offline/dry_run", "dry_run/offline"}
REQUIRED_CATEGORIES = {
    "webhook_misopen",
    "real_trigger_flag_misopen",
    "credential_field_present",
    "supervisor_confirmation_missing",
    "downstream_real_action_misrelease",
}
FALSE_SWITCH_KEYS = {
    "real_trigger",
    "webhook_enabled",
    "network_request_enabled",
    "n8n_connection_enabled",
    "external_send_enabled",
    "config_change_enabled",
    "service_reload_enabled",
    "enterprise_wechat_send_enabled",
    "n8n_connected",
    "webhook_registered",
    "downstream_real_action_released",
    "changed_runtime_config",
    "called_external_system",
}
FORBIDDEN_VALUE_RE = re.compile(
    r"https?://|bearer\s+|token\s*[:=]|api[_ -]?key\s*[:=]|secret\s*[:=]|password\s*[:=]",
    re.IGNORECASE,
)
FORBIDDEN_CODE_RE = re.compile(
    r"\b(requests|urllib|http\.client|socket|websocket|subprocess|webbrowser)\b",
    re.IGNORECASE,
)


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def walk(obj: Any, path: str = "$") -> list[tuple[str, Any]]:
    items: list[tuple[str, Any]] = [(path, obj)]
    if isinstance(obj, dict):
        for key, value in obj.items():
            items.extend(walk(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            items.extend(walk(value, f"{path}[{index}]"))
    return items


def check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": passed, "detail": detail}


def flatten_objects(*roots: Any) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    for root in roots:
        for _, value in walk(root):
            if isinstance(value, dict):
                objects.append(value)
    return objects


def all_offline_dry_run(objects: list[dict[str, Any]]) -> bool:
    guarded = [item for item in objects if "mode" in item or "offline" in item or "dry_run" in item]
    return all(
        item.get("mode") in ACCEPTED_MODES and item.get("offline") is True and item.get("dry_run") is True
        for item in guarded
    )


def false_switch_findings(objects: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    for index, item in enumerate(objects, start=1):
        for key in FALSE_SWITCH_KEYS:
            if key in item and item.get(key) is not False:
                findings.append(f"object{index}.{key}={item.get(key)!r}")
    return findings


def forbidden_value_findings(*roots: Any) -> list[str]:
    findings: list[str] = []
    for root_index, root in enumerate(roots, start=1):
        for path, value in walk(root):
            if isinstance(value, str) and FORBIDDEN_VALUE_RE.search(value):
                findings.append(f"root{root_index}:{path}")
    return findings


def source_code_redline_findings() -> list[str]:
    findings: list[str] = []
    for path in SCRIPT_FILES:
        if not path.exists():
            findings.append(f"missing:{path.name}")
            continue
        text = path.read_text(encoding="utf-8-sig")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if "FORBIDDEN_CODE_RE" in line or "requests|urllib" in line:
                continue
            if FORBIDDEN_CODE_RE.search(line):
                findings.append(f"{path.name}:{line_number}")
    return findings


def main() -> int:
    checks: list[dict[str, Any]] = []
    expected_files = [PACKAGE_JSON, PACKAGE_MD, SCENARIOS_JSON, ROLLBACK_JSON, ROLLBACK_MD, REPORT_JSON, REPORT_MD]
    missing_files = [str(path) for path in expected_files if not path.exists()]
    checks.append(check("产物存在", not missing_files, "全部存在" if not missing_files else "；".join(missing_files)))

    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    scenarios_data = read_json(SCENARIOS_JSON) if SCENARIOS_JSON.exists() else {}
    rollback = read_json(ROLLBACK_JSON) if ROLLBACK_JSON.exists() else {}
    report = read_json(REPORT_JSON) if REPORT_JSON.exists() else {}

    package_scenarios = package.get("scenarios", [])
    scenario_runs = report.get("scenario_runs", [])
    scenario_count_ok = (
        len(package_scenarios) >= 5
        and len(scenario_runs) >= 5
        and scenarios_data.get("scenario_count", 0) >= 5
    )
    checks.append(check("演练数>=5", scenario_count_ok, f"package={len(package_scenarios)} report={len(scenario_runs)}"))

    present_categories = {item.get("category") for item in package_scenarios}
    checks.append(
        check(
            "必备失败演练场景齐全",
            REQUIRED_CATEGORIES <= present_categories,
            "通过" if REQUIRED_CATEGORIES <= present_categories else "缺少：" + "、".join(sorted(REQUIRED_CATEGORIES - present_categories)),
        )
    )

    all_blocked = all(item.get("detection_result", {}).get("blocked") is True for item in package_scenarios) and all(
        item.get("blocked") is True for item in scenario_runs
    )
    checks.append(check("全部被阻断", all_blocked, "通过" if all_blocked else "存在未阻断场景"))

    recovery_states = [item.get("recovery_after_state", {}) for item in scenario_runs]
    recovery_ok = all(
        state.get("mode") in ACCEPTED_MODES
        and state.get("offline") is True
        and state.get("dry_run") is True
        and state.get("real_trigger") is False
        and state.get("webhook_enabled") is False
        and state.get("error_count") == 0
        for state in recovery_states
    )
    checks.append(check("恢复后 offline/dry_run 且触发关闭", recovery_ok, "通过" if recovery_ok else "恢复状态异常"))

    objects = flatten_objects(package, scenarios_data, rollback, report)
    checks.append(check("所有护栏对象均为 offline/dry_run", all_offline_dry_run(objects), "通过" if all_offline_dry_run(objects) else "存在非离线护栏对象"))

    switch_findings = false_switch_findings(objects)
    checks.append(check("real_trigger=false 且 webhook_enabled=false", not switch_findings, "通过" if not switch_findings else "；".join(switch_findings[:30])))

    error_count_ok = (
        package.get("error_count") == 0
        and rollback.get("error_count") == 0
        and report.get("error_count") == 0
        and all(item.get("error_count") == 0 for item in package_scenarios)
        and all(item.get("error_count") == 0 for item in scenario_runs)
    )
    checks.append(check("error_count=0", error_count_ok, "通过" if error_count_ok else "存在错误计数"))

    report_has_required_fields = all(
        item.get("detection_result")
        and item.get("blocking_gates")
        and item.get("rollback_playbook_id")
        and item.get("recovery_after_state")
        for item in scenario_runs
    )
    checks.append(check("报告包含检测结果/阻断闸口/回滚剧本/恢复后状态", report_has_required_fields, "通过" if report_has_required_fields else "字段不完整"))

    forbidden_values = forbidden_value_findings(package, scenarios_data, rollback, report)
    checks.append(check("无真实网络地址或密钥值", not forbidden_values, "通过" if not forbidden_values else "；".join(forbidden_values[:20])))

    code_findings = source_code_redline_findings()
    checks.append(check("脚本未引入网络或外部执行模块", not code_findings, "通过" if not code_findings else "；".join(code_findings)))

    errors = [item["check"] for item in checks if not item["passed"]]
    verify_report = {
        "name": "n8n离线闸口失败演练与回滚剧本包验收",
        "verified_at": now_text(),
        "passed": len(errors) == 0,
        "status": "pass" if not errors else "blocked",
        "error_count": len(errors),
        "errors": errors,
        "checks": checks,
        "metrics": {
            "scenario_count": len(package_scenarios),
            "report_scenario_count": len(scenario_runs),
            "rollback_playbook_count": rollback.get("playbook_count", 0),
            "blocked_scenario_count": sum(1 for item in scenario_runs if item.get("blocked") is True),
            "real_trigger": False,
            "webhook_enabled": False,
        },
        "artifacts": {
            "package_json": str(PACKAGE_JSON),
            "package_markdown": str(PACKAGE_MD),
            "scenarios_json": str(SCENARIOS_JSON),
            "rollback_json": str(ROLLBACK_JSON),
            "rollback_markdown": str(ROLLBACK_MD),
            "report_json": str(REPORT_JSON),
            "report_markdown": str(REPORT_MD),
            "verify_log": str(LOG_JSON),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_JSON.write_text(json.dumps(verify_report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": verify_report["passed"], "error_count": verify_report["error_count"], "log": str(LOG_JSON)}, ensure_ascii=False))
    return 0 if verify_report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
