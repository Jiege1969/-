# -*- coding: utf-8 -*-
"""
Name: verify-stock-assistant-isolated-n8n-implementation-request.py
Purpose: Verify the no-action isolated n8n implementation request for the stock assistant.
Trigger: python 验证股票助手新系统隔离n8n实施申请.py
Dependencies: Python standard library; generator script for isolated n8n implementation request.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Reads local reports and writes verification logs only; does not start, restart, import, enable, trigger, send, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created isolated n8n implementation request verifier.
Marker: stock-assistant-isolated-n8n-implementation-request-verify
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


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: str) -> None:
    checks.append({"检查项": name, "通过": ok, "说明": detail})


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成股票助手新系统隔离n8n实施申请.py"
    subprocess.run([sys.executable, str(generator)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    latest = root / "03数据" / "67新系统隔离n8n实施申请" / "股票助手新系统隔离n8n实施申请_最新.json"
    report = load_json(latest)
    actions = report.get("实际动作", {})
    checks: list[dict[str, Any]] = []

    add_check(checks, "最新实施申请存在", latest.exists(), str(latest))
    add_check(checks, "申请目标是新系统隔离n8n", report.get("申请目标", {}).get("目标容器") == "jiege_v3_n8n", str(report.get("申请目标", {})))
    add_check(checks, "申请不直接启动服务", report.get("是否允许本申请直接启动服务") is False, str(report.get("是否允许本申请直接启动服务")))
    add_check(checks, "compose草案目标已识别", all(report.get("compose草案摘要", {}).get(key) is True for key in ["存在", "包含jiege_v3_n8n", "包含28679端口", "包含n8n数据目录"]), str(report.get("compose草案摘要", {})))
    add_check(checks, "实施前条件完整", len(report.get("实施前必须满足", [])) >= 5, str(report.get("实施前必须满足", [])))
    add_check(checks, "真实动作全部关闭", all(actions.get(key) is False for key in ["启动n8n服务", "重启服务", "导入n8n", "启用n8n工作流", "触发n8n工作流", "写旧系统", "发送企业微信", "写正式库", "调用券商接口", "自动交易"]), str(actions))

    failed = [item for item in checks if not item["通过"]]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查结果": checks,
        "通过": len(checks) - len(failed),
        "失败": len(failed),
    }
    log_dir = root / "04日志" / "新系统隔离n8n实施申请"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-isolated-n8n-implementation-request-verify-{stamp}.json"
    latest_output = log_dir / "stock-assistant-isolated-n8n-implementation-request-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
