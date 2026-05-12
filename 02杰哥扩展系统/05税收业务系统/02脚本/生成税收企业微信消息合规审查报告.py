# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信消息合规审查报告.py
作用：按独立规则审查企业微信拟发送消息是否越界。
安全边界：只读消息预演和合规规则；不读取凭据、不联网、不真实发送。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
RULE = ROOT / "01配置" / "税收企业微信消息合规审查规则.json"
PREVIEW = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信正式入口消息预演_最新.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_JSON = OUT_DIR / "税收企业微信消息合规审查报告_最新.json"
OUT_MD = OUT_DIR / "税收企业微信消息合规审查报告_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rule = load_json(RULE)
    preview = load_json(PREVIEW)
    message = preview.get("消息预演", {}).get("企业微信拟发送消息", "")
    missing_required = [item for item in rule.get("必须包含", []) if item not in message]
    found_prohibited = [item for item in rule.get("禁止短语", []) if item in message]
    sensitive_hits = []
    for item in rule.get("敏感信息模式", []):
        pattern = item.get("正则", "")
        if pattern and re.search(pattern, message):
            sensitive_hits.append(item.get("名称", pattern))
    max_len = int(rule.get("长度限制", {}).get("最大字符数", 1800))
    length_ok = len(message) <= max_len
    passed = not missing_required and not found_prohibited and not sensitive_hits and length_ok
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信消息合规审查报告",
        "生成时间": now,
        "规则来源": str(RULE),
        "消息来源": str(PREVIEW),
        "审查结论": "通过" if passed else "失败",
        "消息字符数": len(message),
        "最大字符数": max_len,
        "缺失必须包含": missing_required,
        "命中禁止短语": found_prohibited,
        "命中敏感信息模式": sensitive_hits,
        "是否真实发送": False,
        "安全边界": rule.get("安全边界", {})
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信消息合规审查报告",
        "",
        f"- 生成时间：{now}",
        f"- 审查结论：{report['审查结论']}",
        f"- 消息字符数：{report['消息字符数']}",
        f"- 最大字符数：{report['最大字符数']}",
        f"- 是否真实发送：{report['是否真实发送']}",
        "",
        "## 缺失必须包含",
        "",
    ]
    for item in missing_required:
        lines.append(f"- {item}")
    if not missing_required:
        lines.append("- 无")
    lines.extend(["", "## 命中禁止短语", ""])
    for item in found_prohibited:
        lines.append(f"- {item}")
    if not found_prohibited:
        lines.append("- 无")
    lines.extend(["", "## 命中敏感信息模式", ""])
    for item in sensitive_hits:
        lines.append(f"- {item}")
    if not sensitive_hits:
        lines.append("- 无")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": "完成", "审查结论": report["审查结论"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
