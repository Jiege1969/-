# -*- coding: utf-8 -*-
"""
名称：更新L3市场风格日表_东方财富只读.py
作用：只读东方财富公开行情、板块和指数数据，生成L3市场风格日表。
触发方式：python 更新L3市场风格日表_东方财富只读.py
安全边界：只读公开数据；只写03数据/245L3评分基础资产；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
import math
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


UT = "bd1d9ddb04089700cf9c27f6f7426281"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def to_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-", "None"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_url_text(url: str, referer: str = "https://quote.eastmoney.com/") -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        "Referer": referer,
        "Accept": "application/json,text/plain,*/*",
        "Connection": "close",
    }
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=25) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.35 * (attempt + 1))
    result = subprocess.run(
        ["curl.exe", "-L", "--max-time", "30", "-A", "Mozilla/5.0", "-e", referer, url],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=40,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(str(last_error) or result.stderr.strip() or f"curl exit {result.returncode}")
    return result.stdout


def fetch_json(url: str, referer: str = "https://quote.eastmoney.com/") -> dict[str, Any]:
    return json.loads(fetch_url_text(url, referer=referer))


def fetch_all_a_share() -> tuple[list[dict[str, Any]], str]:
    fields = "f12,f13,f14,f2,f3,f5,f6,f8,f10,f15,f16,f17,f18,f20,f21,f100"
    rows: list[dict[str, Any]] = []
    first_url = ""
    for page in range(1, 81):
        params = {
            "pn": str(page),
            "pz": "100",
            "po": "1",
            "np": "1",
            "ut": UT,
            "fltt": "2",
            "invt": "2",
            "fid": "f6",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": fields,
        }
        url = "https://82.push2.eastmoney.com/api/qt/clist/get?" + urllib.parse.urlencode(params)
        if not first_url:
            first_url = url
        payload = fetch_json(url)
        diff = (payload.get("data") or {}).get("diff") or []
        if isinstance(diff, dict):
            diff = list(diff.values())
        if not diff:
            break
        rows.extend(diff)
        if len(diff) < 100:
            break
        time.sleep(0.04)
    return rows, first_url


def fetch_sectors(po: str) -> list[dict[str, Any]]:
    params = {
        "pn": "1",
        "pz": "80",
        "po": po,
        "np": "1",
        "ut": UT,
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:90+t:2+f:!50",
        "fields": "f12,f14,f3,f6,f20,f62",
    }
    url = "https://push2.eastmoney.com/api/qt/clist/get?" + urllib.parse.urlencode(params)
    payload = fetch_json(url)
    diff = (payload.get("data") or {}).get("diff") or []
    if isinstance(diff, dict):
        diff = list(diff.values())
    return diff


def parse_kline_row(line: str) -> dict[str, Any]:
    parts = line.split(",")
    return {
        "date": parts[0],
        "open": to_float(parts[1]),
        "close": to_float(parts[2]),
        "high": to_float(parts[3]),
        "low": to_float(parts[4]),
        "volume": to_float(parts[5]),
        "amount": to_float(parts[6]),
        "amplitude_pct": to_float(parts[7]),
        "change_pct": to_float(parts[8]),
        "change_amount": to_float(parts[9]),
        "turnover_pct": to_float(parts[10]) if len(parts) > 10 else None,
    }


def fetch_index_kline(secid: str) -> tuple[str, list[dict[str, Any]]]:
    params = {
        "secid": secid,
        "klt": "101",
        "fqt": "0",
        "beg": "0",
        "end": "20500101",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
    }
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urllib.parse.urlencode(params)
    payload = fetch_json(url)
    data = payload.get("data") or {}
    rows = [parse_kline_row(line) for line in data.get("klines", [])]
    return str(data.get("name") or secid), rows


def percentile(values: list[float], current: float) -> float | None:
    clean = [value for value in values if value is not None and value >= 0]
    if not clean:
        return None
    below = sum(1 for value in clean if value <= current)
    return round(below / len(clean), 4)


def sector_card(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(item.get("f14") or "未知"),
        "change_pct": round(float(item.get("f3") or 0), 4),
        "source": str(item.get("source") or "东方财富公开板块行情"),
    }


def local_quote_rows(root: Path) -> list[dict[str, Any]]:
    snapshot = load_json(root / "03数据" / "04数据快照" / "重点关注池公开行情快照_最新.json", {"行情": []})
    rows = []
    for item in snapshot.get("行情", []):
        rows.append({
            "f12": item.get("代码"),
            "f14": item.get("名称"),
            "f3": item.get("涨跌幅"),
            "f6": item.get("成交额"),
            "f8": item.get("换手率"),
            "f10": item.get("量比"),
            "f100": item.get("行业"),
        })
    return rows


def local_sector_rows(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    overview = load_json(root / "03数据" / "185专家市场总览" / "股票专家市场总览_最新.json", {})
    rows = []
    for item in overview.get("强势方向", []):
        rows.append({
            "f14": item.get("行业"),
            "f3": item.get("当日平均涨跌幅"),
            "f6": None,
            "f20": None,
            "f62": None,
            "source": "股票专家市场总览_最新.json",
        })
    desc = sorted(rows, key=lambda row: float(row.get("f3") or 0), reverse=True)
    asc = sorted(rows, key=lambda row: float(row.get("f3") or 0))
    return desc, asc


def risk_appetite_score(up_down_ratio: float | None, limit_up_count: int, limit_down_count: int, index_change: float | None) -> float:
    ratio_term = 0.0 if up_down_ratio is None else clamp(math.log(max(up_down_ratio, 0.01)) / math.log(2.0), -1, 1) * 0.45
    limit_term = clamp((limit_up_count - limit_down_count) / 120, -1, 1) * 0.30
    index_term = 0.0 if index_change is None else clamp(index_change / 2.5, -1, 1) * 0.25
    return round(clamp(ratio_term + limit_term + index_term, -1, 1), 2)


def final_style_score(risk_score: float, liquidity_pct: float | None, top_sectors: list[dict[str, Any]]) -> int:
    score = 10 + round(risk_score * 4)
    if liquidity_pct is not None:
        if liquidity_pct >= 0.75:
            score += 2
        elif liquidity_pct <= 0.25:
            score -= 2
    if top_sectors and float(top_sectors[0]["change_pct"]) >= 2:
        score += 1
    return int(clamp(score, 0, 20))


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "245L3评分基础资产"
    missing: list[str] = []
    sources: list[dict[str, str]] = []
    quote_scope = "all_market"
    sector_scope = "eastmoney_sector"

    all_rows: list[dict[str, Any]] = []
    try:
        all_rows, all_url = fetch_all_a_share()
        sources.append({"name": "东方财富A股全市场行情列表", "type": "quote", "status": "success"})
        write_json(out_dir / "market_style_raw_a_share_latest.json", {"source_url": all_url, "rows": all_rows})
    except Exception as exc:  # noqa: BLE001
        missing.append(f"全市场A股行情列表获取失败：{exc}")
        all_rows = local_quote_rows(root)
        quote_scope = "local_focus_pool"
        sources.append({"name": "东方财富A股全市场行情列表", "type": "quote", "status": "failed"})
        sources.append({"name": "重点关注池公开行情快照_最新.json", "type": "quote", "status": "success" if all_rows else "failed"})
        if all_rows:
            missing.append("已降级使用重点关注池局部样本，不能替代全市场宽度")

    changes = [to_float(row.get("f3")) for row in all_rows]
    changes = [value for value in changes if value is not None]
    up_count = sum(1 for value in changes if value > 0)
    down_count = sum(1 for value in changes if value < 0)
    limit_up_count = sum(1 for value in changes if value >= 9.8)
    limit_down_count = sum(1 for value in changes if value <= -9.8)
    up_down_ratio = round(up_count / down_count, 4) if down_count else None
    total_amount = round(sum(to_float(row.get("f6")) or 0 for row in all_rows) / 100000000, 2) if all_rows else None

    top_sectors: list[dict[str, Any]] = []
    bottom_sectors: list[dict[str, Any]] = []
    try:
        sectors_desc = fetch_sectors("1")
        sectors_asc = fetch_sectors("0")
        top_sectors = [sector_card(item) for item in sectors_desc[:5]]
        bottom_sectors = [sector_card(item) for item in sectors_asc[:5]]
        sources.append({"name": "东方财富行业板块行情", "type": "sector", "status": "success"})
        write_json(out_dir / "market_style_raw_sectors_latest.json", {"top_source": sectors_desc, "bottom_source": sectors_asc})
    except Exception as exc:  # noqa: BLE001
        missing.append(f"行业板块行情获取失败：{exc}")
        sectors_desc, sectors_asc = local_sector_rows(root)
        sector_scope = "local_expert_overview"
        top_sectors = [sector_card(item) for item in sectors_desc[:5]]
        bottom_sectors = [sector_card(item) for item in sectors_asc[:5]]
        sources.append({"name": "东方财富行业板块行情", "type": "sector", "status": "failed"})
        sources.append({"name": "股票专家市场总览_最新.json", "type": "sector", "status": "success" if top_sectors else "failed"})
        if top_sectors:
            missing.append("已降级使用专家市场总览样本行业强度，不能替代正式全市场板块涨跌幅")

    index_rows: dict[str, dict[str, Any]] = {}
    index_histories: dict[str, list[dict[str, Any]]] = {}
    for label, secid in {
        "沪深300": "1.000300",
        "国证2000": "0.399303",
        "上证指数": "1.000001",
        "深证成指": "0.399001",
    }.items():
        try:
            name, rows = fetch_index_kline(secid)
            if rows:
                index_rows[label] = {"name": name, **rows[-1]}
                index_histories[label] = rows
        except Exception as exc:  # noqa: BLE001
            missing.append(f"{label}指数日线获取失败：{exc}")
    sources.append({"name": "东方财富指数日线", "type": "index", "status": "success" if len(index_rows) >= 3 else "partial"})

    hs300_change = to_float(index_rows.get("沪深300", {}).get("change_pct"))
    gz2000_change = to_float(index_rows.get("国证2000", {}).get("change_pct"))
    large_small_ratio = round(hs300_change / gz2000_change, 4) if hs300_change is not None and gz2000_change not in (None, 0) else None
    relative = (hs300_change - gz2000_change) if hs300_change is not None and gz2000_change is not None else None
    if relative is None:
        dominant = "unknown"
    elif relative > 0.3:
        dominant = "large"
    elif relative < -0.3:
        dominant = "small"
    else:
        dominant = "balanced"

    sh_hist = index_histories.get("上证指数", [])
    sz_hist = index_histories.get("深证成指", [])
    amount_by_date: dict[str, float] = {}
    for row in sh_hist[-80:]:
        if row.get("amount") is not None:
            amount_by_date[row["date"]] = amount_by_date.get(row["date"], 0) + float(row["amount"])
    for row in sz_hist[-80:]:
        if row.get("amount") is not None:
            amount_by_date[row["date"]] = amount_by_date.get(row["date"], 0) + float(row["amount"])
    recent_amounts = [value / 100000000 for _, value in sorted(amount_by_date.items())[-60:]]
    index_total_amount = recent_amounts[-1] if recent_amounts else None
    liquidity_pct = percentile(recent_amounts, index_total_amount) if index_total_amount is not None else None
    if liquidity_pct is None:
        missing.append("两市成交额近60日分位获取失败")

    market_date = (
        index_rows.get("上证指数", {}).get("date")
        or index_rows.get("沪深300", {}).get("date")
        or datetime.now().date().isoformat()
    )
    index_change = to_float(index_rows.get("上证指数", {}).get("change_pct"))
    risk_score = risk_appetite_score(up_down_ratio, limit_up_count, limit_down_count, index_change)
    final_score = final_style_score(risk_score, liquidity_pct, top_sectors)

    status = "confirmed"
    if missing or quote_scope != "all_market" or sector_scope != "eastmoney_sector" or not all_rows or not top_sectors or dominant == "unknown" or liquidity_pct is None:
        status = "partial"

    result = {
        "date": market_date,
        "market": "cn",
        "status": status,
        "data_sources": sources,
        "risk_appetite": {
            "score": risk_score,
            "up_down_ratio": up_down_ratio,
            "up_count": up_count,
            "down_count": down_count,
            "limit_up_count": limit_up_count,
            "limit_down_count": limit_down_count,
            "total_amount": total_amount,
            "evidence": [
                f"{'全市场' if quote_scope == 'all_market' else '重点关注池局部'}样本{len(all_rows)}只，上涨{up_count}只、下跌{down_count}只，涨跌家数比{up_down_ratio}。",
                f"涨停约{limit_up_count}只，跌停约{limit_down_count}只。",
                f"{'全A样本' if quote_scope == 'all_market' else '重点关注池局部样本'}成交额合计约{total_amount}亿元。"
            ],
            "missing": [] if quote_scope == "all_market" and all_rows else ["当前不是全市场宽度，只能作为局部样本证据"],
        },
        "sector_heat": {
            "top_sectors": top_sectors,
            "bottom_sectors": bottom_sectors,
            "hot_theme": top_sectors[0]["name"] if top_sectors else None,
            "evidence": [
                "行业板块热度来自东方财富公开板块行情涨跌幅排序。" if sector_scope == "eastmoney_sector" else "行业板块热度降级来自专家市场总览中的样本行业强度。"
            ] if top_sectors else [],
            "missing": [] if sector_scope == "eastmoney_sector" and top_sectors and bottom_sectors else ["当前不是正式全市场板块涨跌幅"],
        },
        "size_style": {
            "big_small_ratio": large_small_ratio,
            "large_index_change_pct": hs300_change,
            "small_index_change_pct": gz2000_change,
            "dominant": dominant,
            "evidence": [
                f"沪深300涨跌幅{hs300_change}%，国证2000涨跌幅{gz2000_change}%，相对差{round(relative, 4) if relative is not None else None}。"
            ] if dominant != "unknown" else [],
            "missing": [] if dominant != "unknown" else ["大小盘指数相对强弱未完整获取"],
        },
        "liquidity": {
            "total_amount_rank_percentile": liquidity_pct,
            "activity_description": f"指数口径两市成交额近60日分位为{liquidity_pct}。" if liquidity_pct is not None else "成交额分位缺失。",
            "evidence": [
                f"上证指数与深证成指成交额合计约{round(index_total_amount, 2)}亿元，近60日分位{liquidity_pct}。"
            ] if liquidity_pct is not None and index_total_amount is not None else [],
            "missing": [] if liquidity_pct is not None else ["近60日成交额分位缺失"],
        },
        "final_adaptation_score": final_score,
        "moderate_coefficient": round(clamp(1 + (final_score - 10) / 100, 0.85, 1.15), 2),
        "notes_for_stock_type": "该表为全市场通用风格底表。单股L3评分仍需结合个股行业标签计算行业适配，不能仅凭市场强弱直接提高个股结论。",
        "overall_summary": f"市场风险偏好{risk_score}，热点板块为{top_sectors[0]['name'] if top_sectors else '未知'}，大小盘风格为{dominant}，流动性分位为{liquidity_pct}。",
        "missing_summary": "无关键缺口，可作为confirmed市场风格证据。" if status == "confirmed" else "；".join(missing),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "last_reviewed_at": datetime.now().date().isoformat(),
    }
    write_json(out_dir / "market_style_daily_latest.json", result)
    write_json(out_dir / f"market_style_daily_{market_date}.json", result)
    print(json.dumps({"状态": "完成", "风格状态": status, "日期": market_date, "市场风格分": final_score, "输出": str(out_dir)}, ensure_ascii=False))
    return 0 if status in {"confirmed", "partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
