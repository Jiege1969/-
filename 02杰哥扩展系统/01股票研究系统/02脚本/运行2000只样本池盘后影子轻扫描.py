# -*- coding: utf-8 -*-
"""
名称：运行2000只样本池盘后影子轻扫描.py
作用：对2000只样本池做盘后影子轻扫描，输出技术代理评分和分层结果，暂不接入正式报告。
安全边界：只读2000只样本池，只写03数据/2000只影子扫描；不调用大模型；不触发n8n；不发送企业微信；不接券商；不交易。
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def load_previous_scores(out_dir: Path) -> dict[str, float]:
    latest = out_dir / "2000只样本池盘后影子轻扫描_最新.json"
    data = load_json(latest, {})
    rows = data.get("股票", []) if isinstance(data, dict) and isinstance(data.get("股票"), list) else []
    return {str(item.get("代码")): safe_float(item.get("影子评分")) for item in rows if isinstance(item, dict)}


def score_stock(item: dict[str, Any], previous_scores: dict[str, float]) -> dict[str, Any]:
    code = str(item.get("代码", ""))
    amount = safe_float(item.get("最新成交额"))
    market_value = safe_float(item.get("市值"))
    index_weight = safe_float(item.get("中证全指权重"))
    turnover_proxy = amount / market_value if amount > 0 and market_value > 0 else 0.0
    liquidity_score = min(math.log10(amount + 1) * 7, 45) if amount > 0 else 0.0
    size_score = min(math.log10(market_value + 1) * 2, 25) if market_value > 0 else 0.0
    weight_score = min(index_weight * 8, 20)
    turnover_score = min(turnover_proxy * 10000, 20)
    score = round(liquidity_score + size_score + weight_score + turnover_score, 4)
    previous = previous_scores.get(code)
    score_delta = round(score - previous, 4) if previous is not None else None
    strong_signal = bool(score >= 100 or turnover_proxy >= 0.08 or (score_delta is not None and score_delta >= 8))
    layer = "A强势影子候选" if strong_signal else ("B活跃观察" if score >= 90 or turnover_proxy >= 0.04 else "C基础样本")
    return {
        "代码": code,
        "展示代码": item.get("展示代码", ""),
        "名称": item.get("名称", ""),
        "行业": item.get("行业", ""),
        "市场": item.get("市场", ""),
        "市值": market_value,
        "最新成交额": amount,
        "中证全指权重": index_weight,
        "成交额市值比": round(turnover_proxy, 6),
        "影子评分": score,
        "上次影子评分": previous,
        "评分变化": score_delta,
        "影子分层": layer,
        "强势信号": strong_signal,
        "入300池建议": "建议进入300只试运行池活水入口" if strong_signal else "暂不进入300池",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 2000只样本池盘后影子轻扫描 - {report['生成时间']}",
        "",
        f"- 样本数量：{report['样本数量']}",
        f"- 强势信号数量：{report['强势信号数量']}",
        f"- 输出口径：{report['输出口径']}",
        "",
        "| 排名 | 股票 | 行业 | 影子评分 | 评分变化 | 分层 | 建议 |",
        "| ---: | --- | --- | ---: | ---: | --- | --- |",
    ]
    for index, item in enumerate(report["股票"][:50], start=1):
        delta = "" if item.get("评分变化") is None else item.get("评分变化")
        lines.append(f"| {index} | {item.get('名称')}（{item.get('展示代码') or item.get('代码')}） | {item.get('行业')} | {item.get('影子评分')} | {delta} | {item.get('影子分层')} | {item.get('入300池建议')} |")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 未调用大模型。",
        "- 未触发n8n，未发送企业微信，未接券商，未交易。",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    pool_path = root / "03数据" / "01股票池" / "2000只样本股票池_最新.json"
    out_dir = root / "03数据" / "2000只影子扫描"
    pool = load_json(pool_path, {})
    stocks = pool.get("股票列表", []) if isinstance(pool, dict) and isinstance(pool.get("股票列表"), list) else []
    previous_scores = load_previous_scores(out_dir)
    rows = [score_stock(item, previous_scores) for item in stocks if isinstance(item, dict)]
    rows.sort(key=lambda item: (item["强势信号"], item["评分变化"] if item["评分变化"] is not None else -999, item["影子评分"]), reverse=True)
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    report = {
        "名称": "2000只样本池盘后影子轻扫描",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "输入": str(pool_path),
        "样本数量": len(rows),
        "强势信号数量": sum(1 for item in rows if item["强势信号"]),
        "输出口径": "影子扫描，不接入正式报告；无大模型；使用样本池日线可得字段形成技术代理评分。",
        "股票": rows,
        "安全边界": {
            "是否调用大模型": False,
            "是否触发n8n": False,
            "是否真实发送企业微信": False,
            "是否接券商": False,
            "是否交易": False,
        },
    }
    output_json = out_dir / f"2000只样本池盘后影子轻扫描_{stamp}.json"
    output_md = out_dir / f"2000只样本池盘后影子轻扫描_{stamp}.md"
    latest_json = out_dir / "2000只样本池盘后影子轻扫描_最新.json"
    latest_md = out_dir / "2000只样本池盘后影子轻扫描_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"样本数量": len(rows), "强势信号数量": report["强势信号数量"], "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
