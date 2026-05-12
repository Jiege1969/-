# -*- coding: utf-8 -*-
"""
Name: wework-controlled-send-gate.py
Purpose: Check whether the unified message outlet is allowed to enter controlled WeWork real-send gray testing.
Trigger: python 企业微信受控发送闸口.py --check-only
Dependencies: Python standard library; 企业微信受控发送配置模板.json.
Owner system: 02杰哥扩展系统/00公共组件
Safety: Check-only gate by default; reads environment variable presence without printing secret values; writes local gate logs only; does not call WeWork APIs, send messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created controlled WeWork send gate.
Marker: wework-controlled-send-gate
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    root = module_root()
    config_path = root / "01配置" / "企业微信受控发送配置模板.json"
    config = load_json(config_path)
    send = config.get("真实发送", {})
    credential = config.get("凭据来源", {})
    whitelist = config.get("白名单", {}).get("接收人ID列表", [])
    env_names = [
        credential.get("企业ID变量", ""),
        credential.get("应用ID变量", ""),
        credential.get("应用密钥变量", ""),
    ]
    env_present = {name: bool(os.environ.get(name)) for name in env_names if name}
    checks = [
        {"检查项": "配置文件存在", "通过": config_path.exists(), "说明": str(config_path)},
        {"检查项": "默认真实发送关闭", "通过": send.get("是否启用") is False, "说明": str(send.get("是否启用"))},
        {"检查项": "首轮消息上限不超过5", "通过": int(send.get("首轮灰度最大消息数", 999)) <= 5, "说明": str(send.get("首轮灰度最大消息数"))},
        {"检查项": "禁止群发", "通过": send.get("允许群发") is False, "说明": str(send.get("允许群发"))},
        {"检查项": "禁止外部客户", "通过": send.get("允许外部客户") is False, "说明": str(send.get("允许外部客户"))},
        {"检查项": "白名单未扩大", "通过": len(whitelist) <= 1, "说明": str(len(whitelist))},
        {"检查项": "不输出密钥值", "通过": all(isinstance(value, bool) for value in env_present.values()), "说明": str(env_present)},
    ]
    real_send_ready = all(item["通过"] for item in checks) and send.get("是否启用") is True and len(whitelist) == 1 and all(env_present.values())
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "check-only" if args.check_only else "check-only-default",
        "检查结果": checks,
        "环境变量存在情况": env_present,
        "白名单数量": len(whitelist),
        "是否允许真实发送": real_send_ready,
        "当前结论": "真实发送仍未放行；需要受控凭据、本人白名单和显式启用后，才可进入最多5条首轮灰度测试。",
        "实际动作": {
            "读取环境变量是否存在": True,
            "输出密钥值": False,
            "调用企业微信API": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False
        },
    }
    log_dir = root / "04日志" / "企业微信受控发送闸口"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"wework-controlled-send-gate-{stamp}.json"
    latest = log_dir / "wework-controlled-send-gate-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"是否允许真实发送": result["是否允许真实发送"], "白名单数量": result["白名单数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
