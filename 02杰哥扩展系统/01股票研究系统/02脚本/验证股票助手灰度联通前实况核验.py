# -*- coding: utf-8 -*-
"""
Name: verify-stock-assistant-gray-connectivity-preflight.py
Purpose: Verify the live preflight report before limited stock assistant WeWork gray connectivity testing.
Trigger: python 验证股票助手灰度联通前实况核验.py
Dependencies: Python standard library; gray connectivity preflight generator.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Reads local preflight reports and writes verification logs only; does not enable, trigger, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created gray connectivity preflight verifier.
Marker: stock-assistant-gray-connectivity-preflight-verify
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
    generator = root / "02脚本" / "生成股票助手灰度联通前实况核验.py"
    subprocess.run([sys.executable, str(generator)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    latest = root / "03数据" / "70灰度联通前实况核验" / "股票助手灰度联通前实况核验_最新.json"
    report = load_json(latest)
    actions = report.get("实际动作", {})
    checks = report.get("检查项", [])
    failed = [item for item in checks if item.get("通过") is not True]
    dangerous = [key for key in ["启用n8n", "触发n8n", "调用OpenClaw", "发送企业微信", "写旧系统", "写正式库", "调用券商接口", "自动交易"] if actions.get(key) is not False]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "最新报告": str(latest),
        "检查项数量": len(checks),
        "未通过检查项": failed,
        "危险动作异常": dangerous,
        "本地灰度联通": report.get("是否可以进入本地灰度联通演练") is True,
        "真实企业微信发送": report.get("是否可以进入真实企业微信灰度发送") is True,
        "通过": len(checks) >= 7 and not dangerous,
    }
    log_dir = root / "04日志" / "灰度联通前实况核验"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-gray-connectivity-preflight-verify-{stamp}.json"
    latest_output = log_dir / "stock-assistant-gray-connectivity-preflight-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "本地灰度联通": result["本地灰度联通"], "真实企业微信发送": result["真实企业微信发送"], "输出": str(output)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
