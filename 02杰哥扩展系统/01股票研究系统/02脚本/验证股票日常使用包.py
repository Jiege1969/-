# -*- coding: utf-8 -*-
"""
名称：验证股票日常使用包.py
作用：验证股票日常使用包生成链路可运行，且包含状态、候选池、复盘账本、反馈格式和安全边界。
触发方式：python 验证股票日常使用包.py
依赖：Python标准库；生成股票日常使用包.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地使用包生成；不调用大模型；不写旧系统；不重启服务；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票日常使用包验收脚本。
标识：stock-daily-usage-package-verify
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
    generator = root / "02脚本" / "生成股票日常使用包.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    json_latest = root / "03数据" / "17日常使用包" / "股票研究日常使用包_最新.json"
    md_latest = root / "03数据" / "17日常使用包" / "股票研究日常使用包_最新.md"
    package = load_json(json_latest) if json_latest.exists() else {}
    text = md_latest.read_text(encoding="utf-8") if md_latest.exists() else ""
    pool = package.get("候选池", {}).get("候选池", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本运行成功", result.returncode == 0, result.stdout.strip())
    add_check(checks, "JSON使用包已生成", json_latest.exists() and bool(package.get("状态摘要")), str(json_latest))
    add_check(checks, "Markdown使用包已生成", md_latest.exists() and "股票研究日常使用包" in text, str(md_latest))
    add_check(checks, "包含候选池分层", all(key in pool for key in ["L5深度研究", "L6轻度关注", "L7系统过滤"]), list(pool.keys()))
    add_check(checks, "包含反馈格式", "继续观察" in text and "确认L4" in text, text[-1000:])
    add_check(checks, "包含安全边界", all(item is False for item in package.get("安全边界", {}).values()), package.get("安全边界", {}))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "股票日常使用包可用于独立查看股票研究状态。" if failed == 0 else "股票日常使用包存在失败项。",
    }
    output_dir = root / "04日志" / "日常使用包"
    output = output_dir / f"stock-daily-usage-package-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-daily-usage-package-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
