# -*- coding: utf-8 -*-
"""
名称：企业微信受控发送器.py
作用：为统一消息出口提供企业微信应用消息的受控灰度发送能力，默认只演练，真实发送必须显式启用。
触发方式：python 企业微信受控发送器.py --to <用户ID> --content <内容> [--real-send]
依赖：Python标准库；企业微信受控发送配置.json；企业微信本机环境.env或进程环境变量。
所属系统：02杰哥扩展系统/00公共组件
安全边界：只允许白名单本人；最多5条首轮灰度；不群发；不外部客户；不输出密钥值；不写旧系统；不写正式库；不触发交易。
创建修改记录：2026-04-29 创建受控发送器；2026-04-29 日志文件名加入微秒避免同秒覆盖；2026-04-29 区分尝试发送与发送成功；2026-04-30 改为读取新系统本机环境文件；2026-05-01 增加企业微信目标应用档案，可切换到杰哥助手；2026-05-01 支持text/markdown消息类型。
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "01配置" / "企业微信受控发送配置.json"
APP_PROFILE_CONFIG = ROOT / "01配置" / "企业微信应用目标档案.json"
DEFAULT_CONFIRMATION_FILE = ROOT / "01配置" / "企业微信真实发送人工确认令.json"
LOG_DIR = ROOT / "04日志" / "企业微信受控发送器"
COUNTER_DIR = ROOT / "03数据" / "04企业微信灰度发送计数"
SYSTEM_ROOT = ROOT.parents[1]
DEFAULT_FIXED_PUBLIC_EGRESS = {
    "模式": "fixed-public",
    "公网IP": "43.167.210.211",
    "SSH用户": "ubuntu",
    "SSH主机": "43.167.210.211",
    "SSH密钥": str(SYSTEM_ROOT / "01杰哥智能系统" / "01配置" / "云服务器密钥" / "jiege_agent_relay_ed25519"),
}


REMOTE_WECOM_SEND_CODE = r"""
import json
import sys
import urllib.parse
import urllib.request


def emit(data):
    print(json.dumps(data, ensure_ascii=False))


def post_json(url, data, timeout=15):
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
    return json.loads(body)


def get_token(corp_id, secret):
    query = urllib.parse.urlencode({"corpid": corp_id, "corpsecret": secret})
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?{query}"
    with urllib.request.urlopen(url, timeout=15) as response:
        body = response.read().decode("utf-8", errors="replace")
    data = json.loads(body)
    return {"ok": data.get("errcode") == 0, "access_token": data.get("access_token", ""), "raw": data}


def send_message(token, agent_id, to_user, content, msgtype):
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={urllib.parse.quote(token)}"
    if msgtype == "markdown":
        payload = {
            "touser": to_user,
            "msgtype": "markdown",
            "agentid": int(agent_id),
            "markdown": {"content": str(content or "").strip()[:3500]},
            "safe": 0,
        }
    else:
        payload = {
            "touser": to_user,
            "msgtype": "text",
            "agentid": int(agent_id),
            "text": {"content": str(content or "").strip()[:3500]},
            "safe": 0,
        }
    data = post_json(url, payload, timeout=15)
    return {"ok": data.get("errcode") == 0, "raw": data}


def sanitize(data):
    safe = dict(data or {})
    if "access_token" in safe:
        safe["access_token"] = "***hidden***"
    return safe


def current_ip():
    with urllib.request.urlopen("https://api.ipify.org", timeout=8) as response:
        return response.read().decode("utf-8", errors="replace").strip()


payload = json.load(sys.stdin)
result = {
    "ok": False,
    "出口IP": "",
    "token探测": {"ok": False, "企业微信返回": {}},
    "发送结果": None,
}
try:
    result["出口IP"] = current_ip()
except Exception as exc:
    result["出口IP探测错误"] = f"{type(exc).__name__}: {exc}"

try:
    token_data = get_token(payload["corp_id"], payload["secret"])
    result["token探测"] = {"ok": token_data["ok"], "企业微信返回": sanitize(token_data["raw"])}
except Exception as exc:
    result["token探测"] = {
        "ok": False,
        "企业微信返回": {"errcode": -1, "errmsg": f"gettoken_exception:{type(exc).__name__}: {exc}"},
    }
    emit(result)
    raise SystemExit(0)

if not payload.get("real_send"):
    result["ok"] = bool(result["token探测"]["ok"])
    emit(result)
    raise SystemExit(0)

if not token_data["ok"]:
    emit(result)
    raise SystemExit(0)

try:
    send_data = send_message(
        token_data["access_token"],
        payload["agent_id"],
        payload["to_user"],
        payload["content"],
        payload.get("msgtype") or "text",
    )
    result["发送结果"] = {"ok": send_data["ok"], "企业微信返回": sanitize(send_data["raw"])}
    result["ok"] = bool(send_data["ok"])
except Exception as exc:
    result["发送结果"] = {
        "ok": False,
        "企业微信返回": {"errcode": -1, "errmsg": f"send_exception:{type(exc).__name__}: {exc}"},
    }
emit(result)
"""


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_env(path_text: str) -> dict[str, str]:
    path = Path(path_text)
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def read_secret(config: dict[str, Any], key: str) -> str:
    env_value = os.environ.get(key, "").strip()
    if env_value:
        return env_value
    local_env = parse_env(str(config.get("本机环境文件", "")))
    return local_env.get(key, "").strip()


def is_filled(value: str) -> bool:
    text = str(value or "").strip()
    return bool(text and text not in {"待填写", "请填写", "TODO", "todo", "未配置"})


def resolve_app_profile(requested_profile: str = "") -> dict[str, Any]:
    profiles = load_json(APP_PROFILE_CONFIG, {})
    profile_map = profiles.get("应用档案", {}) if isinstance(profiles, dict) else {}
    profile_name = requested_profile.strip() or str(profiles.get("当前启用应用", "")).strip()
    if not profile_name:
        profile_name = "默认应用"
    profile = profile_map.get(profile_name)
    if not profile:
        profile = {
            "说明": "兼容旧配置的默认应用。",
            "企业ID变量": "WECOM_CORP_ID",
            "应用ID变量": "WECOM_AGENT_ID",
            "应用密钥变量": "WECOM_APP_SECRET",
            "状态": "兼容旧配置",
        }
    return {
        "名称": profile_name,
        "配置文件存在": APP_PROFILE_CONFIG.exists(),
        "档案存在": profile_name in profile_map,
        "企业ID变量": profile.get("企业ID变量", "WECOM_CORP_ID"),
        "应用ID变量": profile.get("应用ID变量", "WECOM_AGENT_ID"),
        "应用密钥变量": profile.get("应用密钥变量", "WECOM_APP_SECRET"),
        "状态": profile.get("状态", ""),
        "说明": profile.get("说明", ""),
    }


def today_counter_path() -> Path:
    return COUNTER_DIR / f"企业微信灰度发送计数_{datetime.now().strftime('%Y%m%d')}.json"


def read_counter() -> dict[str, Any]:
    return load_json(today_counter_path(), {"日期": datetime.now().strftime("%Y-%m-%d"), "已真实发送": 0, "记录": []})


def update_counter(record: dict[str, Any]) -> None:
    counter = read_counter()
    counter["已真实发送"] = int(counter.get("已真实发送", 0)) + 1
    counter.setdefault("记录", []).append(record)
    write_json(today_counter_path(), counter)


def trim_content(content: str) -> str:
    text = str(content or "").strip()
    return text[:3500] if len(text) > 3500 else text


def post_json(url: str, data: dict[str, Any], timeout: int = 15) -> dict[str, Any]:
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
    return json.loads(body)


def get_token(corp_id: str, secret: str) -> dict[str, Any]:
    query = urllib.parse.urlencode({"corpid": corp_id, "corpsecret": secret})
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?{query}"
    with urllib.request.urlopen(url, timeout=15) as response:
        body = response.read().decode("utf-8", errors="replace")
    data = json.loads(body)
    return {"ok": data.get("errcode") == 0, "access_token": data.get("access_token", ""), "raw": data}


def send_message(token: str, agent_id: str, to_user: str, content: str, msgtype: str = "text") -> dict[str, Any]:
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={urllib.parse.quote(token)}"
    if msgtype == "markdown":
        payload = {
            "touser": to_user,
            "msgtype": "markdown",
            "agentid": int(agent_id),
            "markdown": {"content": trim_content(content)},
            "safe": 0,
        }
    else:
        payload = {
            "touser": to_user,
            "msgtype": "text",
            "agentid": int(agent_id),
            "text": {"content": trim_content(content)},
            "safe": 0,
        }
    data = post_json(url, payload, timeout=15)
    return {"ok": data.get("errcode") == 0, "raw": data}


def fixed_public_egress_config(config: dict[str, Any]) -> dict[str, Any]:
    configured = config.get("固定公网出口", {}) if isinstance(config, dict) else {}
    merged = dict(DEFAULT_FIXED_PUBLIC_EGRESS)
    if isinstance(configured, dict):
        for key in ["公网IP", "SSH用户", "SSH主机", "SSH密钥"]:
            if str(configured.get(key, "")).strip():
                merged[key] = str(configured[key]).strip()
    return merged


def send_message_via_fixed_public_egress(
    egress: dict[str, Any],
    corp_id: str,
    secret: str,
    agent_id: str,
    to_user: str,
    content: str,
    msgtype: str,
    real_send: bool,
) -> dict[str, Any]:
    key_path = Path(str(egress.get("SSH密钥", "")))
    host = str(egress.get("SSH主机") or egress.get("公网IP") or "").strip()
    user = str(egress.get("SSH用户") or "ubuntu").strip()
    if not key_path.exists():
        return {
            "ok": False,
            "出口IP": "",
            "token探测": {"ok": False, "企业微信返回": {"errcode": -1, "errmsg": f"ssh_key_missing:{key_path}"}},
            "发送结果": None,
        }
    payload = {
        "corp_id": corp_id,
        "secret": secret,
        "agent_id": agent_id,
        "to_user": to_user,
        "content": content,
        "msgtype": msgtype,
        "real_send": real_send,
    }
    remote_command = "python3 -c " + shlex.quote(REMOTE_WECOM_SEND_CODE)
    command = [
        "ssh",
        "-i",
        str(key_path),
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        "-o",
        "StrictHostKeyChecking=accept-new",
        f"{user}@{host}",
        remote_command,
    ]
    completed = subprocess.run(
        command,
        input=json.dumps(payload, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=75,
    )
    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    if completed.returncode != 0:
        return {
            "ok": False,
            "出口IP": "",
            "token探测": {"ok": False, "企业微信返回": {"errcode": -1, "errmsg": f"ssh_failed:{completed.returncode}:{stderr[-500:]}"}},
            "发送结果": None,
        }
    try:
        data = json.loads(stdout.splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return {
            "ok": False,
            "出口IP": "",
            "token探测": {"ok": False, "企业微信返回": {"errcode": -1, "errmsg": "remote_json_parse_failed"}},
            "发送结果": {"ok": False, "企业微信返回": {"errcode": -1, "errmsg": stdout[-500:]}},
        }
    return data if isinstance(data, dict) else {"ok": False, "出口IP": "", "token探测": {}, "发送结果": None}


def sanitize_wework(data: dict[str, Any]) -> dict[str, Any]:
    safe = dict(data)
    if "access_token" in safe:
        safe["access_token"] = "***hidden***"
    return safe


def validate_real_send_confirmation(path: Path, target: str, msgtype: str) -> dict[str, Any]:
    """真实发送必须有当日人工确认令；缺失或范围不匹配时在本地阻断。"""
    data = load_json(path, {})
    today = datetime.now().strftime("%Y-%m-%d")
    allowed_targets = data.get("允许接收人", [])
    if isinstance(allowed_targets, str):
        allowed_targets = [allowed_targets]
    allowed_msgtypes = data.get("允许消息类型", [])
    if isinstance(allowed_msgtypes, str):
        allowed_msgtypes = [allowed_msgtypes]
    expected_token = f"ALLOW_WECOM_REAL_SEND_{datetime.now().strftime('%Y%m%d')}"
    checks = [
        {"检查项": "确认令文件存在", "通过": path.exists()},
        {"检查项": "确认状态为已人工确认", "通过": data.get("确认状态") == "已人工确认"},
        {"检查项": "允许真实发送", "通过": data.get("允许真实发送") is True},
        {"检查项": "有效日期为今天", "通过": data.get("有效日期") == today},
        {"检查项": "确认令匹配当天", "通过": data.get("确认令") == expected_token},
        {"检查项": "目标接收人在确认范围", "通过": bool(target and target in allowed_targets)},
        {"检查项": "消息类型在确认范围", "通过": bool(msgtype and msgtype in allowed_msgtypes)},
        {"检查项": "确认令禁止n8n", "通过": data.get("允许n8n") is False},
        {"检查项": "确认令禁止自动交易", "通过": data.get("允许自动交易") is False},
    ]
    return {
        "路径": str(path),
        "有效": all(item["通过"] for item in checks),
        "检查结果": checks,
        "确认范围摘要": {
            "允许接收人": allowed_targets,
            "允许消息类型": allowed_msgtypes,
            "有效日期": data.get("有效日期", ""),
            "允许n8n": data.get("允许n8n"),
            "允许自动交易": data.get("允许自动交易"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", default="")
    parser.add_argument("--content", default="")
    parser.add_argument("--real-send", action="store_true")
    parser.add_argument("--probe-token", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--app-profile", default="", help="企业微信目标应用档案名称，如：n8n指令通行证、杰哥助手")
    parser.add_argument("--msgtype", default="text", choices=["text", "markdown"], help="企业微信应用消息类型")
    parser.add_argument("--confirmation-file", default="", help="真实发送人工确认令文件；未指定时读取公共配置目录默认确认令")
    parser.add_argument("--egress-mode", default="", choices=["", "local", "fixed-public"], help="发送出口模式；默认本机出口，股票真实推送可使用fixed-public固定公网出口")
    parser.add_argument("--fixed-public-egress", action="store_true", help="等同于--egress-mode fixed-public")
    args = parser.parse_args()

    config = load_json(CONFIG, {})
    egress_mode = "fixed-public" if args.fixed_public_egress else (args.egress_mode or "local")
    fixed_egress = fixed_public_egress_config(config)
    send = config.get("真实发送", {})
    whitelist = config.get("白名单", {}).get("接收人ID列表", [])
    target = args.to.strip() or (whitelist[0] if whitelist else "")
    max_count = int(send.get("首轮灰度最大消息数", 5))
    app_profile = resolve_app_profile(args.app_profile)
    corp_id = read_secret(config, app_profile["企业ID变量"])
    agent_id = read_secret(config, app_profile["应用ID变量"])
    secret = read_secret(config, app_profile["应用密钥变量"])
    confirmation_path = Path(args.confirmation_file) if args.confirmation_file else DEFAULT_CONFIRMATION_FILE
    confirmation_data = load_json(confirmation_path, {})
    try:
        confirmation_max_count = int(confirmation_data.get("每日最大消息数", 0))
        if confirmation_max_count > 0:
            max_count = confirmation_max_count
    except (TypeError, ValueError):
        pass
    counter = read_counter()
    current_count = int(counter.get("已真实发送", 0))
    confirmation = validate_real_send_confirmation(confirmation_path, target, args.msgtype)
    checks = [
        {"检查项": "配置存在", "通过": CONFIG.exists()},
        {"检查项": "目标应用档案存在", "通过": app_profile["档案存在"] or app_profile["名称"] == "默认应用"},
        {"检查项": "真实发送配置启用", "通过": send.get("是否启用") is True},
        {"检查项": "白名单只有本人", "通过": len(whitelist) == 1},
        {"检查项": "目标在白名单", "通过": bool(target and target in whitelist)},
        {"检查项": "首轮发送未超上限", "通过": current_count < max_count},
        {"检查项": "企业微信凭据存在", "通过": is_filled(corp_id) and is_filled(agent_id) and is_filled(secret)},
        {"检查项": "禁止群发", "通过": send.get("允许群发") is False and "|" not in target and "," not in target and "@" not in target},
        {"检查项": "真实发送人工确认令有效", "通过": (not args.real_send) or confirmation["有效"]},
        {"检查项": "固定公网出口配置可用", "通过": egress_mode != "fixed-public" or (Path(str(fixed_egress.get("SSH密钥", ""))).exists() and is_filled(str(fixed_egress.get("SSH主机") or fixed_egress.get("公网IP") or "")))},
    ]
    allowed = all(item["通过"] for item in checks)
    result: dict[str, Any] = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "real-send" if args.real_send else "dry-run",
        "消息类型": args.msgtype,
        "目标应用档案": {
            "名称": app_profile["名称"],
            "状态": app_profile["状态"],
            "企业ID变量": app_profile["企业ID变量"],
            "应用ID变量": app_profile["应用ID变量"],
            "应用密钥变量": app_profile["应用密钥变量"],
            "说明": app_profile["说明"],
        },
        "目标用户": target if target else "",
        "发送出口模式": egress_mode,
        "固定公网出口": {
            "启用": egress_mode == "fixed-public",
            "公网IP": fixed_egress.get("公网IP", ""),
            "SSH主机": fixed_egress.get("SSH主机", ""),
            "SSH用户": fixed_egress.get("SSH用户", ""),
            "SSH密钥存在": Path(str(fixed_egress.get("SSH密钥", ""))).exists(),
            "说明": "固定出口只在本次进程内通过SSH管道转发企业微信API请求，不在云服务器保存企业微信密钥。",
        },
        "内容长度": len(args.content),
        "检查结果": checks,
        "真实发送人工确认令": confirmation,
        "当前计数": current_count,
        "最大计数": max_count,
        "是否允许进入真实发送": allowed,
        "实际动作": {
            "调用企业微信获取token": False,
            "尝试发送企业微信": False,
            "发送企业微信成功": False,
            "输出密钥": False,
            "写旧系统": False,
            "写正式库": False,
            "自动交易": False,
        },
    }
    if allowed and (args.probe_token or args.real_send):
        if egress_mode == "fixed-public":
            remote_result = send_message_via_fixed_public_egress(
                fixed_egress,
                corp_id,
                secret,
                agent_id,
                target,
                args.content,
                args.msgtype,
                args.real_send,
            )
            result["实际动作"]["调用企业微信获取token"] = True
            result["固定公网出口"]["实际出口IP"] = remote_result.get("出口IP", "")
            result["token探测"] = remote_result.get("token探测", {})
            if args.real_send:
                result["实际动作"]["尝试发送企业微信"] = True
                send_result = remote_result.get("发送结果") or {"ok": False, "企业微信返回": {"errcode": -1, "errmsg": "remote_send_result_missing"}}
                result["实际动作"]["发送企业微信成功"] = bool(send_result.get("ok"))
                result["发送结果"] = send_result
                if send_result.get("ok"):
                    update_counter({"时间": result["生成时间"], "目标用户": target, "内容长度": len(args.content), "发送出口模式": egress_mode})
                    result["当前计数"] = current_count + 1
        else:
            token_data = get_token(corp_id, secret)
            result["实际动作"]["调用企业微信获取token"] = True
            result["token探测"] = {"ok": token_data["ok"], "企业微信返回": sanitize_wework(token_data["raw"])}
            if args.real_send and token_data["ok"]:
                send_result = send_message(token_data["access_token"], agent_id, target, args.content, args.msgtype)
                result["实际动作"]["尝试发送企业微信"] = True
                result["实际动作"]["发送企业微信成功"] = bool(send_result["ok"])
                result["发送结果"] = {"ok": send_result["ok"], "企业微信返回": sanitize_wework(send_result["raw"])}
                if send_result["ok"]:
                    update_counter({"时间": result["生成时间"], "目标用户": target, "内容长度": len(args.content), "发送出口模式": egress_mode})
                    result["当前计数"] = current_count + 1
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    output = LOG_DIR / f"wework-controlled-sender-{stamp}.json"
    latest = LOG_DIR / "wework-controlled-sender-最新.json"
    write_json(output, result)
    write_json(latest, result)
    success = allowed and (not args.real_send or bool(result["实际动作"]["发送企业微信成功"]))
    print(json.dumps({"ok": success, "allowed": allowed, "real_send_success": result["实际动作"]["发送企业微信成功"], "输出": str(output)}, ensure_ascii=False))
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
