# -*- coding: utf-8 -*-
"""
Name: verify-stock-assistant-isolated-n8n-startup-preflight.py
Purpose: Verify the readonly preflight report before isolated new-system n8n startup for the stock assistant.
Trigger: python 验证股票助手隔离n8n启动前只读核验.py
Dependencies: Python standard library; generator script for isolated n8n startup preflight.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Reads local reports and writes verification logs only; does not create directories, start, restart, import, enable, trigger, send, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created isolated n8n startup preflight verifier.
Marker: stock-assistant-isolated-n8n-startup-preflight-verify
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
    generator = root / "02脚本" / "生成股票助手隔离n8n启动前只读核验.py"
    subprocess.run([sys.executable, str(generator)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    latest = root / "03数据" / "68隔离n8n启动前只读核验" / "股票助手隔离n8n启动前只读核验_最新.json"
    report = load_json(latest)
    checks = report.get("检查项", [])
    actions = report.get("实际动作", {})
    failed_checks = [item for item in checks if item.get("通过") is not True]
    dangerous = [key for key in ["创建n8n数据目录", "启动n8n服务", "重启服务", "导入n8n", "启用n8n工作流", "触发n8n工作流", "写旧系统", "发送企业微信", "写正式库", "调用券商接口", "自动交易"] if actions.get(key) is not False]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "最新报告": str(latest),
        "检查项数量": len(checks),
        "未通过检查项": failed_checks,
        "危险动作异常": dangerous,
        "通过": len(checks) >= 5 and not dangerous,
        "说明": "允许检查项暴露缺口；验收重点是只读核验已完成且危险动作保持关闭。"
    }
    log_dir = root / "04日志" / "隔离n8n启动前只读核验"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-isolated-n8n-startup-preflight-verify-{stamp}.json"
    latest_output = log_dir / "stock-assistant-isolated-n8n-startup-preflight-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "未通过检查项": len(failed_checks), "输出": str(output)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
