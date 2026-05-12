# -*- coding: utf-8 -*-
"""
名称：验证股票公网回调加密闭环.py
作用：验证企业微信智能机器人公网回调链路，包括GET URL加密校验和POST加密消息回调。
触发方式：python 验证股票公网回调加密闭环.py
依赖：pycryptodome；股票企业微信桥接入口.py；本机桥接127.0.0.1:19302；股票公网入口配置。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只发本地和公网模拟回调；不发送真实企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建修改记录：2026-04-29 创建公网回调加密闭环验收脚本。
"""

from __future__ import annotations

import importlib.util
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_SCRIPT = ROOT / "02脚本" / "股票企业微信桥接入口.py"
LOG_DIR = ROOT / "04日志" / "公网回调验证"
LOCAL_BOT_URL = "http://127.0.0.1:19302/wecom-bot/message"


def load_public_bot_url() -> str:
    """从统一公网入口配置读取智能机器人公网回调地址。"""
    config_path = ROOT / "01配置" / "股票公网入口配置.json"
    if not config_path.exists():
        raise FileNotFoundError(f"缺少股票公网入口配置: {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    base = str(config.get("公网基址") or "").rstrip("/")
    path = str(config.get("智能机器人路径") or "/wecom-bot/message")
    return f"{base}{path}"


def load_bridge_module() -> Any:
    """加载桥接入口模块，复用其中已实现的企业微信加解密函数。"""
    spec = importlib.util.spec_from_file_location("stock_wecom_bridge", BRIDGE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载股票企业微信桥接入口模块")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def http_get(url: str) -> tuple[int, str]:
    """执行GET请求并返回状态码和响应文本。"""
    with urllib.request.urlopen(url, timeout=20) as response:
        return response.status, response.read().decode("utf-8", errors="replace")


def http_post_json(url: str, payload: dict[str, Any]) -> tuple[int, str]:
    """执行JSON POST请求并返回状态码和响应文本。"""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.status, response.read().decode("utf-8", errors="replace")


def build_get_verify_url(bridge: Any, base_url: str, plain_text: str) -> str:
    """构造企业微信后台URL验证GET请求。"""
    timestamp = str(int(time.time()))
    nonce = "jiege-url-verify"
    encrypted = bridge.encrypt_wecom_reply(plain_text, timestamp, nonce, bot=True)
    query = urllib.parse.urlencode(
        {
            "msg_signature": encrypted["msg_signature"],
            "timestamp": encrypted["timestamp"],
            "nonce": encrypted["nonce"],
            "echostr": encrypted["encrypt"],
        }
    )
    return f"{base_url}?{query}"


def build_post_callback(bridge: Any, base_url: str, plain_payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """构造企业微信智能机器人POST加密回调请求。"""
    timestamp = str(int(time.time()))
    nonce = "jiege-post-verify"
    encrypted = bridge.encrypt_wecom_reply(json.dumps(plain_payload, ensure_ascii=False), timestamp, nonce, bot=True)
    query = urllib.parse.urlencode(
        {
            "msg_signature": encrypted["msg_signature"],
            "timestamp": encrypted["timestamp"],
            "nonce": encrypted["nonce"],
        }
    )
    return f"{base_url}?{query}", {"encrypt": encrypted["encrypt"]}


def verify_one_route(bridge: Any, name: str, base_url: str) -> list[dict[str, Any]]:
    """验证单条本地或公网路由。"""
    checks: list[dict[str, Any]] = []

    expected_echo = f"{name}-url-ok"
    get_status, get_body = http_get(build_get_verify_url(bridge, base_url, expected_echo))
    checks.append(
        {
            "检查项": f"{name} GET URL加密校验",
            "状态码": get_status,
            "返回": get_body,
            "通过": get_status == 200 and get_body == expected_echo,
        }
    )

    post_url, post_payload = build_post_callback(
        bridge,
        base_url,
        {"text": "300502", "stream": {"id": f"{name}-encrypted-stream"}},
    )
    post_status, post_body = http_post_json(post_url, post_payload)
    parsed = json.loads(post_body)
    plain_reply = bridge.decrypt_wecom_cipher(
        parsed["encrypt"],
        parsed["msg_signature"],
        parsed["timestamp"],
        parsed["nonce"],
        bot=True,
    )
    checks.append(
        {
            "检查项": f"{name} POST加密回调",
            "状态码": post_status,
            "返回已加密": bool(parsed.get("encrypt")),
            "解密摘要": plain_reply[:300],
            "通过": post_status == 200 and "sz300502" in plain_reply and "stream" in plain_reply,
        }
    )

    return checks


def write_json(path: Path, data: dict[str, Any]) -> None:
    """写入JSON验收日志。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    bridge = load_bridge_module()
    public_bot_url = load_public_bot_url()
    checks = []
    checks.extend(verify_one_route(bridge, "local", LOCAL_BOT_URL))
    checks.extend(verify_one_route(bridge, "public", public_bot_url))

    failed = [item for item in checks if not item["通过"]]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "公网入口": public_bot_url,
        "检查结果": checks,
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "实际动作": {
            "本地GET校验": True,
            "本地POST加密回调": True,
            "公网GET校验": True,
            "公网POST加密回调": True,
            "发送真实企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = LOG_DIR / f"public-callback-encrypted-verify-{stamp}.json"
    latest = LOG_DIR / "public-callback-encrypted-verify-latest.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
