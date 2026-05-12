# -*- coding: utf-8 -*-
"""
名称：验证股票草案吸收报告.py
作用：验证旧股票草案的核心逻辑已被配置化、报告化并进入当前施工清单。
触发方式：python 验证股票草案吸收报告.py
依赖：Python标准库；旧草案吸收规则.json；生成股票草案吸收报告.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读配置和报告；只写新系统股票模块04日志；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口。
创建/修改记录：2026-04-28 创建旧草案吸收报告验收脚本。
标识：stock-draft-absorption-report-verify
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
    generator = root / "02脚本" / "生成股票草案吸收报告.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    rules = load_json(root / "01配置" / "旧草案吸收规则.json")
    report = load_json(root / "03数据" / "08草案吸收" / "旧股票草案吸收报告_最新.json")
    checks: list[dict[str, Any]] = []

    add_check(checks, "生成脚本运行成功", result.returncode == 0, result.stdout.strip())
    add_check(checks, "吸收项不少于8项", len(rules.get("已吸收内容", [])) >= 8, len(rules.get("已吸收内容", [])))
    add_check(checks, "8级分层完整", len(rules.get("8级分层", [])) == 8, len(rules.get("8级分层", [])))
    add_check(checks, "四层过滤漏斗完整", len(rules.get("分层过滤漏斗", [])) == 4, len(rules.get("分层过滤漏斗", [])))
    add_check(checks, "指标参数包含MA RSI MACD 成交量", all(key in rules.get("指标参数", {}) for key in ["MA", "RSI", "MACD", "成交量"]), rules.get("指标参数", {}))
    add_check(checks, "多数据源容错不少于4层", len(rules.get("多数据源容错", [])) >= 4, len(rules.get("多数据源容错", [])))
    add_check(checks, "暂不吸收高风险动作", any(item.get("内容") == "自动买卖操作" for item in rules.get("暂不吸收内容", [])), rules.get("暂不吸收内容", []))
    add_check(checks, "报告声明不交易不推送", report.get("安全边界", {}).get("是否自动交易") is False and report.get("安全边界", {}).get("是否企业微信真实发送") is False, report.get("安全边界", {}))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "旧股票草案核心逻辑已纳入当前股票系统施工规则。" if failed == 0 else "旧股票草案吸收仍有失败项。",
    }
    output_dir = root / "04日志" / "草案吸收"
    output = output_dir / f"stock-draft-absorption-report-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-draft-absorption-report-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
