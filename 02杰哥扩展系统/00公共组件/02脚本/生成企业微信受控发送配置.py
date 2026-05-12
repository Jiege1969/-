# -*- coding: utf-8 -*-
"""
名称：生成企业微信受控发送配置.py
作用：读取新系统企业微信本机环境文件，生成新系统企业微信受控发送配置，不保存明文密钥。
触发方式：python 生成企业微信受控发送配置.py
依赖：Python标准库；企业微信本机环境.env；企业微信受控发送配置模板.json。
所属系统：02杰哥扩展系统/00公共组件
安全边界：只读新系统本机环境文件；不输出密钥值；不调用企业微信API；不发送消息；不写旧系统；不写正式库；不触发n8n；不交易。
创建修改记录：2026-04-29 创建受控发送配置生成脚本；2026-04-30 改为读取新系统企业微信本机环境文件；2026-05-01 增加企业微信目标应用档案存在性摘要。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "01配置"
LOCAL_ENV = CONFIG_DIR / "企业微信本机环境.env"
OUTPUT = CONFIG_DIR / "企业微信受控发送配置.json"
TEMPLATE = CONFIG_DIR / "企业微信受控发送配置模板.json"
APP_PROFILE_CONFIG = CONFIG_DIR / "企业微信应用目标档案.json"


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parse_env(path: Path) -> dict[str, str]:
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


def has_value(env: dict[str, str], key: str) -> bool:
    value = env.get(key, "").strip()
    return bool(value and value not in {"待填写", "请填写"})


def main() -> int:
    template = load_json(TEMPLATE, {})
    app_profiles = load_json(APP_PROFILE_CONFIG, {})
    env = parse_env(LOCAL_ENV)
    default_user = env.get("WECOM_DEFAULT_USER_ID", "").strip()
    whitelist = [default_user] if default_user and default_user not in {"待填写", "请填写"} else []
    config = {
        "名称": "企业微信受控发送配置",
        "作用": "股票系统交付灰度期间的企业微信受控发送配置；不保存明文密钥，只记录新系统环境文件路径、变量名、本人白名单和发送边界。",
        "所属系统": "02杰哥扩展系统/00公共组件",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "来源模板存在": TEMPLATE.exists(),
        "本机环境文件": str(LOCAL_ENV),
        "真实发送": {
            "是否启用": True,
            "首轮灰度最大消息数": 5,
            "允许群发": False,
            "允许外部客户": False,
            "允许非白名单接收人": False,
        },
        "凭据来源": {
            "类型": "进程环境变量优先，新系统本机环境文件备用",
            "企业ID变量": "WECOM_CORP_ID",
            "应用ID变量": "WECOM_AGENT_ID",
            "应用密钥变量": "WECOM_APP_SECRET",
            "目标应用档案文件": str(APP_PROFILE_CONFIG),
            "当前启用应用": app_profiles.get("当前启用应用", "n8n指令通行证"),
        },
        "白名单": {
            "接收人ID列表": whitelist,
            "来源": "新系统企业微信本机环境WECOM_DEFAULT_USER_ID",
            "说明": "首轮只允许本人企业微信ID，最多5条测试消息；不群发、不外部客户。",
        },
        "凭据存在性": {
            "WECOM_CORP_ID": has_value(env, "WECOM_CORP_ID"),
            "WECOM_AGENT_ID": has_value(env, "WECOM_AGENT_ID"),
            "WECOM_APP_SECRET": has_value(env, "WECOM_APP_SECRET"),
            "WECOM_JIEGE_ASSISTANT_AGENT_ID": has_value(env, "WECOM_JIEGE_ASSISTANT_AGENT_ID"),
            "WECOM_JIEGE_ASSISTANT_APP_SECRET": has_value(env, "WECOM_JIEGE_ASSISTANT_APP_SECRET"),
            "WECOM_DEFAULT_USER_ID": bool(whitelist),
        },
        "禁止事项": {
            "保存明文密钥": True,
            "股票系统持有密钥": True,
            "绕过统一消息出口发送": True,
            "超过5条首轮测试消息": True,
            "群发": True,
            "外部客户发送": True,
            "自动交易": True,
        },
    }
    if template:
        config["模板边界"] = template.get("禁止事项", {})
    OUTPUT.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "输出": str(OUTPUT), "白名单数量": len(whitelist), "凭据存在性": config["凭据存在性"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
