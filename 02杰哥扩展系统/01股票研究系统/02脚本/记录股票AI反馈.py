# -*- coding: utf-8 -*-
"""
名称：记录股票AI反馈.py
作用：解析并记录用户对AI分析结果的反馈，如有价值、无价值、继续跟踪、误报。
触发方式：python 记录股票AI反馈.py --command "有价值 sh688047"
依赖：AI分析报告_最新.json（可选，用于补股票名称）。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读AI分析报告；只写04日志/用户反馈；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
标识：stock-ai-feedback-record
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


VALID_FEEDBACK = ["有价值", "无价值", "继续跟踪", "误报", "暂缓观察"]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"必需文件不存在: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if not text:
        return ""
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        if suffix.upper() == "SH":
            return f"sh{num}"
        if suffix.upper() == "SZ":
            return f"sz{num}"
        if suffix.upper() == "BJ":
            return f"bj{num}"
    if len(text) == 6 and text.isdigit():
        if text.startswith(("6", "9")):
            return f"sh{text}"
        if text.startswith(("4", "8")):
            return f"bj{text}"
        return f"sz{text}"
    return text


def parse_feedback(command: str) -> dict[str, Any]:
    text = command.strip()
    feedback = next((item for item in VALID_FEEDBACK if item in text), "")
    code_match = re.search(r"([a-zA-Z]{0,2}\d{6}(?:\.(?:SH|SZ|BJ|sh|sz|bj))?)", text)
    code = normalize_code(code_match.group(1)) if code_match else ""
    reason = text
    if feedback:
        reason = reason.replace(feedback, "", 1).strip()
    if code_match:
        reason = reason.replace(code_match.group(1), "", 1).strip(" ，,;；")
    return {
        "原始命令": text,
        "反馈类型": feedback,
        "代码": code,
        "理由": reason,
        "是否有效": bool(feedback and code),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="记录股票AI反馈")
    parser.add_argument("--command", required=True, help="反馈命令，如：有价值 sh688047 原因")
    args = parser.parse_args()

    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    report_path = root / "03数据" / "135分层日报" / "AI分析报告_最新.json"
    feedback_dir = root / "04日志" / "用户反馈"
    feedback_path = feedback_dir / "反馈日志.json"
    event_path = feedback_dir / f"反馈记录_{stamp}.json"

    parsed = parse_feedback(args.command)
    report = load_json(report_path, required=False)
    report_map = {normalize_code(item.get("代码")): item for item in report.get("分析结果", [])}
    stock = report_map.get(parsed["代码"], {})
    event = {
        "时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "反馈类型": parsed["反馈类型"],
        "代码": parsed["代码"],
        "名称": stock.get("名称", ""),
        "行业": stock.get("行业", ""),
        "理由": parsed["理由"],
        "原始命令": parsed["原始命令"],
        "是否有效": parsed["是否有效"],
        "来源报告日期": report.get("数据日期"),
    }
    existing = load_json(feedback_path, required=False) or {"名称": "股票AI反馈日志", "反馈记录": []}
    records = list(existing.get("反馈记录", []))
    records.append(event)
    output = {
        "名称": "股票AI反馈日志",
        "更新时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "反馈数量": len(records),
        "反馈记录": records,
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写旧系统": False,
            "是否写正式库": False,
        },
    }
    write_json(feedback_path, output)
    write_json(event_path, event)
    print(json.dumps({
        "状态": "完成" if parsed["是否有效"] else "无效反馈",
        "反馈类型": parsed["反馈类型"],
        "代码": parsed["代码"],
        "名称": event["名称"],
        "反馈日志": str(feedback_path),
    }, ensure_ascii=False))
    return 0 if parsed["是否有效"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
