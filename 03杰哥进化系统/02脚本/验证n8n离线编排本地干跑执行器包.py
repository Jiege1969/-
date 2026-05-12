# -*- coding: utf-8 -*-
"""验证 n8n 离线编排本地干跑执行器包。

只读本地执行器包和干跑报告，写入固定验收日志文件。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "75n8n离线编排本地干跑执行器包"
LOG_DIR = ROOT / "04日志" / "n8n离线编排本地干跑执行器包验收"

EXECUTOR_PACKAGE_JSON = DATA_DIR / "n8n离线编排本地干跑执行器包_最新.json"
EMBEDDED_BLUEPRINT_JSON = DATA_DIR / "n8n离线编排本地干跑内置蓝图_最新.json"
DRYRUN_JSON = DATA_DIR / "n8n离线编排本地干跑报告_最新.json"
DRYRUN_MD = DATA_DIR / "n8n离线编排本地干跑报告_最新.md"
LOG_JSON = LOG_DIR / "n8n-offline-local-dryrun-executor-verify-最新.json"

ACCEPTED_MODES = {"offline/dry_run", "dry_run/offline"}
FORBIDDEN_KEY_PARTS = [
    "url",
    "uri",
    "token",
    "secret",
    "credential",
    "credentials",
    "api_key",
    "apikey",
    "password",
]
FORBIDDEN_VALUE_RE = re.compile(r"https?://|bearer\s+|token\s*[:=]|api[_ -]?key\s*[:=]|secret\s*[:=]", re.IGNORECASE)


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


def find_real_access_fields(*objects: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    allowed_keys = {
        "webhook_enabled",
        "real_trigger",
        "network_request_enabled",
        "n8n_connection_enabled",
        "external_send_enabled",
        "config_change_enabled",
        "service_reload_enabled",
        "enterprise_wechat_send_enabled",
    }
    for obj_index, obj in enumerate(objects, start=1):
        for path, value in walk(obj):
            key = path.rsplit(".", 1)[-1].lower()
            if key not in allowed_keys and any(part in key for part in FORBIDDEN_KEY_PARTS):
                findings.append(f"object{obj_index}:{path}")
            if isinstance(value, str) and FORBIDDEN_VALUE_RE.search(value):
                findings.append(f"object{obj_index}:{path}")
            if key in {"active", "execute", "send", "publish", "enabled"} and value is True:
                findings.append(f"object{obj_index}:{path}")
    return findings


def build_check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": passed, "detail": detail}


def main() -> int:
    errors: list[str] = []
    checks: list[dict[str, Any]] = []
    missing_files = [str(path) for path in [EXECUTOR_PACKAGE_JSON, EMBEDDED_BLUEPRINT_JSON, DRYRUN_JSON, DRYRUN_MD] if not path.exists()]
    checks.append(build_check("本地执行器包产物存在", not missing_files, "全部存在" if not missing_files else "；".join(missing_files)))

    package = read_json(EXECUTOR_PACKAGE_JSON) if EXECUTOR_PACKAGE_JSON.exists() else {}
    blueprint = read_json(EMBEDDED_BLUEPRINT_JSON) if EMBEDDED_BLUEPRINT_JSON.exists() else package.get("embedded_blueprint", {})
    dryrun = read_json(DRYRUN_JSON) if DRYRUN_JSON.exists() else {}

    blueprint_nodes = blueprint.get("workflow", {}).get("nodes", [])
    node_runs = dryrun.get("node_runs", [])
    checks.append(build_check("节点数不少于5", len(blueprint_nodes) >= 5 and len(node_runs) >= 5, f"blueprint={len(blueprint_nodes)} dryrun={len(node_runs)}"))

    all_blueprint_offline = all(node.get("mode") in ACCEPTED_MODES and node.get("offline") is True and node.get("dry_run") is True for node in blueprint_nodes)
    all_dryrun_offline = all(item.get("mode") in ACCEPTED_MODES and item.get("offline") is True and item.get("dry_run") is True for item in node_runs)
    checks.append(build_check("所有节点 offline/dry_run", all_blueprint_offline and all_dryrun_offline, "通过" if all_blueprint_offline and all_dryrun_offline else "存在非离线干跑节点"))

    all_real_false = (
        package.get("global_guard", {}).get("real_trigger") is False
        and dryrun.get("real_trigger") is False
        and all(node.get("real_trigger") is False for node in blueprint_nodes)
        and all(item.get("real_trigger") is False for item in node_runs)
    )
    checks.append(build_check("real_trigger=false", all_real_false, "通过" if all_real_false else "存在真实触发风险"))

    all_webhook_false = (
        package.get("global_guard", {}).get("webhook_enabled") is False
        and dryrun.get("webhook_enabled") is False
        and all(node.get("webhook_enabled") is False for node in blueprint_nodes)
        and all(item.get("webhook_enabled") is False for item in node_runs)
    )
    checks.append(build_check("webhook_enabled=false", all_webhook_false, "通过" if all_webhook_false else "存在 webhook 启用风险"))

    no_real_access_fields = find_real_access_fields(package, blueprint, dryrun)
    checks.append(build_check("无真实接入敏感字段", not no_real_access_fields, "通过" if not no_real_access_fields else "；".join(no_real_access_fields)))

    checks.append(build_check("干跑 error_count=0", dryrun.get("error_count") == 0, str(dryrun.get("error_count"))))

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
    checks.append(build_check("红线动作全部关闭", redline_false, "通过" if redline_false else "存在红线开关异常"))

    status_ok = package.get("status") == "offline_local_dryrun_executor_ready" and dryrun.get("status") == "pass"
    checks.append(build_check("包状态与干跑状态通过", status_ok, f"package={package.get('status')} dryrun={dryrun.get('status')}"))

    for item in checks:
        if not item["passed"]:
            errors.append(item["check"])

    report = {
        "name": "n8n离线编排本地干跑执行器包验收",
        "verified_at": now_text(),
        "passed": len(errors) == 0,
        "status": "pass" if not errors else "blocked",
        "error_count": len(errors),
        "errors": errors,
        "checks": checks,
        "metrics": {
            "node_count": len(blueprint_nodes),
            "dryrun_node_count": len(node_runs),
            "ready_count": dryrun.get("metrics", {}).get("ready_count"),
            "blocked_count": dryrun.get("metrics", {}).get("blocked_count"),
            "dryrun_error_count": dryrun.get("error_count"),
            "real_trigger": False,
            "webhook_enabled": False,
        },
        "artifacts": {
            "executor_package": str(EXECUTOR_PACKAGE_JSON),
            "embedded_blueprint": str(EMBEDDED_BLUEPRINT_JSON),
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
