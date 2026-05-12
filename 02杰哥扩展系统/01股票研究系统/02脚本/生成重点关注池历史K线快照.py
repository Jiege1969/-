# -*- coding: utf-8 -*-
"""
名称：生成重点关注池历史K线快照.py
作用：只读调用公开历史K线多源接口，为重点关注池生成日线历史快照。
触发方式：python 生成重点关注池历史K线快照.py
依赖：Python标准库；重点关注股票池.json；技术指标计算规则.json；股票数据源注册表.json；东方财富公开历史K线接口；腾讯公开历史K线接口。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读公开行情；只写新系统股票模块03数据/11历史行情；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建重点关注池历史K线快照脚本；2026-04-28 吸收旧系统腾讯K线兜底经验；2026-05-05 增强东方财富历史K线请求头和重试机制，降低腾讯兜底导致成交额缺失的概率。
标识：stock-focus-history-kline-snapshot
"""

from __future__ import annotations

import json
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


def load_existing_best(output_dir: Path) -> dict[str, Any] | None:
    candidates = []
    for path in output_dir.glob("重点关注池历史K线快照_*.json"):
        if path.name.endswith("_最新.json"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:  # noqa: BLE001
            continue
        success_count = int(data.get("成功数量", 0))
        if success_count > 0:
            candidates.append((success_count, path.stat().st_mtime, data))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return candidates[0][2]


def to_sec_id(code: str) -> str:
    code = str(code or "").strip().lower()
    if code.startswith("sh"):
        return "1." + code[2:]
    if code.startswith("sz"):
        return "0." + code[2:]
    if code.startswith(("6", "9")):
        return "1." + code
    return "0." + code


def code_with_market(code: str) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz")):
        return text
    if text.startswith(("6", "9")):
        return "sh" + text
    return "sz" + text


def fetch_eastmoney_kline(code: str) -> dict[str, Any]:
    params = {
        "secid": to_sec_id(code),
        "klt": "101",
        "fqt": "1",
        "beg": "0",
        "end": "20500101",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
    }
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urllib.parse.urlencode(params)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Referer": f"https://quote.eastmoney.com/{code_with_market(code)}.html",
        "Accept": "application/json,text/plain,*/*",
        "Connection": "close",
    }
    errors = []
    for attempt in range(1, 4):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8", errors="replace"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"第{attempt}次失败：{exc}")
            time.sleep(0.25 * attempt)
    raise RuntimeError("；".join(errors))


def fetch_tencent_kline(code: str, limit: int) -> dict[str, Any]:
    params = {
        "param": f"{code.lower()},day,,,{max(limit, 160)},qfq",
    }
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": f"https://gu.qq.com/{code.lower()}/gp",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_rows(raw: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    rows = []
    klines = raw.get("data", {}).get("klines", []) or []
    for line in klines[-limit:]:
        parts = line.split(",")
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
            "换手率": to_float(parts[10])
        })
    return rows


def parse_tencent_rows(raw: dict[str, Any], code: str, limit: int) -> list[dict[str, Any]]:
    stock_data = (raw.get("data", {}) or {}).get(code.lower(), {}) or {}
    klines = stock_data.get("qfqday") or stock_data.get("day") or []
    rows = []
    previous_close = None
    for line in klines[-limit:]:
        if len(line) < 6:
            continue
        open_price = to_float(line[1])
        close_price = to_float(line[2])
        high_price = to_float(line[3])
        low_price = to_float(line[4])
        volume = to_float(line[5])
        pct = None
        diff = None
        amplitude = None
        if previous_close and close_price is not None:
            diff = round(close_price - previous_close, 4)
            pct = round(diff / previous_close * 100, 4)
        if previous_close and high_price is not None and low_price is not None:
            amplitude = round((high_price - low_price) / previous_close * 100, 4)
        if close_price is not None:
            previous_close = close_price
        rows.append({
            "日期": line[0],
            "开盘": open_price,
            "收盘": close_price,
            "最高": high_price,
            "最低": low_price,
            "成交量": volume,
            "成交额": None,
            "振幅": amplitude,
            "涨跌幅": pct,
            "涨跌额": diff,
            "换手率": None
        })
    return rows


def fetch_kline_multi_source(code: str, limit: int) -> tuple[list[dict[str, Any]], str, str]:
    errors = []
    try:
        raw = fetch_eastmoney_kline(code)
        rows = parse_rows(raw, limit)
        if rows:
            return rows, "东方财富历史K线", ""
        errors.append("东方财富返回空数据")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"东方财富失败：{exc}")
    try:
        raw = fetch_tencent_kline(code, limit)
        rows = parse_tencent_rows(raw, code, limit)
        if rows:
            return rows, "腾讯历史K线", "；".join(errors)
        errors.append("腾讯返回空数据")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"腾讯失败：{exc}")
    return [], "", "；".join(errors)


def to_float(value: str) -> float | None:
    try:
        if value in ("", "-"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> int:
    root = module_root()
    rules = load_json(root / "01配置" / "技术指标计算规则.json")
    focus = load_json(root / "01配置" / "重点关注股票池.json")
    limit = int(rules.get("历史K线", {}).get("目标交易日数量", 160))
    stocks = focus.get("股票池", [])
    results = []
    for stock in stocks:
        code = stock.get("代码", "")
        try:
            rows, source, source_warning = fetch_kline_multi_source(code, limit)
            status = "成功" if rows else "无数据"
            error = source_warning if rows else source_warning or "多源均无数据"
        except Exception as exc:  # noqa: BLE001
            rows = []
            source = ""
            status = "失败"
            error = str(exc)
        results.append({
            "代码": code,
            "名称": stock.get("名称", ""),
            "状态": status,
            "数据源": source,
            "错误": error,
            "记录数": len(rows),
            "K线": rows
        })
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "数据源": "东方财富公开历史K线接口；腾讯公开历史K线接口",
        "规则文件": str(root / "01配置" / "技术指标计算规则.json"),
        "股票数量": len(stocks),
        "成功数量": sum(1 for item in results if item["状态"] == "成功"),
        "历史K线": results,
        "安全边界": {
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False
        }
    }
    output_dir = root / rules.get("输出路径", {}).get("历史K线", "03数据/11历史行情")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"重点关注池历史K线快照_{timestamp}.json"
    latest = output_dir / "重点关注池历史K线快照_最新.json"
    write_json(output, report)
    if report["成功数量"] > 0:
        write_json(latest, report)
        effective_success = report["成功数量"]
        mode = "本次快照"
    else:
        fallback = load_existing_best(output_dir)
        if fallback:
            fallback["降级说明"] = {
                "降级时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "原因": "本次公开历史K线请求全部失败，保留最近可用快照作为最新快照。",
                "失败快照": str(output)
            }
            write_json(latest, fallback)
            effective_success = int(fallback.get("成功数量", 0))
            mode = "缓存兜底"
        else:
            write_json(latest, report)
            effective_success = 0
            mode = "无缓存"
    print(json.dumps({"股票数量": len(stocks), "成功数量": report["成功数量"], "有效成功数量": effective_success, "模式": mode, "输出": str(output)}, ensure_ascii=False))
    return 0 if effective_success > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
