# -*- coding: utf-8 -*-
"""验证 n8n 离线导入前凭据隔离与启用禁入包。"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
SCRIPT_DIR = ROOT / "02脚本"
DATA_DIR = ROOT / "03数据" / "84n8n离线导入前凭据隔离与启用禁入包"
LOG_DIR = ROOT / "04日志" / "n8n离线导入前凭据隔离与启用禁入包验收"

PACKAGE_JSON = DATA_DIR / "n8n离线导入前凭据隔离与启用禁入包_最新.json"
PACKAGE_MD = DATA_DIR / "n8n离线导入前凭据隔离与启用禁入包_最新.md"
CREDENTIAL_ISOLATION_JSON = DATA_DIR / "凭据字段隔离清单_最新.json"
CREDENTIAL_ISOLATION_MD = DATA_DIR / "凭据字段隔离清单_最新.md"
WEBHOOK_DISABLED_JSON = DATA_DIR / "webhook禁用清单_最新.json"
IMPORT_BAN_JSON = DATA_DIR / "导入前禁入条件_最新.json"
ACTIVATION_CONFIRM_JSON = DATA_DIR / "启用前总管确认项_最新.json"
ROLLBACK_REQUIREMENTS_JSON = DATA_DIR / "回滚要求_最新.json"
REPORT_JSON = DATA_DIR / "n8n离线导入前凭据隔离只读检查报告_最新.json"
REPORT_MD = DATA_DIR / "n8n离线导入前凭据隔离只读检查报告_最新.md"
LOG_JSON = LOG_DIR / "n8n-offline-import-credential-isolation-no-activate-verify-最新.json"

SCRIPT_FILES = [
    SCRIPT_DIR / "生成n8n离线导入前凭据隔离与启用禁入包.py",
    SCRIPT_DIR / "执行n8n离线导入前凭据隔离只读检查.py",
    SCRIPT_DIR / "验证n8n离线导入前凭据隔离与启用禁入包.py",
]

FALSE_KEYS = {
    "import_allowed",
    "activation_allowed",
    "credential_values_present",
    "webhook_enabled",
    "real_trigger",
    "network_request_enabled",
    "n8n_connection_enabled",
    "n8n_config_write_enabled",
    "service_reload_enabled",
    "enterprise_wechat_send_enabled",
    "enabled",
    "registered_in_n8n",
    "value_present",
}
TRUE_GUARD_KEYS = {"offline", "read_only", "dry_run"}
FORBIDDEN_REAL_VALUE_RE = re.compile(
    r"https?://|bearer\s+|api[_ -]?key\s*[:=]|secret\s*[:=]|password\s*[:=]|token\s*[:=]",
    re.IGNORECASE,
)
FORBIDDEN_CODE_RE = re.compile(
    r"\b(requests|urllib|http\.client|socket|websocket|webbrowser)\b",
    re.IGNORECASE,
)


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def walk(obj: Any, path: str = "$") -> list[tuple[str, Any]]:
    items = [(path, obj)]
    if isinstance(obj, dict):
        for key, value in obj.items():
            items.extend(walk(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            items.extend(walk(value, f"{path}[{index}]"))
    return items


def flatten_dicts(*roots: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for root in roots:
        for _, value in walk(root):
            if isinstance(value, dict):
                result.append(value)
    return result


def check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": passed, "detail": detail}


def false_key_findings(objects: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    for index, item in enumerate(objects, start=1):
        for key in FALSE_KEYS:
            if key in item and item.get(key) is not False:
                findings.append(f"object{index}.{key}={item.get(key)!r}")
    return findings


def true_guard_findings(objects: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    guarded = [item for item in objects if any(key in item for key in TRUE_GUARD_KEYS)]
    for index, item in enumerate(guarded, start=1):
        for key in TRUE_GUARD_KEYS:
            if key in item and item.get(key) is not True:
                findings.append(f"guard{index}.{key}={item.get(key)!r}")
    return findings


def forbidden_real_value_findings(*roots: Any) -> list[str]:
    findings: list[str] = []
    for root_index, root in enumerate(roots, start=1):
        for path, value in walk(root):
            if isinstance(value, str) and FORBIDDEN_REAL_VALUE_RE.search(value):
                findings.append(f"root{root_index}:{path}")
    return findings


def credential_value_field_findings(slots: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    for slot in slots:
        if slot.get("value_present") is not False:
            findings.append(f"{slot.get('slot_id')}.value_present")
        for key in ("value", "plain_value", "runtime_value", "credential_value"):
            if key in slot and slot.get(key):
                findings.append(f"{slot.get('slot_id')}.{key}")
    return findings


def code_redline_findings() -> list[str]:
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
    expected_files = [
        PACKAGE_JSON,
        PACKAGE_MD,
        CREDENTIAL_ISOLATION_JSON,
        CREDENTIAL_ISOLATION_MD,
        WEBHOOK_DISABLED_JSON,
        IMPORT_BAN_JSON,
        ACTIVATION_CONFIRM_JSON,
        ROLLBACK_REQUIREMENTS_JSON,
        REPORT_JSON,
        REPORT_MD,
    ]
    missing = [str(path) for path in expected_files if not path.exists()]

    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    credential_isolation = read_json(CREDENTIAL_ISOLATION_JSON) if CREDENTIAL_ISOLATION_JSON.exists() else {}
    webhook_disabled = read_json(WEBHOOK_DISABLED_JSON) if WEBHOOK_DISABLED_JSON.exists() else {}
    import_bans = read_json(IMPORT_BAN_JSON) if IMPORT_BAN_JSON.exists() else {}
    confirmations = read_json(ACTIVATION_CONFIRM_JSON) if ACTIVATION_CONFIRM_JSON.exists() else {}
    rollback_requirements = read_json(ROLLBACK_REQUIREMENTS_JSON) if ROLLBACK_REQUIREMENTS_JSON.exists() else {}
    report = read_json(REPORT_JSON) if REPORT_JSON.exists() else {}

    slots = credential_isolation.get("slots", [])
    webhooks = webhook_disabled.get("items", [])
    conditions = import_bans.get("conditions", [])
    confirmation_items = confirmations.get("items", [])
    rollback_items = rollback_requirements.get("requirements", [])
    objects = flatten_dicts(package, credential_isolation, webhook_disabled, import_bans, confirmations, rollback_requirements, report)

    false_findings = false_key_findings(objects)
    true_findings = true_guard_findings(objects)
    real_value_findings = forbidden_real_value_findings(package, credential_isolation, webhook_disabled, import_bans, confirmations, rollback_requirements, report)
    credential_findings = credential_value_field_findings(slots)
    code_findings = code_redline_findings()

    checks = [
        check("产物文件齐全", not missing, "全部存在" if not missing else "；".join(missing)),
        check("凭据隔离项齐全", len(slots) >= 5 and not credential_findings, f"slot_count={len(slots)}"),
        check("webhook全部禁用", len(webhooks) >= 3 and all(item.get("enabled") is False and item.get("real_trigger") is False for item in webhooks), f"webhook_count={len(webhooks)}"),
        check("禁止导入", package.get("import_allowed") is False and report.get("import_allowed") is False, "import_allowed=false"),
        check("禁止启用", package.get("activation_allowed") is False and report.get("activation_allowed") is False, "activation_allowed=false"),
        check("导入前禁入条件齐全", len(conditions) >= 6, f"condition_count={len(conditions)}"),
        check("启用前总管确认项齐全", len(confirmation_items) >= 7 and confirmations.get("supervisor_confirmed") is False, f"confirmation_count={len(confirmation_items)}"),
        check("回滚要求齐全", len(rollback_items) >= 5 and rollback_requirements.get("rollback_requirements_ready") is True, f"rollback_count={len(rollback_items)}"),
        check("禁入开关全部为 false", not false_findings, "通过" if not false_findings else "；".join(false_findings[:40])),
        check("只读离线护栏为 true", not true_findings, "通过" if not true_findings else "；".join(true_findings[:40])),
        check("无真实 URL 或密钥值", not real_value_findings, "通过" if not real_value_findings else "；".join(real_value_findings[:20])),
        check("脚本未引入网络或浏览器模块", not code_findings, "通过" if not code_findings else "；".join(code_findings)),
        check("只读检查报告 error_count=0", report.get("error_count") == 0, f"report_error_count={report.get('error_count')}"),
    ]
    errors = [item["check"] for item in checks if not item["passed"]]
    verify_report = {
        "name": "n8n离线导入前凭据隔离与启用禁入包验收",
        "verified_at": now_text(),
        "passed": len(errors) == 0,
        "status": "pass" if not errors else "blocked",
        "import_allowed": False,
        "activation_allowed": False,
        "credential_values_present": False,
        "webhook_enabled": False,
        "real_trigger": False,
        "error_count": len(errors),
        "errors": errors,
        "checks": checks,
        "metrics": {
            "credential_slot_count": len(slots),
            "webhook_disabled_count": sum(1 for item in webhooks if item.get("enabled") is False),
            "import_ban_condition_count": len(conditions),
            "supervisor_confirmation_count": len(confirmation_items),
            "rollback_requirement_count": len(rollback_items),
        },
        "artifacts": {
            "package_json": str(PACKAGE_JSON),
            "package_markdown": str(PACKAGE_MD),
            "credential_isolation_json": str(CREDENTIAL_ISOLATION_JSON),
            "credential_isolation_markdown": str(CREDENTIAL_ISOLATION_MD),
            "webhook_disabled_json": str(WEBHOOK_DISABLED_JSON),
            "import_ban_json": str(IMPORT_BAN_JSON),
            "activation_confirm_json": str(ACTIVATION_CONFIRM_JSON),
            "rollback_requirements_json": str(ROLLBACK_REQUIREMENTS_JSON),
            "readonly_report_json": str(REPORT_JSON),
            "readonly_report_markdown": str(REPORT_MD),
            "verify_log": str(LOG_JSON),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_JSON.write_text(json.dumps(verify_report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "passed": verify_report["passed"],
                "status": verify_report["status"],
                "error_count": verify_report["error_count"],
                "log": str(LOG_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if verify_report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
