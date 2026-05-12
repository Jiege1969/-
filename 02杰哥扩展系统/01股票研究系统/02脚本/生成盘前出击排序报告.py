# -*- coding: utf-8 -*-
"""
名称：生成盘前出击排序报告.py
作用：把盘前阶段从晨报样例升级为正式《盘前出击排序》产物。
输入：昨日收盘短线观察、昨晚AI分析报告、晨报候选；无盘前消息字段时降级为“基于昨晚条件的预排序”。
安全边界：只读本地报告，只写260策略包；不触发n8n；不发送企业微信；不接券商；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_code(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    lower = text.lower()
    if lower.startswith(("sh", "sz", "bj")):
        return lower
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) != 6:
        return text
    if digits.startswith(("6", "9")):
        return f"sh{digits}"
    if digits.startswith(("0", "2", "3")):
        return f"sz{digits}"
    if digits.startswith(("4", "8")):
        return f"bj{digits}"
    return digits


def display_code(code: str) -> str:
    if len(code) == 8 and code[:2] in {"sh", "sz", "bj"}:
        suffix = {"sh": "SH", "sz": "SZ", "bj": "BJ"}[code[:2]]
        return f"{code[2:]}.{suffix}"
    return code


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def collect_morning_candidates(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for source_name, weight in (("今日重点关注", 40.0), ("新增或替换候选", 25.0)):
        for index, item in enumerate(data.get(source_name, []) if isinstance(data.get(source_name), list) else [], start=1):
            if not isinstance(item, dict):
                continue
            code = normalize_code(item.get("代码"))
            if not code:
                continue
            row = rows.setdefault(code, {
                "代码": code,
                "展示代码": display_code(code),
                "名称": item.get("名称", ""),
                "来源": [],
                "基础分": 0.0,
                "原始候选": item,
            })
            row["名称"] = row["名称"] or item.get("名称", "")
            row["来源"].append(source_name)
            row["基础分"] += max(5.0, weight - index)
            if "暂不进入" in str(item.get("类型", "")):
                row["基础分"] -= 18.0
    return rows


def signal_score(stock: dict[str, Any]) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    for signal in stock.get("指标共振信号", []) if isinstance(stock.get("指标共振信号"), list) else []:
        if not isinstance(signal, dict) or signal.get("触发") is not True:
            continue
        name = str(signal.get("规则名称", ""))
        if "强势突破" in name:
            score += 25.0
            reasons.append("强势突破确认信号已触发")
        elif "反弹" in name or "共振" in name:
            score += 15.0
            reasons.append(f"{name}已触发")
    return score, reasons


def has_preopen_message(item: dict[str, Any]) -> bool:
    keys = ("盘前消息", "盘前消息摘要", "消息共振", "盘前事件", "开盘前消息")
    return any(str(item.get(key, "")).strip() for key in keys)


def build_ranked_rows(close_data: dict[str, Any], ai_data: dict[str, Any], morning_data: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    candidates = collect_morning_candidates(morning_data)
    close_index: dict[str, dict[str, Any]] = {}
    for index, stock in enumerate(close_data.get("股票", []) if isinstance(close_data.get("股票"), list) else [], start=1):
        if not isinstance(stock, dict):
            continue
        code = normalize_code(stock.get("代码"))
        if not code:
            continue
        close_index[code] = stock
        row = candidates.setdefault(code, {
            "代码": code,
            "展示代码": display_code(code),
            "名称": stock.get("名称", ""),
            "来源": [],
            "基础分": 0.0,
            "原始候选": {},
        })
        row["名称"] = row["名称"] or stock.get("名称", "")
        row["来源"].append("昨日收盘短线观察")
        row["基础分"] += max(2.0, 28.0 - index * 2)

    ai_index: dict[str, dict[str, Any]] = {}
    for item in ai_data.get("分析结果", []) if isinstance(ai_data.get("分析结果"), list) else []:
        if not isinstance(item, dict):
            continue
        code = normalize_code(item.get("代码"))
        if not code:
            continue
        ai_index[code] = item
        row = candidates.setdefault(code, {
            "代码": code,
            "展示代码": display_code(code),
            "名称": item.get("名称", ""),
            "来源": [],
            "基础分": 0.0,
            "原始候选": {},
        })
        row["名称"] = row["名称"] or item.get("名称", "")
        row["来源"].append("昨晚AI分析报告")
        row["基础分"] += max(3.0, 18.0 - to_float(item.get("优先级"), 10.0)) + to_float(item.get("调整分")) * 2

    any_preopen_message = any(has_preopen_message(item.get("原始候选", {})) for item in candidates.values())
    mode = "盘前消息共振排序" if any_preopen_message else "基于昨晚条件的预排序"

    ranked: list[dict[str, Any]] = []
    for code, row in candidates.items():
        close_stock = close_index.get(code, {})
        ai_item = ai_index.get(code, {})
        extra_score, signal_reasons = signal_score(close_stock)
        aux = close_stock.get("辅助指标", {}) if isinstance(close_stock.get("辅助指标"), dict) else {}
        price = to_float(aux.get("涨跌幅"), to_float(close_stock.get("涨跌幅")))
        amount_ratio = to_float(aux.get("量比5日"))
        score = row["基础分"] + extra_score
        if price > 3:
            score += 8
        elif price < -3:
            score -= 8
        if amount_ratio > 1.5:
            score += 6
        risk_text = " ".join(str(close_stock.get(key, "")) for key in ("明天短线观察条件", "短线止损参考价", "观察线刷新状态"))
        if "已跌破" in risk_text or "风险复核" in risk_text:
            score -= 18

        reasons = signal_reasons[:]
        if ai_item:
            reasons.append(f"AI优先级{ai_item.get('优先级', '')}，调整分{ai_item.get('调整分', '')}")
        if close_stock:
            reasons.append(f"收盘涨跌幅{price:.2f}%，量比5日{amount_ratio:.2f}")
        if not reasons:
            reasons.append("来自晨报候选，等待盘前消息字段补充")

        ranked.append({
            "代码": code,
            "展示代码": row.get("展示代码") or display_code(code),
            "名称": row.get("名称", ""),
            "观察优先级分": round(score, 2),
            "排序来源": sorted(set(row.get("来源", []))),
            "排序原因": "；".join(reasons[:4]),
            "排序口径": mode,
            "盘前消息状态": "已有盘前消息字段" if any_preopen_message else "无盘前消息字段，降级为基于昨晚条件的预排序",
            "今日观察条件": close_stock.get("明天短线观察条件") or row.get("原始候选", {}).get("观察条件") or "不设具体触发价，等待盘前消息字段与最新行情刷新后再评估。",
            "风险提示": close_stock.get("短线止损参考价") or row.get("原始候选", {}).get("风险提醒") or "若数据未刷新或盘前消息缺失，只保留为排序候选，不形成交易动作。",
        })

    ranked.sort(key=lambda item: item["观察优先级分"], reverse=True)
    for index, item in enumerate(ranked, start=1):
        item["排序"] = index
    return ranked[:10], mode


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 盘前出击排序｜{report['报告日期']}",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 排序口径：{report['排序口径']}",
        f"- 候选数量：{report['候选数量']}",
        "",
        "| 排名 | 股票 | 观察优先级分 | 排序原因 | 今日观察条件 | 风险提示 |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for item in report["股票"]:
        lines.append(
            f"| {item['排序']} | {item['名称']}（{item['展示代码']}） | {item['观察优先级分']} | "
            f"{item['排序原因']} | {item['今日观察条件']} | {item['风险提示']} |"
        )
    lines.extend([
        "",
        "## 盘前消息状态",
        "",
        f"- {report['盘前消息状态']}",
        "",
        "## 安全边界",
        "",
        "- 本报告仅为研究观察排序，不构成投资建议。",
        "- 未触发n8n，未真实发送企业微信，未接券商，未交易。",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
    close_path = out_dir / "收盘短线观察_基于300只轻扫描_最新.json"
    ai_path = root / "03数据" / "135分层日报" / "AI分析报告_最新.json"
    morning_path = out_dir / "开市前晨报样例_最新.json"
    close_data = load_json(close_path, {})
    ai_data = load_json(ai_path, {})
    morning_data = load_json(morning_path, {})

    rows, mode = build_ranked_rows(close_data if isinstance(close_data, dict) else {}, ai_data if isinstance(ai_data, dict) else {}, morning_data if isinstance(morning_data, dict) else {})
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    report = {
        "名称": "盘前出击排序",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "报告日期": now.strftime("%Y-%m-%d"),
        "排序口径": mode,
        "盘前消息状态": "无盘前消息字段，降级为“基于昨晚条件的预排序”。" if mode == "基于昨晚条件的预排序" else "已纳入盘前消息字段。",
        "输入": {
            "昨日收盘短线观察": str(close_path),
            "昨晚AI分析报告": str(ai_path),
            "晨报候选": str(morning_path),
        },
        "候选数量": len(rows),
        "股票": rows,
        "安全边界": {
            "是否触发n8n": False,
            "是否真实发送企业微信": False,
            "是否接券商": False,
            "是否交易": False,
        },
    }
    output_json = out_dir / f"盘前出击排序_{stamp}.json"
    output_md = out_dir / f"盘前出击排序_{stamp}.md"
    latest_json = out_dir / "盘前出击排序_最新.json"
    latest_md = out_dir / "盘前出击排序_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"产物": str(latest_json), "候选数量": len(rows), "排序口径": mode}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
