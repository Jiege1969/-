# -*- coding: utf-8 -*-
"""
名称：验证企业微信统一指令灰度放行门禁.py
作用：验证企业微信统一指令灰度放行门禁可生成，并确认当前只允许本地/影子预演通过，真实灰度未被自动放开。
触发方式：python 验证企业微信统一指令灰度放行门禁.py
依赖：Python标准库；生成企业微信统一指令灰度放行门禁.py。
所属系统：02杰哥扩展系统/00公共组件/企业微信接入设置
安全边界：只运行本地门禁生成和验收；只写入04日志；不真实发送企业微信；不触发Webhook；不触发n8n；不写旧系统；不接入税收真实业务；不接入交易。
创建/修改记录：2026-04-29 创建企业微信统一指令灰度放行门禁验收脚本。
标识：wecom-unified-command-gray-gate-verify
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


def int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成企业微信统一指令灰度放行门禁.py"
    latest_json = root / "03数据" / "10统一指令灰度放行门禁" / "wecom-unified-command-gray-gate-最新.json"
    latest_md = root / "03数据" / "10统一指令灰度放行门禁" / "企业微信统一指令灰度放行门禁_最新.md"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)

    report = load_json(latest_json) if latest_json.exists() else {}
    summary = report.get("汇总", {})
    checks_from_report = report.get("检查项", [])
    rule = report.get("规则", {})
    gray_scope = rule.get("灰度范围", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON门禁存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown门禁存在", latest_md.exists(), str(latest_md))
    add_check(checks, "门禁状态通过", summary.get("门禁状态") == "pass", summary)
    add_check(checks, "门禁检查全部通过", summary.get("失败数量") == 0 and summary.get("通过数量") == len(checks_from_report), summary)
    add_check(checks, "检查项不少于12项", len(checks_from_report) >= 12, len(checks_from_report))
    add_check(checks, "首轮真实消息数为0", int_value(summary.get("最大首轮真实消息数"), 99) == 0, summary)
    add_check(checks, "当前不允许自动真实灰度", int_value(summary.get("最大首轮真实消息数"), 99) == 0 and gray_scope.get("允许真实灰度") is False, {"summary": summary, "gray_scope": gray_scope})
    add_check(checks, "规则禁止扩大白名单", gray_scope.get("允许扩大白名单") is False, gray_scope)
    add_check(checks, "规则禁止交易接口", gray_scope.get("允许交易接口") is False, gray_scope)
    add_check(checks, "规则禁止税收真实业务", gray_scope.get("允许税收真实业务") is False, gray_scope)
    add_check(checks, "规则禁止写旧系统", gray_scope.get("允许写旧系统") is False, gray_scope)
    add_check(checks, "规则禁止写正式业务库", gray_scope.get("允许写正式业务库") is False, gray_scope)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "wecom-unified-command-gray-gate-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
    }
    output = root / "04日志" / "wecom-unified-command-gray-gate-verify-最新.json"
    write_json(output, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
