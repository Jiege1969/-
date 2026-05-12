# -*- coding: utf-8 -*-
"""
名称：验证企业微信股票查询灰度启用闸口.py
作用：验证股票研究系统企业微信查询灰度启用许可令已生成，且真实发送、n8n触发、服务重启和交易接口仍关闭。
触发方式：python 验证企业微信股票查询灰度启用闸口.py
依赖：Python标准库；生成企业微信股票查询灰度启用许可令.py；企业微信股票查询灰度启用规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地验收；不真实发送企业微信；不触发n8n；不启动或重启服务；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建企业微信股票查询灰度启用闸口验收脚本。
标识：stock-wework-query-gray-gate-verify
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
    generator = root / "02脚本" / "生成企业微信股票查询灰度启用许可令.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest_json = root / "03数据" / "19企业微信灰度启用" / "企业微信股票查询灰度启用许可令_最新.json"
    latest_md = root / "03数据" / "19企业微信灰度启用" / "企业微信股票查询灰度启用许可令_最新.md"
    payload = load_json(latest_json)
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    actions = payload.get("实际动作", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "许可令生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "许可令生成成功", result.returncode == 0, {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()})
    add_check(checks, "最新JSON许可令存在", latest_json.exists() and payload.get("模式") == "gray_gate_only", str(latest_json))
    add_check(checks, "最新Markdown许可令存在", latest_md.exists() and "企业微信股票查询灰度启用许可令" in text, str(latest_md))
    add_check(checks, "真实发送仍关闭", actions.get("真实发送企业微信") is False, actions)
    add_check(checks, "n8n正式触发仍关闭", actions.get("触发n8n正式工作流") is False, actions)
    add_check(checks, "服务启动重启仍关闭", actions.get("启动或重启服务") is False, actions)
    add_check(checks, "旧系统写入仍关闭", actions.get("写旧系统") is False, actions)
    add_check(checks, "正式库写入仍关闭", actions.get("写正式业务库") is False, actions)
    add_check(checks, "交易能力仍关闭", actions.get("调用券商接口") is False and actions.get("自动交易") is False, actions)
    add_check(checks, "人工确认边界已写入", "必须人工确认后才可执行" in text and "OpenClaw只做消息网关" in text, text[:300])
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "企业微信股票查询灰度启用闸口已固化，真实链路仍未启用。" if failed == 0 else "企业微信股票查询灰度启用闸口存在失败项。",
    }
    output_dir = root / "04日志" / "企业微信灰度启用"
    output = output_dir / f"stock-wework-query-gray-gate-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest_report = output_dir / "stock-wework-query-gray-gate-verify-最新.json"
    write_json(output, report)
    write_json(latest_report, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
