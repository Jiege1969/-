# -*- coding: utf-8 -*-
"""
Name: verify-isolated-n8n-controlled-start-config.py
Purpose: Verify the isolated v3 n8n compose and controlled startup script before execution.
Trigger: python 验证隔离n8n受控启动配置.py
Dependencies: Python standard library; docker-compose.n8n隔离.yml; 执行隔离n8n受控启动.ps1.
Owner system: 01杰哥智能系统
Safety: Reads local config and scripts only; does not start, restart, import, enable, trigger, send, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created isolated n8n controlled startup config verifier.
Marker: isolated-n8n-controlled-start-config-verify
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
    starter = root / "02脚本" / "执行隔离n8n受控启动.ps1"
    compose_text = compose.read_text(encoding="utf-8-sig", errors="replace") if compose.exists() else ""
    script_text = starter.read_text(encoding="utf-8-sig", errors="replace") if starter.exists() else ""
    checks = [
        {"检查项": "compose存在", "通过": compose.exists(), "说明": str(compose)},
        {"检查项": "启动脚本存在", "通过": starter.exists(), "说明": str(starter)},
        {"检查项": "容器名隔离", "通过": "container_name: jiege_v3_n8n" in compose_text, "说明": "必须使用jiege_v3_n8n"},
        {"检查项": "端口隔离", "通过": "127.0.0.1:28679:5678" in compose_text, "说明": "必须绑定本机28679"},
        {"检查项": "数据目录隔离", "通过": "../03数据/n8n:/home/node/.n8n" in compose_text, "说明": "必须写入新系统01数据目录"},
        {"检查项": "不含旧系统路径", "通过": "杰哥智能体操作系统" not in compose_text and "杰哥智能体操作系统" not in script_text, "说明": "禁止写旧系统"},
        {"检查项": "脚本不导入工作流", "通过": "import:workflow" not in script_text and "import:credentials" not in script_text, "说明": "启动脚本不得导入n8n"},
        {"检查项": "脚本不重启现有服务", "通过": "docker restart" not in script_text.lower() and "docker stop" not in script_text.lower() and " compose down" not in script_text.lower(), "说明": "禁止重启或停止现有服务"},
        {"检查项": "脚本检查旧系统存在", "通过": "jiege_n8n" in script_text, "说明": "旧系统作为保护对象识别"},
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查结果": checks,
        "通过": len(checks) - len(failed),
        "失败": len(failed),
    }
    log_dir = root / "04日志" / "隔离n8n受控启动配置"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"isolated-n8n-controlled-start-config-verify-{stamp}.json"
    latest = log_dir / "isolated-n8n-controlled-start-config-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
