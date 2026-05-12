# -*- coding: utf-8 -*-
"""
Name: verify-stock-assistant-local-gray-connectivity-drill.py
Purpose: Verify the five-sample local gray connectivity drill for the stock assistant.
Trigger: python 验证股票助手本地灰度联通演练.py
Dependencies: Python standard library; local gray connectivity drill executor.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Reads local drill reports and writes verification logs only; does not enable n8n, trigger n8n, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created local gray connectivity drill verifier.
Marker: stock-assistant-local-gray-connectivity-drill-verify
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
    executor = root / "02脚本" / "执行股票助手本地灰度联通演练.py"
    completed = subprocess.run([sys.executable, str(executor)], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    latest = root / "03数据" / "71本地灰度联通演练" / "股票助手本地灰度联通演练_最新.json"
    report = load_json(latest)
    actions = report.get("实际动作", {})
    dangerous = [
        key for key in ["启用n8n", "触发n8n", "调用OpenClaw", "发送企业微信", "写旧系统", "写正式库", "调用券商接口", "自动交易"]
        if actions.get(key) is not False
    ]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "演练报告": str(latest),
        "执行返回码": completed.returncode,
        "标准输出": completed.stdout.strip(),
        "标准错误": completed.stderr.strip(),
        "样例总数": report.get("样例总数", 0),
        "通过样例": report.get("通过样例", 0),
        "危险动作异常": dangerous,
        "通过": report.get("是否通过") is True and report.get("样例总数") == 5 and report.get("通过样例") == 5 and not dangerous,
    }
    log_dir = root / "04日志" / "本地灰度联通演练"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-local-gray-connectivity-drill-verify-{stamp}.json"
    latest_output = log_dir / "stock-assistant-local-gray-connectivity-drill-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "通过样例": result["通过样例"], "样例总数": result["样例总数"], "输出": str(output)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
