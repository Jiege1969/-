# -*- coding: utf-8 -*-
"""验证 n8n 离线编排蓝图与禁触发验收包。

只读取本地产物与只读核对结果，输出验收日志。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "72n8n离线编排蓝图与禁触发验收包"
LOG_DIR = ROOT / "04日志" / "n8n离线编排蓝图与禁触发验收包验收"

BLUEPRINT_JSON = DATA_DIR / "n8n离线编排蓝图_最新.json"
PACKAGE_JSON = DATA_DIR / "n8n离线编排蓝图与禁触发验收包_最新.json"
CHECK_JSON = DATA_DIR / "n8n离线编排蓝图只读核对_最新.json"
LOG_JSON = LOG_DIR / "n8n-offline-blueprint-no-trigger-verify-最新.json"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    for path in [BLUEPRINT_JSON, PACKAGE_JSON, CHECK_JSON]:
        if not path.exists():
            errors.append(f"缺少文件：{path}")

    blueprint = read_json(BLUEPRINT_JSON) if BLUEPRINT_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    check = read_json(CHECK_JSON) if CHECK_JSON.exists() else {}

    if package.get("status") != "offline_blueprint_ready":
        errors.append("生成包状态不是 offline_blueprint_ready")
    if check.get("status") != "pass" or check.get("error_count") != 0:
        errors.append("只读核对未通过或错误数不为 0")

    nodes = blueprint.get("workflow", {}).get("nodes", [])
    if [node.get("name") for node in nodes] != ["收到消息", "分类", "只读脚本", "生成候选回传", "总管确认闸口"]:
        errors.append("节点顺序不符合离线编排目标")
    for node in nodes:
        if node.get("mode") != "dry_run/offline" or node.get("real_trigger") is not False or node.get("webhook_enabled") is not False:
            errors.append(f"节点禁触发字段不合格：{node.get('id')}")

    report = {
        "name": "n8n离线编排蓝图与禁触发验收包验收",
        "verified_at": now_text(),
        "passed": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "metrics": {
            "node_count": len(nodes),
            "check_error_count": check.get("error_count"),
            "all_nodes_offline": all(node.get("mode") == "dry_run/offline" for node in nodes),
            "all_nodes_real_trigger_false": all(node.get("real_trigger") is False for node in nodes),
            "all_nodes_webhook_disabled": all(node.get("webhook_enabled") is False for node in nodes),
        },
        "artifacts": {
            "blueprint_json": str(BLUEPRINT_JSON),
            "package_json": str(PACKAGE_JSON),
            "check_json": str(CHECK_JSON),
            "verify_log": str(LOG_JSON),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "error_count": report["error_count"], "log": str(LOG_JSON)}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
