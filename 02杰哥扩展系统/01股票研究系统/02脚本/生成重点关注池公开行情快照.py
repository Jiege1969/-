# -*- coding: utf-8 -*-
"""
名称：生成重点关注池公开行情快照.py
作用：只读调用公开行情接口，为重点关注池生成当前行情快照，供独立股票分析使用。
触发方式：python 生成重点关注池公开行情快照.py
依赖：Python标准库；重点关注股票池.json；东方财富公开行情接口。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读公开行情；不调用券商接口；不自动交易；不写旧系统；不触发n8n；不发送企业微信；只写入新系统股票模块03数据目录。
创建/修改记录：2026-04-28 创建重点关注池公开行情快照脚本。
标识：stock-focus-public-quote-snapshot
"""

from __future__ import annotations

import json
import argparse
import http.client
import importlib.util
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


def load_json_optional(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def chunked(items: list[Any], size: int) -> list[list[Any]]:
    return [items[index:index + size] for index in range(0, len(items), size)]


def to_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-", "None"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_full_code(code: str) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        suffix = suffix.lower()
        if suffix == "sh":
            return "sh" + num.zfill(6)
        if suffix == "sz":
            return "sz" + num.zfill(6)
        if suffix == "bj":
            return "bj" + num.zfill(6)
    if text.startswith(("4", "8", "920")):
        return "bj" + text.zfill(6)
    if text.startswith(("6", "9")):
        return "sh" + text.zfill(6)
    return "sz" + text.zfill(6) if text.isdigit() else text


def load_quote_tools(root: Path) -> Any:
    path = root / "02脚本" / "股票助手入口.py"
    spec = importlib.util.spec_from_file_location("stock_quote_tools", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def to_sec_id(code: str) -> str:
    code = normalize_full_code(code)
    if code.startswith("sh"):
        return "1." + code[2:]
    if code.startswith(("sz", "bj")):
        return "0." + code[2:]
    return code


def source_key(code: str) -> str:
    return normalize_full_code(code)


def alias_stocks(root: Path) -> list[dict[str, Any]]:
    alias_path = root / "01配置" / "股票简称补充映射.json"
    data = load_json_optional(alias_path)
    rows: list[dict[str, Any]] = []
    for item in data.get("映射", []):
        if not isinstance(item, dict):
            continue
        code = str(item.get("代码") or "").strip()
        name = str(item.get("名称") or "").strip()
        if code and name:
            rows.append({"代码": code, "名称": name, "来源": "股票简称补充映射"})
    return rows


def fetch_quotes(secids: list[str]) -> dict[str, Any]:
    params = {
        "fltt": "2",
        "invt": "2",
        "fields": "f12,f14,f2,f3,f4,f5,f6,f15,f16,f17,f18,f20,f21,f8,f9,f10,f13,f100",
        "secids": ",".join(secids),
    }
    url = "https://push2.eastmoney.com/api/qt/ulist.np/get?" + urllib.parse.urlencode(params)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        "Referer": "https://quote.eastmoney.com/",
        "Accept": "application/json,text/plain,*/*",
        "Connection": "close",
    }
    last_error: Exception | None = None
    for attempt in range(3):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, http.client.RemoteDisconnected, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(0.5)
    raise RuntimeError(f"东方财富公开行情接口请求失败：{last_error}")


def fetch_eastmoney_batch(secids: list[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    rows: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for group in chunked(secids, 80):
        try:
            raw = fetch_quotes(group)
        except RuntimeError as exc:
            errors.append(f"{group[0]}-{group[-1]}: {exc}")
            continue
        for item in raw.get("data", {}).get("diff", []):
            row = {
                "代码": normalize_full_code(item.get("f12") or ""),
                "名称": item.get("f14"),
                "最新价": item.get("f2"),
                "涨跌幅": item.get("f3"),
                "涨跌额": item.get("f4"),
                "成交量": item.get("f5"),
                "成交额": item.get("f6"),
                "最高": item.get("f15"),
                "最低": item.get("f16"),
                "今开": item.get("f17"),
                "昨收": item.get("f18"),
                "市盈率": item.get("f9"),
                "量比": item.get("f10"),
                "换手率": item.get("f8"),
                "行业": item.get("f100"),
                "数据源": "东方财富公开行情接口-全量批量只读",
                "数据新鲜度": "批量实时公开行情",
                "行情时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "成交量单位": "手",
                "成交额单位": "元",
            }
            if row["代码"]:
                rows[row["代码"]] = row
        time.sleep(0.05)
    return rows, errors


def fetch_tencent_batch(codes: list[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    rows: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        "Referer": "https://gu.qq.com/",
        "Accept": "*/*",
        "Connection": "close",
    }
    for group in chunked(codes, 60):
        query = ",".join(group)
        url = "https://qt.gtimg.cn/q=" + urllib.parse.quote(query, safe=",")
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                text = response.read().decode("gbk", errors="replace")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{group[0]}-{group[-1]}: {exc}")
            continue
        for match in re.finditer(r'v_([a-z]{2}\d{6})="([^"]*)";', text):
            fields = match.group(2).split("~")
            if len(fields) < 50 or to_float(fields[3]) in (None, 0):
                continue
            amount_wan = to_float(fields[37])
            row = {
                "代码": normalize_full_code(match.group(1)),
                "名称": fields[1],
                "最新价": to_float(fields[3]),
                "涨跌幅": to_float(fields[32]),
                "涨跌额": to_float(fields[31]),
                "成交量": to_float(fields[36]),
                "成交额": round(amount_wan * 10000, 2) if amount_wan is not None else None,
                "最高": to_float(fields[33]),
                "最低": to_float(fields[34]),
                "今开": to_float(fields[5]),
                "昨收": to_float(fields[4]),
                "市盈率": to_float(fields[39]),
                "量比": to_float(fields[49]),
                "换手率": to_float(fields[38]),
                "数据源": "腾讯公开实时行情接口-全量批量只读",
                "数据新鲜度": "批量实时公开行情",
                "行情时间": fields[30],
                "成交量单位": "手",
                "成交额单位": "元",
            }
            rows[row["代码"]] = row
        time.sleep(0.05)
    return rows, errors


def fetch_sina_batch(codes: list[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    rows: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        "Referer": "https://finance.sina.com.cn/",
        "Accept": "*/*",
        "Connection": "close",
    }
    for group in chunked(codes, 80):
        url = "https://hq.sinajs.cn/list=" + urllib.parse.quote(",".join(group), safe=",")
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                text = response.read().decode("gbk", errors="replace")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{group[0]}-{group[-1]}: {exc}")
            continue
        for match in re.finditer(r'var hq_str_([a-z]{2}\d{6})="([^"]*)";', text):
            parts = match.group(2).split(",")
            if len(parts) < 32 or not parts[0]:
                continue
            current = to_float(parts[3])
            prev_close = to_float(parts[2])
            if current is None or current <= 0:
                continue
            row = {
                "代码": normalize_full_code(match.group(1)),
                "名称": parts[0],
                "最新价": current,
                "涨跌幅": round((current - prev_close) / prev_close * 100, 2) if current is not None and prev_close else None,
                "涨跌额": round(current - prev_close, 2) if current is not None and prev_close is not None else None,
                "成交量": round((to_float(parts[8]) or 0) / 100, 2),
                "成交额": to_float(parts[9]),
                "最高": to_float(parts[4]),
                "最低": to_float(parts[5]),
                "今开": to_float(parts[1]),
                "昨收": prev_close,
                "数据源": "新浪公开实时行情接口-全量批量只读",
                "数据新鲜度": "批量实时公开行情",
                "行情时间": f"{parts[30]} {parts[31]}" if len(parts) > 31 else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "成交量单位": "手",
                "成交额单位": "元",
            }
            rows[row["代码"]] = row
        time.sleep(0.05)
    return rows, errors


def load_scope_stocks(root: Path, scope: str) -> tuple[list[dict[str, Any]], str, Path]:
    if scope == "focus":
        focus_path = root / "01配置" / "重点关注股票池.json"
        focus = load_json(focus_path)
        return list(focus.get("股票池", [])) + alias_stocks(root), "重点关注池", focus_path
    if scope == "seed":
        path = root / "03数据" / "01股票池" / "全市场扫描源头股票池_初始种子_最新.json"
        data = load_json(path)
        return list(data.get("股票池", [])), "全市场扫描源头股票池初始种子", path
    path = root / "03数据" / "01股票池" / "2000只样本股票池_最新.json"
    data = load_json(path)
    return list(data.get("股票列表", [])), "2000只样本股票池", path


def main() -> int:
    parser = argparse.ArgumentParser(description="生成公开行情统一快照")
    parser.add_argument("--scope", choices=["focus", "seed", "all"], default="focus", help="focus=重点关注池；seed=源头种子；all=当前系统2000只全量样本池")
    parser.add_argument("--limit", type=int, default=0, help="调试用限制数量，正式运行保持0")
    args = parser.parse_args()
    root = module_root()
    quote_tools = load_quote_tools(root)
    output_dir = root / "03数据" / "04数据快照"
    if args.scope == "focus":
        latest = output_dir / "重点关注池公开行情快照_最新.json"
        output_prefix = "重点关注池公开行情快照"
    elif args.scope == "seed":
        latest = output_dir / "全市场源头股票池基础行情统一快照_最新.json"
        output_prefix = "全市场源头股票池基础行情统一快照"
    else:
        latest = output_dir / "2000只样本池基础行情统一快照_最新.json"
        output_prefix = "2000只样本池基础行情统一快照"
    stocks, scope_name, source_path = load_scope_stocks(root, args.scope)
    if args.limit > 0:
        stocks = stocks[:args.limit]
    seen_secids: set[str] = set()
    secids = []
    codes = []
    stock_by_code: dict[str, dict[str, Any]] = {}
    for item in stocks:
        secid = to_sec_id(str(item.get("代码", "")).strip())
        code = normalize_full_code(str(item.get("代码", "")).strip())
        if secid and secid not in seen_secids and code.startswith(("sh", "sz", "bj")):
            seen_secids.add(secid)
            secids.append(secid)
            codes.append(code)
            stock_by_code[code] = item
    fallback = load_json_optional(latest)
    degraded = False
    degrade_reason = ""
    source_snapshot_time = ""
    source_errors: dict[str, list[str]] = {}
    try:
        eastmoney_rows, eastmoney_errors = fetch_eastmoney_batch(secids)
        tencent_rows, tencent_errors = fetch_tencent_batch(codes)
        sina_rows, sina_errors = fetch_sina_batch(codes)
        source_errors = {
            "东方财富": eastmoney_errors,
            "腾讯": tencent_errors,
            "新浪": sina_errors,
            "网易": ["当前公开feed在本机返回502/SSL失败，批量链路暂只登记为待恢复源"],
        }
        quote_rows = []
        for code in codes:
            candidates = []
            for source_rows in (eastmoney_rows, tencent_rows, sina_rows):
                row = source_rows.get(code)
                if row:
                    row = dict(row)
                    base = stock_by_code.get(code, {})
                    row["行业"] = row.get("行业") or base.get("行业")
                    row["展示代码"] = base.get("展示代码") or code
                    candidates.append(row)
            unified = quote_tools.arbitrate_public_quote_candidates(candidates)
            if unified:
                unified["名称"] = unified.get("名称") or stock_by_code.get(code, {}).get("名称")
                unified["行业"] = unified.get("行业") or stock_by_code.get(code, {}).get("行业")
                unified["市场"] = stock_by_code.get(code, {}).get("市场")
                unified["展示代码"] = stock_by_code.get(code, {}).get("展示代码") or unified.get("展示代码") or code
                unified["数据标准口径"] = {
                    "成交量单位": "手",
                    "成交额单位": "元",
                    "价格单位": "元",
                    "涨跌幅单位": "%",
                    "处理规则": "多源采集后统一字段与单位，不做简单平均；主源优先，复核源做容差校验。",
                }
                quote_rows.append(unified)
        data_source = "东方财富/腾讯/新浪公开行情批量统一快照；网易登记待恢复"
        data_freshness = "批量实时公开行情；已统一字段、单位并执行多源复核"
    except RuntimeError as exc:
        quote_rows = fallback.get("行情", []) if isinstance(fallback.get("行情"), list) else []
        degraded = True
        degrade_reason = str(exc)
        source_snapshot_time = str(
            fallback.get("降级来源快照生成时间")
            if fallback.get("是否降级") and fallback.get("降级来源快照生成时间")
            else fallback.get("生成时间") or ""
        )
        data_source = "最近一次公开行情快照降级"
        data_freshness = "非实时；公开接口失败时保留链路可运行，报告侧必须显示降级"
    status_counter: dict[str, int] = {}
    for row in quote_rows:
        status = str(row.get("行情复核状态") or "未知")
        status_counter[status] = status_counter.get(status, 0) + 1
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "快照范围": scope_name,
        "数据源": data_source,
        "数据新鲜度": data_freshness,
        "是否降级": degraded,
        "降级原因": degrade_reason,
        "降级来源快照生成时间": source_snapshot_time,
        "输入股票池": str(source_path),
        "补充映射": str(root / "01配置" / "股票简称补充映射.json"),
        "请求数量": len(secids),
        "返回数量": len(quote_rows),
        "复核状态统计": status_counter,
        "数据源错误摘要": source_errors,
        "行情": quote_rows,
        "安全边界": {
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False
        },
        "固定声明": "本快照只用于研究辅助，不构成投资建议，不作为买卖指令。"
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"{output_prefix}_{timestamp}.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({
        "范围": scope_name,
        "请求数量": len(secids),
        "返回数量": len(quote_rows),
        "复核状态统计": status_counter,
        "是否降级": degraded,
        "输出": str(output),
        "最新": str(latest),
    }, ensure_ascii=False))
    return 0 if len(quote_rows) >= min(len(secids), 1) else 1


if __name__ == "__main__":
    raise SystemExit(main())
