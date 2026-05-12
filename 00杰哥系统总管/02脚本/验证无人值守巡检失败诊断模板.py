# -*- coding: utf-8 -*-
"""
名称：验证无人值守巡检失败诊断模板.py
作用：生成并验证无人值守巡检失败诊断模板，确认失败后进入诊断和止损，不自动修复或触发真实动作。
触发方式：python 验证无人值守巡检失败诊断模板.py
依赖：Python标准库；生成无人值守巡检失败诊断模板.py；验证无人值守只读巡检运行记录模板.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证诊断模板；不自动修复；不重试执行；不重启服务；不删除；不覆盖；不触发n8n；不发送企业微信；不写正式库；不写旧系统。
创建/修改记录：2026-04-28 创建无人值守巡检失败诊断模板验证脚本。
标识：unattended-patrol-failure-diagnosis-template-verify
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
    run_record_verify = manager / "02脚本" / "验证无人值守只读巡检运行记录模板.py"
    generator = manager / "02脚本" / "生成无人值守巡检失败诊断模板.py"
    run_record_result = subprocess.run([sys.executable, str(run_record_verify)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "无人值守守护" / "无人值守巡检失败诊断模板_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    summary = report.get("汇总", {})
    switches = report.get("默认开关", {})
    stop_rules = []
    for item in report.get("诊断模板", []):
        stop_rules.extend(item.get("止损条件", []))
    checks = [
        check("运行记录模板可生成", run_record_result.returncode == 0, run_record_result.stdout.strip() or run_record_result.stderr.strip()),
        check("失败诊断模板生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("失败诊断模板文件存在", report_path.exists(), str(report_path)),
        check("模板数量足够", summary.get("模板数量", 0) >= 5, summary),
        check("自动修复数量为零", summary.get("允许自动修复数量") == 0, summary),
        check("重试执行数量为零", summary.get("允许重试执行数量") == 0, summary),
        check("触发真实动作数量为零", summary.get("触发真实动作数量") == 0, summary),
        check("自动修复开关关闭", switches.get("允许自动修复") is False, switches),
        check("重启服务开关关闭", switches.get("允许重启服务") is False, switches),
        check("删除文件开关关闭", switches.get("允许删除文件") is False, switches),
        check("覆盖配置开关关闭", switches.get("允许覆盖配置") is False, switches),
        check("止损条件包含连续失败", any("连续失败2次" in item for item in stop_rules), stop_rules),
        check("止损条件包含高风险动作", any("删除、覆盖、重启" in item for item in stop_rules), stop_rules),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "unattended-patrol-failure-diagnosis-template-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "无人值守守护"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "unattended-patrol-failure-diagnosis-template-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
