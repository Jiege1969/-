# -*- coding: utf-8 -*-
"""
名称：生成2500只学习分析股票池.py
作用：在2000只样本池基础上，补充500只可归因、流动性较好的股票，形成中信前台承载的大样本学习池。
边界：只读本地全A基础池、2000样本池和中信市场位置映射；只写本地03数据/01股票池；不触发n8n；不发送企业微信；不接券商；不交易。
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
STOCK_ROOT = ROOT / "02杰哥扩展系统" / "01股票研究系统"
POOL_DIR = STOCK_ROOT / "03数据" / "01股票池"
MARKET_POSITION_CSV = STOCK_ROOT / "03数据" / "292中信概念板块成分映射" / "中信股票市场位置_最新.csv"
BASE_POOL_JSON = POOL_DIR / "2000只样本股票池_最新.json"
ALL_A_JSON = POOL_DIR / "全A基础股票池_最新.json"
TARGET_SIZE = 2500
MIN_AMOUNT = 5_000_000


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, float) and math.isnan(value):
            return default
        return float(value)
    except Exception:
        return default


def load_market_position() -> dict[str, dict[str, str]]:
    if not MARKET_POSITION_CSV.exists():
        return {}
    result: dict[str, dict[str, str]] = {}
    with MARKET_POSITION_CSV.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            code = str(row.get("股票代码") or "").strip()
            if code:
                result[code] = row
    return result


def concept_count(row: dict[str, str]) -> int:
    text = row.get("概念板块") or ""
    return len([item for item in text.split("、") if item.strip()])


def normalize_base_item(item: dict[str, Any], market_pos: dict[str, dict[str, str]], source: str) -> dict[str, Any]:
    code = str(item.get("代码") or "").strip()
    pos = market_pos.get(code, {})
    amount = safe_float(item.get("最新成交额") or item.get("成交额"))
    return {
        "代码": code,
        "展示代码": item.get("展示代码") or code,
        "名称": item.get("名称") or "",
        "行业": pos.get("行业名称") or item.get("行业") or "未分类",
        "中信细分行业": pos.get("细分行业名称") or "",
        "市场": item.get("市场") or "",
        "板块": item.get("板块") or "",
        "最新成交额": amount,
        "中证全指权重": safe_float(item.get("中证全指权重")),
        "市场位置摘要": pos.get("市场位置摘要") or "",
        "概念数量": concept_count(pos),
        "纳入日期": datetime.now().strftime("%Y-%m-%d"),
        "来源": source,
    }


def candidate_score(item: dict[str, Any], pos: dict[str, str]) -> float:
    amount = safe_float(item.get("成交额") or item.get("最新成交额"))
    board = str(item.get("板块") or "")
    market = str(item.get("市场") or "")
    liquidity_score = math.log10(max(amount, 1.0)) * 10
    concept_score = min(concept_count(pos), 20) * 0.8
    board_score = 6 if board in {"主板", "创业板", "科创板"} else 2
    market_score = 3 if market in {"上交所", "深交所"} else 1
    position_score = 8 if pos else 0
    return round(liquidity_score + concept_score + board_score + market_score + position_score, 4)


def build_learning_pool() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    market_pos = load_market_position()
    base_data = load_json(BASE_POOL_JSON)
    all_a_data = load_json(ALL_A_JSON)
    base_rows = base_data.get("股票列表", [])
    all_rows = all_a_data.get("股票池", [])

    selected: list[dict[str, Any]] = []
    selected_codes: set[str] = set()
    for item in base_rows:
        code = str(item.get("代码") or "").strip()
        if not code or code in selected_codes:
            continue
        selected.append(normalize_base_item(item, market_pos, "2000只样本池基础保留"))
        selected_codes.add(code)

    need = max(0, TARGET_SIZE - len(selected))
    candidates: list[dict[str, Any]] = []
    for item in all_rows:
        code = str(item.get("代码") or "").strip()
        name = str(item.get("名称") or "")
        if not code or code in selected_codes:
            continue
        if item.get("是否ST") or item.get("是否退市风险") or "ST" in name or "退" in name:
            continue
        amount = safe_float(item.get("成交额"))
        if amount < MIN_AMOUNT:
            continue
        pos = market_pos.get(code, {})
        normalized = normalize_base_item(item, market_pos, "全A基础池扩展补充")
        normalized["扩展评分"] = candidate_score(item, pos)
        candidates.append(normalized)

    candidates.sort(key=lambda row: (row.get("扩展评分", 0), row.get("最新成交额", 0)), reverse=True)
    industry_added: Counter[str] = Counter()
    additions: list[dict[str, Any]] = []
    soft_cap = max(8, math.ceil(need / max(1, len({row["行业"] for row in candidates}))) * 3)
    for row in candidates:
        industry = row["行业"]
        if industry_added[industry] >= soft_cap:
            continue
        additions.append(row)
        selected_codes.add(row["代码"])
        industry_added[industry] += 1
        if len(additions) >= need:
            break
    if len(additions) < need:
        for row in candidates:
            if row["代码"] in {item["代码"] for item in additions}:
                continue
            additions.append(row)
            if len(additions) >= need:
                break

    selected.extend(additions[:need])
    selected = selected[:TARGET_SIZE]
    industry_counts = Counter(row["行业"] for row in selected)
    market_counts = Counter(row["市场"] for row in selected)
    meta = {
        "生成时间": now_text(),
        "目标数量": TARGET_SIZE,
        "实际数量": len(selected),
        "基础保留数量": len(base_rows),
        "扩展补充数量": len(additions[:need]),
        "覆盖行业数": len(industry_counts),
        "覆盖市场": dict(market_counts),
        "行业分布TOP20": [{"行业": k, "数量": v} for k, v in industry_counts.most_common(20)],
        "扩展原则": [
            "保留原2000只样本池作为代表性地基。",
            "从全A基础池补充非ST、无退市风险、成交额不低于500万元的股票。",
            "优先补充可在中信市场位置表中归因、成交活跃、概念覆盖较丰富的股票。",
            "本池用于学习观察和方法验证，不作为重点推荐池。",
        ],
    }
    return selected, meta


def write_outputs(rows: list[dict[str, Any]], meta: dict[str, Any]) -> dict[str, str]:
    POOL_DIR.mkdir(parents=True, exist_ok=True)
    stamp = stamp_text()
    latest_json = POOL_DIR / "2500只样本股票池_最新.json"
    latest_csv = POOL_DIR / "2500只样本股票池_最新.csv"
    latest_md = POOL_DIR / "2500只学习分析股票池说明_最新.md"
    archive_json = POOL_DIR / f"2500只样本股票池_{stamp}.json"
    archive_csv = POOL_DIR / f"2500只样本股票池_{stamp}.csv"
    package = {
        "名称": "2500只学习分析股票池",
        "定位": "中信软件前台承载的大样本学习池，用于长期观察、方法验证、反馈沉淀和减少系统重复基础计算压力。",
        "生成时间": meta["生成时间"],
        "数量": len(rows),
        "字段": ["代码", "展示代码", "名称", "行业", "中信细分行业", "市场", "板块", "最新成交额", "中证全指权重", "概念数量", "来源"],
        "股票列表": rows,
        "生成说明": meta,
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否接券商": False,
            "是否交易": False,
        },
    }
    for path in (latest_json, archive_json):
        path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    fieldnames = package["字段"]
    for path in (latest_csv, archive_csv):
        with path.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    lines = [
        f"# 2500只学习分析股票池 - {meta['生成时间']}",
        "",
        f"- 实际数量：{meta['实际数量']}",
        f"- 基础保留：{meta['基础保留数量']}",
        f"- 扩展补充：{meta['扩展补充数量']}",
        f"- 覆盖行业数：{meta['覆盖行业数']}",
        f"- 覆盖市场：{meta['覆盖市场']}",
        "",
        "## 定位",
        "",
        "- 这是中信软件前台承载的大样本学习池，不是重点推荐池。",
        "- 它负责长期观察、方法验证、反馈沉淀和减少股票分析系统重复基础计算压力。",
        "- 深度分析火力仍集中在“杰哥的重点分析股票池”。",
        "",
        "## 扩展原则",
        "",
    ]
    lines.extend([f"- {item}" for item in meta["扩展原则"]])
    lines.extend(["", "## 行业分布TOP20", ""])
    lines.extend([f"- {item['行业']}：{item['数量']}只" for item in meta["行业分布TOP20"]])
    latest_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(latest_json), "csv": str(latest_csv), "说明": str(latest_md)}


def main() -> int:
    rows, meta = build_learning_pool()
    if len(rows) != TARGET_SIZE:
        raise RuntimeError(f"2500学习池生成数量异常：{len(rows)}")
    outputs = write_outputs(rows, meta)
    print(json.dumps({"状态": "完成", "数量": len(rows), "覆盖行业数": meta["覆盖行业数"], "输出": outputs}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
