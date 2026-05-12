# -*- coding: utf-8 -*-
"""
名称：执行股票企业微信n8n适配器禁用态.py
作用：把n8n契约输入转换为股票企业微信统一路由调用，并生成n8n可读取的禁用态输出JSON。
触发方式：python 执行股票企业微信n8n适配器禁用态.py --message-type text --text "分析新易盛"
依赖：Python标准库；股票企业微信n8n适配器禁用态规则.json；执行企业微信股票消息统一路由禁用态.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地n8n适配器禁用态并写入03数据/27n8n适配器禁用态和04日志/n8n适配器禁用态；不导入n8n；不触发n8n；不调用OpenClaw；不真实发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易；不修改正式语音规则。
创建/修改记录：2026-04-28 创建股票企业微信n8n适配器禁用态脚本。
标识：stock-wework-n8n-adapter-dryrun-execute
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
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, path)


def parse_contract_input(args: argparse.Namespace) -> dict[str, Any]:
    if args.input_json:
        data = load_json(Path(args.input_json), {})
    else:
        data = {}
    return {
        "trace_id": data.get("trace_id") or args.trace_id,
        "message_type": data.get("message_type") or args.message_type,
        "text": data.get("text") or args.text,
        "voice_text": data.get("voice_text") or args.voice_text,
        "sender_hash": data.get("sender_hash") or args.sender_hash,
        "created_at": data.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dry_run": True,
    }


def call_router(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    router = root / "02脚本" / "执行企业微信股票消息统一路由禁用态.py"
    message_type = payload.get("message_type", "text")
    command = [sys.executable, str(router), "--message-type", message_type, "--text", payload.get("text", "")]
    if message_type == "voice_confirm":
        command.extend(["--voice-text", payload.get("voice_text", "")])
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    latest = root / "03数据" / "25企业微信统一路由" / "企业微信股票消息统一路由禁用态_最新.json"
    routed = load_json(latest, {})
    return {
        "返回码": result.returncode,
        "标准输出": result.stdout.strip(),
        "标准错误": result.stderr.strip(),
        "路由包": routed,
        "路由包路径": str(latest),
    }


def build_adapter_output(payload: dict[str, Any], router_result: dict[str, Any]) -> dict[str, Any]:
    routed = router_result.get("路由包", {})
    error = ""
    if router_result.get("返回码") != 0:
        error = router_result.get("标准错误") or router_result.get("标准输出") or "统一路由返回非0"
    return {
        "trace_id": payload.get("trace_id"),
        "reply_text": routed.get("reply_text", ""),
        "need_clarification": bool(routed.get("need_clarification")),
        "data_health": routed.get("data_health", {}),
        "real_send": False,
        "trade": False,
        "source_output": router_result.get("路由包路径", ""),
        "error": error,
    }


def build_markdown(package: dict[str, Any]) -> str:
    output = package["n8n输出"]
    return f"""# 股票企业微信n8n适配器禁用态

生成时间：{package['生成时间']}

- trace_id：{output.get('trace_id')}
- need_clarification：{output.get('need_clarification')}
- real_send：{output.get('real_send')}
- trade：{output.get('trade')}
- error：{output.get('error')}

## reply_text

{output.get('reply_text')}

## 安全边界

- 未导入n8n。
- 未触发n8n。
- 未调用OpenClaw。
- 未真实发送企业微信。
- 未写旧系统和正式库。
- 未调用券商接口或自动交易。
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", default="")
    parser.add_argument("--trace-id", default="stock-n8n-adapter-demo")
    parser.add_argument("--message-type", choices=["text", "voice", "voice_confirm"], default="text")
    parser.add_argument("--text", default="分析新易盛")
    parser.add_argument("--voice-text", default="")
    parser.add_argument("--sender-hash", default="local-user")
    args = parser.parse_args()
    root = module_root()
    rules = load_json(root / "01配置" / "股票企业微信n8n适配器禁用态规则.json", {})
    payload = parse_contract_input(args)
    router_result = call_router(root, payload)
    adapter_output = build_adapter_output(payload, router_result)
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": rules.get("模式", "n8n_adapter_dry_run_only"),
        "n8n输入": payload,
        "统一路由调用": router_result,
        "n8n输出": adapter_output,
        "实际动作": {
            "导入n8n": False,
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
    output_dir = root / "03数据" / "27n8n适配器禁用态"
    log_dir = root / "04日志" / "n8n适配器禁用态"
    json_path = output_dir / "股票企业微信n8n适配器禁用态_最新.json"
    latest_json = output_dir / "股票企业微信n8n适配器禁用态_最新.json"
    md_path = output_dir / "股票企业微信n8n适配器禁用态_最新.md"
    latest_md = output_dir / "股票企业微信n8n适配器禁用态_最新.md"
    log_path = log_dir / "stock-wework-n8n-adapter-dryrun-execute-最新.json"
    write_json(json_path, package)
    write_json(latest_json, package)
    write_text(md_path, build_markdown(package))
    write_text(latest_md, build_markdown(package))
    write_json(log_path, package)
    print(json.dumps({"消息类型": payload["message_type"], "输出": str(latest_md), "error": adapter_output["error"]}, ensure_ascii=False))
    return 0 if adapter_output["reply_text"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
