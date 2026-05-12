# -*- coding: utf-8 -*-
"""
Name: verify-isolated-n8n-controlled-refresh-restart-config.py
Purpose: Verify the isolated n8n controlled refresh/restart script before any execution.
Trigger: python 验证隔离n8n受控刷新重启配置.py
Dependencies: Python standard library; 执行隔离n8n受控刷新重启.ps1; docker-compose.n8n隔离.yml.
Owner system: 01杰哥智能系统
Safety: Reads local config and scripts only; does not restart, enable, trigger, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created isolated n8n controlled refresh/restart config verifier.
Marker: isolated-n8n-controlled-refresh-restart-config-verify
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def core_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = core_root()
    compose = root / "01配置" / "docker-compose.n8n隔离.yml"
    script = root / "02脚本" / "执行隔离n8n受控刷新重启.ps1"
    script_text = script.read_text(encoding="utf-8-sig", errors="replace") if script.exists() else ""
    compose_text = compose.read_text(encoding="utf-8-sig", errors="replace") if compose.exists() else ""
    checks = [
        {"检查项": "compose存在", "通过": compose.exists(), "说明": str(compose)},
        {"检查项": "受控刷新脚本存在", "通过": script.exists(), "说明": str(script)},
        {"检查项": "只面向jiege_v3_n8n", "通过": "jiege_v3_n8n" in script_text and "jiege_n8n" in script_text, "说明": "目标和保护对象均需出现"},
        {"检查项": "使用restart而非down", "通过": "restart n8n" in script_text and " compose down" not in script_text.lower() and "docker stop" not in script_text.lower(), "说明": "禁止down或stop"},
        {"检查项": "不删除卷和目录", "通过": all(token not in script_text for token in ["Remove-Item", "--volumes", "docker volume rm", "rm -rf"]), "说明": "禁止删除"},
        {"检查项": "不导入不启用不触发工作流", "通过": "import:workflow" not in script_text and "update:workflow" not in script_text and "Invoke-WebRequest -UseBasicParsing -Uri \"http://127.0.0.1:28679\"" in script_text, "说明": "仅做首页健康检查"},
        {"检查项": "compose仍隔离端口", "通过": "127.0.0.1:28679:5678" in compose_text, "说明": "端口必须隔离"},
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "检查结果": checks, "通过": len(checks) - len(failed), "失败": len(failed)}
    log_dir = root / "04日志" / "隔离n8n受控刷新重启配置"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"isolated-n8n-controlled-refresh-restart-config-verify-{stamp}.json"
    latest = log_dir / "isolated-n8n-controlled-refresh-restart-config-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
