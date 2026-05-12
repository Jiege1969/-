# -*- coding: utf-8 -*-
"""
名称：验证企业微信股票查询禁用态.py
作用：验证企业微信股票查询禁用态模拟链路可运行，且不真实发送、不触发n8n、不调用交易接口。
触发方式：python 验证企业微信股票查询禁用态.py
依赖：Python标准库；模拟企业微信股票查询.py；企业微信股票查询禁用态规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地模拟；不真实发送企业微信；不触发n8n；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建企业微信股票查询禁用态验收脚本。
标识：stock-wework-query-dryrun-verify
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
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def run_message(script: Path, message: str) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(script), "--message", message], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return {"消息": message, "返回码": result.returncode, "标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "模拟企业微信股票查询.py"
    samples = ["分析新易盛", "查看L5候选", "今日股票日常包", "数据健康度"]
    runs = [run_message(script, item) for item in samples]
    latest = root / "03数据" / "18企业微信股票查询禁用态" / "企业微信股票查询禁用态_最新.json"
    latest_md = root / "03数据" / "18企业微信股票查询禁用态" / "企业微信股票查询禁用态_最新.md"
    payload = load_json(latest) if latest.exists() else {}
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    checks: list[dict[str, Any]] = []
    add_check(checks, "模拟脚本存在", script.exists(), str(script))
    add_check(checks, "样例消息全部通过", all(item["返回码"] == 0 for item in runs), runs)
    add_check(checks, "最新JSON输出存在", latest.exists() and payload.get("模式") == "dry_run_only", str(latest))
    add_check(checks, "最新Markdown输出存在", latest_md.exists() and "企业微信股票查询禁用态" in text, str(latest_md))
    add_check(checks, "真实发送关闭", payload.get("企业微信真实发送") is False, payload)
    add_check(checks, "n8n触发关闭", payload.get("触发n8n") is False, payload)
    add_check(checks, "交易接口关闭", payload.get("安全边界", {}).get("是否调用券商接口") is False and payload.get("安全边界", {}).get("是否自动交易") is False, payload.get("安全边界", {}))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "企业微信股票查询禁用态模拟链路可运行。" if failed == 0 else "企业微信股票查询禁用态模拟链路存在失败项。",
    }
    output_dir = root / "04日志" / "企业微信股票查询禁用态"
    output = output_dir / f"stock-wework-query-dryrun-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest_report = output_dir / "stock-wework-query-dryrun-verify-最新.json"
    write_json(output, report)
    write_json(latest_report, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
