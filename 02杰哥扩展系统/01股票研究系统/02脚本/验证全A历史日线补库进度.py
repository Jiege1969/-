# -*- coding: utf-8 -*-
"""
名称：验证全A历史日线补库进度.py
作用：扫描全A历史日线按股票文件，生成补库覆盖率、市场覆盖和数据源降级情况。
边界：只读本地历史日线文件并写进度报告；不联网；不触发n8n；不发送企业微信；不接券商；不交易。
"""

from __future__ import annotations

import json
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


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        suffix = suffix.lower()
        if suffix == "sh":
            return f"sh{num.zfill(6)}"
        if suffix == "sz":
            return f"sz{num.zfill(6)}"
        if suffix == "bj":
            return f"bj{num.zfill(6)}"
    if text.isdigit():
        text = text.zfill(6)
        if text.startswith(("4", "8", "920")):
            return f"bj{text}"
        if text.startswith(("6", "9")):
            return f"sh{text}"
        return f"sz{text}"
    return text


def compact_date(value: Any) -> str:
    return str(value or "").replace("-", "")[:8]


def stock_file(base_dir: Path, code: str) -> Path:
    norm = normalize_code(code)
    market = "bj" if norm.startswith("bj") else "sh" if norm.startswith("sh") else "sz"
    return base_dir / "按股票" / market / f"{norm}.json"


def market_count(rows: list[dict[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        market = str(row.get("市场") or "未知")
        result[market] = result.get(market, 0) + 1
    return dict(sorted(result.items(), key=lambda kv: (-kv[1], kv[0])))


def next_missing(stocks: list[dict[str, Any]], output_dir: Path, market_prefix: str = "", limit: int = 5) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for index, stock in enumerate(stocks):
        code = normalize_code(stock.get("代码"))
        if market_prefix and not code.startswith(market_prefix):
            continue
        if not stock_file(output_dir, code).exists():
            missing.append({
                "全A序号": index,
                "代码": code,
                "名称": stock.get("名称", ""),
                "市场": stock.get("市场", ""),
            })
        if len(missing) >= limit:
            break
    return missing


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 全A历史日线补库进度",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 全A基础池数量：{report['全A基础池数量']}",
        f"- 已补库数量：{report['已补库数量']}",
        f"- 覆盖率：{report['覆盖率']}%",
        f"- 问题数量：{len(report['问题'])}",
        "",
        "## 市场覆盖",
        "",
    ]
    for market, counts in report["市场覆盖"].items():
        lines.append(f"- {market}：{counts['已补库']}/{counts['应补库']}")
    lines.extend(["", "## 数据源统计", ""])
    for source, count in report["数据源统计"].items():
        lines.append(f"- {source}：{count}")
    lines.extend(["", "## 问题", ""])
    if report["问题"]:
        for item in report["问题"][:50]:
            lines.append(f"- {item}")
    else:
        lines.append("- 无")
    lines.extend(["", "## 下一批建议", ""])
    for group, rows in report.get("下一批建议", {}).items():
        if not rows:
            lines.append(f"- {group}：无")
            continue
        summary = "、".join(
            f"{row.get('全A序号')} {row.get('代码')} {row.get('名称')}"
            for row in rows
        )
        lines.append(f"- {group}：{summary}")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    full_a_path = root / "03数据" / "01股票池" / "全A基础股票池_最新.json"
    official_path = root / "03数据" / "01股票池" / "全A基础池官方校验_最新.json"
    output_dir = root / "03数据" / "012全A历史日线"
    full_a = load_json(full_a_path)
    official = load_json(official_path)
    stocks = list(full_a.get("股票池", []))

    issues: list[str] = []
    if official.get("结论") != "通过":
        issues.append("全A基础池官方校验未通过，历史补库进度无效。")

    source_counts: dict[str, int] = {}
    market_total = market_count(stocks)
    market_done = {market: 0 for market in market_total}
    done = 0
    stale_or_bad: list[dict[str, Any]] = []

    for stock in stocks:
        code = normalize_code(stock.get("代码"))
        path = stock_file(output_dir, code)
        if not path.exists():
            continue
        try:
            data = load_json(path)
        except Exception as exc:  # noqa: BLE001
            stale_or_bad.append({"代码": code, "名称": stock.get("名称", ""), "问题": f"文件不可读:{exc}"})
            continue
        rows = data.get("日线", [])
        if not rows:
            stale_or_bad.append({"代码": code, "名称": stock.get("名称", ""), "问题": "日线为空"})
            continue
        today = datetime.now().strftime("%Y%m%d")
        if compact_date(rows[-1].get("日期")) >= today:
            stale_or_bad.append({"代码": code, "名称": stock.get("名称", ""), "问题": "末日包含当天盘中未完结日线"})
            continue
        done += 1
        market = str(stock.get("市场") or "未知")
        market_done[market] = market_done.get(market, 0) + 1
        source = str(data.get("数据源") or "未知")
        source_counts[source] = source_counts.get(source, 0) + 1
        if any(row.get("成交额是否估算") is True for row in rows):
            stale_or_bad.append({"代码": code, "名称": stock.get("名称", ""), "问题": "成交额为估算兜底"})

    market_coverage = {
        market: {"应补库": total, "已补库": market_done.get(market, 0)}
        for market, total in market_total.items()
    }
    next_suggestions = {
        "全市场下一批缺口": next_missing(stocks, output_dir, "", 5),
        "深交所下一批缺口": next_missing(stocks, output_dir, "sz", 5),
        "上交所下一批缺口": next_missing(stocks, output_dir, "sh", 5),
        "北交所下一批缺口": next_missing(stocks, output_dir, "bj", 5),
    }
    coverage = round(done / len(stocks) * 100, 4) if stocks else 0.0
    if stale_or_bad:
        issues.append(f"存在需复核历史日线文件：{len(stale_or_bad)}")

    report = {
        "名称": "全A历史日线补库进度",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not issues else "需复核",
        "全A基础池数量": len(stocks),
        "已补库数量": done,
        "覆盖率": coverage,
        "市场覆盖": market_coverage,
        "数据源统计": dict(sorted(source_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "问题": issues,
        "问题样本": stale_or_bad[:100],
        "下一批建议": next_suggestions,
        "输入": {
            "全A基础股票池": str(full_a_path),
            "全A基础池官方校验": str(official_path),
            "历史日线目录": str(output_dir / "按股票"),
        },
        "安全边界": {
            "是否联网": False,
            "是否触发n8n": False,
            "是否真实发送企业微信": False,
            "是否接券商": False,
            "是否交易": False,
        },
    }
    json_path = output_dir / "全A历史日线补库进度_最新.json"
    md_path = output_dir / "全A历史日线补库进度_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "全A基础池数量": len(stocks),
        "已补库数量": done,
        "覆盖率": coverage,
        "报告": str(md_path),
        "数据": str(json_path),
    }, ensure_ascii=False))
    return 0 if official.get("结论") == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
