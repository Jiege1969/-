# -*- coding: utf-8 -*-
"""
Name: verify-stock-assistant-n8n-inactive-import-result-summary.py
Purpose: Run and summarize stock assistant inactive n8n import result verification from the system manager.
Trigger: python 验证股票助手n8n未激活导入结果汇总.py
Dependencies: Python standard library; stock assistant inactive n8n import result verifier.
Owner system: 00杰哥系统总管
Safety: Reads and verifies new system isolated n8n and stock logs only; does not enable, trigger, send, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created manager summary verifier for inactive n8n import result.
Marker: stock-assistant-n8n-inactive-import-result-summary-verify
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
    stock_root = root / "02杰哥扩展系统" / "01股票研究系统"
    verifier = stock_root / "02脚本" / "验证股票助手n8n未激活导入结果.py"
    completed = subprocess.run([sys.executable, str(verifier)], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    latest = stock_root / "04日志" / "n8n未激活导入结果" / "stock-assistant-n8n-inactive-import-result-verify-最新.json"
    stock_result = load_json(latest)
    failed = completed.returncode != 0 or stock_result.get("失败", 1) != 0
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "股票侧验证脚本": str(verifier),
        "股票侧验证日志": str(latest),
        "返回码": completed.returncode,
        "标准输出": completed.stdout.strip(),
        "标准错误": completed.stderr.strip(),
        "股票侧结果": stock_result,
        "通过": not failed,
    }
    log_dir = root / "00杰哥系统总管" / "04日志" / "n8n未激活导入结果"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-n8n-inactive-import-result-summary-{stamp}.json"
    latest_output = log_dir / "stock-assistant-n8n-inactive-import-result-summary-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
