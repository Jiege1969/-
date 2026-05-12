# -*- coding: utf-8 -*-
"""执行 n8n 离线编排本地干跑。

只读取本包内置离线蓝图，输出节点级模拟输入/输出和 ready/blocked 状态。
不连接 n8n，不启用 webhook，不请求网络，不真实发送企业微信。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "75n8n离线编排本地干跑执行器包"

EXECUTOR_PACKAGE_JSON = DATA_DIR / "n8n离线编排本地干跑执行器包_最新.json"
EMBEDDED_BLUEPRINT_JSON = DATA_DIR / "n8n离线编排本地干跑内置蓝图_最新.json"
DRYRUN_JSON = DATA_DIR / "n8n离线编排本地干跑报告_最新.json"
DRYRUN_MD = DATA_DIR / "n8n离线编排本地干跑报告_最新.md"

MODE = "offline/dry_run"


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


def load_blueprint() -> tuple[dict[str, Any], str]:
    if EXECUTOR_PACKAGE_JSON.exists():
        package = read_json(EXECUTOR_PACKAGE_JSON)
        return package.get("embedded_blueprint", {}), str(EXECUTOR_PACKAGE_JSON)
    if EMBEDDED_BLUEPRINT_JSON.exists():
        return read_json(EMBEDDED_BLUEPRINT_JSON), str(EMBEDDED_BLUEPRINT_JSON)
    return {}, ""


def simulate_node(node: dict[str, Any], previous_output: dict[str, Any] | None) -> dict[str, Any]:
    node_id = str(node.get("id", ""))
    wait_for_supervisor = node.get("wait_for_supervisor") is True
    simulated_input = {
        "from_previous_node": previous_output or {"offline_seed": "本地离线样本"},
        "declared_read_only_input": node.get("read_only_input", []),
        "real_trigger": False,
        "webhook_enabled": False,
    }
    simulated_output = {
        "node_id": node_id,
        "candidate_items": node.get("simulated_output", []),
        "offline": True,
        "dry_run": True,
        "real_trigger": False,
        "webhook_enabled": False,
        "external_delivery": False,
        "requires_supervisor": wait_for_supervisor,
    }
    return {
        "node_id": node_id,
        "node_name": node.get("name", ""),
        "mode": node.get("mode", MODE),
        "offline": True,
        "dry_run": True,
        "status": "blocked" if wait_for_supervisor else "ready",
        "ready": not wait_for_supervisor,
        "blocked": wait_for_supervisor,
        "blocked_reason": "等待总管确认，干跑在本地闸口停止。" if wait_for_supervisor else "",
        "real_trigger": False,
        "webhook_enabled": False,
        "network_request_enabled": False,
        "n8n_connection_enabled": False,
        "external_send_enabled": False,
        "simulated_input": simulated_input,
        "simulated_output": simulated_output,
    }


def build_report(blueprint: dict[str, Any], source_path: str) -> dict[str, Any]:
    errors: list[str] = []
    nodes = blueprint.get("workflow", {}).get("nodes", [])
    node_runs: list[dict[str, Any]] = []
    previous_output: dict[str, Any] | None = None
    for node in nodes:
        node_run = simulate_node(node, previous_output)
        node_runs.append(node_run)
        previous_output = node_run["simulated_output"]

    if not nodes:
        errors.append("未读取到本地离线蓝图节点")

    return {
        "name": "n8n离线编排本地干跑报告",
        "executed_at": now_text(),
        "source": source_path,
        "mode": MODE,
        "offline": True,
        "dry_run": True,
        "real_trigger": False,
        "webhook_enabled": False,
        "network_request_enabled": False,
        "n8n_connection_enabled": False,
        "external_send_enabled": False,
        "config_change_enabled": False,
        "service_reload_enabled": False,
        "enterprise_wechat_send_enabled": False,
        "status": "pass" if not errors else "blocked",
        "error_count": len(errors),
        "errors": errors,
        "metrics": {
            "node_count": len(node_runs),
            "ready_count": sum(1 for item in node_runs if item["ready"]),
            "blocked_count": sum(1 for item in node_runs if item["blocked"]),
            "real_trigger_count": 0,
            "webhook_enabled_count": 0,
        },
        "node_runs": node_runs,
        "final_gate": {
            "status": "blocked",
            "reason": "干跑报告只停在总管确认闸口，不进行真实触发或发送。",
            "real_trigger": False,
            "webhook_enabled": False,
        },
    }


def build_md(report: dict[str, Any]) -> str:
    lines = [
        "# n8n 离线编排本地干跑报告",
        "",
        f"- 执行时间：{report['executed_at']}",
        f"- 总体状态：{report['status']}",
        f"- error_count：{report['error_count']}",
        f"- 节点数：{report['metrics']['node_count']}",
        f"- ready：{report['metrics']['ready_count']}",
        f"- blocked：{report['metrics']['blocked_count']}",
        "- 真实触发：false",
        "- webhook_enabled：false",
        "",
        "| 节点 | 状态 | blocked | 模拟输入 | 模拟输出 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["node_runs"]:
        input_text = "；".join(item["simulated_input"].get("declared_read_only_input", []))
        output_text = "；".join(item["simulated_output"].get("candidate_items", []))
        lines.append(f"| {item['node_id']} {item['node_name']} | {item['status']} | {str(item['blocked']).lower()} | {input_text} | {output_text} |")
    lines.extend(
        [
            "",
            "## 闸口",
            "",
            f"- 状态：{report['final_gate']['status']}",
            f"- 原因：{report['final_gate']['reason']}",
            "- real_trigger：false",
            "- webhook_enabled：false",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    blueprint, source_path = load_blueprint()
    report = build_report(blueprint, source_path)
    write_json(DRYRUN_JSON, report)
    write_text(DRYRUN_MD, build_md(report))
    print(json.dumps({"status": report["status"], "error_count": report["error_count"], "output": str(DRYRUN_JSON)}, ensure_ascii=False))
    return 0 if report["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
