# -*- coding: utf-8 -*-
"""
名称：验证企业微信股票查询消息契约.py
作用：验证股票企业微信查询消息契约已生成，并确认OpenClaw、n8n、股票助手职责边界和真实动作关闭状态。
触发方式：python 验证企业微信股票查询消息契约.py
依赖：Python标准库；生成企业微信股票查询消息契约.py；企业微信股票查询消息契约.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地契约验收；不连接企业微信；不触发n8n；不调用OpenClaw；不发送消息；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建企业微信股票查询消息契约验收脚本。
标识：stock-wework-message-contract-verify
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
    generator = root / "02脚本" / "生成企业微信股票查询消息契约.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest_json = root / "03数据" / "21企业微信消息契约" / "企业微信股票查询消息契约_最新.json"
    latest_md = root / "03数据" / "21企业微信消息契约" / "企业微信股票查询消息契约_最新.md"
    package = load_json(latest_json)
    contract = package.get("契约", {})
    roles = contract.get("角色边界", {})
    actions = package.get("实际动作", {})
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    checks: list[dict[str, Any]] = []
    add_check(checks, "契约生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "契约生成成功", result.returncode == 0, {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()})
    add_check(checks, "最新JSON契约存在", latest_json.exists() and package.get("模式") == "contract_only", str(latest_json))
    add_check(checks, "最新Markdown契约存在", latest_md.exists() and "企业微信股票查询消息契约" in text, str(latest_md))
    add_check(checks, "OpenClaw只做网关", "只做接收、转发、回传" in roles.get("OpenClaw", ""), roles.get("OpenClaw", ""))
    add_check(checks, "n8n为唯一逻辑编排中心", "唯一逻辑编排中心" in roles.get("n8n", ""), roles.get("n8n", ""))
    add_check(checks, "股票助手只做分析草稿", "分析报告" in roles.get("股票助手", ""), roles.get("股票助手", ""))
    add_check(checks, "语音追问规则存在", any("追问一次" in item for item in contract.get("语音容错规则", [])), contract.get("语音容错规则", []))
    add_check(checks, "真实动作全部关闭", all(value is False for value in actions.values()), actions)
    add_check(checks, "交易字段明确关闭", package.get("样例", {}).get("出站", {}).get("trade") is False, package.get("样例", {}).get("出站", {}))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "股票企业微信查询消息契约已固化，真实链路仍未启用。" if failed == 0 else "股票企业微信查询消息契约存在失败项。",
    }
    output_dir = root / "04日志" / "企业微信消息契约"
    output = output_dir / f"stock-wework-message-contract-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-wework-message-contract-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
