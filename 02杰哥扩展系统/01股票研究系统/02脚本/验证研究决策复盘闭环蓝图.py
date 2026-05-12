# -*- coding: utf-8 -*-
"""
名称：验证研究决策复盘闭环蓝图.py
作用：验证股票研究系统的四本账复盘闭环已配置化、目录化、蓝图化，并保持进化边界。
触发方式：python 验证研究决策复盘闭环蓝图.py
依赖：Python标准库；研究决策复盘闭环规则.json；生成研究决策复盘闭环蓝图.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读配置并生成本地蓝图；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建研究决策复盘闭环蓝图验收脚本。
标识：stock-review-evolution-loop-blueprint-verify
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
    generator = root / "02脚本" / "生成研究决策复盘闭环蓝图.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    rules = load_json(root / "01配置" / "研究决策复盘闭环规则.json")
    report = load_json(root / "03数据" / "10复盘闭环" / "00蓝图" / "研究决策复盘闭环蓝图_最新.json")
    checks: list[dict[str, Any]] = []

    ledger_names = [item.get("账本") for item in rules.get("四本账", [])]
    forbidden = rules.get("进化边界", {}).get("禁止", [])
    allowed = rules.get("进化边界", {}).get("允许", [])

    add_check(checks, "生成脚本运行成功", result.returncode == 0, result.stdout.strip())
    add_check(checks, "四本账完整", ledger_names == ["系统判断账", "人工决策账", "结果验证账", "经验提炼账"], ledger_names)
    add_check(checks, "四本账目录已创建", len(report.get("账本目录", [])) == 4 and all(Path(path).exists() for path in report.get("账本目录", [])), report.get("账本目录", []))
    add_check(checks, "归因矩阵四类完整", len(rules.get("归因矩阵", [])) == 4, rules.get("归因矩阵", []))
    add_check(checks, "验证周期包含T+1 T+3 T+5 T+20", [item.get("周期") for item in rules.get("验证周期", [])] == ["T+1", "T+3", "T+5", "T+20"], rules.get("验证周期", []))
    add_check(checks, "允许进入进化候选", "进入03进化系统待提炼样本" in allowed, allowed)
    add_check(checks, "禁止自动交易和自动升级", any("自动买入" in item for item in forbidden) and any("自动升级到L4以上" in item for item in forbidden), forbidden)
    add_check(checks, "报告安全边界关闭真实动作", report.get("安全边界", {}).get("是否自动交易") is False and report.get("安全边界", {}).get("是否企业微信真实发送") is False, report.get("安全边界", {}))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "研究决策复盘闭环已纳入股票系统进化机制。" if failed == 0 else "研究决策复盘闭环仍有失败项。",
    }
    output_dir = root / "04日志" / "复盘闭环"
    output = output_dir / f"stock-review-evolution-loop-blueprint-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-review-evolution-loop-blueprint-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
