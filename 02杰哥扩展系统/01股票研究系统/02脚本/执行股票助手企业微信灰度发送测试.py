# -*- coding: utf-8 -*-
"""
名称：执行股票助手企业微信灰度发送测试.py
作用：调用本地股票助手生成研究回复，并通过公共组件企业微信受控发送器进行dry-run或本人白名单真实灰度发送。
触发方式：python 执行股票助手企业微信灰度发送测试.py --message "分析新易盛" [--real-send]
依赖：Python标准库；股票助手本地服务127.0.0.1:19300；企业微信受控发送器.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只允许股票研究回复；真实发送必须显式参数；只发本人白名单；最多5条；不写旧系统；不交易；不群发。
创建修改记录：2026-04-29 创建股票助手企业微信灰度发送测试脚本；2026-04-29 日志文件名加入微秒避免同秒覆盖；2026-04-29 区分尝试发送与发送成功。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMMON_SENDER = ROOT.parents[0] / "00公共组件" / "02脚本" / "企业微信受控发送器.py"
LOG_DIR = ROOT / "04日志" / "企业微信灰度发送测试"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def call_stock_assistant(message: str) -> dict[str, Any]:
    payload = json.dumps({"问题": message}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:19300/analyze",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8", errors="replace")
    return json.loads(body)


def run_sender(content: str, real_send: bool) -> dict[str, Any]:
    args = [sys.executable, str(COMMON_SENDER), "--content", content]
    if real_send:
        args.append("--real-send")
    completed = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    return {"返回码": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", default="分析新易盛")
    parser.add_argument("--real-send", action="store_true")
    args = parser.parse_args()
    stock_result = call_stock_assistant(args.message)
    reply = str(stock_result.get("回复") or stock_result.get("结果", {}).get("回复") or "").strip()
    if not reply:
        reply = json.dumps(stock_result, ensure_ascii=False)[:2000]
    content = f"【杰哥股票研究助手灰度】\n{reply}"
    sender = run_sender(content, args.real_send)
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "输入消息": args.message,
        "真实发送": args.real_send,
        "股票助手状态": stock_result.get("状态"),
        "回复长度": len(reply),
        "发送器结果": sender,
        "实际动作": {
            "调用股票助手": True,
            "尝试发送企业微信": args.real_send,
            "发送企业微信成功": args.real_send and sender.get("返回码") == 0,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    output = LOG_DIR / f"stock-wework-gray-send-test-{stamp}.json"
    latest = LOG_DIR / "stock-wework-gray-send-test-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"ok": sender.get("返回码") == 0, "真实发送成功": result["实际动作"]["发送企业微信成功"], "输出": str(output)}, ensure_ascii=False))
    return 0 if sender.get("返回码") == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
