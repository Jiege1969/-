# -*- coding: utf-8 -*-
"""
名称：验证知识库系统状态摘要.py
作用：验证知识库系统状态摘要生成链路可运行，并确认本地问答预演、正式库、n8n、企业微信等边界仍处于受控状态。
触发方式：python 验证知识库系统状态摘要.py
依赖：Python标准库；生成知识库系统状态摘要.py。
所属系统：01杰哥智能系统/知识库
安全边界：只运行本地摘要生成和验收；只写入04日志/知识库；不生成向量；不写正式库；不触发n8n；不发送企业微信；不写旧系统；不接入税收业务。
创建/修改记录：2026-04-29 创建知识库系统状态摘要验收脚本；2026-04-29 增加本地问答预演验收项。
标识：knowledge-system-status-summary-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    script_dir = root / "02脚本" / "知识库"
    generator = script_dir / "生成知识库系统状态摘要.py"
    latest_json = root / "03数据" / "知识库" / "05状态摘要" / "knowledge-system-status-summary-最新.json"
    latest_md = root / "03数据" / "知识库" / "05状态摘要" / "知识库系统状态摘要_最新.md"
    log_dir = root / "04日志" / "知识库"

    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON摘要存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown摘要存在", latest_md.exists(), str(latest_md))

    report = load_json(latest_json) if latest_json.exists() else {}
    safety = report.get("安全边界", {})
    add_check(checks, "总体状态健康", report.get("汇总", {}).get("状态") == "healthy", report.get("汇总", {}))
    add_check(checks, "检索增强链路健康", report.get("检索增强链路", {}).get("状态") == "healthy", report.get("检索增强链路", {}))
    add_check(checks, "R02预演器健康", report.get("R02本地入库预演器", {}).get("状态") == "healthy", report.get("R02本地入库预演器", {}))
    add_check(checks, "本地问答预演健康", report.get("本地问答预演", {}).get("状态") == "healthy", report.get("本地问答预演", {}))
    add_check(checks, "未调用模型推理", safety.get("调用模型推理") is False, safety)
    add_check(checks, "未生成向量", safety.get("生成向量") is False, safety)
    add_check(checks, "未写正式库", safety.get("写正式库") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False, safety)
    add_check(checks, "未发送企业微信", safety.get("发送企业微信") is False, safety)
    add_check(checks, "未写旧系统", safety.get("写旧系统") is False, safety)
    add_check(checks, "未接入税收", safety.get("接入税收") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-system-status-summary-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
    }
    output = log_dir / "knowledge-system-status-summary-verify-最新.json"
    write_json(output, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
