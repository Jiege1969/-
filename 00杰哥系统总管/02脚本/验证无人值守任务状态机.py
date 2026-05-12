# -*- coding: utf-8 -*-
"""
名称：验证无人值守任务状态机.py
作用：生成并验证无人值守任务状态机报告，确认关键状态、允许流转和禁止流转存在且真实任务未触发。
触发方式：python 验证无人值守任务状态机.py
依赖：Python 标准库；生成无人值守任务状态机报告.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证任务状态机报告；不触发真实任务；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建无人值守任务状态机验证脚本。
标识：unattended-task-state-machine-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    script = manager / "02脚本" / "生成无人值守任务状态机报告.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "无人值守守护" / "无人值守任务状态机报告_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    states = report.get("允许状态", [])
    blocked = report.get("禁止流转", [])
    switches = report.get("默认开关", {})
    checks = [
        check("任务状态机报告生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("任务状态机报告文件存在", report_path.exists(), str(report_path)),
        check("包含待处理状态", "待处理" in states, states),
        check("包含执行中状态", "执行中" in states, states),
        check("包含待人工确认状态", "待人工确认" in states, states),
        check("包含失败待诊断状态", "失败待诊断" in states, states),
        check("包含禁止执行状态", "禁止执行" in states, states),
        check("禁止执行不得直接到执行中", any(item.get("从") == "禁止执行" and item.get("到") == "执行中" for item in blocked), blocked),
        check("未触发真实任务", report.get("是否触发真实任务") is False, report.get("是否触发真实任务")),
        check("税收业务关闭", switches.get("允许税收业务") is False, switches),
        check("旧系统写入关闭", switches.get("允许旧系统写入") is False, switches),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "unattended-task-state-machine-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "无人值守守护"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "unattended-task-state-machine-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
