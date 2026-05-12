# -*- coding: utf-8 -*-
"""
名称：生成L8指数基底池.py
作用：生成沪深300+中证500指数基底池，作为股票分层池L8客观底盘。
触发方式：python 生成L8指数基底池.py [--offline] [--force-refresh]
依赖：akshare；可选baostock；可选01配置/L8基底池_备用.csv；可选历史缓存L8指数基底池_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读公开指数成分股数据和本地缓存；只写03数据/130指数基底池与04日志/数据源；不触发n8n；不发送企业微信；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-05-01 创建L8指数基底池生成脚本。
标识：stock-l8-index-base-pool-generate
"""

from __future__ import annotations

import argparse
import csv
import json
import traceback
from datetime import date, datetime
from pathlib import Path
from typing import Any


INDEX_CONFIG = {
    "000300": {"指数类型": "沪深300", "指数代码": "000300.SH"},
    "000905": {"指数类型": "中证500", "指数代码": "000905.SH"},
}
CACHE_NORMAL_DAYS = 7
CACHE_MAX_DAYS = 120


def module_root() -> Path:
    # 本脚本约定放在 股票研究系统/02脚本 下，因此 parents[1] 为股票研究系统根目录。
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"必需文件不存在: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_code(code: Any, exchange: Any = None) -> str:
    text = str(code or "").strip().lower()
    if not text:
        return ""
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        suffix = suffix.upper()
        if suffix == "SH":
            return f"sh{num}"
        if suffix == "SZ":
            return f"sz{num}"
        if suffix == "BJ":
            return f"bj{num}"
    exchange_text = str(exchange or "")
    if "上海" in exchange_text or "Shanghai" in exchange_text:
        return f"sh{text}"
    if "深圳" in exchange_text or "Shenzhen" in exchange_text:
        return f"sz{text}"
    if "北京" in exchange_text or "Beijing" in exchange_text:
        return f"bj{text}"
    if len(text) == 6 and text.isdigit():
        if text.startswith(("6", "9")):
            return f"sh{text}"
        if text.startswith(("4", "8")):
            return f"bj{text}"
        return f"sz{text}"
    return text


def display_code(code: Any) -> str:
    norm = normalize_code(code)
    if norm.startswith("sh"):
        return f"{norm[2:]}.SH"
    if norm.startswith("sz"):
        return f"{norm[2:]}.SZ"
    if norm.startswith("bj"):
        return f"{norm[2:]}.BJ"
    return str(code or "").upper()


def parse_data_date(value: Any) -> str:
    if value in (None, "", "未知"):
        return "未知"
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    text = str(value)
    try:
        import pandas as pd  # type: ignore

        parsed = pd.to_datetime(value)
        if not pd.isna(parsed):
            return parsed.strftime("%Y-%m-%d")
    except Exception:  # noqa: BLE001
        pass
    return text[:10] if len(text) >= 10 else text


def parse_cache_age_days(data_date: Any, today: date) -> int | None:
    if not data_date or data_date == "未知":
        return None
    try:
        parsed = datetime.strptime(str(data_date)[:10], "%Y-%m-%d").date()
        return (today - parsed).days
    except ValueError:
        return None


def cache_status(age_days: int | None) -> str:
    if age_days is None:
        return "缓存日期未知"
    if age_days <= CACHE_NORMAL_DAYS:
        return "正常"
    if age_days <= CACHE_MAX_DAYS:
        return "偏旧可用"
    return "超过120天强告警"


def add_stock(
    stocks: dict[str, dict[str, Any]],
    code: str,
    name: str,
    index_type: str,
    index_code: str,
    source: str,
    data_date: str = "未知",
    include_date: str = "未知",
) -> None:
    norm = normalize_code(code)
    if not norm:
        return
    display = display_code(norm)
    relation = {
        "指数类型": index_type,
        "指数代码": index_code,
        "数据日期": data_date or "未知",
        "纳入日期": include_date or "未知",
    }
    if norm not in stocks:
        stocks[norm] = {
            "代码": norm,
            "展示代码": display,
            "名称": name or "",
            "指数类型": index_type,
            "指数代码": index_code,
            "指数归属": [relation],
            "来源": source,
            "是否启用": True,
        }
        return
    existing = stocks[norm]
    if name and not existing.get("名称"):
        existing["名称"] = name
    relations = existing.setdefault("指数归属", [])
    if not any(item.get("指数代码") == index_code for item in relations):
        relations.append(relation)
    existing["指数类型"] = "；".join(item.get("指数类型", "") for item in relations if item.get("指数类型"))
    existing["指数代码"] = "；".join(item.get("指数代码", "") for item in relations if item.get("指数代码"))
    existing["来源"] = "；".join(sorted(set(str(existing.get("来源", "")).split("；") + [source]) - {""}))


def fetch_from_akshare() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    import akshare as ak  # type: ignore

    attempts: list[dict[str, Any]] = []
    stocks: dict[str, dict[str, Any]] = {}
    for symbol, cfg in INDEX_CONFIG.items():
        attempt = {
            "数据源": "akshare.index_stock_cons_csindex",
            "指数": cfg["指数类型"],
            "指数代码": cfg["指数代码"],
            "成功": False,
            "数量": 0,
            "错误": "",
        }
        try:
            df = ak.index_stock_cons_csindex(symbol=symbol)
            attempt["数量"] = int(len(df))
            if df.empty:
                raise RuntimeError("返回空数据")
            for _, row in df.iterrows():
                code = normalize_code(row.get("成分券代码"), row.get("交易所"))
                add_stock(
                    stocks,
                    code=code,
                    name=str(row.get("成分券名称") or ""),
                    index_type=cfg["指数类型"],
                    index_code=cfg["指数代码"],
                    source="akshare.index_stock_cons_csindex",
                    data_date=parse_data_date(row.get("日期")),
                    include_date="未知",
                )
            attempt["成功"] = True
        except Exception as exc:  # noqa: BLE001
            attempt["错误"] = f"{type(exc).__name__}: {exc}"
        attempts.append(attempt)
    return list(stocks.values()), attempts


def load_cache(latest_path: Path, today: date) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    cached = load_json(latest_path)
    if not cached:
        return [], {"存在": False}, "缓存不存在"
    stocks = cached.get("股票池", [])
    data_date = cached.get("数据日期")
    age = parse_cache_age_days(data_date, today)
    status = cache_status(age)
    health = cached.get("数据健康度", {})
    meta = {
        "存在": True,
        "路径": str(latest_path),
        "数据日期": data_date,
        "缓存年龄_天": age,
        "缓存状态": status,
        "缓存是否完整": bool(health.get("是否完整")),
        "缓存股票数": len(stocks),
    }
    if not stocks:
        return [], meta, "缓存无股票池"
    return stocks, meta, status


def ensure_backup_template(template_path: Path) -> bool:
    if template_path.exists():
        return False
    template_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        ["代码", "名称", "指数类型", "指数代码"],
        ["sh600519", "贵州茅台", "沪深300", "000300.SH"],
        ["sh500001", "示例股票", "中证500", "000905.SH"],
    ]
    with template_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)
    return True


def load_backup_csv(csv_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    meta = {"存在": csv_path.exists(), "路径": str(csv_path), "成功": False, "数量": 0, "错误": ""}
    if not csv_path.exists():
        meta["错误"] = "备用CSV不存在"
        return [], meta
    stocks: dict[str, dict[str, Any]] = {}
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                raw_code = row.get("代码") or row.get("code") or row.get("stock_code")
                name = row.get("名称") or row.get("name") or row.get("stock_name") or ""
                index_type = row.get("指数类型") or row.get("index_type") or "未知"
                index_code = row.get("指数代码") or row.get("index_code") or "未知"
                add_stock(
                    stocks,
                    code=normalize_code(raw_code),
                    name=name,
                    index_type=index_type,
                    index_code=index_code,
                    source="L8基底池_备用.csv",
                    data_date="未知",
                    include_date=row.get("纳入日期") or "未知",
                )
        meta["成功"] = bool(stocks)
        meta["数量"] = len(stocks)
        if not stocks:
            meta["错误"] = "备用CSV无有效股票"
    except Exception as exc:  # noqa: BLE001
        meta["错误"] = f"{type(exc).__name__}: {exc}"
    return list(stocks.values()), meta


def fetch_from_baostock() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    import baostock as bs  # type: ignore

    attempts: list[dict[str, Any]] = []
    stocks: dict[str, dict[str, Any]] = {}
    login_result = bs.login()
    if getattr(login_result, "error_code", "0") != "0":
        return [], [{"数据源": "baostock", "成功": False, "错误": getattr(login_result, "error_msg", "登录失败")}]
    try:
        methods = [
            ("query_hs300_stocks", "沪深300", "000300.SH"),
            ("query_zz500_stocks", "中证500", "000905.SH"),
        ]
        for method_name, index_type, index_code in methods:
            attempt = {"数据源": f"baostock.{method_name}", "指数": index_type, "指数代码": index_code, "成功": False, "数量": 0, "错误": ""}
            try:
                method = getattr(bs, method_name)
                rs = method()
                rows = []
                while rs.error_code == "0" and rs.next():
                    rows.append(rs.get_row_data())
                fields = list(getattr(rs, "fields", []) or [])
                attempt["数量"] = len(rows)
                if getattr(rs, "error_code", "0") != "0":
                    raise RuntimeError(getattr(rs, "error_msg", "baostock返回错误"))
                if not rows:
                    raise RuntimeError("返回空数据")
                for row in rows:
                    item = dict(zip(fields, row))
                    add_stock(
                        stocks,
                        code=normalize_code(item.get("code")),
                        name=item.get("code_name") or item.get("name") or "",
                        index_type=index_type,
                        index_code=index_code,
                        source=f"baostock.{method_name}",
                        data_date=item.get("updateDate") or "未知",
                        include_date="未知",
                    )
                attempt["成功"] = True
            except Exception as exc:  # noqa: BLE001
                attempt["错误"] = f"{type(exc).__name__}: {exc}"
            attempts.append(attempt)
    finally:
        bs.logout()
    return list(stocks.values()), attempts


def has_both_indices(stocks: list[dict[str, Any]]) -> bool:
    codes = set()
    for stock in stocks:
        for relation in stock.get("指数归属", []):
            if relation.get("指数代码"):
                codes.add(relation.get("指数代码"))
        if stock.get("指数代码"):
            for part in str(stock.get("指数代码")).split("；"):
                codes.add(part)
    return {"000300.SH", "000905.SH"}.issubset(codes)


def build_report(
    *,
    root: Path,
    stocks: list[dict[str, Any]],
    now: datetime,
    output_path: Path,
    latest_path: Path,
    attempts: list[dict[str, Any]],
    cache_meta: dict[str, Any],
    csv_meta: dict[str, Any],
    selected_source: str,
    degraded: bool,
    downgrade_reason: str,
    offline: bool,
    force_refresh: bool,
    template_created: bool,
) -> dict[str, Any]:
    stock_codes = [item.get("代码") for item in stocks if item.get("代码")]
    duplicate_count = len(stock_codes) - len(set(stock_codes))
    complete = len(stocks) > 0 and duplicate_count == 0 and has_both_indices(stocks)
    if cache_meta.get("缓存年龄_天") is not None and cache_meta.get("缓存年龄_天") > CACHE_MAX_DAYS and selected_source == "cache":
        complete = False
    return {
        "名称": "L8指数基底池",
        "版本": "2026-05-01",
        "定位": "沪深300+中证500客观指数基底池，不包含用户增强观察池主观加权。",
        "数据日期": now.strftime("%Y-%m-%d"),
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成L8指数基底池.py",
        "股票数量": len(stocks),
        "数据源": {
            "实际使用数据源": selected_source,
            "是否降级": degraded,
            "降级原因": downgrade_reason,
            "AKShare尝试": attempts,
            "缓存状态": cache_meta,
            "备用CSV状态": csv_meta,
            "离线模式": offline,
            "强制刷新": force_refresh,
        },
        "字段规则": {
            "代码": "内部代码，sh/sz/bj + 六位数字",
            "展示代码": "外部展示代码，如600519.SH",
            "指数归属": "保留股票所属指数列表；如重复归属则不重复输出股票。",
            "纳入日期": "数据源未提供时填未知，不编造日期。",
        },
        "数据健康度": {
            "目标指数": ["000300.SH", "000905.SH"],
            "输出股票数": len(stocks),
            "重复代码数": duplicate_count,
            "是否覆盖沪深300和中证500": has_both_indices(stocks),
            "是否完整": complete,
            "是否降级": degraded,
            "降级说明": downgrade_reason,
            "缓存年龄_天": cache_meta.get("缓存年龄_天"),
            "缓存状态": cache_meta.get("缓存状态"),
        },
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写旧系统": False,
            "是否写正式库": False,
        },
        "实际动作": {
            "读取公开指数成分股": selected_source in {"akshare", "baostock"} and not offline,
            "读取缓存": selected_source == "cache",
            "读取备用CSV": selected_source == "backup_csv",
            "写入03数据": True,
            "写入04日志": True,
            "写入备用CSV模板": template_created,
            "修改源股票池": False,
            "触发n8n": False,
            "企业微信真实发送": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "输出文件": {
            "时间戳文件": str(output_path),
            "最新文件": str(latest_path),
        },
        "股票池": stocks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="生成L8指数基底池")
    parser.add_argument("--offline", action="store_true", help="离线模式：不访问网络，只使用缓存或备用CSV")
    parser.add_argument("--force-refresh", action="store_true", help="强制尝试网络主源")
    args = parser.parse_args()

    root = module_root()
    now = datetime.now()
    today = now.date()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    output_dir = root / "03数据" / "130指数基底池"
    output_path = output_dir / f"L8指数基底池_{stamp}.json"
    latest_path = output_dir / "L8指数基底池_最新.json"
    log_dir = root / "04日志" / "数据源"
    log_path = log_dir / f"L8指数基底池数据源日志_{stamp}.json"
    latest_log_path = log_dir / "L8指数基底池数据源日志_最新.json"
    backup_csv_path = root / "01配置" / "L8基底池_备用.csv"
    backup_template_path = root / "01配置" / "L8基底池_备用模板.csv"

    template_created = ensure_backup_template(backup_template_path)
    all_attempts: list[dict[str, Any]] = []
    cache_stocks, cache_meta, cache_note = load_cache(latest_path, today)
    csv_stocks: list[dict[str, Any]] = []
    csv_meta: dict[str, Any] = {"存在": backup_csv_path.exists(), "路径": str(backup_csv_path), "成功": False, "数量": 0, "错误": ""}
    selected_source = ""
    degraded = False
    downgrade_reason = ""
    final_stocks: list[dict[str, Any]] = []

    if not args.offline:
        ak_stocks, ak_attempts = fetch_from_akshare()
        all_attempts.extend(ak_attempts)
        ak_success_indices = [item for item in ak_attempts if item.get("成功")]
        if len(ak_success_indices) == len(INDEX_CONFIG) and has_both_indices(ak_stocks):
            final_stocks = ak_stocks
            selected_source = "akshare"
        elif ak_stocks:
            downgrade_reason = "AKShare部分成功，优先回退完整缓存；不使用半池覆盖完整L8"
            if cache_stocks and cache_meta.get("缓存是否完整"):
                final_stocks = cache_stocks
                selected_source = "cache"
                degraded = True
            else:
                final_stocks = ak_stocks
                selected_source = "akshare_partial"
                degraded = True
                downgrade_reason = "AKShare部分成功且无完整缓存，输出不完整诊断结果"
        else:
            downgrade_reason = "AKShare失败，尝试缓存/备用CSV/baostock"

    if args.offline and not final_stocks:
        degraded = True
        downgrade_reason = "离线模式启用，跳过网络数据源"

    if not final_stocks and cache_stocks:
        final_stocks = cache_stocks
        selected_source = "cache"
        degraded = True
        downgrade_reason = downgrade_reason or f"使用缓存：{cache_note}"

    if not final_stocks:
        csv_stocks, csv_meta = load_backup_csv(backup_csv_path)
        if csv_stocks:
            final_stocks = csv_stocks
            selected_source = "backup_csv"
            degraded = True
            downgrade_reason = downgrade_reason or "使用备用CSV"

    if not final_stocks and not args.offline:
        bs_stocks, bs_attempts = fetch_from_baostock()
        all_attempts.extend(bs_attempts)
        if bs_stocks:
            final_stocks = bs_stocks
            selected_source = "baostock"
            degraded = True
            downgrade_reason = downgrade_reason or "AKShare不可用，使用baostock备用数据源"

    if not final_stocks:
        selected_source = "none"
        degraded = True
        downgrade_reason = downgrade_reason or "所有数据源均不可用，未生成有效L8股票池"

    report = build_report(
        root=root,
        stocks=final_stocks,
        now=now,
        output_path=output_path,
        latest_path=latest_path,
        attempts=all_attempts,
        cache_meta=cache_meta,
        csv_meta=csv_meta,
        selected_source=selected_source,
        degraded=degraded,
        downgrade_reason=downgrade_reason,
        offline=args.offline,
        force_refresh=args.force_refresh,
        template_created=template_created,
    )

    log = {
        "名称": "L8指数基底池数据源日志",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成L8指数基底池.py",
        "命令参数": {"offline": args.offline, "force_refresh": args.force_refresh},
        "尝试过的数据源": all_attempts,
        "缓存状态": cache_meta,
        "备用CSV状态": csv_meta,
        "实际使用数据源": selected_source,
        "是否降级": degraded,
        "降级原因": downgrade_reason,
        "输出文件": {"时间戳文件": str(output_path), "最新文件": str(latest_path)},
        "安全边界": report["安全边界"],
        "实际动作": report["实际动作"],
    }

    write_json(output_path, report)
    write_json(latest_path, report)
    write_json(log_path, log)
    write_json(latest_log_path, log)

    summary = {
        "状态": "完成" if report["数据健康度"]["是否完整"] else "部分完成",
        "股票数量": len(final_stocks),
        "实际使用数据源": selected_source,
        "是否降级": degraded,
        "是否完整": report["数据健康度"]["是否完整"],
        "输出": str(output_path),
        "最新": str(latest_path),
        "日志": str(log_path),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if report["数据健康度"]["是否完整"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
