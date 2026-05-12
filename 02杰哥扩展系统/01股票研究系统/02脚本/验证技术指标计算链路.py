# -*- coding: utf-8 -*-
"""
名称：验证技术指标计算链路.py
作用：验证重点关注池历史K线只读采集和技术指标计算链路可运行。
触发方式：python 验证技术指标计算链路.py
依赖：Python标准库；生成重点关注池历史K线快照.py；计算重点关注池技术指标.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读公开行情；只写新系统股票模块；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建技术指标计算链路验收脚本。
标识：stock-technical-indicator-chain-verify
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


def run_script(path: Path, timeout: int = 180) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {"脚本": str(path), "返回码": result.returncode, "标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()}


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    fetch_result = run_script(root / "02脚本" / "生成重点关注池历史K线快照.py", timeout=240)
    calc_result = run_script(root / "02脚本" / "计算重点关注池技术指标.py", timeout=180)
    history = load_json(root / "03数据" / "11历史行情" / "重点关注池历史K线快照_最新.json")
    indicators = load_json(root / "03数据" / "12技术指标" / "重点关注池技术指标_最新.json")
    rows = indicators.get("技术指标", [])
    checks: list[dict[str, Any]] = []
    add_check(checks, "历史K线脚本运行成功", fetch_result["返回码"] == 0, fetch_result)
    add_check(checks, "技术指标脚本运行成功", calc_result["返回码"] == 0, calc_result)
    add_check(checks, "历史K线成功数量大于0", history.get("成功数量", 0) > 0, history.get("成功数量"))
    add_check(checks, "指标成功数量大于0", indicators.get("成功数量", 0) > 0, indicators.get("成功数量"))
    add_check(checks, "指标包含MA RSI MACD", any(item.get("均线", {}).get("MA60") is not None and item.get("RSI14") is not None and item.get("MACD", {}).get("MACD") is not None for item in rows), rows[:1])
    add_check(checks, "真实动作关闭", all(item is False for item in indicators.get("安全边界", {}).values()), indicators.get("安全边界", {}))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "技术指标计算链路可运行。" if failed == 0 else "技术指标计算链路存在失败项。",
    }
    output_dir = root / "04日志" / "技术指标"
    output = output_dir / f"stock-technical-indicator-chain-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-technical-indicator-chain-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
