# -*- coding: utf-8 -*-
"""
名称：判断交易保护施工窗口.py
作用：根据交易保护与施工窗口规则，判断当前是否处于A股交易保护、施工保护、收市分析或空闲维护窗口。
触发方式：python 判断交易保护施工窗口.py
依赖：Python标准库；00杰哥系统总管/01配置/交易保护与施工窗口规则.json。
所属系统：00杰哥系统总管。
输出：00杰哥系统总管/04日志/交易保护/stock-trading-protection-window-*.json；03数据/运行状态/交易保护施工窗口_最新.json。
安全边界：只读规则和当前时间，只写总管日志/状态快照；不重启服务、不触发n8n、不发送企业微信、不调用券商接口、不自动交易。
标识：trading-protection-window-check；施工保护；只读判断。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, time
from pathlib import Path
from typing import Any


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_hhmm(value: str) -> time:
    hour, minute = value.split(":", 1)
    return time(int(hour), int(minute))


def in_window(current: time, start: str, end: str) -> bool:
    return parse_hhmm(start) <= current <= parse_hhmm(end)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", help="用于验收的指定时间，格式 YYYY-MM-DD HH:MM:SS；默认当前本机时间。")
    args = parser.parse_args()

    now = datetime.strptime(args.now, "%Y-%m-%d %H:%M:%S") if args.now else datetime.now()
    manager = manager_root()
    rule_path = manager / "01配置" / "交易保护与施工窗口规则.json"
    rules = load_json(rule_path)

    today = now.strftime("%Y-%m-%d")
    current_time = now.time()
    is_weekend = now.weekday() >= 5
    known_closed = today in set(rules.get("交易日历", {}).get("已知非交易日", []))
    possible_trading_day = not is_weekend and not known_closed

    highest_hits = [
        item.get("名称")
        for item in rules.get("保护窗口", {}).get("最高保护", [])
        if possible_trading_day and in_window(current_time, item["开始"], item["结束"])
    ]
    construction_hits = [
        item.get("名称")
        for item in rules.get("保护窗口", {}).get("施工保护", [])
        if possible_trading_day and in_window(current_time, item["开始"], item["结束"])
    ]

    if highest_hits:
        state = "交易保护"
    elif construction_hits:
        state = "施工保护"
    elif possible_trading_day and in_window(current_time, "15:30", "18:30"):
        state = "收市分析"
    elif current_time >= time(22, 0) or current_time <= time(6, 0):
        state = "夜间维护"
    else:
        state = "空闲维护"

    report = {
        "名称": "交易保护施工窗口判断",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "判断时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "星期": now.weekday() + 1,
        "是否周末": is_weekend,
        "是否已知非交易日": known_closed,
        "是否可能交易日": possible_trading_day,
        "当前运行状态": state,
        "命中最高保护窗口": highest_hits,
        "命中施工保护窗口": construction_hits,
        "保护窗口内允许动作": rules.get("动作分级", {}).get("允许_保护窗口", []),
        "保护窗口内禁止动作": rules.get("动作分级", {}).get("禁止_保护窗口", []),
        "安全边界": {
            "是否重启服务": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
        "规则文件": str(rule_path),
    }

    log_dir = manager / "04日志" / "交易保护"
    state_dir = manager / "03数据" / "运行状态"
    latest = log_dir / "stock-trading-protection-window-最新.json"
    state_latest = state_dir / "交易保护施工窗口_最新.json"
    write_json(latest, report)
    write_json(state_latest, report)

    print(json.dumps({
        "当前运行状态": report["当前运行状态"],
        "是否可能交易日": report["是否可能交易日"],
        "最高保护命中": len(highest_hits),
        "施工保护命中": len(construction_hits),
        "输出": str(state_latest),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

