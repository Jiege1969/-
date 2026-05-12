# -*- coding: utf-8 -*-
"""
名称：验证300只候选复盘执行任务包.py
作用：验证106复盘执行任务包能生成、任务数量和交易日历一致，且不触发高风险动作。
触发方式：python 验证300只候选复盘执行任务包.py
依赖：Python标准库；生成300只候选复盘执行任务包.py；300只候选复盘执行任务包规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写入验收日志；不联网抓取行情；不触发发送链路；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选复盘执行任务包验收脚本。
标识：stock-trial-pool-300-review-execution-task-package-verify
"""

from __future__ import annotations

import json
import os
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


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "说明": detail}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "生成300只候选复盘执行任务包.py"
    rule_path = root / "01配置" / "300只候选复盘执行任务包规则.json"
    checks: list[dict[str, Any]] = [
        check("脚本存在", script.exists(), str(script)),
        check("规则存在", rule_path.exists(), str(rule_path)),
    ]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    run = subprocess.run([sys.executable, str(script)], cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=120)
    checks.append(check("脚本执行", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))
    rule = load_json(rule_path)
    latest = root / rule["输出"]["数据目录"] / rule["输出"]["最新文件"]
    markdown = root / rule["输出"]["数据目录"] / rule["输出"]["报告文件"]
    date_ledger = load_json(root / "03数据" / "98交易日历复盘日期" / "300只候选复盘日期账本_最新.json")
    report = load_json(latest) if latest.exists() else {}
    tasks = report.get("复盘执行任务", [])
    expected_task_count = int(date_ledger.get("入账候选数量", 0)) * len(rule.get("任务周期", []))
    checks.append(check("最新JSON存在", latest.exists(), str(latest)))
    checks.append(check("Markdown报告存在", markdown.exists(), str(markdown)))
    checks.append(check("任务数量正确", len(tasks) == expected_task_count and expected_task_count == 15, {"实际": len(tasks), "预期": expected_task_count}))
    checks.append(check("复盘日期一致", report.get("周期日期") == date_ledger.get("周期日期"), report.get("周期日期")))
    checks.append(check("任务覆盖T+1/T+3/T+5", sorted({task.get("周期") for task in tasks}) == ["T+1", "T+3", "T+5"], sorted({task.get("周期") for task in tasks})))
    checks.append(check("当前不执行真实发送和自动交易", report.get("是否企业微信真实发送") is False and report.get("是否自动交易") is False, {"发送": report.get("是否企业微信真实发送"), "交易": report.get("是否自动交易")}))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作未触发", all(value is False for value in safety.values()), safety))
    text = markdown.read_text(encoding="utf-8-sig") if markdown.exists() else ""
    checks.append(check("Markdown包含到期分组和安全边界", "到期分组" in text and "安全边界" in text, str(markdown)))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "通过": passed, "失败": failed, "检查项": checks, "输出文件": str(latest)}
    output_dir = root / "04日志" / "复盘执行任务包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"trial-pool-300-review-execution-task-package-verify-{stamp}.json"
    latest_log = output_dir / "trial-pool-300-review-execution-task-package-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
