# -*- coding: utf-8 -*-
"""
名称：验证股票研究系统状态摘要.py
作用：验证股票研究系统状态摘要生成链路可运行且不越权。
触发方式：python 验证股票研究系统状态摘要.py
依赖：Python标准库；生成股票研究系统状态摘要.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地状态摘要生成；不调用大模型；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票研究系统状态摘要验收脚本。
标识：stock-research-status-summary-verify
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
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成股票研究系统状态摘要.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest_json = root / "03数据" / "16状态摘要" / "股票研究系统状态摘要_最新.json"
    latest_md = root / "03数据" / "16状态摘要" / "股票研究系统状态摘要_最新.md"
    summary = load_json(latest_json) if latest_json.exists() else {}
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    checks: list[dict[str, Any]] = []
    add_check(checks, "状态摘要脚本运行成功", result.returncode == 0, result.stdout.strip())
    add_check(checks, "JSON摘要已生成", latest_json.exists() and summary.get("重点关注池数量", 0) > 0, str(latest_json))
    add_check(checks, "Markdown摘要已生成", latest_md.exists() and "股票研究系统状态摘要" in text, str(latest_md))
    add_check(checks, "候选池统计存在", set(summary.get("候选池统计", {}).keys()) >= {"L5深度研究", "L6轻度关注", "L7系统过滤"}, summary.get("候选池统计", {}))
    add_check(checks, "复盘账本状态存在", len(summary.get("复盘账本状态", {})) == 4, summary.get("复盘账本状态", {}))
    add_check(checks, "真实动作关闭", all(item is False for item in summary.get("安全边界", {}).values()), summary.get("安全边界", {}))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "股票研究系统状态摘要链路可运行。" if failed == 0 else "股票研究系统状态摘要链路存在失败项。",
    }
    output_dir = root / "04日志" / "状态摘要"
    output = output_dir / f"stock-research-status-summary-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-research-status-summary-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
