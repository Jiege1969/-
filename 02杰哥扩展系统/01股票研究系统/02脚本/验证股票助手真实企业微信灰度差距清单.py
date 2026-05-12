# -*- coding: utf-8 -*-
"""
Name: verify-stock-assistant-real-wework-gray-gap-list.py
Purpose: Verify the remaining gap list before real WeWork whitelist gray tests for the stock assistant.
Trigger: python 验证股票助手真实企业微信灰度差距清单.py
Dependencies: Python standard library; real WeWork gray gap list generator.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Reads local reports and writes verification logs only; does not enable n8n, trigger n8n, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created real WeWork gray gap list verifier.
Marker: stock-assistant-real-wework-gray-gap-list-verify
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
    generator = root / "02脚本" / "生成股票助手真实企业微信灰度差距清单.py"
    subprocess.run([sys.executable, str(generator)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    latest = root / "03数据" / "72真实企业微信灰度差距清单" / "股票助手真实企业微信灰度差距清单_最新.json"
    report = load_json(latest)
    actions = report.get("实际动作", {})
    dangerous = [
        key for key in ["启用n8n", "触发n8n", "调用OpenClaw", "发送企业微信", "写旧系统", "写正式库", "调用券商接口", "自动交易"]
        if actions.get(key) is not False
    ]
    checks = [
        {"检查项": "差距清单存在", "通过": latest.exists(), "说明": str(latest)},
        {"检查项": "已完成事项完整", "通过": len(report.get("已完成", [])) >= 5, "说明": str(report.get("已完成", []))},
        {"检查项": "剩余差距完整", "通过": len(report.get("剩余差距", [])) >= 5, "说明": str(report.get("剩余差距", []))},
        {"检查项": "真实发送仍关闭", "通过": report.get("是否具备真实企业微信灰度发送条件") is False, "说明": str(report.get("是否具备真实企业微信灰度发送条件"))},
        {"检查项": "危险动作关闭", "通过": not dangerous, "说明": str(dangerous)},
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "检查结果": checks, "通过": len(checks) - len(failed), "失败": len(failed)}
    log_dir = root / "04日志" / "真实企业微信灰度差距清单"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-real-wework-gray-gap-list-verify-{stamp}.json"
    latest_output = log_dir / "stock-assistant-real-wework-gray-gap-list-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
