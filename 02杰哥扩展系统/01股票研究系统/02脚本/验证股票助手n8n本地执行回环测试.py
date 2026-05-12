# -*- coding: utf-8 -*-
"""
Name: verify-stock-assistant-n8n-local-execution-loop-test.py
Purpose: Verify the stock assistant local n8n execution-loop test.
Trigger: python 验证股票助手n8n本地执行回环测试.py
Dependencies: Python standard library; local n8n execution-loop test executor.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Verifies local n8n execution logs only; does not enable webhook, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created local n8n execution-loop test verifier.
Marker: stock-assistant-n8n-local-execution-loop-test-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = module_root()
    executor = root / "02脚本" / "执行股票助手n8n本地执行回环测试.py"
    completed = subprocess.run([sys.executable, str(executor)], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    latest = root / "04日志" / "n8n本地执行回环测试" / "stock-assistant-n8n-local-execution-loop-test-最新.json"
    report = load_json(latest)
    actions = report.get("实际动作", {})
    dangerous = [key for key in ["启用Webhook", "触发Webhook", "调用OpenClaw", "发送企业微信", "写旧系统", "写正式库", "调用券商接口", "自动交易"] if actions.get(key) is not False]
    checks = [
        {"检查项": "执行返回码通过", "通过": completed.returncode == 0, "说明": completed.stdout.strip() or completed.stderr.strip()},
        {"检查项": "n8n执行通过", "通过": report.get("execute", {}).get("返回码") == 0, "说明": str(report.get("execute", {}))},
        {"检查项": "本地回环输出存在", "通过": "local_execution_loop" in report.get("execute", {}).get("stdout", ""), "说明": report.get("execute", {}).get("stdout", "")[:500]},
        {"检查项": "无外部危险动作", "通过": not dangerous, "说明": str(dangerous)},
        {"检查项": "总体通过", "通过": report.get("是否通过") is True, "说明": str(report.get("是否通过"))},
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "检查结果": checks, "通过": len(checks) - len(failed), "失败": len(failed)}
    log_dir = root / "04日志" / "n8n本地执行回环测试结果"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-n8n-local-execution-loop-test-verify-{stamp}.json"
    latest_output = log_dir / "stock-assistant-n8n-local-execution-loop-test-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
