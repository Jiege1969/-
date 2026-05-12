# -*- coding: utf-8 -*-
"""
Name: verify-isolated-n8n-controlled-start-config-summary.py
Purpose: Run and summarize isolated v3 n8n controlled startup config verification from the system manager.
Trigger: python 验证隔离n8n受控启动配置汇总.py
Dependencies: Python standard library; isolated n8n controlled startup config verifier.
Owner system: 00杰哥系统总管
Safety: Reads and verifies new system config only; writes manager verification logs only; does not start, restart, import, enable, trigger, send, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created manager summary verifier for isolated n8n controlled startup config.
Marker: isolated-n8n-controlled-start-config-summary-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = system_root()
    verifier = root / "01杰哥智能系统" / "02脚本" / "验证隔离n8n受控启动配置.py"
    completed = subprocess.run([sys.executable, str(verifier)], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    latest = root / "01杰哥智能系统" / "04日志" / "隔离n8n受控启动配置" / "isolated-n8n-controlled-start-config-verify-最新.json"
    result = load_json(latest)
    failed = completed.returncode != 0 or result.get("失败", 1) != 0
    summary = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "核心侧验证脚本": str(verifier),
        "核心侧验证日志": str(latest),
        "返回码": completed.returncode,
        "标准输出": completed.stdout.strip(),
        "标准错误": completed.stderr.strip(),
        "核心侧结果": result,
        "通过": not failed,
    }
    log_dir = root / "00杰哥系统总管" / "04日志" / "隔离n8n受控启动配置"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"isolated-n8n-controlled-start-config-summary-{stamp}.json"
    latest_output = log_dir / "isolated-n8n-controlled-start-config-summary-最新.json"
    write_json(output, summary)
    write_json(latest_output, summary)
    print(json.dumps({"通过": summary["通过"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
