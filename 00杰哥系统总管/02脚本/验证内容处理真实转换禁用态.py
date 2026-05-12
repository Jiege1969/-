"""
名称：验证内容处理真实转换禁用态.py
作用：执行并验证内容处理真实转换禁用态检查，确认真实转换、源文件覆盖、删除、外发、跳过格式校验、n8n触发和企业微信真实发送均关闭。
触发方式：python 验证内容处理真实转换禁用态.py
依赖：Python 标准库；执行内容处理真实转换禁用态检查.py。
所属系统：00杰哥系统总管
安全边界：只执行禁用态检查；不执行真实转换；不覆盖源文件；不删除源文件；不外发转换结果；不跳过格式校验；不触发n8n；不真实发送企业微信。
创建/修改记录：2026-04-27 创建内容处理真实转换禁用态验收脚本。
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
    return v3_root() / "02杰哥扩展系统" / "04内容处理系统"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "执行内容处理真实转换禁用态检查.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = root / "03数据" / "05本地转换门禁" / "内容处理真实转换禁用态检查_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    checks = [
        check("禁用态检查生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("禁用态检查报告存在", report_path.exists(), str(report_path)),
        check("执行器为禁用态", report.get("执行器状态") == "禁用态", report.get("执行器状态")),
        check("真实转换关闭", report.get("是否执行真实转换") is False, report.get("是否执行真实转换")),
        check("源文件覆盖关闭", report.get("是否覆盖源文件") is False, report.get("是否覆盖源文件")),
        check("源文件删除关闭", report.get("是否删除源文件") is False, report.get("是否删除源文件")),
        check("转换结果外发关闭", report.get("是否外发转换结果") is False, report.get("是否外发转换结果")),
        check("跳过格式校验关闭", report.get("是否跳过格式校验") is False, report.get("是否跳过格式校验")),
        check("n8n触发关闭", report.get("是否触发n8n") is False, report.get("是否触发n8n")),
        check("企业微信真实发送关闭", report.get("是否企业微信真实发送") is False, report.get("是否企业微信真实发送")),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "content-real-convert-disabled-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = v3_root() / "00杰哥系统总管" / "04日志" / "内容处理门禁"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"content-real-convert-disabled-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "content-real-convert-disabled-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
