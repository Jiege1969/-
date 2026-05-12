# -*- coding: utf-8 -*-
"""
名称：生成全A基础数据库统一索引.py
作用：汇总全A股票池、官方校验、券商本机原始日线、正式历史日线和多源比对状态。
边界：只读本地数据和配置；只写索引报告；不联网；不调用券商接口；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "01配置"
DATA = ROOT / "03数据"
OUT_DIR = DATA / "016全A基础数据库索引"


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
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


def file_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"存在": False}
    stat = path.stat()
    return {
        "存在": True,
        "路径": str(path),
        "大小": stat.st_size,
        "更新时间": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
    }


def count_local_files(base: Path) -> dict[str, Any]:
    result = {"总数": 0, "sh": 0, "sz": 0, "bj": 0}
    for market in ("sh", "sz", "bj"):
        count = len(list((base / "按股票" / market).glob("*.json"))) if (base / "按股票" / market).exists() else 0
        result[market] = count
        result["总数"] += count
    return result


def build_stock_index(stocks: list[dict[str, Any]], citic_base: Path, formal_base: Path, limit: int = 100) -> list[dict[str, Any]]:
    rows = []
    for stock in stocks[:limit]:
        code = normalize_code(stock.get("代码"))
        rows.append({
            "代码": code,
            "展示代码": stock.get("展示代码", ""),
            "名称": stock.get("名称", ""),
            "市场": stock.get("市场", ""),
            "板块": stock.get("板块", ""),
            "行业": stock.get("行业", ""),
            "中信原始日线": stock_file(citic_base, code).exists(),
            "正式前复权日线": stock_file(formal_base, code).exists(),
        })
    return rows


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 全A基础数据库统一索引",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 全A股票数量：{report['全A股票池']['股票数量']}",
        f"- 官方校验：{report['官方校验']['结论']}",
        "",
        "## 数据资产状态",
        "",
        f"- 中信本机原始日线：{report['中信本机原始日线']['文件覆盖']['总数']} / {report['全A股票池']['股票数量']}，口径：不复权原始价",
        f"- 正式前复权日线：{report['正式前复权日线']['文件覆盖']['总数']} / {report['全A股票池']['股票数量']}，口径：前复权为主",
        f"- 多源比对：{report['多源比对'].get('结论', '缺失')}，可比对 {report['多源比对'].get('可比对数量', 0)} 只，问题 {len(report['多源比对'].get('问题', []))} 个",
        "",
        "## 市场分布",
        "",
    ]
    for market, count in report["全A股票池"]["市场分布"].items():
        lines.append(f"- {market}：{count}")
    lines.extend(["", "## 使用原则", ""])
    for item in report["使用原则"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    full_a_path = DATA / "01股票池" / "全A基础股票池_最新.json"
    official_path = DATA / "01股票池" / "全A基础池官方校验_最新.json"
    registry_path = CONFIG / "股票数据源注册表.json"
    citic_base = DATA / "013券商本机历史日线" / "中信证券"
    formal_base = DATA / "012全A历史日线"
    compare_path = DATA / "014历史日线多源比对" / "正式历史库_vs_中信本机库比对_最新.json"
    citic_coverage_path = citic_base / "中信证券本机日线覆盖进度_最新.json"
    formal_progress_path = formal_base / "全A历史日线补库进度_最新.json"

    full_a = read_json(full_a_path, {})
    official = read_json(official_path, {})
    registry = read_json(registry_path, {})
    compare = read_json(compare_path, {})
    citic_coverage = read_json(citic_coverage_path, {})
    formal_progress = read_json(formal_progress_path, {})
    stocks = list(full_a.get("股票池", []))

    market_counts: dict[str, int] = {}
    for stock in stocks:
        market = stock.get("市场", "未知")
        market_counts[market] = market_counts.get(market, 0) + 1

    issues: list[str] = []
    if official.get("结论") != "通过":
        issues.append("全A官方校验未通过")
    if count_local_files(citic_base)["总数"] != len(stocks):
        issues.append("中信本机原始日线未全量覆盖")
    if compare.get("问题"):
        issues.append("历史日线多源比对存在问题")

    report = {
        "名称": "全A基础数据库统一索引",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not issues else "需复核",
        "问题": issues,
        "全A股票池": {
            "文件": file_summary(full_a_path),
            "股票数量": len(stocks),
            "市场分布": dict(sorted(market_counts.items(), key=lambda kv: kv[0])),
        },
        "官方校验": {
            "文件": file_summary(official_path),
            "结论": official.get("结论", "缺失"),
            "缺失数量": official.get("缺失数量", official.get("统计", {}).get("缺失数量")),
            "多余数量": official.get("多余数量", official.get("统计", {}).get("多余数量")),
        },
        "数据源注册表": {
            "文件": file_summary(registry_path),
            "数据源数量": len(registry.get("数据源", [])),
        },
        "中信本机原始日线": {
            "目录": str(citic_base),
            "文件覆盖": count_local_files(citic_base),
            "覆盖报告": citic_coverage,
            "口径": "不复权原始价",
        },
        "正式前复权日线": {
            "目录": str(formal_base),
            "文件覆盖": count_local_files(formal_base),
            "进度报告": formal_progress,
            "口径": "前复权为主",
        },
        "多源比对": compare,
        "样本索引": build_stock_index(stocks, citic_base, formal_base, 100),
        "使用原则": [
            "全A基础股票池是股票范围基准，必须以官方交易所名单校验通过为前置。",
            "中信本机原始日线用于快速建库、补缺和校验，价格口径为不复权原始价。",
            "正式前复权日线用于技术指标和推荐模型默认分析，不得与不复权价格直接混算。",
            "盘中数据只进入观察，不进入正式历史底座；盘后完整日线才进入正式分析。",
            "多源差异先标记待复核，不自动覆盖。"
        ],
        "安全边界": {
            "是否联网": False,
            "是否调用券商接口": False,
            "是否修改中信目录": False,
            "是否自动交易": False,
            "是否发送企业微信": False,
        },
    }
    json_path = OUT_DIR / "全A基础数据库统一索引_最新.json"
    md_path = OUT_DIR / "全A基础数据库统一索引_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "全A股票数量": len(stocks),
        "中信原始日线覆盖": report["中信本机原始日线"]["文件覆盖"]["总数"],
        "正式日线覆盖": report["正式前复权日线"]["文件覆盖"]["总数"],
        "问题数量": len(issues),
        "报告": str(md_path),
        "数据": str(json_path),
    }, ensure_ascii=False))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
