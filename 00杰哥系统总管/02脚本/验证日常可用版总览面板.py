# -*- coding: utf-8 -*-
"""
名称：验证日常可用版总览面板.py
作用：验证日常可用版总览面板可生成，并确认该面板只读取状态、不触发真实业务。
触发方式：python 验证日常可用版总览面板.py
依赖：Python标准库；生成日常可用版总览面板.py。
所属系统：00杰哥系统总管
安全边界：只运行本地总览生成和验收；只写入04日志；不触发n8n；不发送企业微信；不写旧系统；不执行真实业务；不接入交易。
创建/修改记录：2026-04-29 创建日常可用版总览面板验收脚本。
标识：daily-usable-overview-dashboard-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    manager = manager_root()
    generator = manager / "02脚本" / "生成日常可用版总览面板.py"
    latest_json = manager / "03数据" / "日常可用版总览" / "daily-usable-overview-dashboard-最新.json"
    latest_md = manager / "03数据" / "日常可用版总览" / "日常可用版总览面板_最新.md"
    log_dir = manager / "04日志" / "日常可用版总览"

    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON总览存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown总览存在", latest_md.exists(), str(latest_md))

    report = load_json(latest_json) if latest_json.exists() else {}
    summary = report.get("汇总", {})
    safety = report.get("安全边界", {})
    add_check(checks, "总体状态健康", summary.get("状态") == "healthy", summary)
    add_check(checks, "入口全部可用", summary.get("日常入口可用") == summary.get("日常入口总数"), summary)
    add_check(checks, "资源巡检健康", summary.get("资源巡检状态") == "healthy", summary)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False, safety)
    add_check(checks, "未发送企业微信", safety.get("发送企业微信") is False, safety)
    add_check(checks, "未写旧系统", safety.get("写旧系统") is False, safety)
    add_check(checks, "未执行真实业务", safety.get("执行真实业务") is False, safety)
    add_check(checks, "未接入交易", safety.get("交易接口") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "daily-usable-overview-dashboard-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
    }
    output = log_dir / f"daily-usable-overview-dashboard-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = log_dir / "daily-usable-overview-dashboard-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
