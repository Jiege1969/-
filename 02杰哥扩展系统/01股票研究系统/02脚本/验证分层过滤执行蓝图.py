# -*- coding: utf-8 -*-
"""
名称：验证分层过滤执行蓝图.py
作用：验证分层过滤规则和执行蓝图具备可落地、可放量、可防止复杂度失控的约束。
触发方式：python 验证分层过滤执行蓝图.py
依赖：Python标准库；分层过滤规则.json；生成分层过滤执行蓝图.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读配置和生成本地蓝图；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建分层过滤执行蓝图验收脚本。
标识：stock-layered-filter-blueprint-verify
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
    generator = root / "02脚本" / "生成分层过滤执行蓝图.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    rules = load_json(root / "01配置" / "分层过滤规则.json")
    report = load_json(root / "03数据" / "09分层过滤" / "分层过滤执行蓝图_最新.json")
    checks: list[dict[str, Any]] = []

    add_check(checks, "生成脚本运行成功", result.returncode == 0, result.stdout.strip())
    add_check(checks, "四个过滤阶段完整", len(rules.get("过滤阶段", [])) == 4, len(rules.get("过滤阶段", [])))
    add_check(checks, "运行模式包含体验试运行核心盘后", all(name in rules.get("运行模式", {}) for name in ["体验模式", "试运行模式", "核心模式", "盘后轻扫描模式"]), rules.get("运行模式", {}))
    add_check(checks, "L1到L4为人工确认层", all(rules.get("层级权限", {}).get(level) == "人工确认层" for level in ["L1", "L2", "L3", "L4"]), rules.get("层级权限", {}))
    s4_stage = rules.get("过滤阶段", [])[-1] if rules.get("过滤阶段") else {}
    s4_text = json.dumps(s4_stage, ensure_ascii=False)
    add_check(
        checks,
        "S4只输出研究建议且L4必须人工确认",
        "自动交易指令" in s4_text and "必须人工确认" in s4_text and "买入" not in s4_text,
        s4_stage,
    )
    add_check(checks, "禁止事项包含不自动买入", any("买入指令" in item for item in rules.get("禁止事项", [])), rules.get("禁止事项", []))
    add_check(checks, "蓝图生成阶段数为4", len(report.get("过滤阶段", [])) == 4, len(report.get("过滤阶段", [])))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "分层过滤执行蓝图已具备后续施工依据。" if failed == 0 else "分层过滤执行蓝图仍有失败项。",
    }
    output_dir = root / "04日志" / "分层过滤"
    output = output_dir / f"stock-layered-filter-blueprint-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-layered-filter-blueprint-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
