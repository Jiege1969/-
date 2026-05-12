# -*- coding: utf-8 -*-
"""
名称：验证R03办公材料草稿预演器.py
作用：生成并验证R03办公材料草稿预演器联检报告，确认预演器就绪但冻结。
触发方式：python 验证R03办公材料草稿预演器.py
依赖：Python 标准库；执行R03办公材料草稿预演器.py。
所属系统：02杰哥扩展系统/03本职工作系统
安全边界：只生成和验证office_draft_dry_run报告；不输出正式文档；不覆盖原文件；不联网；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建R03办公材料草稿预演器验证脚本。
标识：r03-office-draft-executor-verify
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


def system_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "执行R03办公材料草稿预演器.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = root / "03数据" / "04本地生成门禁" / "R03办公材料草稿预演器联检_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    checks_data = report.get("联检结果", {})
    checks = [
        check("预演器联检生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("预演器联检文件存在", report_path.exists(), str(report_path)),
        check("执行器状态为就绪但冻结", report.get("执行器状态") == "就绪但冻结", report.get("执行器状态")),
        check("未输出正式文档", report.get("是否输出正式文档") is False, report.get("是否输出正式文档")),
        check("未允许进入正式输出", report.get("是否允许进入正式输出") is False, report.get("是否允许进入正式输出")),
        check("正式文档输出关闭", checks_data.get("正式文档输出关闭") is True, checks_data),
        check("覆盖原文件关闭", checks_data.get("覆盖原文件关闭") is True, checks_data),
        check("最终闸口未放行", checks_data.get("最终闸口未放行") is True, checks_data),
        check("R03窗口未开放", checks_data.get("R03窗口未开放") is True, checks_data),
        check("R03许可令未签发", checks_data.get("R03许可令未签发") is True, checks_data),
        check("旧系统写入关闭", checks_data.get("旧系统写入关闭") is True, checks_data),
        check("税收业务关闭", checks_data.get("税收业务关闭") is True, checks_data),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "r03-office-draft-executor-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "04日志" / "本地生成门禁"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    output = output_dir / f"r03-office-draft-executor-verify-{timestamp}.json"
    latest = output_dir / "r03-office-draft-executor-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    manager_output_dir = system_root() / "00杰哥系统总管" / "04日志" / "办公材料门禁"
    manager_output_dir.mkdir(parents=True, exist_ok=True)
    manager_output = manager_output_dir / f"r03-office-draft-executor-verify-{timestamp}.json"
    manager_latest = manager_output_dir / "r03-office-draft-executor-verify-最新.json"
    manager_output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    manager_latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
