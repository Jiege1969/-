# -*- coding: utf-8 -*-
"""
名称：记录人工反馈到决策账.py
作用：把用户自然语言反馈解析为人工决策账记录，服务后续结果验证和经验提炼。
触发方式：python 记录人工反馈到决策账.py --feedback "继续观察：新易盛，原因：等待回踩确认"
依赖：Python标准库；复盘账本运行规则.json；股票池模板.json；重点关注股票池.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写新系统股票模块03数据/10复盘闭环/02人工决策账；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建人工反馈入账脚本。
标识：stock-human-feedback-ledger-record
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_code(code: str) -> str:
    code = str(code or "").strip().lower()
    if code.startswith(("sh", "sz")):
        return code[2:]
    return code


def load_stocks(root: Path) -> list[dict[str, Any]]:
    merged = load_json(root / "01配置" / "股票池模板.json", {"股票池": []}).get("股票池", [])
    focus = load_json(root / "01配置" / "重点关注股票池.json", {"股票池": []}).get("股票池", [])
    by_code: dict[str, dict[str, Any]] = {}
    for item in focus + merged:
        code = str(item.get("代码") or item.get("code") or "").strip()
        if code:
            by_code[code] = item
    return list(by_code.values())


def parse_feedback(text: str, stocks: list[dict[str, Any]]) -> dict[str, Any]:
    feedback = text.strip()
    action = "未识别"
    for candidate in ["确认L4", "继续观察", "暂不关注", "无价值", "系统看错", "我判断错了"]:
        if feedback.startswith(candidate):
            action = candidate
            break
    stock = None
    for item in stocks:
        code = str(item.get("代码") or item.get("code") or "")
        name = str(item.get("名称") or item.get("name") or "")
        if name and name in feedback:
            stock = item
            break
        if code and (code in feedback or normalize_code(code) in feedback):
            stock = item
            break
    reason = ""
    match = re.search(r"原因[：:](.*)$", feedback)
    if match:
        reason = match.group(1).strip()
    elif "，" in feedback:
        reason = feedback.split("，", 1)[1].strip()
    confirm_level = "未确认"
    enter_l4_or_above = False
    if action == "确认L4":
        confirm_level = "L4观察仓"
        enter_l4_or_above = True
    elif action == "继续观察":
        confirm_level = "L5继续研究或L6轻度关注"
    elif action in {"暂不关注", "无价值"}:
        confirm_level = "暂不升级"
    return {
        "原始反馈": feedback,
        "用户反馈": action,
        "股票代码": stock.get("代码") if stock else "",
        "股票名称": stock.get("名称") if stock else "",
        "确认层级": confirm_level,
        "是否进入L4及以上": enter_l4_or_above,
        "人工理由": reason or "未填写",
        "解析状态": "已识别" if action != "未识别" and stock else "待人工补充",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feedback", default="继续观察：新易盛，原因：验收样例，等待回踩确认", help="用户反馈文本")
    parser.add_argument("--sample", action="store_true", help="标记为验收样例")
    args = parser.parse_args()
    root = module_root()
    rules = load_json(root / "01配置" / "复盘账本运行规则.json")
    parsed = parse_feedback(args.feedback, load_stocks(root))
    record = {
        "记录时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "记录类型": "验收样例" if args.sample else "人工反馈",
        "反馈记录": parsed,
        "可用反馈格式": rules.get("反馈模板", []),
        "安全边界": {
            "是否联网": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False
        }
    }
    ledger_dir = root / rules.get("账本路径", {}).get("人工决策账", "03数据/10复盘闭环/02人工决策账")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = ledger_dir / f"人工决策账记录_{timestamp}.json"
    latest = ledger_dir / "人工决策账记录_最新.json"
    write_json(output, record)
    write_json(latest, record)
    print(json.dumps({"解析状态": parsed["解析状态"], "股票名称": parsed["股票名称"], "用户反馈": parsed["用户反馈"], "输出": str(output)}, ensure_ascii=False))
    return 0 if parsed["解析状态"] == "已识别" else 1


if __name__ == "__main__":
    raise SystemExit(main())
