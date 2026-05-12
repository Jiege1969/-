"""
名称：验证办公材料正式输出禁用态.py
作用：执行并验证办公材料正式输出禁用态检查，确认正式文档生成、覆盖、涉密读取、外发、上传、n8n触发和企业微信真实发送均关闭。
触发方式：python 验证办公材料正式输出禁用态.py
依赖：Python 标准库；执行办公材料正式输出禁用态检查.py。
所属系统：00杰哥系统总管
安全边界：只执行禁用态检查；不生成正式文档；不覆盖正式文档；不读取涉密资料；不自动外发；不上传；不触发n8n；不真实发送企业微信。
创建/修改记录：2026-04-27 创建办公材料正式输出禁用态验收脚本。
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


def module_root() -> Path:
    return v3_root() / "02杰哥扩展系统" / "03本职工作系统"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "执行办公材料正式输出禁用态检查.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = root / "03数据" / "04本地生成门禁" / "办公材料正式输出禁用态检查_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    checks = [
        check("禁用态检查生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("禁用态检查报告存在", report_path.exists(), str(report_path)),
        check("执行器为禁用态", report.get("执行器状态") == "禁用态", report.get("执行器状态")),
        check("正式文档生成关闭", report.get("是否生成正式文档") is False, report.get("是否生成正式文档")),
        check("正式文档覆盖关闭", report.get("是否覆盖正式文档") is False, report.get("是否覆盖正式文档")),
        check("涉密读取关闭", report.get("是否读取涉密资料") is False, report.get("是否读取涉密资料")),
        check("自动外发关闭", report.get("是否自动外发") is False, report.get("是否自动外发")),
        check("自动上传关闭", report.get("是否自动上传") is False, report.get("是否自动上传")),
        check("n8n触发关闭", report.get("是否触发n8n") is False, report.get("是否触发n8n")),
        check("企业微信真实发送关闭", report.get("是否企业微信真实发送") is False, report.get("是否企业微信真实发送")),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "office-final-output-disabled-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = v3_root() / "00杰哥系统总管" / "04日志" / "办公材料门禁"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"office-final-output-disabled-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
