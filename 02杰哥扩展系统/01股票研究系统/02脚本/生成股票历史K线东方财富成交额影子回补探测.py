# -*- coding: utf-8 -*-
"""
名称：生成股票历史K线东方财富成交额影子回补探测.py
作用：只读探测东方财富历史K线成交额字段，生成样本股正式历史成交额影子回补包。
安全边界：只读公开东方财富历史K线接口；只写 03数据/226历史K线东方财富成交额影子回补探测；不覆盖历史K线最新快照、不改脚本、不发送企业微信、不触发 n8n、不交易。
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
OUT_DIR = DATA / "226历史K线东方财富成交额影子回补探测"
CONDITION_220_JSON = DATA / "220价位成交额条件口径" / "股票价位成交额条件口径预览_最新.json"
TURNOVER_223_JSON = DATA / "223正式成交额源补齐预演" / "股票正式成交额源补齐预演_最新.json"
HISTORY_LATEST_JSON = DATA / "11历史行情" / "重点关注池历史K线快照_最新.json"
HISTORY_SCRIPT = ROOT / "02脚本" / "生成重点关注池历史K线快照.py"


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


def yuan_text(value: Any) -> str:
    number = to_float(value)
    if number is None:
        return "缺失"
    return f"{number / 100000000:.2f}亿元"


def normalize_code(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text.startswith(("sz", "sh")):
        text = text[2:]
    return text


def to_sec_id(code: str) -> str:
    pure = normalize_code(code)
    if pure.startswith(("6", "9")):
        return "1." + pure
    return "0." + pure


def eastmoney_url(code: str, begin: str, end: str) -> str:
    params = {
        "secid": to_sec_id(code),
        "klt": "101",
        "fqt": "1",
        "beg": begin.replace("-", ""),
        "end": end.replace("-", ""),
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
    }
    return "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urllib.parse.urlencode(params)


def fetch_eastmoney_kline(code: str, begin: str, end: str, retries: int = 3) -> tuple[dict[str, Any], list[str]]:
    url = eastmoney_url(code, begin, end)
    errors = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Referer": f"https://quote.eastmoney.com/{'sh' if to_sec_id(code).startswith('1.') else 'sz'}{normalize_code(code)}.html",
        "Accept": "application/json,text/plain,*/*",
        "Connection": "close",
    }
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as response:
                return json.loads(response.read().decode("utf-8", errors="replace")), errors
        except Exception as exc:  # noqa: BLE001
            errors.append(f"第{attempt}次失败：{exc}")
            time.sleep(0.5 * attempt)
    return {}, errors


def parse_rows(raw: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for line in (raw.get("data") or {}).get("klines", []) or []:
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
            "成交额显示": yuan_text(parts[6]),
            "振幅": to_float(parts[7]),
            "涨跌幅": to_float(parts[8]),
            "涨跌额": to_float(parts[9]),
            "换手率": to_float(parts[10]),
        })
    return rows


def compare_with_220(rows: list[dict[str, Any]], condition: dict[str, Any]) -> list[dict[str, Any]]:
    by_date = {row["日期"]: row for row in rows}
    result = []
    for item in condition.get("近5日明细", []) or []:
        date = str(item.get("日期", ""))
        formal = by_date.get(date, {})
        estimated = to_float(item.get("成交额"))
        amount = to_float(formal.get("成交额"))
        delta = None
        delta_rate = None
        if estimated and amount is not None:
            delta = amount - estimated
            delta_rate = delta / estimated * 100
        result.append({
            "日期": date,
            "估算成交额": estimated,
            "估算成交额显示": yuan_text(estimated),
            "东方财富正式成交额": amount,
            "东方财富正式成交额显示": yuan_text(amount),
            "差额": delta,
            "差额显示": yuan_text(delta) if delta is not None else "无法对照",
            "差异比例": round(delta_rate, 4) if delta_rate is not None else None,
            "可回补": amount is not None and amount > 0,
        })
    return result


def average_amount(rows: list[dict[str, Any]]) -> float | None:
    values = [to_float(row.get("东方财富正式成交额")) for row in rows if row.get("可回补")]
    values = [value for value in values if value is not None]
    if not values:
        return None
    return sum(values) / len(values)


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票历史K线东方财富成交额影子回补探测",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 样本股票：{report['样本股票'].get('名称')}（{report['样本股票'].get('市场代码')}）",
        "",
        "## 一、探测结果",
        "",
    ]
    for key, value in report["探测结果"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 二、近5日正式成交额对照", ""])
    for item in report["近5日正式成交额对照"]:
        lines.append(
            f"- {item['日期']}：估算 {item['估算成交额显示']}；"
            f"东方财富正式 {item['东方财富正式成交额显示']}；差异 {item['差额显示']}；可回补={item['可回补']}"
        )
    lines.extend(["", "## 三、脚本增强建议", ""])
    for item in report["脚本增强建议"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、下一步计划", "", report["下一步计划"], ""])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    condition = load_json(CONDITION_220_JSON)
    turnover_223 = load_json(TURNOVER_223_JSON)
    latest_history = load_json(HISTORY_LATEST_JSON)
    sample = condition.get("样本股票") or turnover_223.get("样本股票") or {"名称": "新易盛", "代码": "300502", "市场代码": "sz300502"}
    code = sample.get("代码") or sample.get("市场代码") or "300502"
    dates = [str(item.get("日期", "")) for item in condition.get("近5日明细", []) or [] if item.get("日期")]
    begin = min(dates) if dates else "2026-04-01"
    end = max(dates) if dates else "2026-05-05"
    raw, errors = fetch_eastmoney_kline(str(code), begin, end)
    rows = parse_rows(raw)
    compare = compare_with_220(rows, condition)
    formal_count = sum(1 for item in compare if item["可回补"])
    formal_avg = average_amount(compare)
    formal_threshold = formal_avg * 1.2 if formal_avg is not None else None
    current_history_source = ""
    for item in latest_history.get("历史K线", []) or []:
        if normalize_code(item.get("代码")) == normalize_code(code) or item.get("名称") == sample.get("名称"):
            current_history_source = str(item.get("数据源", ""))
            break
    can_backfill = formal_count == len(compare) and formal_count >= 5
    report = {
        "名称": "股票历史K线东方财富成交额影子回补探测",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "样本股票": sample,
        "当前结论": (
            "东方财富历史K线正式成交额探测成功，样本近5日均可回补；下一步可做历史K线生成脚本请求头与重试增强。"
            if can_backfill
            else "东方财富历史K线正式成交额探测未满足近5日完整回补，继续保留估算降级。"
        ),
        "读取文件": {
            "220价位成交额条件口径": str(CONDITION_220_JSON),
            "223正式成交额源预演": str(TURNOVER_223_JSON),
            "历史K线最新快照": str(HISTORY_LATEST_JSON),
            "历史K线生成脚本": str(HISTORY_SCRIPT),
        },
        "探测请求": {
            "接口": "东方财富公开历史K线接口",
            "代码": code,
            "secid": to_sec_id(str(code)),
            "开始日期": begin,
            "结束日期": end,
            "请求头增强": ["User-Agent", "Referer", "Accept", "Connection: close"],
            "重试次数": 3,
            "错误": errors,
        },
        "探测结果": {
            "是否成功": bool(rows),
            "返回记录数": len(rows),
            "当前历史K线最新快照来源": current_history_source,
            "近5日可回补天数": f"{formal_count}/{len(compare)}",
            "正式近5日均额": yuan_text(formal_avg),
            "正式近5日均额1.2倍": yuan_text(formal_threshold),
            "是否可解除样本估算降级": can_backfill,
        },
        "近5日正式成交额对照": compare,
        "脚本增强建议": [
            "`生成重点关注池历史K线快照.py` 的东方财富请求增加 Referer、Accept、Connection: close 等请求头。",
            "东方财富请求增加 3 次短间隔重试；全部失败后再走腾讯兜底。",
            "腾讯兜底仍保留，但当腾讯兜底导致 `成交额=None` 时，必须继续在 220/221/222 标注估算降级。",
            "增强后先生成影子历史K线快照，不直接覆盖 `重点关注池历史K线快照_最新.json`。",
        ],
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
        "下一步计划": "基于本探测结果，做历史K线生成脚本的影子增强方案；先生成影子历史K线快照和重算220口径，再决定是否替换最新快照。",
    }
    latest_json = OUT_DIR / "股票历史K线东方财富成交额影子回补探测_最新.json"
    latest_md = OUT_DIR / "股票历史K线东方财富成交额影子回补探测_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "返回记录数": len(rows),
        "近5日可回补": f"{formal_count}/{len(compare)}",
        "正式近5日均额": yuan_text(formal_avg),
        "输出": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
