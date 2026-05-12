# -*- coding: utf-8 -*-
"""验证 n8n 离线导入包静态扫描与禁用态导出草案包。"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
SCRIPT_DIR = ROOT / "02脚本"
DATA_DIR = ROOT / "03数据" / "87n8n离线导入包静态扫描与禁用态导出草案包"
LOG_DIR = ROOT / "04日志" / "n8n离线导入包静态扫描与禁用态导出草案包验收"

PACKAGE_JSON = DATA_DIR / "n8n离线导入包静态扫描与禁用态导出草案包_最新.json"
PACKAGE_MD = DATA_DIR / "n8n离线导入包静态扫描与禁用态导出草案包_最新.md"
DRAFT_JSON = DATA_DIR / "n8n禁用态离线导入包草案_最新.json"
DRAFT_MD = DATA_DIR / "n8n禁用态离线导入包草案_最新.md"
SCAN_RULES_JSON = DATA_DIR / "静态扫描规则_最新.json"
SOURCE_SUMMARY_JSON = DATA_DIR / "第84包承接摘要_最新.json"
SCAN_REPORT_JSON = DATA_DIR / "n8n离线导入包静态扫描报告_最新.json"
SCAN_REPORT_MD = DATA_DIR / "n8n离线导入包静态扫描报告_最新.md"
LOG_JSON = LOG_DIR / "n8n-offline-disabled-import-static-scan-verify-最新.json"

SCRIPT_FILES = [
    SCRIPT_DIR / "生成n8n离线导入包静态扫描与禁用态导出草案包.py",
    SCRIPT_DIR / "执行n8n离线导入包静态扫描.py",
    SCRIPT_DIR / "验证n8n离线导入包静态扫描与禁用态导出草案包.py",
]

FALSE_KEYS = {
    "active",
    "webhook_enabled",
    "real_trigger",
    "credential_values_present",
    "import_allowed",
    "activation_allowed",
    "external_network_action_allowed",
    "n8n_connection_allowed",
    "n8n_config_write_allowed",
    "service_reload_allowed",
    "enterprise_wechat_send_allowed",
    "register_webhook",
    "save_runtime_data",
    "contains_real_url",
    "contains_real_secret",
    "contains_credential_value",
}
TRUE_KEYS = {"disabled", "offline", "read_only", "dry_run"}
REAL_URL_RE = re.compile(r"https?://|www\.|[a-z0-9][a-z0-9.-]+\.(?:com|cn|net|org)(?:/|\b)", re.IGNORECASE)
SECRET_SHAPE_RE = re.compile(
    r"bearer\s+[a-z0-9._-]+|api[_ -]?key\s*[:=]\s*\S+|secret\s*[:=]\s*\S+|password\s*[:=]\s*\S+|token\s*[:=]\s*\S+",
    re.IGNORECASE,
)
FORBIDDEN_CODE_RE = re.compile(r"\b(requests|urllib|http\.client|socket|websocket|webbrowser)\b", re.IGNORECASE)


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
    return {"check": name, "passed": passed, "detail": detail}


def bool_findings(*roots: Any) -> list[str]:
    findings: list[str] = []
    for root in roots:
        for path, value in walk(root):
            key = path.rsplit(".", 1)[-1]
            if key in FALSE_KEYS and value is not False:
                findings.append(f"{path}={value!r}")
            if key in TRUE_KEYS and value is not True:
                findings.append(f"{path}={value!r}")
            key_lower = key.lower()
            if value is True and ("webhook" in key_lower or "trigger" in key_lower or key_lower == "active"):
                findings.append(f"{path}=true")
    return findings


def real_value_findings(*roots: Any) -> list[str]:
    findings: list[str] = []
    for root in roots:
        for path, value in walk(root):
            if not isinstance(value, str):
                continue
            if REAL_URL_RE.search(value):
                findings.append(f"{path}:real_url_shape")
            if SECRET_SHAPE_RE.search(value):
                findings.append(f"{path}:secret_shape")
    return findings


def credential_value_field_findings(*roots: Any) -> list[str]:
    findings: list[str] = []
    for root in roots:
        for path, value in walk(root):
            key = path.rsplit(".", 1)[-1]
            if key in {"value", "plain_value", "runtime_value", "credential_value", "secret_value"} and value:
                findings.append(path)
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


def action_findings(draft: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    nodes = draft.get("workflow", {}).get("nodes", [])
    for node in nodes:
        node_name = node.get("name", "unknown")
        action_surface = {
            "name": node.get("name", ""),
            "type": node.get("type", ""),
            "purpose": node.get("purpose", ""),
            "operation": node.get("operation", ""),
        }
        node_text = json.dumps(action_surface, ensure_ascii=False).lower()
        if any(word in node_text for word in ["http_request", "webhook_call", "external_api_call", "socket_connect", "browser_open"]):
            findings.append(f"{node_name}:external_network_action")
        if any(word in node_text for word in ["enterprise_wechat_send", "wecom_send", "企业微信发送", "真实企业微信发送"]):
            findings.append(f"{node_name}:enterprise_wechat_send_action")
        if node.get("type") != "disabled.placeholder":
            findings.append(f"{node_name}:not_disabled_placeholder")
    return findings


def main() -> int:
    expected_files = [
        PACKAGE_JSON,
        PACKAGE_MD,
        DRAFT_JSON,
        DRAFT_MD,
        SCAN_RULES_JSON,
        SOURCE_SUMMARY_JSON,
        SCAN_REPORT_JSON,
        SCAN_REPORT_MD,
    ]
    missing = [str(path) for path in expected_files if not path.exists()]

    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    draft = read_json(DRAFT_JSON) if DRAFT_JSON.exists() else {}
    scan_rules = read_json(SCAN_RULES_JSON) if SCAN_RULES_JSON.exists() else {}
    source_summary = read_json(SOURCE_SUMMARY_JSON) if SOURCE_SUMMARY_JSON.exists() else {}
    scan_report = read_json(SCAN_REPORT_JSON) if SCAN_REPORT_JSON.exists() else {}
    workflow = draft.get("workflow", {})
    nodes = workflow.get("nodes", [])

    bool_errors = bool_findings(package, draft, scan_rules, source_summary, scan_report)
    real_value_errors = real_value_findings(package, draft, scan_rules, source_summary, scan_report)
    credential_errors = credential_value_field_findings(draft)
    action_errors = action_findings(draft)
    code_errors = code_redline_findings()

    checks = [
        check("产物文件齐全", not missing, "全部存在" if not missing else "；".join(missing)),
        check("导入包草案存在", DRAFT_JSON.exists() and DRAFT_MD.exists(), f"json={DRAFT_JSON.exists()} md={DRAFT_MD.exists()}"),
        check("草案禁用态完整", draft.get("disabled") is True and draft.get("active") is False and workflow.get("disabled") is True and workflow.get("active") is False, "disabled=true active=false"),
        check("webhook与真实触发为false", draft.get("webhook_enabled") is False and draft.get("real_trigger") is False and workflow.get("webhook_enabled") is False and workflow.get("real_trigger") is False, "webhook_enabled=false real_trigger=false"),
        check("凭据值不存在", draft.get("credential_values_present") is False and not credential_errors, "credential_values_present=false"),
        check("导入与启用不允许", draft.get("import_allowed") is False and draft.get("activation_allowed") is False and package.get("import_allowed") is False and package.get("activation_allowed") is False, "import_allowed=false activation_allowed=false"),
        check("扫描错误数为0", scan_report.get("scan_error_count") == 0, f"scan_error_count={scan_report.get('scan_error_count')}"),
        check("扫描报告error_count=0", scan_report.get("error_count") == 0, f"report_error_count={scan_report.get('error_count')}"),
        check("布尔红线无越界", not bool_errors, "通过" if not bool_errors else "；".join(bool_errors[:40])),
        check("无真实URL或密钥形态", not real_value_errors, "通过" if not real_value_errors else "；".join(real_value_errors[:20])),
        check("无外部网络动作与真实企业微信发送动作", not action_errors, "通过" if not action_errors else "；".join(action_errors)),
        check("脚本未引入网络或浏览器模块", not code_errors, "通过" if not code_errors else "；".join(code_errors)),
        check("节点均为禁用占位", len(nodes) >= 5 and all(node.get("disabled") is True and node.get("active") is False for node in nodes), f"node_count={len(nodes)}"),
    ]
    errors = [item["check"] for item in checks if not item["passed"]]

    verify_report = {
        "name": "n8n离线导入包静态扫描与禁用态导出草案包验收",
        "verified_at": now_text(),
        "passed": len(errors) == 0,
        "status": "pass" if not errors else "blocked",
        "disabled": True,
        "active": False,
        "webhook_enabled": False,
        "real_trigger": False,
        "credential_values_present": False,
        "import_allowed": False,
        "activation_allowed": False,
        "scan_error_count": scan_report.get("scan_error_count", -1),
        "error_count": len(errors),
        "errors": errors,
        "checks": checks,
        "metrics": {
            "node_count": len(nodes),
            "disabled_node_count": sum(1 for node in nodes if node.get("disabled") is True),
            "scan_rule_count": scan_rules.get("rule_count", 0),
            "source84_exists": source_summary.get("source_exists", False),
        },
        "artifacts": {
            "package_json": str(PACKAGE_JSON),
            "package_markdown": str(PACKAGE_MD),
            "draft_json": str(DRAFT_JSON),
            "draft_markdown": str(DRAFT_MD),
            "scan_rules_json": str(SCAN_RULES_JSON),
            "source_summary_json": str(SOURCE_SUMMARY_JSON),
            "scan_report_json": str(SCAN_REPORT_JSON),
            "scan_report_markdown": str(SCAN_REPORT_MD),
            "verify_log": str(LOG_JSON),
        },
        "redlines": [
            "不接 n8n",
            "不触发 webhook",
            "不请求网络",
            "不改配置",
            "不重载服务",
            "不真实发送企业微信",
        ],
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_JSON.write_text(json.dumps(verify_report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "passed": verify_report["passed"],
                "status": verify_report["status"],
                "scan_error_count": verify_report["scan_error_count"],
                "error_count": verify_report["error_count"],
                "log": str(LOG_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if verify_report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
