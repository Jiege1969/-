# -*- coding: utf-8 -*-
"""验证 n8n 离线干跑多场景回归与闸口矩阵包。"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
SCRIPT_DIR = ROOT / "02脚本"
DATA_DIR = ROOT / "03数据" / "78n8n离线干跑多场景回归与闸口矩阵包"
LOG_DIR = ROOT / "04日志" / "n8n离线干跑多场景回归与闸口矩阵包验收"

PACKAGE_JSON = DATA_DIR / "n8n离线干跑多场景回归与闸口矩阵包_最新.json"
SCENARIOS_JSON = DATA_DIR / "n8n离线干跑多场景回归场景_最新.json"
GATE_MATRIX_JSON = DATA_DIR / "n8n离线干跑闸口矩阵_最新.json"
GATE_MATRIX_MD = DATA_DIR / "n8n离线干跑闸口矩阵_最新.md"
DRYRUN_JSON = DATA_DIR / "n8n离线干跑多场景回归报告_最新.json"
DRYRUN_MD = DATA_DIR / "n8n离线干跑多场景回归报告_最新.md"
LOG_JSON = LOG_DIR / "n8n-offline-multiscenario-gate-matrix-verify-最新.json"

SCRIPT_FILES = [
    SCRIPT_DIR / "生成n8n离线干跑多场景回归与闸口矩阵包.py",
    SCRIPT_DIR / "执行n8n离线干跑多场景回归.py",
    SCRIPT_DIR / "验证n8n离线干跑多场景回归与闸口矩阵包.py",
]

ACCEPTED_MODES = {"offline/dry_run", "dry_run/offline"}
ALLOWED_SENSITIVE_KEYS = {
    "webhook_enabled",
    "real_trigger",
    "network_request_enabled",
    "n8n_connection_enabled",
    "external_send_enabled",
    "config_change_enabled",
    "service_reload_enabled",
    "enterprise_wechat_send_enabled",
}
FORBIDDEN_KEY_PARTS = ["url", "uri", "token", "secret", "credential", "credentials", "api_key", "apikey", "password"]
FORBIDDEN_VALUE_RE = re.compile(
    r"https?://|bearer\s+|token\s*[:=]|api[_ -]?key\s*[:=]|secret\s*[:=]|credential\s*[:=]|password\s*[:=]",
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


def all_offline_dry_run(items: list[dict[str, Any]]) -> bool:
    return all(item.get("mode") in ACCEPTED_MODES and item.get("offline") is True and item.get("dry_run") is True for item in items)


def all_switch_false(items: list[dict[str, Any]], key: str) -> bool:
    return all(item.get(key) is False for item in items)


def flatten_scenario_objects(package: dict[str, Any], dryrun: dict[str, Any]) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    objects.append(package)
    objects.append(dryrun)
    for scenario in package.get("scenarios", []):
        objects.append(scenario)
        objects.extend(scenario.get("nodes", []))
    for scenario in dryrun.get("scenario_runs", []):
        objects.append(scenario)
        objects.extend(scenario.get("dry_run_node_results", []))
    for row in package.get("gate_matrix", {}).get("rows", []):
        objects.append(row)
    return objects


def find_sensitive_fields(objects: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    for index, obj in enumerate(objects, start=1):
        for path, value in walk(obj):
            key = path.rsplit(".", 1)[-1].split("[", 1)[0].lower()
            if key not in ALLOWED_SENSITIVE_KEYS and any(part in key for part in FORBIDDEN_KEY_PARTS):
                findings.append(f"object{index}:{path}")
            if isinstance(value, str) and FORBIDDEN_VALUE_RE.search(value):
                findings.append(f"object{index}:{path}")
            if key in {"active", "execute", "send", "publish", "enabled"} and value is True:
                findings.append(f"object{index}:{path}")
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
    missing_files = [
        str(path)
        for path in [PACKAGE_JSON, SCENARIOS_JSON, GATE_MATRIX_JSON, GATE_MATRIX_MD, DRYRUN_JSON, DRYRUN_MD]
        if not path.exists()
    ]
    checks.append(check("产物存在", not missing_files, "全部存在" if not missing_files else "；".join(missing_files)))

    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    scenarios_data = read_json(SCENARIOS_JSON) if SCENARIOS_JSON.exists() else {}
    matrix = read_json(GATE_MATRIX_JSON) if GATE_MATRIX_JSON.exists() else {}
    dryrun = read_json(DRYRUN_JSON) if DRYRUN_JSON.exists() else {}

    package_scenarios = package.get("scenarios", [])
    scenario_runs = dryrun.get("scenario_runs", [])
    scenario_count_ok = len(package_scenarios) >= 5 and len(scenario_runs) >= 5 and scenarios_data.get("scenario_count", 0) >= 5
    checks.append(check("场景数不少于5", scenario_count_ok, f"package={len(package_scenarios)} dryrun={len(scenario_runs)}"))

    objects = flatten_scenario_objects(package, dryrun)
    checks.append(check("所有场景offline/dry_run", all_offline_dry_run(objects), "通过" if all_offline_dry_run(objects) else "存在非离线干跑对象"))
    checks.append(check("real_trigger=false", all_switch_false(objects, "real_trigger"), "通过" if all_switch_false(objects, "real_trigger") else "存在真实触发风险"))
    checks.append(check("webhook_enabled=false", all_switch_false(objects, "webhook_enabled"), "通过" if all_switch_false(objects, "webhook_enabled") else "存在webhook启用风险"))

    sensitive_findings = find_sensitive_fields(objects)
    checks.append(check("无真实接入敏感字段", not sensitive_findings, "通过" if not sensitive_findings else "；".join(sensitive_findings[:20])))

    dryrun_error_ok = dryrun.get("error_count") == 0 and all(item.get("error_count") == 0 for item in scenario_runs)
    checks.append(check("dry_run error_count=0", dryrun_error_ok, str(dryrun.get("error_count"))))

    matrix_ok = matrix.get("scenario_count", 0) >= 5 and matrix.get("gate_count", 0) >= 5 and bool(matrix.get("rows"))
    checks.append(check("闸口矩阵JSON/MD存在且有内容", matrix_ok and GATE_MATRIX_MD.exists(), f"rows={len(matrix.get('rows', []))}"))

    required_categories = {
        "tax_message_to_candidate",
        "stock_display_inspection",
        "video_render_block",
        "supervisor_confirmation_gate",
        "exception_failure_grading",
    }
    present_categories = {item.get("category") for item in package_scenarios}
    checks.append(check("必备五类场景齐全", required_categories <= present_categories, "通过" if required_categories <= present_categories else "缺少场景"))

    redline_false = all(
        dryrun.get(key) is False
        for key in [
            "network_request_enabled",
            "n8n_connection_enabled",
            "external_send_enabled",
            "config_change_enabled",
            "service_reload_enabled",
            "enterprise_wechat_send_enabled",
        ]
    )
    checks.append(check("红线动作全部关闭", redline_false, "通过" if redline_false else "存在红线开关异常"))

    code_findings = source_code_redline_findings()
    checks.append(check("脚本未引入网络或外部执行模块", not code_findings, "通过" if not code_findings else "；".join(code_findings)))

    errors = [item["check"] for item in checks if not item["passed"]]
    report = {
        "name": "n8n离线干跑多场景回归与闸口矩阵包验收",
        "verified_at": now_text(),
        "passed": len(errors) == 0,
        "status": "pass" if not errors else "blocked",
        "error_count": len(errors),
        "errors": errors,
        "checks": checks,
        "metrics": {
            "scenario_count": len(package_scenarios),
            "dryrun_scenario_count": len(scenario_runs),
            "gate_count": matrix.get("gate_count", 0),
            "matrix_row_count": len(matrix.get("rows", [])),
            "dryrun_error_count": dryrun.get("error_count"),
            "real_trigger": False,
            "webhook_enabled": False,
        },
        "artifacts": {
            "package_json": str(PACKAGE_JSON),
            "scenarios_json": str(SCENARIOS_JSON),
            "gate_matrix_json": str(GATE_MATRIX_JSON),
            "gate_matrix_markdown": str(GATE_MATRIX_MD),
            "dryrun_json": str(DRYRUN_JSON),
            "dryrun_markdown": str(DRYRUN_MD),
            "verify_log": str(LOG_JSON),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "error_count": report["error_count"], "log": str(LOG_JSON)}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
