# -*- coding: utf-8 -*-
"""执行 n8n 离线导入前凭据隔离只读检查。

只读取本包 JSON 产物；不连接 n8n，不启用 webhook，不请求网络，
不写 n8n 配置，不重载服务，不真实发送企业微信。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "84n8n离线导入前凭据隔离与启用禁入包"

PACKAGE_JSON = DATA_DIR / "n8n离线导入前凭据隔离与启用禁入包_最新.json"
CREDENTIAL_ISOLATION_JSON = DATA_DIR / "凭据字段隔离清单_最新.json"
WEBHOOK_DISABLED_JSON = DATA_DIR / "webhook禁用清单_最新.json"
IMPORT_BAN_JSON = DATA_DIR / "导入前禁入条件_最新.json"
ACTIVATION_CONFIRM_JSON = DATA_DIR / "启用前总管确认项_最新.json"
ROLLBACK_REQUIREMENTS_JSON = DATA_DIR / "回滚要求_最新.json"
REPORT_JSON = DATA_DIR / "n8n离线导入前凭据隔离只读检查报告_最新.json"
REPORT_MD = DATA_DIR / "n8n离线导入前凭据隔离只读检查报告_最新.md"

MODE = "offline/import_precheck"

GLOBAL_GUARD = {
    "mode": MODE,
    "offline": True,
    "read_only": True,
    "dry_run": True,
    "import_allowed": False,
    "activation_allowed": False,
    "credential_values_present": False,
    "webhook_enabled": False,
    "real_trigger": False,
    "network_request_enabled": False,
    "n8n_connection_enabled": False,
    "n8n_config_write_enabled": False,
    "service_reload_enabled": False,
    "enterprise_wechat_send_enabled": False,
}


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


def check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return guard_copy({"check": name, "passed": passed, "detail": detail, "error_count": 0 if passed else 1})


def main() -> int:
    package = read_json(PACKAGE_JSON)
    credential_isolation = read_json(CREDENTIAL_ISOLATION_JSON)
    webhook_disabled = read_json(WEBHOOK_DISABLED_JSON)
    import_bans = read_json(IMPORT_BAN_JSON)
    confirmations = read_json(ACTIVATION_CONFIRM_JSON)
    rollback_requirements = read_json(ROLLBACK_REQUIREMENTS_JSON)

    slots = credential_isolation.get("slots", [])
    webhooks = webhook_disabled.get("items", [])
    conditions = import_bans.get("conditions", [])
    confirmation_items = confirmations.get("items", [])
    rollback_items = rollback_requirements.get("requirements", [])

    checks = [
        check("凭据字段隔离清单齐全", len(slots) >= 5 and all(slot.get("value_present") is False for slot in slots), f"slot_count={len(slots)}"),
        check("webhook禁用清单齐全", len(webhooks) >= 3 and all(item.get("enabled") is False for item in webhooks), f"webhook_count={len(webhooks)}"),
        check("导入前禁入条件齐全", len(conditions) >= 6 and package.get("import_allowed") is False, f"condition_count={len(conditions)}"),
        check("启用前总管确认项齐全", len(confirmation_items) >= 7 and package.get("activation_allowed") is False, f"confirmation_count={len(confirmation_items)}"),
        check("回滚要求齐全", len(rollback_items) >= 5 and rollback_requirements.get("rollback_requirements_ready") is True, f"rollback_count={len(rollback_items)}"),
        check("红线开关保持关闭", all(package.get(key) is False for key in ["credential_values_present", "webhook_enabled", "real_trigger"]), "credential_values_present=false webhook_enabled=false real_trigger=false"),
    ]
    errors = [item["check"] for item in checks if not item["passed"]]

    report = guard_copy(
        {
            "name": "n8n离线导入前凭据隔离只读检查报告",
            "checked_at": now_text(),
            "status": "pass" if not errors else "blocked",
            "import_allowed": False,
            "activation_allowed": False,
            "credential_values_present": False,
            "webhook_enabled": False,
            "real_trigger": False,
            "checks": checks,
            "metrics": {
                "credential_slot_count": len(slots),
                "webhook_disabled_count": sum(1 for item in webhooks if item.get("enabled") is False),
                "import_ban_condition_count": len(conditions),
                "supervisor_confirmation_count": len(confirmation_items),
                "rollback_requirement_count": len(rollback_items),
            },
            "source_files": {
                "package": str(PACKAGE_JSON),
                "credential_isolation": str(CREDENTIAL_ISOLATION_JSON),
                "webhook_disabled": str(WEBHOOK_DISABLED_JSON),
                "import_bans": str(IMPORT_BAN_JSON),
                "activation_confirmations": str(ACTIVATION_CONFIRM_JSON),
                "rollback_requirements": str(ROLLBACK_REQUIREMENTS_JSON),
            },
            "redline_statement": "只读检查；不接 n8n，不触发 webhook，不请求网络，不改配置，不重载服务，不真实发送企业微信",
            "errors": errors,
            "error_count": len(errors),
        }
    )
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, build_md(report))
    print(
        json.dumps(
            {
                "status": report["status"],
                "import_allowed": report["import_allowed"],
                "activation_allowed": report["activation_allowed"],
                "credential_values_present": report["credential_values_present"],
                "webhook_enabled": report["webhook_enabled"],
                "real_trigger": report["real_trigger"],
                "error_count": report["error_count"],
                "output": str(REPORT_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["error_count"] == 0 else 1


def build_md(report: dict[str, Any]) -> str:
    lines = [
        "# n8n 离线导入前凭据隔离只读检查报告",
        "",
        f"- 检查时间：{report['checked_at']}",
        f"- 状态：{report['status']}",
        "- import_allowed=false",
        "- activation_allowed=false",
        "- credential_values_present=false",
        "- webhook_enabled=false",
        "- real_trigger=false",
        f"- error_count={report['error_count']}",
        "",
        "| 检查项 | 结果 | 说明 |",
        "| --- | --- | --- |",
    ]
    for item in report["checks"]:
        lines.append(f"| {item['check']} | {item['passed']} | {item['detail']} |")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
