# -*- coding: utf-8 -*-
"""
名称：生成企业微信可信IP放行状态报告.py
作用：汇总企业微信应用消息可信IP阻断状态，给出恢复灰度测试的下一步动作。
触发方式：python 生成企业微信可信IP放行状态报告.py
依赖：Python标准库；企业微信受控发送器日志；企业微信真实灰度阻断诊断。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读日志并生成报告；不调用企业微信API；不发送消息；不写旧系统；不交易。
创建修改记录：2026-04-29 创建可信IP放行状态报告脚本；2026-04-29 改为扫描最近日志，避免被dry-run覆盖。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMMON_LOG_DIR = ROOT.parents[0] / "00公共组件" / "04日志" / "企业微信受控发送器"
OUTPUT_DIR = ROOT / "03数据" / "85企业微信可信IP放行状态"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def recent_sender_logs(limit: int = 50) -> list[dict[str, Any]]:
    if not COMMON_LOG_DIR.exists():
        return []
    files = sorted(
        [path for path in COMMON_LOG_DIR.glob("wework-controlled-sender-*.json") if "最新" not in path.name],
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )[:limit]
    logs: list[dict[str, Any]] = []
    for path in files:
        data = load_json(path, {})
        if isinstance(data, dict):
            data["_文件"] = str(path)
            logs.append(data)
    return logs


def find_latest_ip_block(logs: list[dict[str, Any]]) -> dict[str, Any]:
    for item in logs:
        send_result = item.get("发送结果", {}).get("企业微信返回", {})
        if send_result.get("errcode") == 60020:
            return item
    return {}


def main() -> int:
    logs = recent_sender_logs()
    latest_block = find_latest_ip_block(logs)
    send_result = latest_block.get("发送结果", {}).get("企业微信返回", {})
    errcode = send_result.get("errcode")
    errmsg = str(send_result.get("errmsg") or "")
    blocked_ip = ""
    marker = "from ip:"
    if marker in errmsg:
        blocked_ip = errmsg.split(marker, 1)[1].split(",", 1)[0].strip()
    status = "需放行可信IP" if errcode == 60020 else "未检测到可信IP阻断"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": status,
        "扫描日志数量": len(logs),
        "阻断来源日志": latest_block.get("_文件", ""),
        "最近企业微信返回": {
            "errcode": errcode,
            "errmsg摘要": errmsg[:300],
            "识别到的公网IP": blocked_ip,
        },
        "当前判断": "应用消息通道需要在企业微信后台可信IP中放行该公网IP；response_url路线不依赖此应用消息可信IP。",
        "恢复动作": [
            "在企业微信后台应用可信IP中加入识别到的公网IP。",
            "放行后运行企业微信受控发送器token探测。",
            "再执行最多5条本人白名单真实灰度消息。",
        ],
        "安全边界": {
            "本脚本调用企业微信API": False,
            "本脚本发送企业微信": False,
            "写旧系统": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = OUTPUT_DIR / f"企业微信可信IP放行状态_{stamp}.json"
    latest_output = OUTPUT_DIR / "企业微信可信IP放行状态_最新.json"
    write_json(output, report)
    write_json(latest_output, report)
    print(json.dumps({"状态": status, "识别到的公网IP": blocked_ip, "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
