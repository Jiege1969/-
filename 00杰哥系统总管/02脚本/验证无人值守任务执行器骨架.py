# -*- coding: utf-8 -*-
"""
名称：验证无人值守任务执行器骨架.py
作用：生成并验证无人值守任务执行器骨架报告，确认当前只做计划，不实际调用执行器或触发真实动作。
触发方式：python 验证无人值守任务执行器骨架.py
依赖：Python标准库；生成无人值守任务执行器骨架报告.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证任务计划报告；不调用任务执行器；不触发n8n；不联网；不发送企业微信；不写正式库；不写旧系统。
创建/修改记录：2026-04-28 创建无人值守任务执行器骨架验证脚本。
标识：unattended-task-executor-skeleton-verify
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
    script = manager / "02脚本" / "生成无人值守任务执行器骨架报告.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "无人值守守护" / "无人值守任务执行器骨架报告_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    summary = report.get("汇总", {})
    switches = report.get("默认开关", {})
    plans = report.get("任务计划", [])
    checks = [
        check("执行器骨架报告生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("执行器骨架报告文件存在", report_path.exists(), str(report_path)),
        check("执行模式为只计划", report.get("执行模式") == "plan_only", report.get("执行模式")),
        check("包含任务计划", len(plans) >= 3, len(plans)),
        check("存在只生成计划任务", summary.get("仅生成计划数量", 0) >= 1, summary),
        check("存在阻断任务", summary.get("阻断数量", 0) >= 1, summary),
        check("实际调用执行器为零", summary.get("实际调用执行器数量") == 0, summary),
        check("触发n8n为零", summary.get("触发n8n数量") == 0, summary),
        check("真实联网为零", summary.get("真实联网数量") == 0, summary),
        check("真实发送为零", summary.get("真实发送数量") == 0, summary),
        check("写正式库为零", summary.get("写正式库数量") == 0, summary),
        check("写旧系统为零", summary.get("写旧系统数量") == 0, summary),
        check("实际调用总开关关闭", switches.get("允许实际调用执行器") is False, switches),
        check("n8n总开关关闭", switches.get("允许触发n8n") is False, switches),
        check("旧系统写入总开关关闭", switches.get("允许旧系统写入") is False, switches),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "unattended-task-executor-skeleton-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "无人值守守护"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "unattended-task-executor-skeleton-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
