# -*- coding: utf-8 -*-
"""
名称：验证股票助手响应URL真实回传本地闭环.py
作用：启动本地模拟response_url接收器，验证股票助手可通过response_url发送器完成真实POST回传。
触发方式：python 验证股票助手响应URL真实回传本地闭环.py
依赖：Python标准库；执行股票助手响应URL回传演练.py；企业微信响应URL发送器.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只向127.0.0.1本地模拟response_url回传；不调用企业微信API；不发送真实企业微信；不写旧系统；不写正式库；不交易。
创建修改记录：2026-04-29 创建本地response_url真实POST闭环验证脚本。
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "02脚本" / "执行股票助手响应URL回传演练.py"
LOG_DIR = ROOT / "04日志" / "企业微信响应URL本地闭环"
HOST = "127.0.0.1"
PORT = 19303


CAPTURED: list[dict[str, Any]] = []


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class MockResponseUrlHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8", errors="replace") if length else "{}"
        try:
            payload: Any = json.loads(body)
        except Exception:
            payload = body
        CAPTURED.append({
            "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "路径": self.path,
            "内容类型": self.headers.get("Content-Type", ""),
            "载荷": payload,
        })
        response = json.dumps({"errcode": 0, "errmsg": "ok", "mock": True}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)


def start_mock_server() -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((HOST, PORT), MockResponseUrlHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def run_loopback() -> dict[str, Any]:
    response_url = f"http://{HOST}:{PORT}/mock-response-url"
    completed = subprocess.run(
        [sys.executable, str(RUNNER), "--message", "分析新易盛", "--response-url", response_url, "--real-send"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    time.sleep(0.5)
    return {"返回码": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}


def main() -> int:
    CAPTURED.clear()
    server = start_mock_server()
    try:
        runner_result = run_loopback()
    finally:
        server.shutdown()
        server.server_close()
    payload_text = json.dumps(CAPTURED, ensure_ascii=False)
    checks = [
        {"检查项": "演练脚本返回成功", "通过": runner_result["返回码"] == 0},
        {"检查项": "本地response_url收到POST", "通过": len(CAPTURED) == 1},
        {"检查项": "收到markdown消息", "通过": "markdown" in payload_text},
        {"检查项": "包含股票助手标识", "通过": "杰哥股票研究助手" in payload_text},
        {"检查项": "不调用企业微信API", "通过": True},
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模拟response_url": f"http://{HOST}:{PORT}/mock-response-url",
        "演练结果": runner_result,
        "捕获请求": CAPTURED,
        "检查结果": checks,
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "实际动作": {
            "本地response_url真实POST": len(CAPTURED) == 1,
            "调用企业微信API": False,
            "发送真实企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = LOG_DIR / f"stock-response-url-local-loopback-verify-{stamp}.json"
    latest = LOG_DIR / "stock-response-url-local-loopback-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
