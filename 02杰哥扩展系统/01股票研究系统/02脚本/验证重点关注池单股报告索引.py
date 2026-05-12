# -*- coding: utf-8 -*-
"""
名称：验证重点关注池单股报告索引.py
作用：验证重点关注池19只股票均可生成单股即时研究报告索引。
触发方式：python 验证重点关注池单股报告索引.py
依赖：Python标准库；生成重点关注池单股报告索引.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地索引验收；不联网；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建重点关注池单股报告索引验收脚本。
标识：stock-focus-single-report-index-verify
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


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成重点关注池单股报告索引.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    latest_json = root / "03数据" / "23单股即时报告" / "重点关注池单股报告索引_最新.json"
    latest_md = root / "03数据" / "23单股即时报告" / "重点关注池单股报告索引_最新.md"
    package = load_json(latest_json)
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    safety = package.get("安全边界", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "索引生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "索引生成成功", result.returncode == 0, {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()})
    add_check(checks, "最新JSON索引存在", latest_json.exists() and package.get("股票数量") == 19, str(latest_json))
    add_check(checks, "最新Markdown索引存在", latest_md.exists() and "重点关注池单股报告索引" in text, str(latest_md))
    add_check(checks, "19只股票全部成功", package.get("股票数量") == 19 and package.get("成功数量") == 19 and package.get("失败数量") == 0, package)
    add_check(checks, "高风险动作关闭", all(value is False for value in safety.values()), safety)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "重点关注池单股报告索引可用。" if failed == 0 else "重点关注池单股报告索引存在失败项。",
    }
    output_dir = root / "04日志" / "单股即时报告"
    output = output_dir / f"stock-focus-single-report-index-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-focus-single-report-index-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
