# -*- coding: utf-8 -*-
"""验证 n8n 禁用态导入草案人工签收与回滚演练包。"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
SCRIPT_DIR = ROOT / "02脚本"
DATA_DIR = ROOT / "03数据" / "91n8n禁用态导入草案人工签收与回滚演练包"
LOG_DIR = ROOT / "04日志" / "n8n禁用态导入草案人工签收与回滚演练包验收"

PACKAGE_JSON = DATA_DIR / "n8n禁用态导入草案人工签收与回滚演练包_最新.json"
PACKAGE_MD = DATA_DIR / "n8n禁用态导入草案人工签收与回滚演练包_最新.md"
SOURCE_SUMMARY_JSON = DATA_DIR / "第87包承接摘要_最新.json"
SIGNOFF_JSON = DATA_DIR / "n8n禁用态导入草案人工签收单_最新.json"
SIGNOFF_MD = DATA_DIR / "n8n禁用态导入草案人工签收单_最新.md"
ROLLBACK_JSON = DATA_DIR / "n8n禁用态导入草案禁用态回滚演练_最新.json"
ROLLBACK_MD = DATA_DIR / "n8n禁用态导入草案禁用态回滚演练_最新.md"
DRILL_REPORT_JSON = DATA_DIR / "n8n禁用态导入草案只读演练报告_最新.json"
DRILL_REPORT_MD = DATA_DIR / "n8n禁用态导入草案只读演练报告_最新.md"
LOG_JSON = LOG_DIR / "n8n-disabled-import-signoff-rollback-drill-verify-最新.json"

SCRIPT_FILES = [
    SCRIPT_DIR / "生成n8n禁用态导入草案人工签收与回滚演练包.py",
    SCRIPT_DIR / "执行n8n禁用态导入草案只读回滚演练.py",
    SCRIPT_DIR / "验证n8n禁用态导入草案人工签收与回滚演练包.py",
]

FALSE_KEYS = {
    "active",
    "webhook_enabled",
    "real_trigger",
    "credential_values_present",
    "network_request",
    "rollback_executed",
    "import_allowed",
    "activation_allowed",
    "n8n_connection_allowed",
    "n8n_config_write_allowed",
    "service_reload_allowed",
    "enterprise_wechat_send_allowed",
    "formal_rule_write_allowed",
    "signed",
}
TRUE_KEYS = {"offline", "read_only", "dry_run", "simulation_only", "disabled", "requires_supervisor_confirmation", "unsigned"}
REQUIRED_SCENARIOS = {"导入前备份", "导入失败回滚", "误激活回滚", "凭据泄露阻断"}
FORBIDDEN_CODE_RE = re.compile(r"\b(requests|urllib|http\.client|socket|websocket|webbrowser)\b", re.IGNORECASE)
REAL_URL_RE = re.compile(r"https?://|www\.|[a-z0-9][a-z0-9.-]+\.(?:com|cn|net|org)(?:/|\b)", re.IGNORECASE)
SECRET_SHAPE_RE = re.compile(r"bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|secret\s*[:=]\s*\S+|password\s*[:=]\s*\S+|token\s*[:=]\s*\S+", re.IGNORECASE)


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


def check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": passed, "detail": detail, "error_count": 0 if passed else 1}


def bool_findings(*roots: Any) -> list[str]:
    findings: list[str] = []
    for root in roots:
        for path, value in walk(root):
            key = path.rsplit(".", 1)[-1]
            if key in FALSE_KEYS and value is not False:
                findings.append(f"{path}={value!r}")
            if key in TRUE_KEYS and value is not True:
                findings.append(f"{path}={value!r}")
            if value is True and key.lower() in {"active", "webhook_enabled", "real_trigger", "network_request", "rollback_executed"}:
                findings.append(f"{path}=true")
    return findings


def real_value_findings(*roots: Any) -> list[str]:
    findings: list[str] = []
    forbidden_value_keys = {"value", "plain_value", "runtime_value", "credential_value", "secret_value", "password", "token"}
    for root in roots:
        for path, value in walk(root):
            key = path.rsplit(".", 1)[-1].lower()
            if key in forbidden_value_keys and value:
                findings.append(f"{path}:credential_value_field")
            if isinstance(value, str):
                if REAL_URL_RE.search(value):
                    findings.append(f"{path}:real_url_shape")
                if SECRET_SHAPE_RE.search(value):
                    findings.append(f"{path}:secret_shape")
    return findings


def scenario_findings(rollback_drill: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    scenarios = rollback_drill.get("scenarios", [])
    titles = {item.get("title") for item in scenarios}
    missing = REQUIRED_SCENARIOS - titles
    findings.extend(f"missing:{title}" for title in sorted(missing))
    for item in scenarios:
        scenario_id = item.get("scenario_id", "unknown")
        if item.get("simulation_only") is not True:
            findings.append(f"{scenario_id}:simulation_only_not_true")
        if item.get("rollback_executed") is not False:
            findings.append(f"{scenario_id}:rollback_executed_not_false")
        if item.get("network_request") is not False:
            findings.append(f"{scenario_id}:network_request_not_false")
        expected = item.get("expected_result", {})
        for key in ["disabled", "active", "webhook_enabled", "real_trigger", "credential_values_present", "network_request", "rollback_executed"]:
            if key == "disabled" and expected.get(key) is not True:
                findings.append(f"{scenario_id}:expected_disabled_not_true")
            if key != "disabled" and expected.get(key) is not False:
                findings.append(f"{scenario_id}:expected_{key}_not_false")
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
        SOURCE_SUMMARY_JSON,
        SIGNOFF_JSON,
        SIGNOFF_MD,
        ROLLBACK_JSON,
        ROLLBACK_MD,
        DRILL_REPORT_JSON,
        DRILL_REPORT_MD,
        *SCRIPT_FILES,
    ]
    missing = [str(path) for path in expected_files if not path.exists()]

    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    source_summary = read_json(SOURCE_SUMMARY_JSON) if SOURCE_SUMMARY_JSON.exists() else {}
    signoff = read_json(SIGNOFF_JSON) if SIGNOFF_JSON.exists() else {}
    rollback_drill = read_json(ROLLBACK_JSON) if ROLLBACK_JSON.exists() else {}
    drill_report = read_json(DRILL_REPORT_JSON) if DRILL_REPORT_JSON.exists() else {}

    bool_errors = bool_findings(package, source_summary, signoff, rollback_drill, drill_report)
    real_value_errors = real_value_findings(package, source_summary, signoff, rollback_drill, drill_report)
    scenario_errors = scenario_findings(rollback_drill)
    code_errors = code_redline_findings()

    checks = [
        check("产物文件齐全", not missing, "全部存在" if not missing else "；".join(missing)),
        check("人工签收单默认未签收", signoff.get("status") == "unsigned" and signoff.get("unsigned") is True and signoff.get("signed") is False, "status=unsigned signed=false"),
        check("人工签收禁止导入与激活", signoff.get("import_allowed") is False and signoff.get("activation_allowed") is False, "import_allowed=false activation_allowed=false"),
        check("主管确认必需", signoff.get("requires_supervisor_confirmation") is True, "requires_supervisor_confirmation=true"),
        check("回滚演练四场景齐全且仅仿真", not scenario_errors, "通过" if not scenario_errors else "；".join(scenario_errors)),
        check("只读演练报告通过", drill_report.get("status") == "pass" and drill_report.get("error_count") == 0, f"status={drill_report.get('status')} error_count={drill_report.get('error_count')}"),
        check("报告确认禁用态", drill_report.get("disabled") is True and drill_report.get("active") is False, "disabled=true active=false"),
        check("报告确认无触发", drill_report.get("webhook_enabled") is False and drill_report.get("real_trigger") is False, "webhook_enabled=false real_trigger=false"),
        check("报告确认无凭据值", drill_report.get("credential_values_present") is False, "credential_values_present=false"),
        check("报告确认无网络请求与无真实回滚", drill_report.get("network_request") is False and drill_report.get("rollback_executed") is False, "network_request=false rollback_executed=false"),
        check("布尔红线无越界", not bool_errors, "通过" if not bool_errors else "；".join(bool_errors[:50])),
        check("无真实URL或密钥形态", not real_value_errors, "通过" if not real_value_errors else "；".join(real_value_errors[:30])),
        check("脚本未引入网络或浏览器模块", not code_errors, "通过" if not code_errors else "；".join(code_errors)),
    ]
    errors = [item["check"] for item in checks if not item["passed"]]

    verify_report = {
        "name": "n8n禁用态导入草案人工签收与回滚演练包验收",
        "verified_at": now_text(),
        "passed": len(errors) == 0,
        "status": "pass" if not errors else "blocked",
        "disabled": True,
        "active": False,
        "webhook_enabled": False,
        "real_trigger": False,
        "credential_values_present": False,
        "network_request": False,
        "rollback_executed": False,
        "import_allowed": False,
        "activation_allowed": False,
        "requires_supervisor_confirmation": True,
        "error_count": len(errors),
        "errors": errors,
        "checks": checks,
        "metrics": {
            "scenario_count": len(rollback_drill.get("scenarios", [])),
            "simulation_only_scenario_count": sum(1 for item in rollback_drill.get("scenarios", []) if item.get("simulation_only") is True),
            "source87_package_exists": source_summary.get("source_package_exists", False),
            "source87_draft_exists": source_summary.get("source_draft_exists", False),
            "source87_scan_report_exists": source_summary.get("source_scan_report_exists", False),
        },
        "artifacts": {
            "package_json": str(PACKAGE_JSON),
            "package_markdown": str(PACKAGE_MD),
            "source_summary_json": str(SOURCE_SUMMARY_JSON),
            "signoff_json": str(SIGNOFF_JSON),
            "signoff_markdown": str(SIGNOFF_MD),
            "rollback_json": str(ROLLBACK_JSON),
            "rollback_markdown": str(ROLLBACK_MD),
            "drill_report_json": str(DRILL_REPORT_JSON),
            "drill_report_markdown": str(DRILL_REPORT_MD),
            "verify_log": str(LOG_JSON),
        },
        "redlines": [
            "不接n8n",
            "不触发webhook",
            "不请求网络",
            "不真实发送企业微信",
            "不改运行配置",
            "不重载服务",
            "不写正式规则",
        ],
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_JSON.write_text(json.dumps(verify_report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": verify_report["passed"], "status": verify_report["status"], "error_count": verify_report["error_count"], "log": str(LOG_JSON)}, ensure_ascii=False))
    return 0 if verify_report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
