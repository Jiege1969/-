# -*- coding: utf-8 -*-
"""
名称：验证L5日报复盘联动链路.py
作用：验证L5日报生成后能联动生成系统判断账、人工决策账模板、结果验证计划和经验提炼候选账。
触发方式：python 验证L5日报复盘联动链路.py
依赖：Python标准库；运行L5日报复盘联动链路.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地L5日报复盘联动验收；不调用大模型；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建L5日报复盘联动链路验收脚本。
标识：stock-l5-review-loop-verify
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
    runner = root / "02脚本" / "运行L5日报复盘联动链路.py"
    result = subprocess.run([sys.executable, str(runner)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    run_report = load_json(root / "04日志" / "L5复盘联动" / "stock-l5-review-loop-run-最新.json")
    checks: list[dict[str, Any]] = []
    add_check(checks, "联动脚本运行成功", result.returncode == 0, result.stdout.strip())
    add_check(checks, "执行脚本数量不少于6", run_report.get("执行数量", 0) >= 6, run_report.get("执行数量"))
    add_check(checks, "所有子脚本成功", all(item.get("返回码") == 0 for item in run_report.get("执行结果", [])), run_report.get("执行结果", []))
    add_check(checks, "关键输出文件存在", all(Path(path).exists() for path in run_report.get("输出文件", {}).values()), run_report.get("输出文件", {}))
    add_check(checks, "真实动作关闭", all(item is False for item in run_report.get("安全边界", {}).values()), run_report.get("安全边界", {}))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "L5日报复盘联动链路可运行。" if failed == 0 else "L5日报复盘联动链路存在失败项。",
    }
    output_dir = root / "04日志" / "L5复盘联动"
    output = output_dir / f"stock-l5-review-loop-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-l5-review-loop-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
