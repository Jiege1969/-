# -*- coding: utf-8 -*-
"""
名称：比对全A历史日线_正式库_vs_中信本机.py
作用：比对正式历史日线库与中信证券本机原始日线库的覆盖、共同日期成交字段和口径差异。
边界：只读两个本地数据目录；不联网；不触发外部系统；不交易。
说明：正式库多为前复权，中信库为不复权原始价，默认不比较价格。
      末日不一致和成交额差异常由源头更新节奏、复权口径造成，归为警告；
      缺库、空日线、无共同日期、共同日期成交量明显不一致才归为硬问题。
"""

from __future__ import annotations

import argparse
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


def market_dir(code: str) -> str:
    if code.startswith("bj"):
        return "bj"
    if code.startswith("sh"):
        return "sh"
    return "sz"


def stock_file(base: Path, code: str) -> Path:
    norm = normalize_code(code)
    return base / "按股票" / market_dir(norm) / f"{norm}.json"


def compact_date(value: Any) -> str:
    return str(value or "").replace("-", "")[:8]


def row_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {compact_date(row.get("日期")): row for row in rows if compact_date(row.get("日期"))}


def to_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-", "--"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def relative_diff(a: Any, b: Any) -> float | None:
    af = to_float(a)
    bf = to_float(b)
    if af is None or bf is None:
        return None
    denom = max(abs(af), abs(bf), 1.0)
    return round(abs(af - bf) / denom, 6)


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 正式历史库 vs 中信本机库比对报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 抽样/扫描数量：{report['扫描数量']}",
        f"- 正式库存在：{report['正式库存在数量']}",
        f"- 中信库存在：{report['中信库存在数量']}",
        f"- 可比对数量：{report['可比对数量']}",
        f"- 硬问题数量：{report['问题数量']}",
        f"- 警告数量：{report['警告数量']}",
        "",
        "## 口径",
        "",
        "- 正式库多为前复权价格，中信本机库是不复权原始价，因此本报告不比较价格。",
        "- 本报告重点比较覆盖、共同日期成交量，用于发现缺口和明显异常。",
        "- 正式库与中信库末日不同，通常代表源头更新节奏不同，先记警告，不直接判失败。",
        "- 成交额受复权口径影响较大，先记警告；后续以官方正式库作为分析主库。",
        "",
        "## 硬问题样本",
        "",
    ]
    if report["问题"]:
        for item in report["问题"][:80]:
            lines.append(f"- {item}")
    else:
        lines.append("- 无")
    lines.extend(["", "## 警告样本", ""])
    if report["警告"]:
        for item in report["警告"][:80]:
            lines.append(f"- {item}")
    else:
        lines.append("- 无")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="比对正式历史库与中信本机原始库")
    parser.add_argument("--limit", type=int, default=0, help="抽样数量；0表示全量")
    parser.add_argument("--amount-tolerance", type=float, default=0.08, help="成交额相对差异容忍度")
    parser.add_argument("--volume-tolerance", type=float, default=0.03, help="成交量相对差异容忍度")
    args = parser.parse_args()

    root = module_root()
    full_a_path = root / "03数据" / "01股票池" / "全A基础股票池_最新.json"
    formal_base = root / "03数据" / "012全A历史日线"
    citic_base = root / "03数据" / "013券商本机历史日线" / "中信证券"
    output_dir = root / "03数据" / "014历史日线多源比对"
    stocks = list(load_json(full_a_path).get("股票池", []))
    targets = stocks[:args.limit] if args.limit and args.limit > 0 else stocks

    issues: list[str] = []
    warnings: list[str] = []
    formal_exists = 0
    citic_exists = 0
    comparable = 0
    for stock in targets:
        code = normalize_code(stock.get("代码"))
        name = stock.get("名称", "")
        formal_path = stock_file(formal_base, code)
        citic_path = stock_file(citic_base, code)
        if formal_path.exists():
            formal_exists += 1
        else:
            continue
        if citic_path.exists():
            citic_exists += 1
        else:
            issues.append(f"{code} {name}：正式库存在，但中信本机库缺失")
            continue
        formal_data = load_json(formal_path)
        citic_data = load_json(citic_path)
        formal_rows = formal_data.get("日线", [])
        citic_rows = citic_data.get("日线", [])
        if not formal_rows or not citic_rows:
            issues.append(f"{code} {name}：存在空日线")
            continue
        comparable += 1
        formal_last = compact_date(formal_rows[-1].get("日期"))
        citic_last = compact_date(citic_rows[-1].get("日期"))
        if formal_last != citic_last:
            warnings.append(f"{code} {name}：末日不一致，正式库{formal_last}，中信库{citic_last}，按共同日期继续比对")
        shared_dates = sorted(set(row_map(formal_rows)).intersection(row_map(citic_rows)))
        if not shared_dates:
            issues.append(f"{code} {name}：无共同日期可比对")
            continue
        check_date = shared_dates[-1]
        f_row = row_map(formal_rows)[check_date]
        c_row = row_map(citic_rows)[check_date]
        volume_diff = relative_diff(f_row.get("成交量"), c_row.get("成交量"))
        amount_diff = relative_diff(f_row.get("成交额"), c_row.get("成交额"))
        if volume_diff is not None and volume_diff > args.volume_tolerance:
            issues.append(f"{code} {name}：{check_date}成交量差异{volume_diff}，正式{f_row.get('成交量')}，中信{c_row.get('成交量')}")
        if amount_diff is not None and amount_diff > args.amount_tolerance:
            warnings.append(f"{code} {name}：{check_date}成交额差异{amount_diff}，正式{f_row.get('成交额')}，中信{c_row.get('成交额')}，疑似复权/源头口径差异")

    report = {
        "名称": "正式历史库 vs 中信本机库比对报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not issues else "需复核",
        "扫描数量": len(targets),
        "正式库存在数量": formal_exists,
        "中信库存在数量": citic_exists,
        "可比对数量": comparable,
        "成交额容忍度": args.amount_tolerance,
        "成交量容忍度": args.volume_tolerance,
        "问题数量": len(issues),
        "警告数量": len(warnings),
        "问题": issues[:500],
        "警告": warnings[:500],
        "输入": {
            "全A基础股票池": str(full_a_path),
            "正式历史库": str(formal_base),
            "中信本机库": str(citic_base),
        },
        "安全边界": {
            "是否联网": False,
            "是否登录券商": False,
            "是否调用券商接口": False,
            "是否修改中信目录": False,
            "是否交易": False,
        },
    }
    json_path = output_dir / "正式历史库_vs_中信本机库比对_最新.json"
    md_path = output_dir / "正式历史库_vs_中信本机库比对_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "扫描数量": len(targets),
        "正式库存在数量": formal_exists,
        "中信库存在数量": citic_exists,
        "可比对数量": comparable,
        "问题数量": report["问题数量"],
        "警告数量": report["警告数量"],
        "报告": str(md_path),
        "数据": str(json_path),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
