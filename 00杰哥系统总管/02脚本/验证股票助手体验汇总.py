# -*- coding: utf-8 -*-
"""
名称：验证股票助手体验汇总.py
作用：由00总管统一验证股票研究系统独立体验入口，确保新股票助手可像旧股票服务一样本地使用。
触发方式：python 验证股票助手体验汇总.py
依赖：Python标准库；02扩展系统/01股票研究系统/02脚本/启动股票助手.ps1；验证股票助手体验.py。
所属系统：00杰哥系统总管
安全边界：只启动或复用127.0.0.1:19300本地股票助手；不停止旧系统；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口。
创建/修改记录：2026-04-28 创建股票助手体验总管验收汇总。
标识：stock-assistant-experience-summary-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_command(command: list[str], timeout: int = 180) -> dict[str, Any]:
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {
        "命令": command,
        "返回码": result.returncode,
        "标准输出": result.stdout.strip(),
        "标准错误": result.stderr.strip(),
    }


def main() -> int:
    root = system_root()
    stock_root = root / "02杰哥扩展系统" / "01股票研究系统"
    start_script = stock_root / "02脚本" / "启动股票助手.ps1"
    verify_script = stock_root / "02脚本" / "验证股票助手体验.py"
    checks: list[dict[str, Any]] = []

    checks.append({"名称": "启动脚本存在", "通过": start_script.exists(), "详情": str(start_script)})
    checks.append({"名称": "体验验收脚本存在", "通过": verify_script.exists(), "详情": str(verify_script)})

    start_result = run_command([
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(start_script),
    ], timeout=120)
    checks.append({"名称": "股票助手可启动或复用", "通过": start_result["返回码"] == 0, "详情": start_result})

    verify_result = run_command([sys.executable, str(verify_script)], timeout=180)
    checks.append({"名称": "股票助手体验验收通过", "通过": verify_result["返回码"] == 0, "详情": verify_result})

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "系统根目录": str(root),
        "股票系统目录": str(stock_root),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "股票助手体验入口已纳入总管统一验收。" if failed == 0 else "股票助手体验入口总管验收存在失败项。",
    }
    output_dir = root / "00杰哥系统总管" / "04日志" / "股票助手体验"
    output = output_dir / "stock-assistant-experience-summary-verify-最新.json"
    latest = output_dir / "stock-assistant-experience-summary-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
