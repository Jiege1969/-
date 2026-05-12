"""
名称：验证日常可用版入口.py
作用：执行日常可用版入口检查和入口面板生成，验证本机入口层达到日常可用版基础要求。
触发方式：python 验证日常可用版入口.py
依赖：Python 标准库；检查日常可用版本地入口.py；生成日常可用版入口面板.py。
所属系统：00杰哥系统总管
安全边界：只读检查本地入口并写入新系统日志/文档；不触发业务、不发送企业微信、不写旧系统、不接入税收业务。
创建/修改记录：2026-04-27 创建日常可用版入口验收脚本；2026-05-01 放宽全量入口检查超时并记录超时而非直接崩溃。
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


def run_script(path: Path, timeout: int = 900) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return {
            "是否完成": True,
            "是否超时": False,
            "返回码": result.returncode,
            "标准输出": result.stdout.strip(),
            "标准错误": result.stderr.strip(),
            "超时秒数": timeout,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "是否完成": False,
            "是否超时": True,
            "返回码": None,
            "标准输出": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "标准错误": (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
            "超时秒数": timeout,
            "错误": f"执行超时：{path}",
        }


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = v3_root()
    check_script = root / "00杰哥系统总管" / "02脚本" / "检查日常可用版本地入口.py"
    panel_script = root / "00杰哥系统总管" / "02脚本" / "生成日常可用版入口面板.py"
    check_result = run_script(check_script, timeout=900)
    panel_result = run_script(panel_script, timeout=300)
    report_path = root / "00杰哥系统总管" / "04日志" / "日常可用版" / "daily-usable-entry-check-最新.json"
    panel_path = root / "00杰哥系统总管" / "07文档" / "日常可用版入口面板.md"
    report = load_json(report_path) if report_path.exists() else {}
    checks = [
        check("入口检查脚本执行成功", check_result.get("返回码") == 0, check_result),
        check("入口面板生成成功", panel_result.get("返回码") == 0, panel_result),
        check("入口检查报告存在", report_path.exists(), str(report_path)),
        check("入口面板文档存在", panel_path.exists(), str(panel_path)),
        check("必检入口全部可用", report.get("汇总", {}).get("不可用") == 0, report.get("汇总", {})),
        check("安全边界未触发真实业务", all(value is False for value in report.get("安全边界", {}).values()), report.get("安全边界", {})),
    ]
    output_dir = root / "00杰哥系统总管" / "04日志" / "日常可用版"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "daily-usable-entry-verify-最新.json"
    result = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "daily-usable-entry-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if result["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
