# -*- coding: utf-8 -*-
"""
名称：验证复盘账本可运行.py
作用：验证四本账已从蓝图进入可运行状态，能够生成系统判断账、人工决策账模板、结果验证计划和经验提炼候选账。
触发方式：python 验证复盘账本可运行.py
依赖：Python标准库；记录系统判断账.py；生成人工决策账模板.py；生成结果验证计划.py；生成经验提炼候选账.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行新股票系统本地账本脚本；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建复盘账本可运行验收脚本。
标识：stock-review-ledger-runtime-verify
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


def run_script(path: Path) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return {
        "脚本": str(path),
        "返回码": result.returncode,
        "标准输出": result.stdout.strip(),
        "标准错误": result.stderr.strip()
    }


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    scripts = [
        root / "02脚本" / "记录系统判断账.py",
        root / "02脚本" / "生成人工决策账模板.py",
        root / "02脚本" / "生成结果验证计划.py",
        root / "02脚本" / "生成经验提炼候选账.py",
        root / "02脚本" / "验证人工反馈入账.py",
    ]
    results = [run_script(path) for path in scripts]
    rules = load_json(root / "01配置" / "复盘账本运行规则.json")
    ledger_paths = rules.get("账本路径", {})
    system_judgment = load_json(root / ledger_paths.get("系统判断账", "03数据/10复盘闭环/01系统判断账") / "系统判断账_最新.json")
    human_template = load_json(root / ledger_paths.get("人工决策账", "03数据/10复盘闭环/02人工决策账") / "人工决策账模板_最新.json")
    verification_plan = load_json(root / ledger_paths.get("结果验证账", "03数据/10复盘闭环/03结果验证账") / "结果验证计划_最新.json")
    experience_candidate = load_json(root / ledger_paths.get("经验提炼账", "03数据/10复盘闭环/04经验提炼账") / "经验提炼候选账_最新.json")
    checks: list[dict[str, Any]] = []

    add_check(checks, "账本脚本和反馈入账验收全部运行成功", all(item["返回码"] == 0 for item in results), results)
    add_check(checks, "系统判断账有记录", system_judgment.get("记录数量", 0) > 0, system_judgment.get("记录数量"))
    add_check(checks, "人工决策账模板已生成", len(human_template.get("候选决策记录", [])) > 0, len(human_template.get("候选决策记录", [])))
    add_check(checks, "结果验证计划覆盖四个周期", verification_plan.get("任务数量", 0) >= system_judgment.get("记录数量", 0) * 4, verification_plan.get("任务数量"))
    add_check(checks, "经验提炼候选账已生成", experience_candidate.get("候选状态") == "待结果验证完成后提炼", experience_candidate.get("候选状态"))
    add_check(checks, "真实动作关闭", all(item is False for item in system_judgment.get("安全边界", {}).values()), system_judgment.get("安全边界", {}))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "复盘四本账已具备本地可运行能力。" if failed == 0 else "复盘四本账运行存在失败项。",
    }
    output_dir = root / "04日志" / "复盘闭环"
    output = output_dir / f"stock-review-ledger-runtime-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-review-ledger-runtime-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
