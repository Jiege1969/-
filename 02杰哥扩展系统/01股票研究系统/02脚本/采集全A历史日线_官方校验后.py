# -*- coding: utf-8 -*-
"""
名称：采集全A历史日线_官方校验后.py
作用：在全A基础池通过官方交易所名单校验后，分批采集全A历史日线，建立历史数据底座。
边界：只读公开历史日线接口并写入股票系统03数据；不触发n8n；不发送企业微信；不接券商；不交易。

定位：
1. 全A来源用于建池发现和历史补齐。
2. 本脚本必须在“全A基础池官方校验”通过后运行。
3. 本脚本是历史补库工具，不进入每日行情硬刷新链路；日常增量行情后续走官方/可靠实时渠道。
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import time
import urllib.parse
import urllib.request
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_end_date() -> str:
    """历史补库默认只取上一自然日，避免开市盘中混入未完结日线。"""
    return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def to_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-", "--"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


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


def display_code(code: str) -> str:
    if code.startswith("sh"):
        return f"{code[2:]}.SH"
    if code.startswith("sz"):
        return f"{code[2:]}.SZ"
    if code.startswith("bj"):
        return f"{code[2:]}.BJ"
    return code.upper()


def to_sec_id(code: str) -> str:
    norm = normalize_code(code)
    if norm.startswith("sh"):
        return f"1.{norm[2:]}"
    if norm.startswith(("sz", "bj")):
        return f"0.{norm[2:]}"
    if norm.startswith(("6", "9")):
        return f"1.{norm}"
    return f"0.{norm}"


def code_with_market(code: str) -> str:
    return normalize_code(code)


def adjust_flag(adjust: str) -> str:
    return {"none": "0", "qfq": "1", "hfq": "2"}.get(adjust, "1")


def baostock_adjust_flag(adjust: str) -> str:
    return {"hfq": "1", "qfq": "2", "none": "3"}.get(adjust, "2")


def adjust_name(adjust: str) -> str:
    return {"none": "不复权", "qfq": "前复权", "hfq": "后复权"}.get(adjust, "前复权")


def fetch_eastmoney_kline(code: str, start: str, end: str, adjust: str, timeout: int = 6) -> dict[str, Any]:
    params = {
        "secid": to_sec_id(code),
        "klt": "101",
        "fqt": adjust_flag(adjust),
        "beg": start,
        "end": end,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
    }
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urllib.parse.urlencode(params)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        "Referer": f"https://quote.eastmoney.com/{code_with_market(code)}.html",
        "Accept": "application/json,text/plain,*/*",
        "Connection": "close",
    }
    errors: list[str] = []
    for attempt in range(1, 2):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8", errors="replace"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"第{attempt}次失败:{exc}")
            time.sleep(0.25 * attempt)
    raise RuntimeError("；".join(errors))


def fetch_tencent_kline(code: str, limit: int = 1000, timeout: int = 6) -> dict[str, Any]:
    norm = normalize_code(code)
    params = {"param": f"{norm},day,,,{max(limit, 160)},qfq"}
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urllib.parse.urlencode(params)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": f"https://gu.qq.com/{norm}/gp",
        "Accept": "application/json,text/plain,*/*",
    }
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def baostock_code(code: str) -> str:
    norm = normalize_code(code)
    if norm.startswith("sh"):
        return f"sh.{norm[2:]}"
    if norm.startswith("sz"):
        return f"sz.{norm[2:]}"
    return ""


def fetch_baostock_kline(code: str, start: str, end: str, adjust: str) -> list[dict[str, Any]]:
    bs_code = baostock_code(code)
    if not bs_code:
        raise RuntimeError("baostock暂不支持该市场")
    import baostock as bs  # type: ignore

    start_date = f"{start[:4]}-{start[4:6]}-{start[6:8]}"
    end_date = f"{end[:4]}-{end[4:6]}-{end[6:8]}"
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        login = bs.login()
    if getattr(login, "error_code", "") != "0":
        raise RuntimeError(f"baostock登录失败:{getattr(login, 'error_msg', '')}")
    try:
        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,pctChg",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag=baostock_adjust_flag(adjust),
        )
        if getattr(rs, "error_code", "") != "0":
            raise RuntimeError(f"baostock查询失败:{getattr(rs, 'error_msg', '')}")
        rows: list[dict[str, Any]] = []
        while rs.next():
            data = rs.get_row_data()
            if len(data) < 12:
                continue
            volume_share = to_float(data[7])
            close = to_float(data[5])
            preclose = to_float(data[6])
            high = to_float(data[3])
            low = to_float(data[4])
            diff = round(close - preclose, 4) if close is not None and preclose is not None else None
            amplitude = round((high - low) / preclose * 100, 4) if high is not None and low is not None and preclose else None
            rows.append({
                "日期": data[0],
                "开盘": to_float(data[2]),
                "收盘": close,
                "最高": high,
                "最低": low,
                "成交量": round(volume_share / 100, 2) if volume_share is not None else None,
                "成交额": to_float(data[8]),
                "振幅": amplitude,
                "涨跌幅": to_float(data[11]),
                "涨跌额": diff,
                "换手率": to_float(data[10]),
                "成交量单位": "手",
                "成交额单位": "元",
            })
        return rows
    finally:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            bs.logout()


def parse_eastmoney_rows(raw: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    klines = ((raw.get("data") or {}).get("klines") or [])
    for line in klines:
        parts = str(line).split(",")
        if len(parts) < 11:
            continue
        rows.append({
            "日期": parts[0],
            "开盘": to_float(parts[1]),
            "收盘": to_float(parts[2]),
            "最高": to_float(parts[3]),
            "最低": to_float(parts[4]),
            "成交量": to_float(parts[5]),
            "成交额": to_float(parts[6]),
            "振幅": to_float(parts[7]),
            "涨跌幅": to_float(parts[8]),
            "涨跌额": to_float(parts[9]),
            "换手率": to_float(parts[10]),
            "成交量单位": "手",
            "成交额单位": "元",
        })
    return rows


def parse_tencent_rows(raw: dict[str, Any], code: str) -> list[dict[str, Any]]:
    norm = normalize_code(code)
    stock_data = ((raw.get("data") or {}).get(norm) or {})
    klines = stock_data.get("qfqday") or stock_data.get("day") or []
    rows: list[dict[str, Any]] = []
    previous_close: float | None = None
    for line in klines:
        if len(line) < 6:
            continue
        close = to_float(line[2])
        high = to_float(line[3])
        low = to_float(line[4])
        volume = to_float(line[5])
        pct = None
        diff = None
        amplitude = None
        if previous_close and close is not None:
            diff = round(close - previous_close, 4)
            pct = round(diff / previous_close * 100, 4)
        if previous_close and high is not None and low is not None:
            amplitude = round((high - low) / previous_close * 100, 4)
        estimated_amount = None
        if volume is not None and close is not None:
            estimated_amount = round(volume * 100 * close, 2)
        if close is not None:
            previous_close = close
        rows.append({
            "日期": line[0],
            "开盘": to_float(line[1]),
            "收盘": close,
            "最高": high,
            "最低": low,
            "成交量": volume,
            "成交额": estimated_amount,
            "成交额是否估算": True,
            "振幅": amplitude,
            "涨跌幅": pct,
            "涨跌额": diff,
            "换手率": None,
            "成交量单位": "手",
            "成交额单位": "元",
        })
    return rows


def fetch_history(code: str, start: str, end: str, adjust: str, allow_estimated: bool) -> tuple[list[dict[str, Any]], str, str]:
    errors: list[str] = []
    def eastmoney_job() -> tuple[list[dict[str, Any]], str]:
        raw = fetch_eastmoney_kline(code, start, end, adjust)
        rows = parse_eastmoney_rows(raw)
        if not rows:
            raise RuntimeError("东方财富返回空数据")
        return rows, "东方财富公开历史日线接口"

    def baostock_job() -> tuple[list[dict[str, Any]], str]:
        rows = fetch_baostock_kline(code, start, end, adjust)
        if not rows:
            raise RuntimeError("Baostock返回空数据")
        return rows, "Baostock公开历史日线接口"

    executor = ThreadPoolExecutor(max_workers=2)
    futures = {
        executor.submit(eastmoney_job): "东方财富",
        executor.submit(baostock_job): "Baostock",
    }
    try:
        pending = set(futures)
        while pending:
            done, pending = wait(pending, timeout=7, return_when=FIRST_COMPLETED)
            if not done:
                errors.append("东方财富/Baostock并行等待超时")
                for future in pending:
                    future.cancel()
                break
            for future in done:
                label = futures[future]
                try:
                    rows, source = future.result()
                    for rest in pending:
                        rest.cancel()
                    executor.shutdown(wait=False, cancel_futures=True)
                    return rows, source, "；".join(errors)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{label}失败:{exc}")
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
    if not allow_estimated:
        return [], "", "；".join(errors + ["未启用腾讯估算成交额兜底，禁止写入正式历史底座"])
    try:
        raw = fetch_tencent_kline(code)
        rows = parse_tencent_rows(raw, code)
        if rows:
            return rows, "腾讯公开复权日线接口-成交额估算兜底", "；".join(errors)
        errors.append("腾讯返回空数据")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"腾讯失败:{exc}")
    return [], "", "；".join(errors)


def stock_file(base_dir: Path, code: str) -> Path:
    norm = normalize_code(code)
    market = "bj" if norm.startswith("bj") else "sh" if norm.startswith("sh") else "sz"
    return base_dir / "按股票" / market / f"{norm}.json"


def existing_is_fresh(path: Path, end: str) -> bool:
    if not path.exists():
        return False
    try:
        data = load_json(path)
    except Exception:
        return False
    rows = data.get("日线", [])
    if not rows:
        return False
    last_date = str(rows[-1].get("日期", "")).replace("-", "")
    return bool(last_date and last_date >= end)


def build_stock_record(stock: dict[str, Any], rows: list[dict[str, Any]], source: str, warning: str, start: str, end: str, adjust: str) -> dict[str, Any]:
    return {
        "代码": normalize_code(stock.get("代码")),
        "展示代码": stock.get("展示代码") or display_code(normalize_code(stock.get("代码"))),
        "名称": stock.get("名称", ""),
        "市场": stock.get("市场", ""),
        "板块": stock.get("板块", ""),
        "行业": stock.get("行业", ""),
        "采集时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "采集范围": {"开始": start, "结束": end},
        "复权": adjust_name(adjust),
        "数据源": source,
        "数据源警告": warning,
        "官方校验状态": "全A基础池官方校验已通过后采集",
        "记录数": len(rows),
        "首日": rows[0].get("日期") if rows else "",
        "末日": rows[-1].get("日期") if rows else "",
        "字段口径": {
            "成交量": "手",
            "成交额": "元；腾讯兜底时为成交量*收盘价*100估算",
            "价格": "元",
            "复权": adjust_name(adjust),
        },
        "日线": rows,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 全A历史日线采集批次报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 本批目标数量：{report['本批目标数量']}",
        f"- 成功：{report['成功数量']}",
        f"- 跳过：{report['跳过数量']}",
        f"- 失败：{report['失败数量']}",
        "",
        "## 口径",
        "",
    ]
    for item in report["口径声明"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 失败样本", ""])
    failed = [item for item in report["明细"] if item.get("状态") == "失败"]
    if failed:
        for item in failed[:30]:
            lines.append(f"- {item.get('代码')} {item.get('名称')}：{item.get('错误')}")
    else:
        lines.append("- 无")
    return "\n".join(lines) + "\n"


def parse_codes_arg(codes: str) -> set[str]:
    if not codes:
        return set()
    return {normalize_code(code) for code in codes.replace("，", ",").split(",") if normalize_code(code)}


def main() -> int:
    parser = argparse.ArgumentParser(description="官方校验后分批采集全A历史日线")
    parser.add_argument("--start", default="19900101", help="开始日期，YYYYMMDD")
    parser.add_argument("--end", default=default_end_date(), help="结束日期，YYYYMMDD；默认上一自然日，避免盘中未完结数据")
    parser.add_argument("--adjust", choices=["none", "qfq", "hfq"], default="qfq", help="复权方式")
    parser.add_argument("--offset", type=int, default=0, help="从全A基础池第几只开始")
    parser.add_argument("--limit", type=int, default=20, help="本批采集数量；全量补库时分批提高")
    parser.add_argument("--market", choices=["all", "sh", "sz", "bj"], default="all", help="按市场分批：all/sh/sz/bj")
    parser.add_argument("--codes", default="", help="指定代码，逗号分隔；指定后忽略offset")
    parser.add_argument("--force", action="store_true", help="即使本地已有新鲜文件也重新采集")
    parser.add_argument("--allow-estimated", action="store_true", help="允许腾讯估算成交额兜底；默认禁止写入正式历史底座")
    parser.add_argument("--sleep", type=float, default=0.08, help="每只股票采集后的间隔秒数")
    args = parser.parse_args()

    root = module_root()
    full_a_path = root / "03数据" / "01股票池" / "全A基础股票池_最新.json"
    official_check_path = root / "03数据" / "01股票池" / "全A基础池官方校验_最新.json"
    output_dir = root / "03数据" / "012全A历史日线"

    official_check = load_json(official_check_path)
    if official_check.get("结论") != "通过":
        raise SystemExit("全A基础池官方校验未通过，禁止采集历史日线。")

    full_a = load_json(full_a_path)
    all_stocks = list(full_a.get("股票池", []))
    if args.market != "all":
        all_stocks = [
            stock for stock in all_stocks
            if normalize_code(stock.get("代码")).startswith(args.market)
        ]
    selected_codes = parse_codes_arg(args.codes)
    if selected_codes:
        stocks = [stock for stock in all_stocks if normalize_code(stock.get("代码")) in selected_codes]
    else:
        stocks = all_stocks[args.offset: args.offset + max(args.limit, 0)]

    details: list[dict[str, Any]] = []
    success = 0
    skipped = 0
    failed = 0

    for stock in stocks:
        code = normalize_code(stock.get("代码"))
        path = stock_file(output_dir, code)
        if not args.force and existing_is_fresh(path, args.end):
            skipped += 1
            details.append({
                "代码": code,
                "名称": stock.get("名称", ""),
                "状态": "跳过",
                "原因": "本地历史日线已覆盖到结束日期",
                "路径": str(path),
            })
            continue
        try:
            rows, source, warning = fetch_history(code, args.start, args.end, args.adjust, args.allow_estimated)
            if not rows:
                raise RuntimeError(warning or "多源均无历史日线")
            record = build_stock_record(stock, rows, source, warning, args.start, args.end, args.adjust)
            write_json(path, record)
            success += 1
            details.append({
                "代码": code,
                "名称": stock.get("名称", ""),
                "状态": "成功",
                "数据源": source,
                "记录数": len(rows),
                "首日": record["首日"],
                "末日": record["末日"],
                "路径": str(path),
                "警告": warning,
            })
        except Exception as exc:  # noqa: BLE001
            failed += 1
            details.append({
                "代码": code,
                "名称": stock.get("名称", ""),
                "状态": "失败",
                "错误": str(exc),
                "路径": str(path),
            })
        time.sleep(max(args.sleep, 0))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "名称": "全A历史日线采集批次报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if failed == 0 and (success + skipped) > 0 else "需复核",
        "全A基础池": str(full_a_path),
        "官方校验": str(official_check_path),
        "本批目标数量": len(stocks),
        "成功数量": success,
        "跳过数量": skipped,
        "失败数量": failed,
        "参数": vars(args),
        "输出目录": str(output_dir / "按股票"),
        "口径声明": [
            "本脚本只在官方交易所名单校验通过后运行。",
            "全A公开来源用于历史补齐和覆盖检查，不作为每日正式行情入口。",
            "东方财富与Baostock历史日线含正式成交额；腾讯兜底时成交额为估算，必须保留标记。",
            "默认不允许估算成交额写入正式历史底座；只有显式传入--allow-estimated时才会写入需复核数据。",
            "本脚本按批次运行，支持断点跳过；全量补库应分批执行并留存批次报告。",
        ],
        "明细": details,
        "安全边界": {
            "是否触发n8n": False,
            "是否真实发送企业微信": False,
            "是否接券商": False,
            "是否交易": False,
        },
    }
    report_path = output_dir / f"全A历史日线采集批次报告_{timestamp}.json"
    latest_report = output_dir / "全A历史日线采集批次报告_最新.json"
    md_path = output_dir / f"全A历史日线采集批次报告_{timestamp}.md"
    latest_md = output_dir / "全A历史日线采集批次报告_最新.md"
    write_json(report_path, report)
    write_json(latest_report, report)
    markdown = build_markdown(report)
    write_text(md_path, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({
        "状态": report["结论"],
        "本批目标数量": len(stocks),
        "成功数量": success,
        "跳过数量": skipped,
        "失败数量": failed,
        "报告": str(latest_md),
        "数据": str(latest_report),
    }, ensure_ascii=False))
    return 0 if failed == 0 and (success + skipped) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
