# -*- coding: utf-8 -*-
"""
Name: verify-stock-assistant-n8n-post-refresh-webhook-gray-acceptance-plan-summary.py
Purpose: Verify stock assistant post-refresh Webhook gray acceptance plan from manager acceptance.
Trigger: python 验证股票助手n8n刷新后Webhook灰度验收预案汇总.py
Dependencies: Python standard library; stock module post-refresh Webhook gray acceptance plan verifier.
Owner system: 00杰哥系统总管
Safety: Delegates local plan verification only; does not restart, stop, enable, trigger Webhook, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created manager summary verifier for post-refresh Webhook gray acceptance plan.
Marker: stock-assistant-n8n-post-refresh-webhook-gray-acceptance-plan-summary-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return manager_root().parents[0]


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = system_root()
    verifier = root / "02杰哥扩展系统" / "01股票研究系统" / "02脚本" / "验证股票助手n8n刷新后Webhook灰度验收预案.py"
    completed = subprocess.run([sys.executable, str(verifier)], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    ok = completed.returncode == 0
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查项": "股票助手n8n刷新后Webhook灰度验收预案汇总",
        "通过": ok,
        "验证脚本": str(verifier),
        "标准输出": completed.stdout.strip(),
        "标准错误": completed.stderr.strip(),
        "安全边界": "只读预案汇总，不重启、不启用、不触发、不发送、不写旧系统、不交易"
    }
    log_dir = manager_root() / "04日志" / "股票助手n8n刷新后Webhook灰度验收预案汇总"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-n8n-post-refresh-webhook-gray-acceptance-plan-summary-verify-{stamp}.json"
    latest = log_dir / "stock-assistant-n8n-post-refresh-webhook-gray-acceptance-plan-summary-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": ok, "输出": str(output)}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
