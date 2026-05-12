# -*- coding: utf-8 -*-
"""
名称：验证无人值守巡检用户摘要模板.py
作用：生成并验证无人值守巡检用户摘要模板，确认当前不真实推送、不发送企业微信、不触发n8n。
触发方式：python 验证无人值守巡检用户摘要模板.py
依赖：Python标准库；生成无人值守巡检用户摘要模板.py；验证无人值守巡检失败诊断模板.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证用户摘要模板；不真实推送；不发送企业微信；不触发n8n；不自动确认；不自动修复；不写旧系统。
创建/修改记录：2026-04-28 创建无人值守巡检用户摘要模板验证脚本。
标识：unattended-patrol-user-summary-template-verify
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
    diagnosis_verify = manager / "02脚本" / "验证无人值守巡检失败诊断模板.py"
    generator = manager / "02脚本" / "生成无人值守巡检用户摘要模板.py"
    diagnosis_result = subprocess.run([sys.executable, str(diagnosis_verify)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "无人值守守护" / "无人值守巡检用户摘要模板_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    summary = report.get("汇总", {})
    switches = report.get("默认开关", {})
    user_summary = report.get("用户摘要模板", {})
    checks = [
        check("失败诊断模板可生成", diagnosis_result.returncode == 0, diagnosis_result.stdout.strip() or diagnosis_result.stderr.strip()),
        check("用户摘要模板生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("用户摘要模板文件存在", report_path.exists(), str(report_path)),
        check("摘要数量为一", summary.get("摘要数量") == 1, summary),
        check("真实推送为零", summary.get("真实推送数量") == 0, summary),
        check("企业微信发送为零", summary.get("企业微信发送数量") == 0, summary),
        check("触发n8n为零", summary.get("触发n8n数量") == 0, summary),
        check("自动确认为零", summary.get("自动确认数量") == 0, summary),
        check("自动修复为零", summary.get("自动修复数量") == 0, summary),
        check("写旧系统为零", summary.get("写旧系统数量") == 0, summary),
        check("真实推送开关关闭", switches.get("允许真实推送") is False, switches),
        check("企业微信发送开关关闭", switches.get("允许企业微信发送") is False, switches),
        check("包含用户需关注事项", bool(user_summary.get("用户需关注事项")), user_summary),
        check("包含系统未做事项", bool(user_summary.get("系统未做事项")), user_summary),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "unattended-patrol-user-summary-template-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "无人值守守护"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "unattended-patrol-user-summary-template-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
