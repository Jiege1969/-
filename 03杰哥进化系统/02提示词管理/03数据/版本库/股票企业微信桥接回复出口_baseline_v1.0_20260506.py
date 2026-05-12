# -*- coding: utf-8 -*-
"""
名称：股票企业微信桥接入口.py
作用：提供股票系统企业微信灰度桥接本地HTTP入口，承接OpenClaw、n8n或企业微信智能机器人转发的消息并调用股票助手生成回复。
触发方式：python 股票企业微信桥接入口.py
依赖：Python标准库；股票助手本地服务127.0.0.1:19300；企业微信响应URL发送器.py；企业微信本机环境.env。
所属系统：02杰哥扩展系统/01股票研究系统
输出：本地 HTTP 服务 127.0.0.1:19302；企业微信桥接日志；图文报告HTML/PNG/SVG代理响应。
安全边界：仅绑定127.0.0.1:19302；默认dry-run；不保存明文response_url；不写旧系统；不写正式库；不连接券商接口；不自动交易。
创建修改记录：2026-04-29 创建本地桥接入口；吸收旧系统智能机器人stream回复和response_url捕获逻辑；2026-04-30 改为读取新系统企业微信本机环境文件。
标识：stock-wecom-bridge-service
"""

from __future__ import annotations

import hashlib
import html as html_lib
import json
import os
import base64
import re
import struct
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

from Crypto.Cipher import AES


ROOT = Path(__file__).resolve().parents[1]
COMMON_RESPONSE_SENDER = ROOT.parents[0] / "00公共组件" / "02脚本" / "企业微信响应URL发送器.py"
LOCAL_ENV_PATH = ROOT.parents[0] / "00公共组件" / "01配置" / "企业微信本机环境.env"
LOG_DIR = ROOT / "04日志" / "企业微信桥接入口"
HOST = "127.0.0.1"
PORT = 19302
STOCK_ASSISTANT_CARD_URL = "http://127.0.0.1:19300/card/latest.svg"
STOCK_ASSISTANT_CARD_PNG_URL = "http://127.0.0.1:19300/card/latest.png"
STOCK_ASSISTANT_SIGNAL_ICON_URL = "http://127.0.0.1:19300/card/signal-icon.png"
PUBLIC_STOCK_RECO_URL = "http://43.167.210.211/wecom-bot/message?view=stock-reco"
SYSTEM_MANAGER_PROXY_URL = "http://127.0.0.1:19310/wecom/system-manager"
SYSTEM_MANAGER_PRIVATE_CONFIG = ROOT.parents[0] / "00公共组件" / "企业微信接入设置" / "01配置" / "企业微信助手私密配置_本机.json"
ASSISTANT_ROUTE_CONFIG = {
    "/wecom/system-manager": ("杰哥系统管家", "http://127.0.0.1:19310/wecom/system-manager"),
    "/wecom/work-secretary": ("杰哥工作秘书", "http://127.0.0.1:19310/wecom/work-secretary"),
    "/wecom/video-assistant": ("杰哥视频助理", "http://127.0.0.1:19310/wecom/video-assistant"),
    "/wecom/unified": ("杰哥系统管家", "http://127.0.0.1:19310/wecom/unified"),
}
EXPERT_OVERVIEW_JSON = ROOT / "03数据" / "185专家市场总览" / "股票专家市场总览_最新.json"


def load_env_file(path: Path) -> dict[str, str]:
    """只读新系统本机环境文件中的企业微信回调配置，不把密钥写入日志。"""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


ENV_FILE_VALUES = load_env_file(LOCAL_ENV_PATH)


def config_value(*names: str) -> str:
    """优先读进程环境变量，缺省时只读新系统本机环境文件。"""
    for name in names:
        value = os.getenv(name) or ENV_FILE_VALUES.get(name, "")
        if value:
            return value
    return ""


def mask_url(url: str) -> str:
    """只记录response_url指纹，避免长期日志保存真实回调地址。"""
    if not url:
        return ""
    return f"sha256:{hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]}"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_request(handler: BaseHTTPRequestHandler, bot: bool, crypto_config: tuple[str, str, str] | None = None) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or 0)
    body_bytes = handler.rfile.read(length) if length else b"{}"
    body = body_bytes.decode("utf-8", errors="replace")
    query = parse_qs(urlparse(handler.path).query)
    query_args = {key: values[0] for key, values in query.items() if values}
    if body.strip().startswith("<xml"):
        return parse_wecom_xml_body(body, query_args, bot=bot, crypto_config=crypto_config)
    try:
        data = json.loads(body)
        if isinstance(data, dict) and (data.get("encrypt") or data.get("Encrypt")):
            plain = decrypt_wecom_cipher(
                str(data.get("encrypt") or data.get("Encrypt") or ""),
                query_args.get("msg_signature") or str(data.get("msg_signature") or ""),
                query_args.get("timestamp") or str(data.get("timestamp") or ""),
                query_args.get("nonce") or str(data.get("nonce") or ""),
                bot=bot,
                crypto_config=crypto_config,
            )
            parsed = parse_plain_wecom_message(plain)
            parsed["__encrypted_request"] = True
            parsed["__timestamp"] = query_args.get("timestamp") or str(data.get("timestamp") or "")
            parsed["__nonce"] = query_args.get("nonce") or str(data.get("nonce") or "")
            return parsed
        return data if isinstance(data, dict) else {"raw": data}
    except Exception:
        return {"raw": body}


def parse_wecom_xml_body(body: str, query: dict[str, str], bot: bool, crypto_config: tuple[str, str, str] | None = None) -> dict[str, Any]:
    """解析企业微信XML请求，支持外层Encrypt密文。"""
    root = ET.fromstring(body)
    encrypt_node = root.find("Encrypt")
    if encrypt_node is not None and encrypt_node.text:
        plain = decrypt_wecom_cipher(
            encrypt_node.text,
            query.get("msg_signature", ""),
            query.get("timestamp", ""),
            query.get("nonce", ""),
            bot=bot,
            crypto_config=crypto_config,
        )
        data = parse_plain_wecom_message(plain)
        data["__encrypted_request"] = True
        data["__timestamp"] = query.get("timestamp", "")
        data["__nonce"] = query.get("nonce", "")
        data["__xml_request"] = True
        return data
    return {child.tag: child.text or "" for child in list(root)}


def parse_plain_wecom_message(plain: str) -> dict[str, Any]:
    """把企业微信解密后的明文消息转换成统一字典。"""
    text = str(plain or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {"content": data}
    except Exception:
        pass
    if text.startswith("<xml"):
        root = ET.fromstring(text)
        return {child.tag: child.text or "" for child in list(root)}
    return {"content": text}


def wecom_signature(token: str, timestamp: str, nonce: str, cipher_text: str) -> str:
    """按企业微信规则计算SHA1签名。"""
    raw = "".join(sorted([token, timestamp, nonce, cipher_text]))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def pkcs7_unpad(data: bytes) -> bytes:
    """去除企业微信AES-CBC明文末尾的PKCS7填充。"""
    if not data:
        raise ValueError("空明文无法去填充")
    pad = data[-1]
    if pad < 1 or pad > 32:
        raise ValueError("PKCS7填充长度异常")
    return data[:-pad]


def pkcs7_pad(data: bytes, block_size: int = 32) -> bytes:
    """按企业微信规则补齐PKCS7填充。"""
    pad = block_size - (len(data) % block_size)
    if pad == 0:
        pad = block_size
    return data + bytes([pad]) * pad


def wecom_crypto_config(bot: bool) -> tuple[str, str, str]:
    """读取企业微信机器人或应用回调Token/AESKey/接收ID。"""
    if bot:
        token = config_value("WECOM_BOT_CALLBACK_TOKEN", "WECOM_CALLBACK_TOKEN")
        aes_key = config_value("WECOM_BOT_CALLBACK_AES_KEY", "WECOM_CALLBACK_AES_KEY")
        receiver = config_value("WECOM_BOT_ID", "WECOM_CORP_ID")
    else:
        token = config_value("WECOM_CALLBACK_TOKEN")
        aes_key = config_value("WECOM_CALLBACK_AES_KEY")
        receiver = config_value("WECOM_CORP_ID")
    if not token or not aes_key:
        raise ValueError("缺少企业微信回调Token或EncodingAESKey")
    return token, aes_key, receiver


def system_manager_crypto_config() -> tuple[str, str, str]:
    return assistant_crypto_config("杰哥系统管家", "WECOM_SYSTEM_MANAGER")


def assistant_crypto_config(assistant_name: str, env_prefix: str = "") -> tuple[str, str, str]:
    token = config_value(f"{env_prefix}_CALLBACK_TOKEN") if env_prefix else ""
    aes_key = config_value(f"{env_prefix}_CALLBACK_AES_KEY") if env_prefix else ""
    receiver = config_value(f"{env_prefix}_BOT_ID", "WECOM_BOT_ID", "WECOM_CORP_ID") if env_prefix else config_value("WECOM_BOT_ID", "WECOM_CORP_ID")
    if SYSTEM_MANAGER_PRIVATE_CONFIG.exists():
        try:
            data = json.loads(SYSTEM_MANAGER_PRIVATE_CONFIG.read_text(encoding="utf-8-sig", errors="replace"))
            for item in data.get("助手", []):
                if isinstance(item, dict) and item.get("名称") == assistant_name:
                    token = token or str(item.get("Token") or "")
                    aes_key = aes_key or str(item.get("EncodingAESKey") or "")
                    receiver = receiver or str(item.get("BotID") or "")
                    break
        except Exception:
            pass
    if not token or not aes_key:
        raise ValueError(f"缺少{assistant_name}回调Token或EncodingAESKey")
    return token, aes_key, receiver


def decrypt_wecom_cipher(
    cipher_text: str,
    signature: str,
    timestamp: str,
    nonce: str,
    bot: bool,
    crypto_config: tuple[str, str, str] | None = None,
) -> str:
    """校验并解密企业微信回调密文。"""
    token, aes_key, receiver = crypto_config or wecom_crypto_config(bot)
    if not cipher_text or not signature or not timestamp or not nonce:
        raise ValueError("缺少企业微信回调校验参数")
    expected = wecom_signature(token, timestamp, nonce, cipher_text)
    if expected != signature:
        raise ValueError("msg_signature不匹配")
    aes_bytes = base64.b64decode(aes_key + "=")
    if len(aes_bytes) != 32:
        raise ValueError("EncodingAESKey解码后长度不是32字节")
    decryptor = AES.new(aes_bytes, AES.MODE_CBC, aes_bytes[:16])
    plain = pkcs7_unpad(decryptor.decrypt(base64.b64decode(cipher_text)))
    if len(plain) < 20:
        raise ValueError("解密结果过短")
    msg_len = struct.unpack("!I", plain[16:20])[0]
    message = plain[20:20 + msg_len]
    actual_receiver = plain[20 + msg_len:].decode("utf-8", errors="ignore")
    if not bot and receiver and actual_receiver and actual_receiver != receiver:
        raise ValueError("回调接收ID与配置不一致")
    return message.decode("utf-8", errors="ignore")


def encrypt_wecom_reply(
    plain: str,
    timestamp: str,
    nonce: str,
    bot: bool,
    crypto_config: tuple[str, str, str] | None = None,
) -> dict[str, str]:
    """加密企业微信智能机器人同步回复。"""
    token, aes_key, receiver = crypto_config or wecom_crypto_config(bot)
    aes_bytes = base64.b64decode(aes_key + "=")
    if len(aes_bytes) != 32:
        raise ValueError("EncodingAESKey解码后长度不是32字节")
    plain_bytes = plain.encode("utf-8")
    payload = os.urandom(16) + struct.pack("!I", len(plain_bytes)) + plain_bytes + receiver.encode("utf-8")
    encryptor = AES.new(aes_bytes, AES.MODE_CBC, aes_bytes[:16])
    cipher_text = base64.b64encode(encryptor.encrypt(pkcs7_pad(payload))).decode("utf-8")
    signature = wecom_signature(token, timestamp, nonce, cipher_text)
    return {
        "encrypt": cipher_text,
        "msg_signature": signature,
        "timestamp": timestamp,
        "nonce": nonce,
    }


def build_wecom_text_xml_reply(data: dict[str, Any], content: str) -> str:
    """构建企业微信普通应用被动文本回复明文XML。"""
    to_user = str(data.get("FromUserName") or data.get("FromUser") or "").strip()
    from_user = str(data.get("ToUserName") or data.get("ToUser") or "").strip()
    safe_content = str(content or "").replace("]]>", "]]]]><![CDATA[>")
    return "\n".join([
        "<xml>",
        f"<ToUserName><![CDATA[{to_user}]]></ToUserName>",
        f"<FromUserName><![CDATA[{from_user}]]></FromUserName>",
        f"<CreateTime>{int(datetime.now().timestamp())}</CreateTime>",
        "<MsgType><![CDATA[text]]></MsgType>",
        f"<Content><![CDATA[{safe_content}]]></Content>",
        "</xml>",
    ])


def encrypt_wecom_xml_reply(plain_xml: str, timestamp: str, nonce: str, bot: bool) -> str:
    """把普通应用被动回复XML加密成企业微信要求的外层XML。"""
    encrypted = encrypt_wecom_reply(plain_xml, timestamp, nonce, bot=bot)
    return "\n".join([
        "<xml>",
        f"<Encrypt><![CDATA[{encrypted['encrypt']}]]></Encrypt>",
        f"<MsgSignature><![CDATA[{encrypted['msg_signature']}]]></MsgSignature>",
        f"<TimeStamp>{encrypted['timestamp']}</TimeStamp>",
        f"<Nonce><![CDATA[{encrypted['nonce']}]]></Nonce>",
        "</xml>",
    ])


def decrypt_wecom_echo(
    echo: str,
    signature: str,
    timestamp: str,
    nonce: str,
    bot: bool,
    crypto_config: tuple[str, str, str] | None = None,
) -> str:
    """处理企业微信后台URL保存时的echostr解密。"""
    return decrypt_wecom_cipher(echo, signature, timestamp, nonce, bot=bot, crypto_config=crypto_config)


def extract_text(data: dict[str, Any]) -> str:
    for key in ("text", "Text", "Content", "content", "消息", "问题", "query", "message", "question"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    text_obj = data.get("text")
    if isinstance(text_obj, dict):
        for key in ("content", "Content"):
            value = text_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    for key in ("markdown", "stream"):
        value = data.get(key)
        if isinstance(value, dict):
            for sub_key in ("content", "Content"):
                sub_value = value.get(sub_key)
                if isinstance(sub_value, str) and sub_value.strip():
                    return sub_value.strip()
    return ""


def is_recommendation_message(message: str) -> bool:
    """识别推荐/总览类问题，统一走专家总览口径，避免把后台长指标草稿推到手机端。"""
    text = str(message or "").replace(" ", "").strip()
    keywords = (
        "今日推荐",
        "今天推荐",
        "每日推荐",
        "推荐股票",
        "股票推荐",
        "推荐几只股票",
        "推荐一下股票",
        "有什么推荐",
        "请推荐",
        "分析推荐",
        "观察股票",
    )
    return bool(text) and any(keyword in text for keyword in keywords)


def infer_entrance_role(data: dict[str, Any], message: str, robot_stream: bool) -> str:
    """根据显式字段和问题类型判断股票助手入口角色。推荐类问题优先走专家总览。"""
    for key in ("入口角色", "role", "角色", "bot_role", "BotRole"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if is_recommendation_message(message):
        return "专家"
    return "助手" if robot_stream else "专家"


def extract_response_url(data: dict[str, Any]) -> str:
    for key in ("response_url", "ResponseUrl", "responseUrl"):
        value = data.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    return ""


def is_trade_instruction(message: str) -> bool:
    """识别交易/券商/账户执行意图；股票系统只分析，不执行这些动作。"""
    text = str(message or "").strip().lower()
    if not text:
        return False
    patterns = [
        r"买入|买进|卖出|清仓|建仓|加仓|减仓|补仓|满仓|半仓|调仓|换仓",
        r"下单|撤单|挂单|委托|成交|交易|自动交易|程序化交易",
        r"券商|证券账户|资金账户|银证|融资融券|两融",
        r"\bbuy\b|\bsell\b|\border\b|\btrade\b|\bbroker\b",
    ]
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def build_trade_block_result(message: str, data: dict[str, Any], robot_stream: bool) -> dict[str, Any]:
    """交易意图统一拦截，不调用股票助手、不写库、不外发、不触发交易链路。"""
    reply = "已拦截：本系统只提供股票研究分析和风险提示，不执行任何交易指令，不连接券商接口，不自动交易，不下单。"
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "输入消息": message,
        "股票助手状态": "已拦截",
        "回复": reply,
        "企业微信内容": reply,
        "response_url存在": bool(extract_response_url(data)),
        "response_url指纹": mask_url(extract_response_url(data)),
        "真实回传": False,
        "发送器结果": None,
        "实际动作": {
            "调用股票助手": False,
            "尝试response_url回传": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    write_json(LOG_DIR / f"stock-wework-bridge-{stamp}.json", result)
    write_json(LOG_DIR / "stock-wework-bridge-最新.json", result)
    if robot_stream:
        result["智能机器人回复"] = build_stream_reply(reply, data)
    return result


def call_stock_assistant(message: str, remember_context: bool = True, entrance_role: str = "助手") -> dict[str, Any]:
    payload = json.dumps({"问题": message, "不记录上下文": not remember_context, "入口角色": entrance_role}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:19300/analyze",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8", errors="replace")
    return json.loads(body)


def call_response_sender(response_url: str, content: str, real_send: bool) -> dict[str, Any]:
    args = [sys.executable, str(COMMON_RESPONSE_SENDER), "--response-url", response_url, "--content", content]
    if real_send:
        args.append("--real-send")
    completed = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    return {"返回码": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}


def call_system_manager(message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """把系统管家公网路径代理到本机19310；不触发n8n、不发真实企业微信、不交易。"""
    return call_unified_assistant(message, data, SYSTEM_MANAGER_PROXY_URL, "stock-public-bridge-system-manager-proxy")


def call_unified_assistant(message: str, data: dict[str, Any] | None, local_url: str, source: str) -> dict[str, Any]:
    """把通用助手公网路径代理到本机19310；只做本机低风险路由和预演。"""
    payload = {
        "text": str(message or "").strip(),
        "source": source,
    }
    if isinstance(data, dict):
        for key in ("Content", "content", "message", "text", "query", "q"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                payload[key] = value.strip()
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        local_url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=6) as response:
        raw = response.read().decode("utf-8", errors="replace")
    result = json.loads(raw)
    if not isinstance(result, dict):
        return {"状态": "异常", "reply_text": str(result)}
    return result


def extract_stream_id(data: dict[str, Any]) -> str:
    """从企业微信智能机器人或OpenClaw转发包里提取流ID。"""
    stream = data.get("stream")
    if isinstance(stream, dict):
        value = stream.get("id")
        if value:
            return str(value)
    for key in ("stream_id", "msgid", "MsgId", "msg_id", "id"):
        value = data.get(key)
        if value:
            return str(value)
    return f"jiege-stock-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"


def trim_wecom_text(content: str) -> str:
    """企业微信回复长度做保守裁剪，避免单条消息过长导致回调失败。"""
    text = str(content or "").strip()
    return text[:3500] if len(text) > 3500 else text


def trim_wecom_app_text(content: str) -> str:
    """普通企业微信应用被动回复按UTF-8字节保守裁剪，避免中文长文本被平台截断。"""
    text = str(content or "").strip()
    limit = 1800
    if len(text.encode("utf-8")) <= limit:
        return text
    suffix = "\n\n（内容较长，已截取。请先打开上方完整图文报告，或回复“分析 股票名”查看单股详情。）"
    budget = limit - len(suffix.encode("utf-8"))
    kept: list[str] = []
    used = 0
    for line in text.splitlines():
        addition = (line + "\n").encode("utf-8")
        if used + len(addition) > budget:
            break
        kept.append(line)
        used += len(addition)
    if not kept:
        raw = text.encode("utf-8")[:budget]
        return raw.decode("utf-8", errors="ignore").rstrip() + suffix
    return "\n".join(kept).rstrip() + suffix


def strip_markdown_links(content: str) -> str:
    """聊天气泡最终出口：Markdown链接只保留可读文字，不把URL暴露给手机端。"""
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", str(content or ""))
    text = re.sub(r"\[([^\]]+)\]\((?:https?://|/)[^)]+\)", r"\1", text)
    return text


def prepare_wecom_chat_content(content: str, limit: int = 1600) -> str:
    """企业微信聊天气泡统一最终渲染器：短、纯文本、无长URL、答案优先。"""
    text = compact_daily_app_text(content)
    text = strip_markdown_links(text)
    cleaned: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            cleaned.append("")
            continue
        if PUBLIC_STOCK_RECO_URL in line or re.search(r"http://43\.167\.210\.211/wecom-bot/message\?ask=分析", line):
            cleaned.append(line)
            continue
        if re.search(r"https?://|[A-Z]:\\", line):
            continue
        if line.startswith(("图形报告", "图形报告PNG", "详细图文报告", "完整报告：", "本地PNGURL")):
            continue
        cleaned.append(line)
    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) <= limit:
        return text
    cut = text.rfind("\n", 0, limit)
    if cut < 900:
        cut = limit
    return text[:cut].rstrip() + "\n\n（内容较长，已截断。请回复“分析 股票名”查看单股详情。）"


def compact_expert_overview_app_text(text: str) -> str:
    """压缩【杰哥的股票分析专家】市场总览，保证详情入口出现在手机端可见区域。"""
    if "今日摘要：" not in text or "完整图文报告：" not in text:
        return ""
    header_match = re.search(r"【[^】]*股票分析报告[^】]*】", text)
    detail_match = re.search(r"http://43\.167\.210\.211/wecom-bot/message\?view=stock-reco", text)
    overall_match = re.search(r"整体结论：([^\n]+)", text)
    summary_part = text.split("整体结论：", 1)[0].split("今日摘要：", 1)[-1]
    stock_lines = re.findall(r"(?m)^\d+[、.]\s*([^\n]+)", summary_part)
    direction_part = text.split("主要方向：", 1)[1] if "主要方向：" in text else ""
    direction_lines = re.findall(r"(?m)^-\s*([^\n]+)", direction_part)
    observed_part = text.split("观察股票：", 1)[1].split("主要方向：", 1)[0] if "观察股票：" in text and "主要方向：" in text else ""
    observed_lines = re.findall(r"(?m)^\d+[.、]\s*([^\n]+)", observed_part)
    lines = [
        header_match.group(0) if header_match else "【股票分析报告】",
        "",
        "完整图文报告：",
        detail_match.group(0) if detail_match else PUBLIC_STOCK_RECO_URL,
        "",
        "打开后可点股票名称查看单股详细分析。",
        "",
        "专家总览：",
    ]
    if overall_match:
        lines.append(overall_match.group(1).strip())
    lines.extend(["", "重点关注："])
    for index, line in enumerate(stock_lines[:5], start=1):
        cleaned = re.sub(r"\s+", " ", line).strip()
        lines.append(f"{index}. {cleaned}")
    if observed_lines:
        clean_obs = [re.sub(r"\s+", " ", item).strip() for item in observed_lines[:5]]
        lines.extend(["", "观察股票：", "、".join(clean_obs)])
    if direction_lines:
        lines.extend(["", "主要方向：", "、".join(item.strip() for item in direction_lines[:3])])
    lines.extend([
        "",
        "证据边界：未人工核验的信息仍按待核验处理。",
        "说明：本消息为研究摘要，不构成投资建议，不作为买卖指令。",
    ])
    return "\n".join(lines)


def compact_daily_app_text(content: str) -> str:
    """给普通企业微信应用生成较短的每日推荐文本，避免被动回复超长后被平台截断。"""
    text = strip_markdown_links(content)
    expert_text = compact_expert_overview_app_text(text)
    if expert_text:
        return expert_text
    if "今日推荐以下" not in text and "可观察股票" not in text:
        return text

    header_match = re.search(r"【股票分析报告｜行情数据截止[^】]+】", text)
    count_match = re.search(r"今日推荐以下(\d+)只股票", text)
    rec_blocks = re.findall(
        r"(?ms)^\d+\.\s*([^：\n]+)：([^\n]+)\n+【建议策略】：?[ \t]*\n+(?:[ \t]*\n)*([^\n]+)\n+【参考价位】：?[ \t]*\n+(?:[ \t]*\n)*([^\n]+)\n+【主要风险】：?[ \t]*\n+(?:[ \t]*\n)*([^\n]+)",
        text,
    )
    obs_blocks = re.findall(r"(?m)^\d+\.\s*([^：\n]+)：观察等待[^\n]*", text.split("可观察股票：", 1)[1] if "可观察股票：" in text else "")
    if not rec_blocks:
        simple_recs = re.findall(r"(?m)^\d+\.\s*([^：\n]+)：(重点关注|重点推荐|常规推荐)[^\n]*", text.split("可观察股票：", 1)[0])
        simple_obs = re.findall(r"(?m)^\d+\.\s*([^：\n]+)：观察等待[^\n]*", text.split("可观察股票：", 1)[1] if "可观察股票：" in text else "")
        lines = [
            header_match.group(0) if header_match else "【股票分析报告】",
            "",
            f"杰哥，您好！根据系统分析，今日重点关注{len(simple_recs)}只，观察{len(simple_obs)}只：",
            "",
        ]
        if simple_recs:
            lines.append("重点关注：")
            for index, (label, level) in enumerate(simple_recs[:5], start=1):
                lines.append(f"{index}. {label}：{level}")
            lines.append("")
        if simple_obs:
            lines.append("观察股票：")
            lines.append("、".join(label for label in simple_obs[:6]))
            lines.append("")
        lines.extend([
            "口径说明：重点关注=条件达标，优先研究；观察股票=方向值得看但条件不足。",
            "说明：本消息为研究摘要，仅供人工查看，不构成投资建议，不作为买卖指令。",
        ])
        return "\n".join(lines)

    lines = [
        header_match.group(0) if header_match else "【股票分析报告】",
        "",
        f"杰哥，您好！根据系统分析，今日推荐以下{count_match.group(1) if count_match else len(rec_blocks)}只股票供您重点参考：",
        "",
    ]
    for index, (label, level, strategy, ref, risk) in enumerate(rec_blocks[:4], start=1):
        short_strategy = strategy.strip()
        if len(short_strategy) > 52:
            short_strategy = short_strategy[:51] + "…"
        short_ref = ref.strip()
        if len(short_ref) > 58:
            short_ref = short_ref[:57] + "…"
        short_risk = risk.strip()
        if len(short_risk) > 48:
            short_risk = short_risk[:47] + "…"
        lines.extend([
            f"{index}. {label}：{level}",
            "",
            "【建议策略】：",
            "",
            short_strategy,
            "",
            "【参考价位】：",
            "",
            short_ref,
            "",
            "【主要风险】：",
            "",
            short_risk,
            "",
        ])

    if obs_blocks:
        clean_obs = [item.strip() for item in obs_blocks[:5] if item.strip()]
        if clean_obs:
            lines.extend([
                f"观察股票：{'、'.join(clean_obs)}",
                "说明：观察股票方向值得看，但当前条件尚未完全达到推荐标准。",
                "",
            ])

    lines.extend([
        "口径说明：推荐股票=条件达标；观察股票=方向值得看但条件不足。",
        "说明：本消息为研究摘要，仅供人工查看，不构成投资建议，不作为买卖指令。",
    ])
    return "\n".join(lines)


def prepare_wecom_app_content(content: str) -> str:
    """普通企业微信应用专用前台文本：纯文本、短摘要、不暴露Markdown语法。"""
    return trim_wecom_app_text(prepare_wecom_chat_content(content, limit=1800))


def build_stock_report_image_line(stock_result: dict[str, Any]) -> str:
    """从股票助手结果中提取本次绑定PNG图片，恢复企业微信“图片置顶+正文”的展示形态。"""
    card = stock_result.get("图形报告")
    if not isinstance(card, dict):
        return ""
    url = str(card.get("公网PNGURL") or "").strip()
    if not url or "card=report_png" not in url or "name=" not in url:
        return ""
    return f"![股票图形报告]({url})"


def build_stream_reply(content: str, data: dict[str, Any], finish: bool = True) -> dict[str, Any]:
    """构建旧系统验证过的企业微信智能机器人stream同步回复结构。"""
    return {
        "msgtype": "stream",
        "stream": {
            "id": extract_stream_id(data),
            "finish": bool(finish),
            "content": trim_wecom_text(content),
        },
    }


def process_message(data: dict[str, Any], robot_stream: bool = False) -> dict[str, Any]:
    message = extract_text(data)
    response_url = extract_response_url(data)
    real_send = bool(data.get("real_send") is True)
    if not message:
        reply = ""
        result = {"状态": "已忽略", "原因": "空消息或非文本事件", "真实回传": False, "回复": reply}
        if robot_stream:
            result["智能机器人回复"] = build_stream_reply(reply, data)
        return result
    if is_trade_instruction(message):
        return build_trade_block_result(message, data, robot_stream)
    stream_id = extract_stream_id(data)
    remember_context = stream_id != "status-probe"
    entrance_role = infer_entrance_role(data, message, robot_stream)
    stock_result = call_stock_assistant(message, remember_context=remember_context, entrance_role=entrance_role)
    reply = str(stock_result.get("回复") or "").strip()
    wecom_reply = str(stock_result.get("企业微信回复") or reply).strip()
    if not reply:
        reply = json.dumps(stock_result, ensure_ascii=False)[:2000]
    content = wecom_reply
    content = prepare_wecom_chat_content(content)
    image_line = build_stock_report_image_line(stock_result)
    if image_line:
        content = f"{image_line}\n\n{content}".strip()
    sender = None
    if response_url:
        sender = call_response_sender(response_url, content, real_send)
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "输入消息": message,
        "股票助手状态": stock_result.get("状态"),
        "回复": reply,
        "企业微信内容": content,
        "response_url存在": bool(response_url),
        "response_url指纹": mask_url(response_url),
        "真实回传": real_send,
        "发送器结果": sender,
        "实际动作": {
            "调用股票助手": True,
            "尝试response_url回传": bool(response_url and real_send),
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    write_json(LOG_DIR / f"stock-wework-bridge-{stamp}.json", result)
    write_json(LOG_DIR / "stock-wework-bridge-最新.json", result)
    if robot_stream:
        result["智能机器人回复"] = build_stream_reply(content, data)
    return result


def response_json(handler: BaseHTTPRequestHandler, data: dict[str, Any], status: int = 200) -> None:
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def response_text(handler: BaseHTTPRequestHandler, text: str, status: int = 200) -> None:
    body = str(text or "").encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/plain; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def response_xml(handler: BaseHTTPRequestHandler, text: str, status: int = 200) -> None:
    body = str(text or "").encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/xml; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def response_html(handler: BaseHTTPRequestHandler, text: str, status: int = 200) -> None:
    body = str(text or "").encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def markdown_reply_to_html(content: str) -> str:
    text = str(content or "").strip()
    image_pattern = re_image = r"!\[([^\]]*)\]\(([^)]+)\)"
    image_urls: list[tuple[str, str]] = []

    def collect_image(match: Any) -> str:
        image_urls.append((match.group(1), match.group(2)))
        return ""

    import re

    text_without_images = re.sub(image_pattern, collect_image, text)
    escaped = html_lib.escape(text_without_images)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+|/[^)]+)\)",
        lambda m: f'<a href="{html_lib.escape(m.group(2), quote=True)}">{html_lib.escape(m.group(1))}</a>',
        escaped,
    ).replace("\n", "<br>")
    images = []
    for alt, url in image_urls:
        safe_alt = html_lib.escape(alt)
        safe_url = html_lib.escape(url, quote=True)
        images.append(f'<p><img src="{safe_url}" alt="{safe_alt}" style="max-width:100%;border:1px solid #ddd;border-radius:6px;"></p>')
    return "\n".join([
        "<!doctype html>",
        "<html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">",
        "<title>杰哥股票图文报告</title>",
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.65;padding:16px;max-width:900px;margin:auto;color:#1f2937}code{background:#f3f4f6;padding:2px 4px;border-radius:4px}</style>",
        "</head><body>",
        *images,
        f"<div>{escaped}</div>",
        "</body></html>",
    ])


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception:
        return {}


def stock_detail_href(name: str) -> str:
    return f"/wecom-bot/message?ask={quote('分析' + str(name or '').strip())}"


def build_stock_reco_html() -> str:
    """生成手机端图文推荐页，承担企业微信气泡里无法渲染Markdown链接的详情入口。"""
    try:
        call_stock_assistant("专家总览", remember_context=False, entrance_role="专家")
    except Exception:
        pass
    record = read_json(EXPERT_OVERVIEW_JSON)
    recommended = record.get("重点关注名单", []) if isinstance(record.get("重点关注名单"), list) else []
    observed = record.get("可观察股票", []) if isinstance(record.get("可观察股票"), list) else []
    data_date = html_lib.escape(str(record.get("数据日期") or ""))
    market_state = html_lib.escape(str(record.get("市场状态") or "待复核"))
    strong_dirs = record.get("强势方向", []) if isinstance(record.get("强势方向"), list) else []
    evidence_gaps = record.get("证据缺口", []) if isinstance(record.get("证据缺口"), list) else []

    def render_list(title: str, rows: list[dict[str, Any]]) -> str:
        items: list[str] = []
        for item in rows[:12]:
            name = str(item.get("名称") or "").strip()
            code = str(item.get("代码") or "").strip()
            level = str(item.get("等级") or "").strip()
            label = html_lib.escape(f"{name}({code})" if code else name)
            level_text = html_lib.escape(level)
            href = html_lib.escape(stock_detail_href(name), quote=True)
            items.append(f'<li><div><a class="stock" href="{href}">{label}</a><a class="btn" href="{href}">查看详细报告</a></div><span>{level_text}</span></li>')
        if not items:
            items.append("<li><span>暂无</span></li>")
        return f"<section><h2>{html_lib.escape(title)}</h2><ol>{''.join(items)}</ol></section>"

    def render_direction_rows() -> str:
        rows: list[str] = []
        for item in strong_dirs[:5]:
            if not isinstance(item, dict):
                continue
            industry = html_lib.escape(str(item.get("行业") or "-"))
            state = html_lib.escape(str(item.get("景气状态") or "待核验"))
            rows.append(f"<li><span class=\"plain\">{industry}</span><span>{state}</span></li>")
        if not rows:
            rows.append("<li><span class=\"plain\">行业方向待刷新</span><span>待核验</span></li>")
        return "<section><h2>主要方向</h2><ol>" + "".join(rows) + "</ol></section>"

    def render_gap_rows() -> str:
        rows: list[str] = []
        for item in evidence_gaps[:4]:
            if not isinstance(item, dict):
                continue
            gap = html_lib.escape(str(item.get("缺口") or "证据缺口"))
            impact = html_lib.escape(str(item.get("影响股票数") or "-"))
            suggestion = html_lib.escape(str(item.get("建议") or "继续核验"))
            rows.append(f"<li><span class=\"plain\">{gap}：影响{impact}只</span><span>{suggestion}</span></li>")
        if not rows:
            rows.append("<li><span class=\"plain\">公告、行业价格、部分财报证据</span><span>继续核验</span></li>")
        return "<section><h2>证据边界</h2><ol>" + "".join(rows) + "</ol></section>"

    return "\n".join([
        "<!doctype html>",
        "<html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">",
        "<title>股票推荐图文报告</title>",
        "<style>",
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.65;margin:0;color:#172033;background:#f5f7fb}",
        "main{max-width:780px;margin:auto;background:#fff;min-height:100vh;padding:18px 16px 28px}",
        "h1{font-size:22px;margin:0 0 6px}h2{font-size:18px;margin:22px 0 10px;border-left:4px solid #2563eb;padding-left:8px}",
        "p{margin:8px 0;color:#4b5563}.tip{background:#eef6ff;border:1px solid #bfdbfe;border-radius:8px;padding:10px 12px;color:#1e3a8a}",
        "ol{padding-left:0;list-style:none;margin:0}li{display:flex;gap:10px;justify-content:space-between;border-bottom:1px solid #edf0f5;padding:10px 0;align-items:flex-start}",
        "a{color:#075985;text-decoration:none;font-weight:700}.stock{display:block}.btn{display:inline-block;margin-top:6px;background:#e0f2fe;color:#075985;border-radius:6px;padding:3px 8px;font-size:13px}span{color:#4b5563;text-align:right;max-width:42%}.plain{text-align:left;max-width:62%;font-weight:700;color:#172033}.summary{font-size:15px;background:#fafafa;border:1px solid #eee;border-radius:8px;padding:10px 12px}",
        "</style></head><body><main>",
        f"<h1>股票推荐图文报告</h1><p>数据截止：{data_date}</p>",
        f"<p class=\"tip\">今日系统结论：重点关注{len(recommended)}只，观察{len(observed)}只；{market_state}。点击股票名称或“查看详细报告”进入单股图文报告。</p>",
        render_list("重点关注", recommended),
        render_list("观察股票", observed),
        render_direction_rows(),
        "<section><h2>下一步看什么</h2><div class=\"summary\">先看重点关注股是否守住各自风险线；再看成交活跃度是否维持。观察股只有出现转强条件后，才提高研究优先级。</div></section>",
        render_gap_rows(),
        "<p>说明：本页面仅供研究参考，不构成投资建议，不作为买卖指令。</p>",
        "</main></body></html>",
    ])


def response_bytes(handler: BaseHTTPRequestHandler, body: bytes, content_type: str, status: int = 200) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)
        if path in ASSISTANT_ROUTE_CONFIG:
            args = {key: values[0] for key, values in query.items() if values}
            assistant_name, local_url = ASSISTANT_ROUTE_CONFIG[path]
            crypto_config = assistant_crypto_config(assistant_name)
            if args.get("echostr"):
                try:
                    plain = decrypt_wecom_echo(
                        args.get("echostr", ""),
                        args.get("msg_signature", ""),
                        args.get("timestamp", ""),
                        args.get("nonce", ""),
                        bot=True,
                        crypto_config=crypto_config,
                    )
                    response_text(self, plain)
                except Exception as exc:
                    response_text(self, f"校验失败：{exc}", status=403)
                return
            message = (query.get("text") or query.get("message") or query.get("content") or query.get("q") or ["帮助"])[0]
            try:
                response_json(self, call_unified_assistant(message, {"text": message}, local_url, f"stock-public-bridge-{assistant_name}"))
            except Exception as exc:
                response_json(self, {
                    "状态": "失败",
                    "错误": str(exc),
                    "路径": path,
                    "安全边界": {"触发n8n": False, "真实发送企业微信": False, "交易接口": False},
                }, status=503)
            return
        if path in {"/health", "/健康"}:
            response_json(self, {
                "状态": "正常",
                "服务": "股票企业微信桥接入口",
                "端口": PORT,
                "能力": ["本地股票查询", "n8n/OpenClaw桥接", "企业微信智能机器人stream回复", "response_url脱敏捕获"],
                "边界": {"写旧系统": False, "调用券商接口": False, "自动交易": False},
                "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            return
        if path == "/股票推荐图文报告":
            try:
                response_html(self, build_stock_reco_html())
            except Exception as exc:
                response_text(self, f"股票推荐图文报告暂不可用：{exc}", status=503)
            return
        if path == "/wecom-bot/message" and query.get("view", [""])[0] in {"stock-reco", "recommendation", "股票推荐图文报告"}:
            try:
                response_html(self, build_stock_reco_html())
            except Exception as exc:
                response_text(self, f"股票推荐图文报告暂不可用：{exc}", status=503)
            return
        if path in {"/stock-report", "/股票报告"} or (path == "/wecom-bot/message" and (query.get("ask") or query.get("text") or query.get("query"))):
            ask = (query.get("ask") or query.get("text") or query.get("query") or [""])[0]
            try:
                result = call_stock_assistant(ask or "今日分析", remember_context=True, entrance_role="助手")
                report_path = Path(str(result.get("标准报告v2路径") or ""))
                if report_path.exists():
                    content = report_path.read_text(encoding="utf-8-sig", errors="replace")
                else:
                    content = str(result.get("企业微信回复") or result.get("回复") or "")
                response_html(self, markdown_reply_to_html(content))
            except Exception as exc:
                response_text(self, f"股票图文报告暂不可用：{exc}", status=503)
            return
        if path in {"/stock-card/latest.svg", "/stock-card/latest", "/股票图形报告/最新.svg"} or (path == "/wecom-bot/message" and query.get("card", [""])[0] == "latest"):
            try:
                request = urllib.request.Request(STOCK_ASSISTANT_CARD_URL, headers={"User-Agent": "jiege-stock-card-proxy/1.0"})
                with urllib.request.urlopen(request, timeout=6) as response:
                    response_bytes(self, response.read(), "image/svg+xml; charset=utf-8")
            except Exception as exc:
                response_text(self, f"股票图形报告暂不可用：{exc}", status=503)
            return
        if path in {"/stock-card/latest.png", "/股票图形报告/最新.png"} or (path == "/wecom-bot/message" and query.get("card", [""])[0] in {"latest_png", "png", "report_png"}):
            try:
                name = Path(str((query.get("name") or [""])[0])).name
                target_url = STOCK_ASSISTANT_CARD_PNG_URL
                if name and query.get("card", [""])[0] == "report_png":
                    target_url = f"http://127.0.0.1:19300/card/report.png?name={quote(name)}"
                request = urllib.request.Request(target_url, headers={"User-Agent": "jiege-stock-card-png-proxy/1.0"})
                with urllib.request.urlopen(request, timeout=6) as response:
                    response_bytes(self, response.read(), "image/png")
            except Exception as exc:
                response_text(self, f"股票PNG图形报告暂不可用：{exc}", status=503)
            return
        if path in {"/stock-card/signal-icon.png", "/股票图形报告/星级图标.png"} or (path == "/wecom-bot/message" and query.get("card", [""])[0] in {"signal_icon", "star_icon"}):
            try:
                request = urllib.request.Request(STOCK_ASSISTANT_SIGNAL_ICON_URL, headers={"User-Agent": "jiege-stock-signal-icon-proxy/1.0"})
                with urllib.request.urlopen(request, timeout=6) as response:
                    response_bytes(self, response.read(), "image/png")
            except Exception as exc:
                response_text(self, f"股票星级图标暂不可用：{exc}", status=503)
            return
        if path in {"/wecom-bot/message", "/wecom/message"}:
            args = {key: values[0] for key, values in query.items() if values}
            try:
                plain = decrypt_wecom_echo(
                    args.get("echostr", ""),
                    args.get("msg_signature", ""),
                    args.get("timestamp", ""),
                    args.get("nonce", ""),
                    bot=path == "/wecom-bot/message",
                )
                response_text(self, plain)
            except Exception as exc:
                response_text(self, f"校验失败：{exc}", status=403)
            return
        response_json(self, {"状态": "未找到", "路径": path}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path in ASSISTANT_ROUTE_CONFIG:
            try:
                assistant_name, local_url = ASSISTANT_ROUTE_CONFIG[path]
                crypto_config = assistant_crypto_config(assistant_name)
                data = read_request(self, bot=True, crypto_config=crypto_config)
                message = extract_text(data) or "帮助"
                result = call_unified_assistant(message, data, local_url, f"stock-public-bridge-{assistant_name}")
                if data.get("__encrypted_request"):
                    stream_id = extract_stream_id(data)
                    plain_reply = build_stream_reply(str(result.get("reply_text") or result.get("回复") or ""), {"stream": {"id": stream_id}})
                    encrypted = encrypt_wecom_reply(
                        json.dumps(plain_reply, ensure_ascii=False),
                        str(data.get("__timestamp") or int(datetime.now().timestamp())),
                        str(data.get("__nonce") or "jiege"),
                        bot=True,
                        crypto_config=crypto_config,
                    )
                    response_json(self, encrypted)
                    return
                response_json(self, result)
            except Exception as exc:
                response_json(self, {
                    "状态": "失败",
                    "错误": str(exc),
                    "路径": path,
                    "安全边界": {"触发n8n": False, "真实发送企业微信": False, "交易接口": False},
                }, status=503)
            return
        if path not in {"/wecom/stock", "/wecom/message", "/wecom-bot/message", "/企业微信/股票"}:
            response_json(self, {"状态": "未找到", "路径": path}, status=404)
            return
        try:
            robot_stream = path == "/wecom-bot/message"
            data = read_request(self, bot=robot_stream)
            if not extract_text(data):
                # 普通企业微信应用会推送进入应用、菜单、链接预览等非文本事件。
                # 这些事件不应回复“没有收到可分析文本”，否则会造成用户看到多条无意义提示。
                if robot_stream and data.get("__encrypted_request"):
                    encrypted = encrypt_wecom_reply(
                        json.dumps(build_stream_reply("", data), ensure_ascii=False),
                        str(data.get("__timestamp") or int(datetime.now().timestamp())),
                        str(data.get("__nonce") or "jiege"),
                        bot=True,
                    )
                    response_json(self, encrypted)
                    return
                if robot_stream:
                    response_json(self, {"状态": "已忽略", "原因": "空消息或非文本事件", "智能机器人回复": build_stream_reply("", data)})
                    return
                response_text(self, "success")
                return
            result = process_message(data, robot_stream=robot_stream)
            if robot_stream and data.get("__encrypted_request"):
                plain_reply = result.get("智能机器人回复") or build_stream_reply(str(result.get("回复") or ""), data)
                encrypted = encrypt_wecom_reply(
                    json.dumps(plain_reply, ensure_ascii=False),
                    str(data.get("__timestamp") or int(datetime.now().timestamp())),
                    str(data.get("__nonce") or "jiege"),
                    bot=True,
                )
                response_json(self, encrypted)
                return
            if path == "/wecom/message" and data.get("__encrypted_request"):
                content = prepare_wecom_app_content(str(result.get("企业微信内容") or result.get("回复") or ""))
                plain_xml = build_wecom_text_xml_reply(data, content)
                encrypted_xml = encrypt_wecom_xml_reply(
                    plain_xml,
                    str(data.get("__timestamp") or int(datetime.now().timestamp())),
                    str(data.get("__nonce") or "jiege"),
                    bot=False,
                )
                response_xml(self, encrypted_xml)
                return
            response_json(self, result)
        except Exception as exc:
            response_json(self, {"状态": "失败", "错误": str(exc)}, status=500)


def main() -> int:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(json.dumps({"状态": "启动", "地址": f"http://{HOST}:{PORT}", "服务": "股票企业微信桥接入口"}, ensure_ascii=False))
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
