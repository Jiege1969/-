# -*- coding: utf-8 -*-
"""
名称：验证企业微信股票消息统一路由禁用态.py
作用：验证企业微信股票文字、语音、语音确认学习消息可经统一路由生成禁用态回复包。
触发方式：python 验证企业微信股票消息统一路由禁用态.py
依赖：Python标准库；执行企业微信股票消息统一路由禁用态.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地统一路由验收；不联网；不触发n8n；不调用OpenClaw；不真实发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易；不修改正式语音规则。
创建/修改记录：2026-04-28 创建企业微信股票消息统一路由禁用态验收脚本。
标识：stock-wework-message-router-dryrun-verify
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


def run_case(script: Path, args: list[str]) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    latest = script.parents[1] / "03数据" / "25企业微信统一路由" / "企业微信股票消息统一路由禁用态_最新.json"
    return {"返回码": result.returncode, "标准输出": result.stdout.strip(), "标准错误": result.stderr.strip(), "包": load_json(latest)}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "执行企业微信股票消息统一路由禁用态.py"
    text_case = run_case(script, ["--message-type", "text", "--text", "分析新易盛"])
    voice_case = run_case(script, ["--message-type", "voice", "--text", "帮我看看这个票"])
    confirm_case = run_case(script, ["--message-type", "voice_confirm", "--voice-text", "分析新一生", "--text", "确认：新易盛"])
    latest_md = root / "03数据" / "25企业微信统一路由" / "企业微信股票消息统一路由禁用态_最新.md"
    actions = confirm_case.get("包", {}).get("实际动作", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "统一路由脚本存在", script.exists(), str(script))
    add_check(checks, "文字查询路由通过", text_case["返回码"] == 0 and text_case["包"].get("message_type") == "text" and text_case["包"].get("need_clarification") is False, text_case)
    add_check(checks, "语音低置信度路由追问", voice_case["返回码"] == 0 and voice_case["包"].get("message_type") == "voice" and voice_case["包"].get("need_clarification") is True, voice_case)
    add_check(checks, "语音确认学习路由通过", confirm_case["返回码"] == 0 and confirm_case["包"].get("message_type") == "voice_confirm" and confirm_case["包"].get("need_clarification") is False, confirm_case)
    add_check(checks, "统一输出字段完整", all(key in confirm_case["包"] for key in ["reply_text", "need_clarification", "real_send", "trade"]), confirm_case["包"])
    add_check(checks, "最新Markdown存在", latest_md.exists() and "企业微信股票消息统一路由禁用态" in latest_md.read_text(encoding="utf-8"), str(latest_md))
    add_check(checks, "高风险动作关闭", all(value is False for value in actions.values()) and confirm_case["包"].get("real_send") is False and confirm_case["包"].get("trade") is False, actions)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "企业微信股票消息统一路由禁用态可用。" if failed == 0 else "企业微信股票消息统一路由禁用态存在失败项。",
    }
    output_dir = root / "04日志" / "企业微信统一路由"
    output = output_dir / f"stock-wework-message-router-dryrun-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-wework-message-router-dryrun-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
