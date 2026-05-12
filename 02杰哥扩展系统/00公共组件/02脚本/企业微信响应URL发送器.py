# -*- coding: utf-8 -*-
"""
名称：企业微信响应URL发送器.py
作用：通过企业微信智能机器人回调中的response_url回传消息，规避应用消息可信IP白名单限制。
触发方式：python 企业微信响应URL发送器.py --response-url <url> --content <内容> [--real-send]
依赖：Python标准库；企业微信智能机器人回调提供的response_url。
所属系统：02杰哥扩展系统/00公共组件
安全边界：默认dry-run；真实发送必须显式参数和有效response_url；不保存response_url明文到长期配置；不写旧系统；不写正式库；不交易。
创建修改记录：2026-04-29 创建response_url回传发送器。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "04日志" / "企业微信响应URL发送器"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def trim_content(content: str) -> str:
    text = str(content or "").strip()
    return text[:3500] if len(text) > 3500 else text


def mask_url(url: str) -> str:
    if not url:
        return ""
    return f"sha256:{hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]}"


def post_json(url: str, data: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read().decode("utf-8", errors="replace")
        status = response.status
    try:
        parsed: Any = json.loads(body)
    except Exception:
        parsed = body[:500]
    return {"状态码": status, "返回": parsed}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--response-url", default="")
    parser.add_argument("--content", default="")
    parser.add_argument("--real-send", action="store_true")
    args = parser.parse_args()
    response_url = args.response_url.strip()
    content = trim_content(args.content)
    checks = [
        {"检查项": "response_url格式", "通过": response_url.startswith(("http://", "https://"))},
        {"检查项": "内容非空", "通过": bool(content)},
    ]
    allowed = all(item["通过"] for item in checks)
    result: dict[str, Any] = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "real-send" if args.real_send else "dry-run",
        "response_url指纹": mask_url(response_url),
        "内容长度": len(content),
        "检查结果": checks,
        "是否允许发送": allowed,
        "实际动作": {
            "尝试response_url回传": False,
            "response_url回传成功": False,
            "输出response_url明文": False,
            "写旧系统": False,
            "写正式库": False,
            "自动交易": False,
        },
    }
    if allowed and args.real_send:
        payload = {"msgtype": "markdown", "markdown": {"content": content}}
        response = post_json(response_url, payload)
        result["实际动作"]["尝试response_url回传"] = True
        result["实际动作"]["response_url回传成功"] = int(response.get("状态码", 500)) < 400
        result["回传结果"] = response
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    output = LOG_DIR / f"wework-response-url-sender-{stamp}.json"
    latest = LOG_DIR / "wework-response-url-sender-最新.json"
    write_json(output, result)
    write_json(latest, result)
    success = allowed and (not args.real_send or result["实际动作"]["response_url回传成功"])
    print(json.dumps({"ok": success, "real_send_success": result["实际动作"]["response_url回传成功"], "输出": str(output)}, ensure_ascii=False))
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
