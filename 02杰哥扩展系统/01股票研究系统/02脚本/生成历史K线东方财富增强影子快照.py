# -*- coding: utf-8 -*-
"""
名称：生成历史K线东方财富增强影子快照.py
作用：按现有历史K线股票清单，只读生成东方财富增强请求版历史K线影子快照。
安全边界：只读公开东方财富历史K线接口；只写 03数据/227历史K线东方财富增强影子快照；不覆盖11历史行情最新快照、不改正式脚本、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "227历史K线东方财富增强影子快照"
HISTORY_LATEST_JSON = DATA / "11历史行情" / "重点关注池历史K线快照_最新.json"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def to_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_code(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text.startswith(("sz", "sh")):
        text = text[2:]
    return text


def code_with_market(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text.startswith(("sz", "sh")):
        return text
    pure = normalize_code(text)
    return ("sh" if pure.startswith(("6", "9")) else "sz") + pure


def to_sec_id(value: Any) -> str:
    code = normalize_code(value)
    return ("1." if code.startswith(("6", "9")) else "0.") + code


def fetch_eastmoney(code: str, limit: int, retries: int = 3) -> tuple[list[dict[str, Any]], list[str]]:
    params = {
        "secid": to_sec_id(code),
        "klt": "101",
        "fqt": "1",
        "beg": "0",
        "end": "20500101",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
    }
    full_code = code_with_market(code)
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urllib.parse.urlencode(params)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Referer": f"https://quote.eastmoney.com/{full_code}.html",
        "Accept": "application/json,text/plain,*/*",
        "Connection": "close",
    }
    errors = []
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as response:
                raw = json.loads(response.read().decode("utf-8", errors="replace"))
            rows = parse_rows(raw, limit)
            if rows:
                return rows, errors
            errors.append(f"第{attempt}次返回空K线")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"第{attempt}次失败：{exc}")
        time.sleep(0.25 * attempt)
    return [], errors


def parse_rows(raw: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    rows = []
    for line in ((raw.get("data") or {}).get("klines") or [])[-limit:]:
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
        })
    return rows


def yuan_text(value: Any) -> str:
    number = to_float(value)
    if number is None:
        return "缺失"
    return f"{number / 100000000:.2f}亿元"


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 历史K线东方财富增强影子快照",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 一、汇总",
        "",
    ]
    for key, value in report["汇总"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 二、股票结果", ""])
    for item in report["历史K线"]:
        last = item.get("K线", [{}])[-1] if item.get("K线") else {}
        lines.append(
            f"- {item['名称']}（{item['代码']}）：{item['状态']}；记录数={item['记录数']}；"
            f"最后日期={last.get('日期', '-')}; 最后成交额={yuan_text(last.get('成交额'))}"
        )
    lines.extend(["", "## 三、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 四、下一步计划", "", report["下一步计划"], ""])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    current = load_json(HISTORY_LATEST_JSON)
    source_items = current.get("历史K线", []) or []
    limit = max([int(item.get("记录数") or 0) for item in source_items] + [160])
    results = []
    for item in source_items:
        code = item.get("代码", "")
        rows, errors = fetch_eastmoney(str(code), limit=limit, retries=3)
        has_amount = any((to_float(row.get("成交额")) or 0) > 0 for row in rows)
        results.append({
            "代码": code_with_market(code),
            "名称": item.get("名称", ""),
            "状态": "成功" if rows and has_amount else "失败",
            "数据源": "东方财富历史K线增强影子请求" if rows else "",
            "原最新快照数据源": item.get("数据源", ""),
            "错误": "；".join(errors),
            "记录数": len(rows),
            "含正式成交额": has_amount,
            "K线": rows,
        })
        time.sleep(0.15)
    success = sum(1 for item in results if item["状态"] == "成功")
    with_amount = sum(1 for item in results if item["含正式成交额"])
    total = len(results)
    report = {
        "名称": "历史K线东方财富增强影子快照",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "当前结论": (
            "东方财富增强影子快照全量成功，历史成交额正式源具备替换腾讯兜底的影子验证基础。"
            if total and success == total
            else "东方财富增强影子快照未全量成功，仍需保留腾讯兜底和估算降级。"
        ),
        "读取文件": {
            "当前历史K线最新快照": str(HISTORY_LATEST_JSON),
        },
        "汇总": {
            "股票数量": total,
            "成功数量": success,
            "含正式成交额数量": with_amount,
            "失败数量": total - success,
            "目标记录数": limit,
            "是否可进入220正式口径影子重算": total > 0 and success == total,
        },
        "历史K线": results,
        "安全边界": {
            "联网只读公开接口": True,
            "覆盖历史K线最新快照": False,
            "修改历史K线生成脚本": False,
            "修改220口径": False,
            "修改221短文": False,
            "修改222影子分支": False,
            "修改正式短回复生成器": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "下一步计划": "若验收通过，基于本影子快照重算220价位成交额条件口径；仍不覆盖11历史行情最新快照。",
    }
    latest_json = OUT_DIR / "历史K线东方财富增强影子快照_最新.json"
    latest_md = OUT_DIR / "历史K线东方财富增强影子快照_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "股票数量": total,
        "成功数量": success,
        "含正式成交额数量": with_amount,
        "输出": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
