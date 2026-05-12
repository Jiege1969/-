# -*- coding: utf-8 -*-
"""
Name: verify-stock-assistant-n8n-webhook-local-controlled-enable-test.py
Purpose: Verify the local controlled n8n webhook enable-test result for the stock assistant.
Trigger: python 验证股票助手n8nWebhook本地受控启用测试.py
Dependencies: Python standard library; local controlled webhook enable test executor.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Verifies local test logs and active state only; does not call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 rebuilt verifier with explicit allowed local actions.
Marker: stock-assistant-n8n-webhook-local-controlled-enable-test-verify
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
    executor = root / "02脚本" / "执行股票助手n8nWebhook本地受控启用测试.py"
    completed = subprocess.run([sys.executable, str(executor)], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=420)
    latest = root / "04日志" / "n8nWebhook本地受控启用测试" / "stock-assistant-n8n-webhook-local-controlled-enable-test-最新.json"
    report = load_json(latest)
    actions = report.get("实际动作", {})
    allowed_true_actions = {"临时启用n8nWebhook", "本地触发n8nWebhook", "关闭n8nWebhook"}
    dangerous = [key for key, value in actions.items() if key not in allowed_true_actions and value is True]
    checks = [
        {"检查项": "执行返回码通过", "通过": completed.returncode == 0, "说明": completed.stdout.strip() or completed.stderr.strip()},
        {"检查项": "本地POST返回200", "通过": report.get("本地POST结果", {}).get("status") == 200, "说明": str(report.get("本地POST结果", {}))[:500]},
        {"检查项": "测试后已关闭Webhook", "通过": report.get("实际动作", {}).get("关闭n8nWebhook") is True, "说明": str(report.get("关闭后激活列表", ""))[:500]},
        {"检查项": "无真实外部动作", "通过": not dangerous, "说明": str(dangerous)},
        {"检查项": "总体通过", "通过": report.get("是否通过") is True, "说明": str(report.get("是否通过"))},
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "检查结果": checks, "通过": len(checks) - len(failed), "失败": len(failed)}
    log_dir = root / "04日志" / "n8nWebhook本地受控启用测试结果"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-n8n-webhook-local-controlled-enable-test-verify-{stamp}.json"
    latest_output = log_dir / "stock-assistant-n8n-webhook-local-controlled-enable-test-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
