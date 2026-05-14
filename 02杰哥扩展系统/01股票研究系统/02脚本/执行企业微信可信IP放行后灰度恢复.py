# -*- coding: utf-8 -*-
"""
名称：执行企业微信可信IP放行后灰度恢复.py
作用：在企业微信可信IP放行后，按受控规则恢复股票助手本人白名单灰度测试。
触发方式：python 执行企业微信可信IP放行后灰度恢复.py [--real-send]
依赖：Python标准库；生成企业微信可信IP放行状态报告.py；企业微信受控发送器.py；执行股票助手企业微信灰度发送测试.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：默认只探测不真实发送；真实发送必须显式--real-send；只允许本人白名单；最多5条；不写旧系统；不写正式库；不交易。
创建修改记录：2026-04-29 创建可信IP放行后灰度恢复脚本。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = ROOT.parents[0] / "00公共组件"
IP_REPORT = ROOT / "02脚本" / "生成企业微信可信IP放行状态报告.py"
SENDER = COMMON_ROOT / "02脚本" / "企业微信受控发送器.py"
GRAY_SEND = ROOT / "02脚本" / "执行股票助手企业微信灰度发送测试.py"
LOG_DIR = ROOT / "04日志" / "企业微信可信IP放行后灰度恢复"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run(args: list[str], timeout: int = 120) -> dict[str, Any]:
    completed = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {"返回码": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real-send", action="store_true")
    parser.add_argument("--message", default="分析新易盛")
    args = parser.parse_args()
    ip_status = run([sys.executable, str(IP_REPORT)], timeout=60)
    token_probe = run([sys.executable, str(SENDER), "--content", "股票系统可信IP放行后token探测，不真实发送。", "--probe-token", "--egress-mode", "fixed-public"], timeout=120)
    gray_args = [sys.executable, str(GRAY_SEND), "--message", args.message, "--egress-mode", "fixed-public"]
    if args.real_send:
        gray_args.append("--real-send")
    gray_result = run(gray_args, timeout=120)
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "real-send" if args.real_send else "probe-only",
        "输入消息": args.message,
        "可信IP状态报告": ip_status,
        "token探测": token_probe,
        "灰度测试": gray_result,
        "实际动作": {
            "发送真实企业微信": args.real_send and gray_result["返回码"] == 0,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    output = LOG_DIR / f"wework-ip-whitelist-gray-recovery-{stamp}.json"
    latest = LOG_DIR / "wework-ip-whitelist-gray-recovery-最新.json"
    write_json(output, result)
    write_json(latest, result)
    ok = token_probe["返回码"] == 0 and gray_result["返回码"] == 0
    print(json.dumps({"ok": ok, "真实发送": result["实际动作"]["发送真实企业微信"], "输出": str(output)}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
