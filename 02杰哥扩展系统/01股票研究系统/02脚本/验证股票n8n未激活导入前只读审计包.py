# -*- coding: utf-8 -*-
"""
名称：验证股票n8n未激活导入前只读审计包.py
作用：验证股票n8n未激活导入前只读审计包已生成，且审计过程未调用n8n API、未导入、未启用、未触发。
触发方式：python 验证股票n8n未激活导入前只读审计包.py
依赖：Python标准库；生成股票n8n未激活导入前只读审计包.py；股票n8n未激活导入前只读审计规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地审计包验收；不调用n8n API；不导入n8n；不启用Webhook；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票n8n未激活导入前只读审计包验收脚本。
标识：stock-n8n-inactive-import-preread-audit-package-verify
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
    generator = root / "02脚本" / "生成股票n8n未激活导入前只读审计包.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest_json = root / "03数据" / "38n8n导入前只读审计" / "股票n8n未激活导入前只读审计包_最新.json"
    latest_md = root / "03数据" / "38n8n导入前只读审计" / "股票n8n未激活导入前只读审计包_最新.md"
    report = load_json(latest_json)
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    actions = report.get("实际动作", {})
    workflow_audit = report.get("工作流草案审计", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "生成脚本执行成功", result.returncode == 0, {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()})
    add_check(checks, "最新JSON存在", latest_json.exists() and "工作流草案审计" in report, str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists() and "股票n8n未激活导入前只读审计包" in text, str(latest_md))
    add_check(checks, "工作流保持未激活", workflow_audit.get("active") is False, workflow_audit.get("active"))
    add_check(checks, "无非允许节点类型", workflow_audit.get("非允许节点类型") == [], workflow_audit.get("非允许节点类型"))
    add_check(checks, "导入启用均需人工确认", workflow_audit.get("需要人工确认导入") is True and workflow_audit.get("需要人工确认启用") is True, workflow_audit)
    add_check(checks, "审计未执行高风险动作", all(value is False for value in actions.values()), actions)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "股票n8n未激活导入前只读审计包可用。" if failed == 0 else "股票n8n未激活导入前只读审计包存在失败项。",
    }
    output_dir = root / "04日志" / "n8n导入前只读审计"
    output = output_dir / f"stock-n8n-inactive-import-preread-audit-package-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-n8n-inactive-import-preread-audit-package-verify-最新.json"
    write_json(output, verify)
    write_json(latest, verify)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
