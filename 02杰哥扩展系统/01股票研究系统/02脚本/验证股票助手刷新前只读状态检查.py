# -*- coding: utf-8 -*-
"""
名称：验证股票助手刷新前只读状态检查.py
作用：验证股票助手刷新前只读状态检查报告已生成，并确认检查过程没有停止、启动、重启或触发真实链路。
触发方式：python 验证股票助手刷新前只读状态检查.py
依赖：Python标准库；生成股票助手刷新前只读状态检查.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地只读状态检查验收；不停止服务；不启动服务；不重启服务；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手刷新前只读状态检查验收脚本。
标识：stock-assistant-prerefresh-readonly-status-check-verify
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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成股票助手刷新前只读状态检查.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    latest_json = root / "03数据" / "37助手刷新前只读状态" / "股票助手刷新前只读状态检查_最新.json"
    latest_md = root / "03数据" / "37助手刷新前只读状态" / "股票助手刷新前只读状态检查_最新.md"
    report = load_json(latest_json)
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    actions = report.get("实际动作", {})
    probe_paths = [item.get("path") for item in report.get("接口探测", [])]
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "生成脚本执行成功", result.returncode == 0, {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()})
    add_check(checks, "最新JSON存在", latest_json.exists() and len(report.get("接口探测", [])) >= 6, str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists() and "股票助手刷新前只读状态检查" in text, str(latest_md))
    add_check(checks, "关键接口已探测", all(path in probe_paths for path in ["/health", "/data-health", "/status-summary", "/daily-package"]), probe_paths)
    add_check(checks, "刷新需求有结论", isinstance(report.get("是否需要刷新"), bool), report.get("当前结论"))
    add_check(checks, "高风险动作未执行", all(value is False for value in actions.values()), actions)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "股票助手刷新前只读状态检查可用。" if failed == 0 else "股票助手刷新前只读状态检查存在失败项。",
    }
    output_dir = root / "04日志" / "助手刷新前只读状态"
    output = output_dir / f"stock-assistant-prerefresh-readonly-status-check-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-assistant-prerefresh-readonly-status-check-verify-最新.json"
    write_json(output, verify)
    write_json(latest, verify)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
