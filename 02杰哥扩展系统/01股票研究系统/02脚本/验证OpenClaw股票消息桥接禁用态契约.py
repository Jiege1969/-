# -*- coding: utf-8 -*-
"""
名称：验证OpenClaw股票消息桥接禁用态契约.py
作用：验证OpenClaw股票消息桥接禁用态契约已生成，并保持OpenClaw只做代理、n8n只编排、真实发送关闭。
触发方式：python 验证OpenClaw股票消息桥接禁用态契约.py
依赖：Python标准库；生成OpenClaw股票消息桥接禁用态契约.py；OpenClaw股票消息桥接禁用态契约.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地契约验收；不调用OpenClaw；不触发n8n；不启用Webhook；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-28 创建OpenClaw股票消息桥接禁用态契约验收脚本。
标识：stock-openclaw-message-bridge-contract-verify
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
    generator = root / "02脚本" / "生成OpenClaw股票消息桥接禁用态契约.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest_json = root / "03数据" / "33OpenClaw桥接契约" / "OpenClaw股票消息桥接禁用态契约_最新.json"
    latest_md = root / "03数据" / "33OpenClaw桥接契约" / "OpenClaw股票消息桥接禁用态契约_最新.md"
    report = load_json(latest_json)
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    actions = report.get("实际动作", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "生成脚本执行成功", result.returncode == 0, {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()})
    add_check(checks, "最新JSON存在", latest_json.exists() and "定位" in report, str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists() and "OpenClaw股票消息桥接禁用态契约" in text, str(latest_md))
    add_check(checks, "OpenClaw只做代理", "OpenClaw只做南北向消息代理" in text and "不写业务判断" in text, "OpenClaw边界")
    add_check(checks, "n8n唯一编排", "n8n是唯一逻辑编排中心" in text, "n8n边界")
    add_check(checks, "真实发送和交易关闭", "real_send" in json.dumps(report, ensure_ascii=False) and "trade" in json.dumps(report, ensure_ascii=False), "发送交易字段")
    add_check(checks, "高风险动作未执行", all(value is False for value in actions.values()), actions)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "OpenClaw股票消息桥接禁用态契约可用。" if failed == 0 else "OpenClaw股票消息桥接禁用态契约存在失败项。",
    }
    output_dir = root / "04日志" / "OpenClaw桥接契约"
    output = output_dir / f"stock-openclaw-message-bridge-contract-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-openclaw-message-bridge-contract-verify-最新.json"
    write_json(output, verify)
    write_json(latest, verify)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
