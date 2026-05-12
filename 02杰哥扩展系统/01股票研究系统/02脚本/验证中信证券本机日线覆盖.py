# -*- coding: utf-8 -*-
"""
名称：验证中信证券本机日线覆盖.py
作用：扫描券商本机原始日线补充库，生成覆盖率、市场分布和缺口报告。
边界：只读本地补充库；不联网；不登录；不交易；不修改中信证券软件目录。
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
        if suffix in {"sh", "sz", "bj"}:
            return f"{suffix}{num.zfill(6)}"
    if text.isdigit():
        text = text.zfill(6)
        if text.startswith(("4", "8", "920")):
            return f"bj{text}"
        if text.startswith(("6", "9")):
            return f"sh{text}"
        return f"sz{text}"
    return text


def market_of(code: str) -> str:
    if code.startswith("bj"):
        return "北交所"
    if code.startswith("sh"):
        return "上交所"
    return "深交所"


def stock_file(base_dir: Path, code: str) -> Path:
    norm = normalize_code(code)
    market = "bj" if norm.startswith("bj") else "sh" if norm.startswith("sh") else "sz"
    return base_dir / "按股票" / market / f"{norm}.json"


def next_missing(stocks: list[dict[str, Any]], base_dir: Path, prefix: str, limit: int = 8) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, stock in enumerate(stocks):
        code = normalize_code(stock.get("代码"))
        if prefix and not code.startswith(prefix):
            continue
        if not stock_file(base_dir, code).exists():
            result.append({
                "全A序号": index,
                "代码": code,
                "名称": stock.get("名称", ""),
                "市场": stock.get("市场", "") or market_of(code),
            })
        if len(result) >= limit:
            break
    return result


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 中信证券本机日线覆盖进度",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 全A基础池数量：{report['全A基础池数量']}",
        f"- 已入库数量：{report['已入库数量']}",
        f"- 覆盖率：{report['覆盖率']}%",
        f"- 问题数量：{len(report['问题'])}",
        "",
        "## 市场覆盖",
        "",
    ]
    for market, counts in report["市场覆盖"].items():
        lines.append(f"- {market}：{counts['已入库']}/{counts['应入库']}")
    lines.extend(["", "## 下一批建议", ""])
    for group, rows in report["下一批建议"].items():
        if not rows:
            lines.append(f"- {group}：无")
            continue
        summary = "、".join(f"{row['全A序号']} {row['代码']} {row['名称']}" for row in rows)
        lines.append(f"- {group}：{summary}")
    lines.extend(["", "## 问题", ""])
    if report["问题"]:
        for item in report["问题"][:50]:
            lines.append(f"- {item}")
    else:
        lines.append("- 无")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    full_a_path = root / "03数据" / "01股票池" / "全A基础股票池_最新.json"
    official_path = root / "03数据" / "01股票池" / "全A基础池官方校验_最新.json"
    base_dir = root / "03数据" / "013券商本机历史日线" / "中信证券"
    full_a = load_json(full_a_path)
    official = load_json(official_path)
    stocks = list(full_a.get("股票池", []))

    issues: list[str] = []
    if official.get("结论") != "通过":
        issues.append("全A基础池官方校验未通过")

    market_total: dict[str, int] = {}
    market_done: dict[str, int] = {}
    done = 0
    bad_samples: list[dict[str, Any]] = []
    for stock in stocks:
        code = normalize_code(stock.get("代码"))
        market = stock.get("市场", "") or market_of(code)
        market_total[market] = market_total.get(market, 0) + 1
        path = stock_file(base_dir, code)
        if not path.exists():
            continue
        try:
            data = load_json(path)
            rows = data.get("日线", [])
            if not rows:
                raise RuntimeError("日线为空")
            if data.get("复权") != "不复权原始价":
                raise RuntimeError("复权口径不是不复权原始价")
        except Exception as exc:  # noqa: BLE001
            bad_samples.append({"代码": code, "名称": stock.get("名称", ""), "问题": str(exc)})
            continue
        done += 1
        market_done[market] = market_done.get(market, 0) + 1

    if bad_samples:
        issues.append(f"存在需复核文件：{len(bad_samples)}")
    coverage = round(done / len(stocks) * 100, 4) if stocks else 0.0
    market_coverage = {
        market: {"应入库": total, "已入库": market_done.get(market, 0)}
        for market, total in sorted(market_total.items(), key=lambda kv: kv[0])
    }
    report = {
        "名称": "中信证券本机日线覆盖进度",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not issues else "需复核",
        "全A基础池数量": len(stocks),
        "已入库数量": done,
        "覆盖率": coverage,
        "市场覆盖": market_coverage,
        "下一批建议": {
            "全市场下一批缺口": next_missing(stocks, base_dir, "", 8),
            "深交所下一批缺口": next_missing(stocks, base_dir, "sz", 8),
            "上交所下一批缺口": next_missing(stocks, base_dir, "sh", 8),
            "北交所下一批缺口": next_missing(stocks, base_dir, "bj", 8),
        },
        "问题": issues,
        "问题样本": bad_samples[:100],
        "输入": {
            "全A基础股票池": str(full_a_path),
            "全A基础池官方校验": str(official_path),
            "中信本机补充库": str(base_dir),
        },
        "安全边界": {
            "是否联网": False,
            "是否登录券商": False,
            "是否调用券商接口": False,
            "是否修改中信目录": False,
            "是否交易": False,
        },
    }
    json_path = base_dir / "中信证券本机日线覆盖进度_最新.json"
    md_path = base_dir / "中信证券本机日线覆盖进度_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "全A基础池数量": len(stocks),
        "已入库数量": done,
        "覆盖率": coverage,
        "报告": str(md_path),
        "数据": str(json_path),
    }, ensure_ascii=False))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
