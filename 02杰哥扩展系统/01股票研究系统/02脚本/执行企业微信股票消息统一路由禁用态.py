# -*- coding: utf-8 -*-
"""
名称：执行企业微信股票消息统一路由禁用态.py
作用：统一路由企业微信股票文字查询、语音查询和语音确认学习消息，生成禁用态回复包。
触发方式：python 执行企业微信股票消息统一路由禁用态.py --message-type text --text "分析新易盛"
依赖：Python标准库；企业微信股票消息统一路由规则.json；模拟企业微信股票查询.py；生成企业微信语音追问短回复.py；生成企业微信语音确认学习回复.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地禁用态路由并写入03数据/25企业微信统一路由和04日志/企业微信统一路由；不联网；不触发n8n；不调用OpenClaw；不真实发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易；不修改正式语音规则。
创建/修改记录：2026-04-28 创建企业微信股票消息统一路由禁用态脚本。
标识：stock-wework-message-router-dryrun-execute
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_python(script: Path, args: list[str]) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=180)
    return {"返回码": result.returncode, "标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()}


def route_text(root: Path, text: str) -> dict[str, Any]:
    script = root / "02脚本" / "模拟企业微信股票查询.py"
    run = run_python(script, ["--message", text])
    latest = root / "03数据" / "18企业微信股票查询禁用态" / "企业微信股票查询禁用态_最新.json"
    payload = load_json(latest, {})
    result = payload.get("结果", {})
    return {
        "路由类型": "text",
        "运行结果": run,
        "源输出": str(latest),
        "reply_text": result.get("回复", ""),
        "need_clarification": result.get("状态") not in {"完成", "已拦截"},
        "trade_guard": bool(result.get("trade_guard")),
        "data_health": result.get("数据健康度", {}),
    }


def route_voice(root: Path, text: str) -> dict[str, Any]:
    script = root / "02脚本" / "生成企业微信语音追问短回复.py"
    run = run_python(script, ["--text", text])
    latest = root / "03数据" / "24企业微信短回复" / "企业微信语音追问短回复_最新.json"
    payload = load_json(latest, {})
    return {
        "路由类型": "voice",
        "运行结果": run,
        "源输出": str(latest),
        "reply_text": payload.get("回复", ""),
        "need_clarification": bool(payload.get("需要追问")),
        "data_health": {},
    }


def route_voice_confirm(root: Path, text: str, voice_text: str) -> dict[str, Any]:
    script = root / "02脚本" / "生成企业微信语音确认学习回复.py"
    run = run_python(script, ["--voice-text", voice_text, "--confirm-text", text])
    latest = root / "03数据" / "24企业微信短回复" / "企业微信语音确认学习回复_最新.json"
    payload = load_json(latest, {})
    return {
        "路由类型": "voice_confirm",
        "运行结果": run,
        "源输出": str(latest),
        "reply_text": payload.get("回复", ""),
        "need_clarification": False,
        "data_health": {},
    }


def build_markdown(package: dict[str, Any]) -> str:
    return f"""# 企业微信股票消息统一路由禁用态

生成时间：{package['生成时间']}

- 消息类型：{package['message_type']}
- 路由类型：{package['路由结果'].get('路由类型')}
- 是否需要追问：{package['need_clarification']}
- 真实发送：{package['real_send']}
- 交易：{package['trade']}

## 回复草稿

{package['reply_text']}

## 安全边界

- 不真实发送企业微信。
- 不触发n8n。
- 不调用OpenClaw。
- 不写旧系统。
- 不写正式库。
- 不调用券商接口。
- 不自动交易。
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--message-type", choices=["text", "voice", "voice_confirm"], default="text")
    parser.add_argument("--text", default="分析新易盛")
    parser.add_argument("--voice-text", default="")
    parser.add_argument("--sender", default="dry-run-user")
    args = parser.parse_args()
    root = module_root()
    rules = load_json(root / "01配置" / "企业微信股票消息统一路由规则.json", {})
    if args.message_type == "text":
        routed = route_text(root, args.text)
    elif args.message_type == "voice":
        routed = route_voice(root, args.text)
    else:
        routed = route_voice_confirm(root, args.text, args.voice_text or args.text)
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": rules.get("模式", "dry_run_router_only"),
        "sender": args.sender,
        "message_type": args.message_type,
        "text": args.text,
        "voice_text": args.voice_text,
        "路由结果": routed,
        "reply_text": routed.get("reply_text", ""),
        "need_clarification": bool(routed.get("need_clarification")),
        "data_health": routed.get("data_health", {}),
        "real_send": False,
        "trade": False,
        "实际动作": {
            "联网": False,
            "触发n8n": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
            "修改正式语音规则": False,
        },
    }
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = root / "03数据" / "25企业微信统一路由"
    log_dir = root / "04日志" / "企业微信统一路由"
    json_path = output_dir / "企业微信股票消息统一路由禁用态_最新.json"
    latest_json = output_dir / "企业微信股票消息统一路由禁用态_最新.json"
    md_path = output_dir / "企业微信股票消息统一路由禁用态_最新.md"
    latest_md = output_dir / "企业微信股票消息统一路由禁用态_最新.md"
    log_path = log_dir / "stock-wework-message-router-dryrun-execute-最新.json"
    write_json(json_path, package)
    write_json(latest_json, package)
    markdown = build_markdown(package)
    write_text(md_path, markdown)
    write_text(latest_md, markdown)
    write_json(log_path, package)
    print(json.dumps({"消息类型": args.message_type, "需要追问": package["need_clarification"], "输出": str(latest_md)}, ensure_ascii=False))
    return 0 if package["reply_text"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
