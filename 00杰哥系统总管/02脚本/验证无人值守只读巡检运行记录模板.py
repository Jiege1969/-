# -*- coding: utf-8 -*-
"""
名称：验证无人值守只读巡检运行记录模板.py
作用：生成并验证无人值守只读巡检运行记录模板，确认当前只登记模板，不执行巡检或自动修复。
触发方式：python 验证无人值守只读巡检运行记录模板.py
依赖：Python标准库；生成无人值守只读巡检运行记录模板.py；验证无人值守只读巡检调度草案.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证运行记录模板；不执行巡检；不创建系统计划任务；不触发n8n；不联网；不发送企业微信；不写正式库；不写旧系统；不自动修复。
创建/修改记录：2026-04-28 创建无人值守只读巡检运行记录模板验证脚本。
标识：unattended-readonly-patrol-run-record-template-verify
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
    schedule_verify = manager / "02脚本" / "验证无人值守只读巡检调度草案.py"
    generator = manager / "02脚本" / "生成无人值守只读巡检运行记录模板.py"
    schedule_result = subprocess.run([sys.executable, str(schedule_verify)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "无人值守守护" / "无人值守只读巡检运行记录模板_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    summary = report.get("汇总", {})
    switches = report.get("默认开关", {})
    checks = [
        check("调度草案可生成", schedule_result.returncode == 0, schedule_result.stdout.strip() or schedule_result.stderr.strip()),
        check("运行记录模板生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("运行记录模板文件存在", report_path.exists(), str(report_path)),
        check("模板数量足够", summary.get("模板数量", 0) >= 5, summary),
        check("全部未执行", summary.get("未执行数量") == summary.get("模板数量"), summary),
        check("实际执行巡检为零", summary.get("实际执行巡检数量") == 0, summary),
        check("触发修复为零", summary.get("触发修复数量") == 0, summary),
        check("进入诊断为零", summary.get("进入诊断数量") == 0, summary),
        check("进入经验提炼为零", summary.get("进入经验提炼数量") == 0, summary),
        check("触发n8n为零", summary.get("触发n8n数量") == 0, summary),
        check("真实联网为零", summary.get("真实联网数量") == 0, summary),
        check("写正式库为零", summary.get("写正式库数量") == 0, summary),
        check("写旧系统为零", summary.get("写旧系统数量") == 0, summary),
        check("执行巡检开关关闭", switches.get("允许执行巡检") is False, switches),
        check("自动修复开关关闭", switches.get("允许自动修复") is False, switches),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "unattended-readonly-patrol-run-record-template-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "无人值守守护"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "unattended-readonly-patrol-run-record-template-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
