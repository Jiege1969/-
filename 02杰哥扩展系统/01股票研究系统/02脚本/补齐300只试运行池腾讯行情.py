# -*- coding: utf-8 -*-
"""
名称：补齐300只试运行池腾讯行情.py
作用：用腾讯公开行情接口只读补齐300只试运行池的现价、涨跌幅、成交额、市值等轻扫描字段。
触发方式：python 补齐300只试运行池腾讯行情.py
依赖：Python标准库；300只试运行池_最新.json；腾讯公开行情接口qt.gtimg.cn。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读公开行情并写入股票模块03数据目录；不覆盖原始试运行池；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建腾讯行情补齐脚本。
标识：stock-trial-pool-300-tencent-quote-enrich
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
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


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[index:index + size] for index in range(0, len(items), size)]


def fetch_tencent_quotes(codes: list[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    quotes: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for group in chunked(codes, 60):
        query = ",".join(group)
        url = "https://qt.gtimg.cn/q=" + urllib.parse.quote(query, safe=",")
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                text = response.read().decode("gbk", errors="replace")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{group[0]}-{group[-1]}: {exc}")
            continue
        for match in re.finditer(r'v_([a-z]{2}\d{6})="([^"]*)";', text):
            code = match.group(1)
            fields = match.group(2).split("~")
            if len(fields) < 56 or safe_float(fields[3]) <= 0:
                continue
            amount_wan = safe_float(fields[37])
            quotes[code] = {
                "名称": fields[1],
                "现价": safe_float(fields[3]),
                "昨收": safe_float(fields[4]),
                "开盘": safe_float(fields[5]),
                "最高": safe_float(fields[33]),
                "最低": safe_float(fields[34]),
                "涨跌额": safe_float(fields[31]),
                "涨跌幅": safe_float(fields[32]),
                "成交量": safe_float(fields[36]),
                "成交额": round(amount_wan * 10000, 2),
                "成交额万元": amount_wan,
                "换手率": safe_float(fields[38]),
                "流通市值": round(safe_float(fields[44]) * 100000000, 2),
                "总市值": round(safe_float(fields[45]) * 100000000, 2),
                "市盈率": safe_float(fields[39]),
                "行情时间": fields[30],
                "行情来源": "腾讯公开行情",
            }
        time.sleep(0.05)
    return quotes, errors


def main() -> int:
    root = module_root()
    source = root / "03数据" / "91试运行池" / "300只试运行池_最新.json"
    pool = load_json(source)
    stocks = pool.get("股票池", [])
    codes = [str(stock.get("代码", "")).strip() for stock in stocks if str(stock.get("代码", "")).strip()]
    quotes, errors = fetch_tencent_quotes(codes)

    enriched: list[dict[str, Any]] = []
    for stock in stocks:
        code = str(stock.get("代码", "")).strip()
        quote = quotes.get(code)
        if quote:
            merged = {**stock, **quote}
            merged["行情补齐状态"] = "成功"
        else:
            merged = dict(stock)
            merged["行情补齐状态"] = "失败"
        enriched.append(merged)

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "输入文件": str(source),
        "行情来源": "腾讯公开行情",
        "股票数量": len(stocks),
        "补齐成功数量": len(quotes),
        "补齐失败数量": max(len(stocks) - len(quotes), 0),
        "失败批次": errors,
        "股票池": enriched,
        "安全边界": {
            "触发n8n": False,
            "企业微信真实发送": False,
            "写正式库": False,
            "写旧系统": False,
            "调用券商接口": False,
            "自动交易": False,
            "重启服务": False,
            "覆盖原始试运行池": False
        },
    }
    output_dir = root / "03数据" / "91试运行池"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"300只试运行池_行情补齐_{stamp}.json"
    latest = output_dir / "300只试运行池_行情补齐_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"股票数量": len(stocks), "补齐成功": len(quotes), "输出": str(output)}, ensure_ascii=False))
    return 0 if len(quotes) >= min(5, len(stocks)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
