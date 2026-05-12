# -*- coding: utf-8 -*-
"""
名称：运行300只试运行池盘后轻扫描.py
作用：读取300只试运行池，生成盘后轻扫描候选清单和数据健康度说明。
触发方式：python 运行300只试运行池盘后轻扫描.py
依赖：Python标准库；300只试运行池盘后轻扫描规则.json；300只试运行池_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读试运行池并写入股票模块03数据目录；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只试运行池盘后轻扫描脚本。
标识：stock-trial-pool-300-after-market-scan
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def has_real_quote(stock: dict[str, Any]) -> bool:
    return safe_float(stock.get("现价")) > 0 and safe_float(stock.get("成交额")) > 0


def log_score(value: Any, factor: float, cap: float) -> float:
    number = max(safe_float(value), 0.0)
    if number <= 0:
        return 0.0
    return min(math.log10(number + 1) * factor, cap)


def score_stock(stock: dict[str, Any], rule: dict[str, Any], pool_health: str) -> tuple[float, list[str], list[str]]:
    weights = rule.get("评分权重", {})
    score = safe_float(stock.get("评分")) * safe_float(weights.get("原始入池评分"), 0.45)
    reasons: list[str] = []
    risks: list[str] = []

    if "强制保留" in str(stock.get("入池原因", "")):
        score += safe_float(weights.get("重点关注池", 25))
        reasons.append("用户重点关注池强制保留，优先进入观察。")

    if has_real_quote(stock):
        score += safe_float(weights.get("真实行情字段完整", 10))
        reasons.append("具备现价和成交额字段，可进入轻量比较。")
    else:
        score += safe_float(weights.get("数据降级扣分", -15))
        risks.append("实时价格或成交额缺失，本轮只作为观察候选，不给强结论。")

    amount_score = log_score(stock.get("成交额"), 4.0, 20.0) * safe_float(weights.get("成交额"), 0.2)
    free_mv_score = log_score(stock.get("流通市值"), 3.0, 12.0) * safe_float(weights.get("流通市值"), 0.12)
    pct_score = min(abs(safe_float(stock.get("涨跌幅"))) * 2.0, 10.0) * safe_float(weights.get("涨跌幅活跃度"), 0.1)
    score += amount_score + free_mv_score + pct_score

    if amount_score > 0:
        reasons.append("成交额字段显示具备一定活跃度。")
    if free_mv_score > 0:
        reasons.append("流通市值字段具备样本代表性。")
    if pct_score > 0:
        reasons.append("涨跌幅活跃度进入观察范围。")
    if pool_health != "健康":
        risks.append(f"试运行池数据健康度为{pool_health}，后续深度分析前需要补齐行情源。")
    if not reasons:
        reasons.append("根据入池评分和样本覆盖要求进入候选观察。")

    return round(max(0.0, score), 4), reasons, risks


def evaluate_health(stocks: list[dict[str, Any]], rule: dict[str, Any]) -> dict[str, Any]:
    total = len(stocks)
    quote_ok = sum(1 for stock in stocks if has_real_quote(stock))
    ratio = quote_ok / total if total else 0.0
    if total <= 0:
        status = "失败"
    elif ratio >= 0.8:
        status = "健康"
    else:
        status = "降级"
    return {
        "状态": status,
        "股票数量": total,
        "真实行情字段完整数量": quote_ok,
        "真实行情字段完整比例": round(ratio, 4),
        "判定规则": rule.get("数据健康度规则", {}),
    }


def build_candidate(stock: dict[str, Any], score: float, reasons: list[str], risks: list[str]) -> dict[str, Any]:
    return {
        "代码": stock.get("代码"),
        "名称": stock.get("名称"),
        "市场": stock.get("市场"),
        "行业": stock.get("行业") or "未分类",
        "轻扫描评分": score,
        "入池原因": stock.get("入池原因"),
        "数据源": stock.get("来源"),
        "现价": stock.get("现价"),
        "涨跌幅": stock.get("涨跌幅"),
        "成交额": stock.get("成交额"),
        "流通市值": stock.get("流通市值"),
        "候选理由": reasons,
        "风险和降级说明": risks or ["未发现轻扫描层面的突出降级风险。"],
        "后续动作": "进入深度分析候选，不直接推送，不自动交易。",
    }


def build_markdown(report: dict[str, Any]) -> str:
    health = report["数据健康度"]
    lines = [
        "# 300只试运行池盘后轻扫描报告",
        "",
        f"生成时间：{report['生成时间']}",
        f"数据健康度：{health['状态']}，真实行情字段完整 {health['真实行情字段完整数量']}/{health['股票数量']}。",
        "",
        "说明：本报告用于盘后研究候选筛选，不构成投资建议，不触发企业微信真实推送，不自动交易。",
        "",
        "## 候选清单",
        "",
    ]
    for index, item in enumerate(report["候选清单"], start=1):
        reason = "；".join(item["候选理由"][:2])
        risk = "；".join(item["风险和降级说明"][:2])
        lines.append(f"{index}. {item['名称']}（{item['代码']}）：轻扫描评分 {item['轻扫描评分']}。")
        lines.append(f"   - 理由：{reason}")
        lines.append(f"   - 风险：{risk}")
    lines.extend(
        [
            "",
            "## 下一步",
            "",
            "- 对候选清单执行深度分析前，先补齐行情、技术指标、公告和财务数据。",
            "- 数据健康度为降级时，只允许形成观察清单，不允许生成强推荐结论。",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只试运行池盘后轻扫描规则.json"
    rule = load_json(rule_path)
    enriched_path = root / rule["输入"].get("行情补齐池", "")
    pool_path = enriched_path if enriched_path.exists() else root / rule["输入"]["试运行池"]
    pool = load_json(pool_path)
    stocks = pool.get("股票池", [])
    health = evaluate_health(stocks, rule)

    scored: list[dict[str, Any]] = []
    for stock in stocks:
        score, reasons, risks = score_stock(stock, rule, health["状态"])
        scored.append(build_candidate(stock, score, reasons, risks))

    selected: list[dict[str, Any]] = []
    industry_count: dict[str, int] = {}
    min_count = int(rule.get("候选数量", {}).get("最少", 5))
    max_count = int(rule.get("候选数量", {}).get("最多", 10))
    for item in sorted(scored, key=lambda row: row["轻扫描评分"], reverse=True):
        if len(selected) >= max_count:
            break
        industry = item.get("行业") or "未分类"
        if industry_count.get(industry, 0) >= 3 and len(selected) >= min_count:
            continue
        selected.append(item)
        industry_count[industry] = industry_count.get(industry, 0) + 1

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": str(pool_path),
        "数据健康度": health,
        "候选清单": selected,
        "候选数量": len(selected),
        "安全边界": rule.get("安全边界", {}),
        "实际动作": {
            "触发n8n": False,
            "企业微信真实发送": False,
            "写正式库": False,
            "写旧系统": False,
            "调用券商接口": False,
            "自动交易": False,
            "重启服务": False,
        },
    }

    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"300只试运行池盘后轻扫描_{stamp}.json"
    latest = output_dir / rule["输出"]["最新文件"]
    markdown = output_dir / f"300只试运行池盘后轻扫描报告_{stamp}.md"
    markdown_latest = output_dir / rule["输出"]["报告文件"]
    write_json(output, report)
    write_json(latest, report)
    text = build_markdown(report)
    write_text(markdown, text)
    write_text(markdown_latest, text)
    print(json.dumps({"候选数量": len(selected), "数据健康度": health["状态"], "输出": str(output)}, ensure_ascii=False))
    return 0 if len(selected) >= min_count and health["状态"] != "失败" else 1


if __name__ == "__main__":
    raise SystemExit(main())
