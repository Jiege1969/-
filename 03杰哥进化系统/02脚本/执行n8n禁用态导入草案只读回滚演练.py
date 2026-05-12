# -*- coding: utf-8 -*-
"""执行 n8n 禁用态导入草案只读回滚演练。

只读取第91包本地 JSON/MD 材料并生成演练报告；不连接 n8n，不触发 webhook，
不请求网络，不导入，不激活，不执行真实回滚。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "91n8n禁用态导入草案人工签收与回滚演练包"

PACKAGE_JSON = DATA_DIR / "n8n禁用态导入草案人工签收与回滚演练包_最新.json"
SIGNOFF_JSON = DATA_DIR / "n8n禁用态导入草案人工签收单_最新.json"
SIGNOFF_MD = DATA_DIR / "n8n禁用态导入草案人工签收单_最新.md"
ROLLBACK_JSON = DATA_DIR / "n8n禁用态导入草案禁用态回滚演练_最新.json"
ROLLBACK_MD = DATA_DIR / "n8n禁用态导入草案禁用态回滚演练_最新.md"
DRILL_REPORT_JSON = DATA_DIR / "n8n禁用态导入草案只读演练报告_最新.json"
DRILL_REPORT_MD = DATA_DIR / "n8n禁用态导入草案只读演练报告_最新.md"

MODE = "offline/disabled_import_read_only_rollback_drill"

GLOBAL_GUARD = {
    "mode": MODE,
    "offline": True,
    "read_only": True,
    "dry_run": True,
    "simulation_only": True,
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
    "n8n_connection_allowed": False,
    "n8n_config_write_allowed": False,
    "service_reload_allowed": False,
    "enterprise_wechat_send_allowed": False,
    "formal_rule_write_allowed": False,
}

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
SCENARIO_TITLES = {"导入前备份", "导入失败回滚", "误激活回滚", "凭据泄露阻断"}


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
            if value is True and key.lower() in {"active", "webhook_enabled", "real_trigger", "network_request", "rollback_executed"}:
                findings.append(f"{path}=true")
    return findings


def credential_value_field_findings(*roots: Any) -> list[str]:
    findings: list[str] = []
    forbidden_keys = {"value", "plain_value", "runtime_value", "credential_value", "secret_value", "password", "token"}
    for root in roots:
        for path, value in walk(root):
            key = path.rsplit(".", 1)[-1].lower()
            if key in forbidden_keys and value:
                findings.append(path)
    return findings


def scenario_findings(rollback_drill: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    scenarios = rollback_drill.get("scenarios", [])
    titles = {item.get("title") for item in scenarios}
    missing_titles = SCENARIO_TITLES - titles
    findings.extend(f"missing:{title}" for title in sorted(missing_titles))
    for item in scenarios:
        if item.get("simulation_only") is not True:
            findings.append(f"{item.get('scenario_id')}:simulation_only_not_true")
        if item.get("rollback_executed") is not False:
            findings.append(f"{item.get('scenario_id')}:rollback_executed_not_false")
        if item.get("network_request") is not False:
            findings.append(f"{item.get('scenario_id')}:network_request_not_false")
    return findings


def build_md(report: dict[str, Any]) -> str:
    lines = [
        "# n8n禁用态导入草案只读演练报告",
        "",
        f"- 演练时间：{report['drilled_at']}",
        f"- 状态：{report['status']}",
        "- disabled=true",
        "- active=false",
        "- webhook_enabled=false",
        "- real_trigger=false",
        "- credential_values_present=false",
        "- network_request=false",
        "- rollback_executed=false",
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
    signoff = read_json(SIGNOFF_JSON)
    rollback_drill = read_json(ROLLBACK_JSON)

    bool_errors = bool_findings(package, signoff, rollback_drill)
    credential_errors = credential_value_field_findings(signoff, rollback_drill)
    scenario_errors = scenario_findings(rollback_drill)
    markdown_exists = SIGNOFF_MD.exists() and ROLLBACK_MD.exists()

    checks = [
        check("人工签收单默认未签收", signoff.get("status") == "unsigned" and signoff.get("unsigned") is True and signoff.get("signed") is False, "status=unsigned signed=false"),
        check("导入与激活保持禁止", signoff.get("import_allowed") is False and signoff.get("activation_allowed") is False, "import_allowed=false activation_allowed=false"),
        check("主管确认为必需", signoff.get("requires_supervisor_confirmation") is True, "requires_supervisor_confirmation=true"),
        check("四类回滚演练场景齐全", not scenario_errors, "通过" if not scenario_errors else "；".join(scenario_errors)),
        check("全链路只读仿真", not bool_errors, "通过" if not bool_errors else "；".join(bool_errors[:40])),
        check("凭据值不存在", not credential_errors, "credential_values_present=false" if not credential_errors else "；".join(credential_errors)),
        check("签收与回滚演练MD存在", markdown_exists, f"signoff_md={SIGNOFF_MD.exists()} rollback_md={ROLLBACK_MD.exists()}"),
    ]
    errors = [item["check"] for item in checks if not item["passed"]]
    report = guard_copy(
        {
            "name": "n8n禁用态导入草案只读演练报告",
            "version": "disabled-import-read-only-drill-report-v1",
            "drilled_at": now_text(),
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
            "checks": checks,
            "errors": errors,
            "findings": {
                "bool_errors": bool_errors,
                "credential_errors": credential_errors,
                "scenario_errors": scenario_errors,
            },
            "metrics": {
                "scenario_count": len(rollback_drill.get("scenarios", [])),
                "simulation_only_scenario_count": sum(1 for item in rollback_drill.get("scenarios", []) if item.get("simulation_only") is True),
            },
            "source_files": {
                "package": str(PACKAGE_JSON),
                "signoff": str(SIGNOFF_JSON),
                "rollback_drill": str(ROLLBACK_JSON),
            },
            "error_count": len(errors),
        }
    )
    write_json(DRILL_REPORT_JSON, report)
    write_text(DRILL_REPORT_MD, build_md(report))
    print(json.dumps({"status": report["status"], "error_count": report["error_count"], "report": str(DRILL_REPORT_JSON)}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
