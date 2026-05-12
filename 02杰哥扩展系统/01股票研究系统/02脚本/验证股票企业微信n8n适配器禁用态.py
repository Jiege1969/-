# -*- coding: utf-8 -*-
"""
名称：验证股票企业微信n8n适配器禁用态.py
作用：验证n8n契约输入可通过禁用态适配器调用股票企业微信统一路由并生成n8n输出JSON。
触发方式：python 验证股票企业微信n8n适配器禁用态.py
依赖：Python标准库；执行股票企业微信n8n适配器禁用态.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地n8n适配器验收；不导入n8n；不触发n8n；不调用OpenClaw；不真实发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易；不修改正式语音规则。
创建/修改记录：2026-04-28 创建股票企业微信n8n适配器禁用态验收脚本。
标识：stock-wework-n8n-adapter-dryrun-verify
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
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def run_case(script: Path, args: list[str]) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    latest = script.parents[1] / "03数据" / "27n8n适配器禁用态" / "股票企业微信n8n适配器禁用态_最新.json"
    return {"返回码": result.returncode, "标准输出": result.stdout.strip(), "标准错误": result.stderr.strip(), "包": load_json(latest)}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "执行股票企业微信n8n适配器禁用态.py"
    text_case = run_case(script, ["--message-type", "text", "--text", "分析新易盛", "--trace-id", "case-text"])
    voice_case = run_case(script, ["--message-type", "voice", "--text", "帮我看看这个票", "--trace-id", "case-voice"])
    confirm_case = run_case(script, ["--message-type", "voice_confirm", "--voice-text", "分析新一生", "--text", "确认：新易盛", "--trace-id", "case-confirm"])
    latest_md = root / "03数据" / "27n8n适配器禁用态" / "股票企业微信n8n适配器禁用态_最新.md"
    output = confirm_case.get("包", {}).get("n8n输出", {})
    actions = confirm_case.get("包", {}).get("实际动作", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "n8n适配器脚本存在", script.exists(), str(script))
    add_check(checks, "文字输入适配通过", text_case["返回码"] == 0 and text_case["包"].get("n8n输出", {}).get("reply_text"), text_case)
    add_check(checks, "语音追问适配通过", voice_case["返回码"] == 0 and voice_case["包"].get("n8n输出", {}).get("need_clarification") is True, voice_case)
    add_check(checks, "语音确认适配通过", confirm_case["返回码"] == 0 and output.get("need_clarification") is False, confirm_case)
    add_check(checks, "输出字段完整", all(key in output for key in ["trace_id", "reply_text", "need_clarification", "real_send", "trade", "error"]), output)
    add_check(checks, "真实发送和交易关闭", output.get("real_send") is False and output.get("trade") is False, output)
    add_check(checks, "最新Markdown存在", latest_md.exists() and "股票企业微信n8n适配器禁用态" in latest_md.read_text(encoding="utf-8"), str(latest_md))
    add_check(checks, "高风险动作关闭", all(value is False for value in actions.values()), actions)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "股票企业微信n8n适配器禁用态可用。" if failed == 0 else "股票企业微信n8n适配器禁用态存在失败项。",
    }
    output_dir = root / "04日志" / "n8n适配器禁用态"
    output_path = output_dir / "stock-wework-n8n-adapter-dryrun-verify-最新.json"
    write_json(output_path, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output_path)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
