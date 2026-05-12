# -*- coding: utf-8 -*-
"""执行 n8n 离线导入包静态扫描。

只读取本包禁用态草案和扫描规则；不连接 n8n，不触发 webhook，
不请求网络，不写 n8n 配置，不重载服务，不真实发送企业微信。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "87n8n离线导入包静态扫描与禁用态导出草案包"

PACKAGE_JSON = DATA_DIR / "n8n离线导入包静态扫描与禁用态导出草案包_最新.json"
DRAFT_JSON = DATA_DIR / "n8n禁用态离线导入包草案_最新.json"
DRAFT_MD = DATA_DIR / "n8n禁用态离线导入包草案_最新.md"
SCAN_RULES_JSON = DATA_DIR / "静态扫描规则_最新.json"
SCAN_REPORT_JSON = DATA_DIR / "n8n离线导入包静态扫描报告_最新.json"
SCAN_REPORT_MD = DATA_DIR / "n8n离线导入包静态扫描报告_最新.md"

MODE = "offline/disabled_import_static_scan"

GLOBAL_GUARD = {
    "mode": MODE,
    "offline": True,
    "read_only": True,
    "dry_run": True,
    "disabled": True,
    "active": False,
    "webhook_enabled": False,
    "real_trigger": False,
    "credential_values_present": False,
    "import_allowed": False,
    "activation_allowed": False,
    "external_network_action_allowed": False,
    "n8n_connection_allowed": False,
    "n8n_config_write_allowed": False,
    "service_reload_allowed": False,
    "enterprise_wechat_send_allowed": False,
}

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
NETWORK_ACTION_WORDS = {"http_request", "webhook_call", "external_api_call", "socket_connect", "browser_open"}
ENTERPRISE_WECHAT_SEND_WORDS = {"enterprise_wechat_send", "wecom_send", "企业微信发送", "真实企业微信发送"}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def guard_copy(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    data = dict(GLOBAL_GUARD)
    if extra:
        data.update(extra)
    return data


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
    return guard_copy({"check": name, "passed": passed, "detail": detail, "error_count": 0 if passed else 1})


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
        if any(word in node_text for word in NETWORK_ACTION_WORDS):
            findings.append(f"{node_name}:external_network_action")
        if any(word.lower() in node_text for word in ENTERPRISE_WECHAT_SEND_WORDS):
            findings.append(f"{node_name}:enterprise_wechat_send_action")
        if node.get("type") != "disabled.placeholder":
            findings.append(f"{node_name}:not_disabled_placeholder")
    return findings


def credential_value_field_findings(draft: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    for path, value in walk(draft):
        key = path.rsplit(".", 1)[-1]
        if key in {"value", "plain_value", "runtime_value", "credential_value", "secret_value"} and value:
            findings.append(path)
    return findings


def build_md(report: dict[str, Any]) -> str:
    lines = [
        "# n8n 离线导入包静态扫描报告",
        "",
        f"- 扫描时间：{report['scanned_at']}",
        f"- 状态：{report['status']}",
        "- disabled=true",
        "- active=false",
        "- webhook_enabled=false",
        "- real_trigger=false",
        "- credential_values_present=false",
        "- import_allowed=false",
        "- activation_allowed=false",
        f"- scan_error_count={report['scan_error_count']}",
        f"- error_count={report['error_count']}",
        "",
        "| 检查项 | 结果 | 说明 |",
        "| --- | --- | --- |",
    ]
    for item in report["checks"]:
        lines.append(f"| {item['check']} | {item['passed']} | {item['detail']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    package = read_json(PACKAGE_JSON)
    draft = read_json(DRAFT_JSON)
    scan_rules = read_json(SCAN_RULES_JSON)
    draft_md_exists = DRAFT_MD.exists()

    workflow = draft.get("workflow", {})
    nodes = workflow.get("nodes", [])
    bool_errors = bool_findings(package, draft, scan_rules)
    real_value_errors = real_value_findings(package, draft, scan_rules)
    action_errors = action_findings(draft)
    credential_errors = credential_value_field_findings(draft)

    checks = [
        check("草案文件存在", DRAFT_JSON.exists() and draft_md_exists, f"json={DRAFT_JSON.exists()} md={draft_md_exists}"),
        check("草案顶层禁用态完整", draft.get("disabled") is True and draft.get("active") is False, "disabled=true active=false"),
        check("工作流禁用态完整", workflow.get("disabled") is True and workflow.get("active") is False, "workflow.disabled=true workflow.active=false"),
        check("webhook与触发器禁用", draft.get("webhook_enabled") is False and draft.get("real_trigger") is False and workflow.get("webhook_enabled") is False and workflow.get("real_trigger") is False, "webhook_enabled=false real_trigger=false"),
        check("凭据值缺席", draft.get("credential_values_present") is False and not credential_errors, "credential_values_present=false"),
        check("导入启用双禁", draft.get("import_allowed") is False and draft.get("activation_allowed") is False, "import_allowed=false activation_allowed=false"),
        check("布尔开关无越界", not bool_errors, "通过" if not bool_errors else "；".join(bool_errors[:30])),
        check("无真实URL或密钥形态", not real_value_errors, "通过" if not real_value_errors else "；".join(real_value_errors[:20])),
        check("无外部网络动作", not action_errors or all("external_network_action" not in item for item in action_errors), "通过" if not action_errors else "；".join(action_errors)),
        check("无真实企业微信发送动作", not action_errors or all("enterprise_wechat_send_action" not in item for item in action_errors), "通过" if not action_errors else "；".join(action_errors)),
        check("节点均为禁用占位", len(nodes) >= 5 and all(node.get("disabled") is True and node.get("active") is False for node in nodes), f"node_count={len(nodes)}"),
        check("静态扫描规则存在", scan_rules.get("rule_count", 0) >= 7, f"rule_count={scan_rules.get('rule_count', 0)}"),
    ]
    errors = [item["check"] for item in checks if not item["passed"]]
    scan_error_count = len(errors)

    report = guard_copy(
        {
            "name": "n8n离线导入包静态扫描报告",
            "scanned_at": now_text(),
            "status": "pass" if scan_error_count == 0 else "blocked",
            "scan_error_count": scan_error_count,
            "checks": checks,
            "errors": errors,
            "findings": {
                "bool_errors": bool_errors,
                "real_value_errors": real_value_errors,
                "action_errors": action_errors,
                "credential_errors": credential_errors,
            },
            "metrics": {
                "node_count": len(nodes),
                "disabled_node_count": sum(1 for node in nodes if node.get("disabled") is True),
                "scan_rule_count": scan_rules.get("rule_count", 0),
            },
            "source_files": {
                "package": str(PACKAGE_JSON),
                "draft": str(DRAFT_JSON),
                "draft_markdown": str(DRAFT_MD),
                "scan_rules": str(SCAN_RULES_JSON),
            },
            "error_count": scan_error_count,
        }
    )
    write_json(SCAN_REPORT_JSON, report)
    write_text(SCAN_REPORT_MD, build_md(report))
    print(
        json.dumps(
            {
                "status": report["status"],
                "scan_error_count": report["scan_error_count"],
                "error_count": report["error_count"],
                "output": str(SCAN_REPORT_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if scan_error_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
