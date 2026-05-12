# -*- coding: utf-8 -*-
"""执行 n8n 离线编排蓝图只读核对。

只读取本地蓝图文件，检查禁触发约束，不连接 n8n，不调用网络。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "72n8n离线编排蓝图与禁触发验收包"
BLUEPRINT_JSON = DATA_DIR / "n8n离线编排蓝图_最新.json"
PACKAGE_JSON = DATA_DIR / "n8n离线编排蓝图与禁触发验收包_最新.json"
CHECK_JSON = DATA_DIR / "n8n离线编排蓝图只读核对_最新.json"
CHECK_MD = DATA_DIR / "n8n离线编排蓝图只读核对_最新.md"

EXPECTED_FLOW = ["收到消息", "分类", "只读脚本", "生成候选回传", "总管确认闸口"]
FORBIDDEN_KEY_PARTS = [
    "url",
    "uri",
    "token",
    "secret",
    "credential",
    "credentials",
    "auth",
    "api_key",
    "apikey",
    "webhook_url",
    "webhook_id",
    "webhook_path",
    "n8n_url",
]
FORBIDDEN_VALUE_RE = re.compile(
    r"https?://|bearer\s+|token\s*[:=]|webhook[_ -]*(token|url|id|path)\s*[:=]|x-hook|x-webhook",
    re.IGNORECASE,
)


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


def walk(obj: Any, path: str = "$") -> list[tuple[str, Any]]:
    items: list[tuple[str, Any]] = [(path, obj)]
    if isinstance(obj, dict):
        for key, value in obj.items():
            items.extend(walk(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            items.extend(walk(value, f"{path}[{index}]"))
    return items


def find_forbidden_fields(blueprint: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    allowed_guard_keys = {"real_trigger", "webhook_enabled"}
    for path, value in walk(blueprint):
        key = path.rsplit(".", 1)[-1].lower()
        if key not in allowed_guard_keys and any(part in key for part in FORBIDDEN_KEY_PARTS):
            findings.append(f"发现禁用字段：{path}")
        if isinstance(value, str) and FORBIDDEN_VALUE_RE.search(value):
            findings.append(f"发现疑似 URL/token/webhook 值：{path}")
        if key in {"active", "enabled", "execute", "send", "publish"} and value is True:
            findings.append(f"发现真实动作开关为 true：{path}")
    return findings


def build_check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": passed, "detail": detail}


def build_md(report: dict[str, Any]) -> str:
    rows = [f"| {item['check']} | {'pass' if item['passed'] else 'blocked'} | {item['detail']} |" for item in report["checks"]]
    return "\n".join(
        [
            "# n8n 离线编排蓝图只读核对",
            "",
            f"- 核对时间：{report['checked_at']}",
            f"- 总体状态：{report['status']}",
            f"- 错误数：{report['error_count']}",
            "",
            "| 核对项 | 结果 | 说明 |",
            "| --- | --- | --- |",
            *rows,
            "",
        ]
    )


def main() -> int:
    errors: list[str] = []
    checks: list[dict[str, Any]] = []
    if not BLUEPRINT_JSON.exists():
        errors.append(f"蓝图不存在：{BLUEPRINT_JSON}")
        blueprint: dict[str, Any] = {}
    else:
        blueprint = read_json(BLUEPRINT_JSON)

    nodes = blueprint.get("workflow", {}).get("nodes", [])
    flow = blueprint.get("workflow", {}).get("flow", [])
    checks.append(build_check("流程覆盖收到消息到总管确认闸口", flow == EXPECTED_FLOW, " -> ".join(flow)))
    checks.append(build_check("节点数量不少于 5", len(nodes) >= 5, str(len(nodes))))

    missing_guard: list[str] = []
    for node in nodes:
        if node.get("mode") != "dry_run/offline":
            missing_guard.append(f"{node.get('id')} mode")
        if node.get("real_trigger") is not False:
            missing_guard.append(f"{node.get('id')} real_trigger")
        if node.get("webhook_enabled") is not False:
            missing_guard.append(f"{node.get('id')} webhook_enabled")
    checks.append(build_check("所有节点禁触发字段正确", not missing_guard, "；".join(missing_guard) if missing_guard else "全部节点通过"))

    edge_errors: list[str] = []
    for edge in blueprint.get("workflow", {}).get("edges", []):
        if edge.get("mode") != "dry_run/offline" or edge.get("real_trigger") is not False or edge.get("webhook_enabled") is not False:
            edge_errors.append(f"{edge.get('from')}->{edge.get('to')}")
    checks.append(build_check("所有边禁触发字段正确", not edge_errors, "；".join(edge_errors) if edge_errors else "全部边通过"))

    global_guard = blueprint.get("global_guard", {})
    guard_ok = (
        global_guard.get("mode") == "dry_run/offline"
        and global_guard.get("real_trigger") is False
        and global_guard.get("webhook_enabled") is False
        and global_guard.get("network_call_enabled") is False
        and global_guard.get("n8n_connection_enabled") is False
        and global_guard.get("external_delivery_enabled") is False
        and global_guard.get("production_rule_enabled") is False
    )
    checks.append(build_check("全局禁触发与离线模式正确", guard_ok, json.dumps(global_guard, ensure_ascii=False)))

    forbidden_findings = find_forbidden_fields(blueprint)
    checks.append(build_check("无 URL/token/凭据/真实动作字段", not forbidden_findings, "；".join(forbidden_findings) if forbidden_findings else "未发现禁用字段和值"))

    output_files = [BLUEPRINT_JSON, PACKAGE_JSON, DATA_DIR / "n8n离线编排蓝图说明_最新.md", DATA_DIR / "n8n禁触发验收清单_最新.md"]
    missing_files = [str(path) for path in output_files if not path.exists()]
    checks.append(build_check("离线蓝图与验收包文件存在", not missing_files, "；".join(missing_files) if missing_files else str(len(output_files))))

    for item in checks:
        if not item["passed"]:
            errors.append(item["check"])

    report = {
        "name": "n8n离线编排蓝图只读核对",
        "checked_at": now_text(),
        "status": "pass" if not errors else "blocked",
        "error_count": len(errors),
        "errors": errors,
        "checks": checks,
        "source": str(BLUEPRINT_JSON),
    }
    write_json(CHECK_JSON, report)
    write_text(CHECK_MD, build_md(report))
    print(json.dumps({"status": report["status"], "error_count": report["error_count"], "output": str(CHECK_JSON)}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
