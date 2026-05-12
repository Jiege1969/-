# -*- coding: utf-8 -*-
"""
名称：验证OpenClaw股票桥接沙盒验收包.py
作用：验证OpenClaw股票桥接沙盒验收包已生成，并确认真实OpenClaw、n8n、企业微信发送均未触发。
触发方式：python 验证OpenClaw股票桥接沙盒验收包.py
依赖：Python标准库；生成OpenClaw股票桥接沙盒验收包.py；OpenClaw股票桥接沙盒验收规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地沙盒验收；不调用真实OpenClaw；不调用n8n API；不导入n8n；不启用Webhook；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-28 创建OpenClaw股票桥接沙盒验收包验收脚本。
标识：stock-openclaw-bridge-sandbox-acceptance-package-verify
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
    generator = root / "02脚本" / "生成OpenClaw股票桥接沙盒验收包.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    latest_json = root / "03数据" / "39OpenClaw桥接沙盒验收" / "OpenClaw股票桥接沙盒验收包_最新.json"
    latest_md = root / "03数据" / "39OpenClaw桥接沙盒验收" / "OpenClaw股票桥接沙盒验收包_最新.md"
    report = load_json(latest_json)
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    actions = report.get("实际动作", {})
    n8n_input = report.get("n8n标准输入", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "生成脚本执行成功", result.returncode == 0, {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()})
    add_check(checks, "最新JSON存在", latest_json.exists() and report.get("是否通过沙盒验收") is True, str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists() and "OpenClaw股票桥接沙盒验收包" in text, str(latest_md))
    add_check(checks, "n8n标准输入字段正确", n8n_input.get("gateway") == "openclaw" and n8n_input.get("business") == "stock", n8n_input)
    add_check(checks, "安全字段关闭", n8n_input.get("safety", {}).get("real_send") is False and n8n_input.get("safety", {}).get("trade") is False, n8n_input.get("safety", {}))
    add_check(checks, "沙盒未触发高风险动作", all(value is False for value in actions.values()), actions)
    add_check(checks, "生成回复包", bool(load_json(Path(report.get("统一路由最新", ""))).get("reply_text")) if report.get("统一路由最新") else False, report.get("统一路由最新"))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "OpenClaw股票桥接沙盒验收包可用。" if failed == 0 else "OpenClaw股票桥接沙盒验收包存在失败项。",
    }
    output_dir = root / "04日志" / "OpenClaw桥接沙盒验收"
    output = output_dir / f"stock-openclaw-bridge-sandbox-acceptance-package-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-openclaw-bridge-sandbox-acceptance-package-verify-最新.json"
    write_json(output, verify)
    write_json(latest, verify)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
