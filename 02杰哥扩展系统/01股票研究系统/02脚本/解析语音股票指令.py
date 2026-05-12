# -*- coding: utf-8 -*-
"""
名称：解析语音股票指令.py
作用：把语音识别后的普通话、重庆话、同音误识别文本解析为标准股票研究指令。
触发方式：python 解析语音股票指令.py --text "给我看哈新一盛"
依赖：Python标准库；语音股票指令容错规则.json；重点关注股票池.json；股票池模板.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读配置和股票池；只写新系统股票模块04日志；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建语音股票指令解析脚本。
标识：stock-voice-command-tolerance-parse
"""

from __future__ import annotations

import argparse
import difflib
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


def clean_text(text: str, dialect_rules: list[dict[str, str]]) -> str:
    cleaned = re.sub(r"\s+", "", str(text or "").strip())
    cleaned = cleaned.replace("，", ",").replace("。", "")
    for item in dialect_rules:
        cleaned = cleaned.replace(item.get("方言或口语", ""), item.get("标准含义", ""))
    cleaned = append_spoken_digit_code(cleaned)
    return cleaned


def append_spoken_digit_code(text: str) -> str:
    digit_map = {
        "零": "0",
        "〇": "0",
        "一": "1",
        "幺": "1",
        "二": "2",
        "两": "2",
        "三": "3",
        "四": "4",
        "五": "5",
        "六": "6",
        "七": "7",
        "八": "8",
        "九": "9",
    }
    pattern = "[" + "".join(digit_map.keys()) + "]{6,}"
    matches = re.findall(pattern, text)
    codes = []
    for match in matches:
        code = "".join(digit_map.get(char, "") for char in match)
        if len(code) >= 6:
            codes.append(code[:6])
    if not codes:
        return text
    return text + "|" + "|".join(codes)


def normalize_code(code: str) -> str:
    code = str(code or "").strip().lower()
    return code[2:] if code.startswith(("sh", "sz")) else code


def load_stocks(root: Path) -> list[dict[str, Any]]:
    focus = load_json(root / "01配置" / "重点关注股票池.json", {"股票池": []}).get("股票池", [])
    merged = load_json(root / "01配置" / "股票池模板.json", {"股票池": []}).get("股票池", [])
    by_code: dict[str, dict[str, Any]] = {}
    for item in focus + merged:
        code = str(item.get("代码") or item.get("code") or "").strip()
        name = str(item.get("名称") or item.get("name") or "").strip()
        if code and name:
            by_code[code] = {"代码": code, "名称": name}
    return list(by_code.values())


def detect_intent(text: str, rules: dict[str, Any]) -> dict[str, Any]:
    for item in rules.get("支持意图", []):
        for phrase in item.get("触发表达", []):
            if phrase in text:
                return {"意图": item.get("意图"), "触发表达": phrase, "置信度": 1.0}
    return {"意图": "股票分析", "触发表达": "默认", "置信度": 0.7}


def build_alias_map(stocks: list[dict[str, Any]], rules: dict[str, Any]) -> list[dict[str, Any]]:
    alias_map = []
    aliases = rules.get("股票同音别名", {})
    for stock in stocks:
        name = stock["名称"]
        code = stock["代码"]
        alias_map.append({"文本": name, "标准名称": name, "代码": code, "类型": "标准名称"})
        alias_map.append({"文本": normalize_code(code), "标准名称": name, "代码": code, "类型": "股票代码"})
        alias_map.append({"文本": code, "标准名称": name, "代码": code, "类型": "股票代码"})
        for alias in aliases.get(name, []):
            alias_map.append({"文本": alias, "标准名称": name, "代码": code, "类型": "同音别名"})
    return alias_map


def detect_stock(text: str, alias_map: list[dict[str, Any]]) -> dict[str, Any]:
    direct_matches = []
    for item in alias_map:
        alias = str(item.get("文本", ""))
        if alias and alias in text:
            score = 1.0 if item.get("类型") in {"标准名称", "股票代码"} else 0.92
            direct_matches.append({**item, "置信度": score, "匹配方式": item.get("类型")})
    if direct_matches:
        direct_matches.sort(key=lambda item: item["置信度"], reverse=True)
        return {"最佳匹配": direct_matches[0], "候选": direct_matches[:5]}

    fuzzy_matches = []
    for item in alias_map:
        alias = str(item.get("文本", ""))
        if not alias:
            continue
        ratio = difflib.SequenceMatcher(None, text, alias).ratio()
        partial = max((difflib.SequenceMatcher(None, piece, alias).ratio() for piece in split_candidates(text)), default=0)
        score = max(ratio, partial)
        if score >= 0.55:
            fuzzy_matches.append({**item, "置信度": round(score, 4), "匹配方式": "模糊匹配"})
    fuzzy_matches.sort(key=lambda item: item["置信度"], reverse=True)
    return {"最佳匹配": fuzzy_matches[0] if fuzzy_matches else None, "候选": fuzzy_matches[:5]}


def split_candidates(text: str) -> list[str]:
    chunks = [text]
    for keyword in ["分析", "看一下", "讲一下", "呈现", "查一下", "研究一下", "帮我看", "给我看看", "行情", "怎么样"]:
        text = text.replace(keyword, "|")
    chunks.extend([piece for piece in text.split("|") if piece])
    return [piece for piece in chunks if piece]


def decide_action(stock_match: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    best = stock_match.get("最佳匹配")
    if not best:
        return {"执行状态": "不执行", "原因": "未识别到股票", "需要确认": True}
    score = float(best.get("置信度", 0))
    direct = float(thresholds.get("直接执行", 0.82))
    confirm = float(thresholds.get("需要确认", 0.62))
    if score >= direct:
        return {"执行状态": "可执行", "原因": "股票实体高置信度", "需要确认": False}
    if score >= confirm:
        return {"执行状态": "需确认", "原因": "股票实体中等置信度", "需要确认": True}
    return {"执行状态": "不执行", "原因": "股票实体低置信度", "需要确认": True}


def parse_command(text: str) -> dict[str, Any]:
    root = module_root()
    rules = load_json(root / "01配置" / "语音股票指令容错规则.json")
    cleaned = clean_text(text, rules.get("重庆话归一", []))
    stocks = load_stocks(root)
    alias_map = build_alias_map(stocks, rules)
    intent = detect_intent(cleaned, rules)
    stock_match = detect_stock(cleaned, alias_map)
    decision = decide_action(stock_match, rules.get("置信度阈值", {}))
    best = stock_match.get("最佳匹配") or {}
    return {
        "原始文本": text,
        "归一文本": cleaned,
        "意图": intent,
        "股票": {
            "代码": best.get("代码", ""),
            "名称": best.get("标准名称", ""),
            "匹配文本": best.get("文本", ""),
            "匹配方式": best.get("匹配方式", ""),
            "置信度": best.get("置信度", 0)
        },
        "候选": stock_match.get("候选", []),
        "执行判断": decision,
        "标准动作": {
            "接口": "/analyze" if intent.get("意图") in {"股票分析", "行情查询"} else "/feedback",
            "参数": {"问题": f"分析{best.get('标准名称', '')}"} if best else {}
        },
        "安全边界": {
            "是否联网": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="给我看哈新一盛", help="语音识别后的文本")
    args = parser.parse_args()
    result = parse_command(args.text)
    root = module_root()
    output_dir = root / "04日志" / "语音股票指令"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"stock-voice-command-tolerance-parse-{timestamp}.json"
    latest = output_dir / "stock-voice-command-tolerance-parse-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"执行状态": result["执行判断"]["执行状态"], "股票": result["股票"], "输出": str(output)}, ensure_ascii=False))
    return 0 if result["执行判断"]["执行状态"] in {"可执行", "需确认"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
