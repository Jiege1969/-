# -*- coding: utf-8 -*-
"""
名称：生成股票验证建议预览.py
作用：读取判断复盘账，生成T5/T20/T60/T120验证建议预览，不自动确认验证结果。
触发方式：python 生成股票验证建议预览.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地账本与行情快照；只写04日志/复盘预览；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不自动修改规则。
标识：stock-validation-suggestion-preview
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


PERIOD_CALENDAR_DAYS = {
    "T5": 7,
    "T10": 14,
    "T20": 28,
    "T60": 84,
    "T120": 168,
}


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


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
            return suffix + num
    if text.isdigit():
        if text.startswith(("6", "9")):
            return "sh" + text.zfill(6)
        if text.startswith(("4", "8")):
            return "bj" + text.zfill(6)
        return "sz" + text.zfill(6)
    return text


def collect_dicts(value: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(value, dict):
        rows.append(value)
        for child in value.values():
            rows.extend(collect_dicts(child))
    elif isinstance(value, list):
        for child in value:
            rows.extend(collect_dicts(child))
    return rows


def find_quote(snapshot: Any, code: str, name: str) -> dict[str, Any]:
    target = normalize_code(code)
    for item in collect_dicts(snapshot):
        item_code = normalize_code(item.get("代码") or item.get("code") or item.get("股票代码"))
        item_name = str(item.get("名称") or item.get("name") or item.get("股票名称") or "")
        if item_code == target or (name and item_name == name):
            if item.get("最新价") is not None or item.get("现价") is not None:
                return item
    return {}


def to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(str(value).replace("%", "").replace(",", ""))
    except (TypeError, ValueError):
        return None


def parse_date(text: Any) -> datetime | None:
    try:
        return datetime.strptime(str(text), "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def period_result(record: dict[str, Any], period: str, now: datetime, snapshot: Any) -> dict[str, Any]:
    report_date = parse_date(record.get("报告日期"))
    if not report_date:
        return {"验证周期": period, "状态": "未验证", "原因": "报告日期缺失或格式错误"}
    elapsed_days = (now.date() - report_date.date()).days
    required_days = PERIOD_CALENDAR_DAYS.get(period, 28)
    if elapsed_days < required_days:
        return {
            "验证周期": period,
            "状态": "未到期",
            "已过自然日": elapsed_days,
            "参考到期自然日": required_days,
            "原因": "尚未达到该周期的近似自然日窗口",
        }

    code = record.get("股票代码")
    name = record.get("股票名称")
    quote = find_quote(snapshot, code, name)
    base_price = to_float(record.get("基准价格"))
    current_price = to_float(quote.get("最新价") or quote.get("现价"))
    if base_price is None or current_price is None or base_price <= 0:
        return {
            "验证周期": period,
            "状态": "未验证",
            "原因": "缺少基准价格或当前行情价格，不能计算区间表现",
        }

    pct = (current_price / base_price - 1) * 100
    if pct >= 5:
        suggestion = "有效"
    elif pct >= 0:
        suggestion = "部分有效"
    else:
        suggestion = "无效"
    return {
        "验证周期": period,
        "状态": "待人工确认",
        "个股区间涨跌幅": round(pct, 2),
        "基准价格": base_price,
        "当前价格": current_price,
        "初步验证建议": suggestion,
        "说明": "该建议只基于价格表现粗算，正式结果需结合行业、大盘和人工复核。",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票验证建议预览 - {report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 判断复盘记录数：{report['判断复盘记录数']}",
        f"- 生成建议数：{report['生成建议数']}",
        "- 本文件只做预览，不自动确认验证结果，不自动修改规则。",
        "",
        "## 明细",
        "",
    ]
    if not report["建议预览"]:
        lines.append("- 暂无可生成验证建议的记录。")
    for item in report["建议预览"]:
        lines.append(f"### {item.get('股票名称')}({item.get('股票代码')})")
        lines.append(f"- 判断日期：{item.get('报告日期')}")
        lines.append(f"- 判断主因：{item.get('判断主因')}")
        lines.append(f"- 关注等级：{item.get('关注等级')}")
        for result in item.get("周期建议", []):
            lines.append(f"- {result.get('验证周期')}：{result.get('状态')}；{result.get('初步验证建议', result.get('原因', ''))}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    replay_path = root / "04日志" / "复盘" / "判断复盘账_最新.json"
    quote_path = root / "03数据" / "04数据快照" / "重点关注池公开行情快照_最新.json"
    out_dir = root / "04日志" / "复盘"

    replay_records = load_json(replay_path, [])
    if not isinstance(replay_records, list):
        replay_records = []
    quote_snapshot = load_json(quote_path, {})

    previews: list[dict[str, Any]] = []
    for record in replay_records:
        periods = record.get("应验证周期") or []
        if not isinstance(periods, list):
            periods = [str(periods)]
        item = {
            "股票代码": record.get("股票代码"),
            "股票名称": record.get("股票名称"),
            "报告日期": record.get("报告日期"),
            "判断主因": record.get("判断主因"),
            "关注等级": record.get("关注等级"),
            "原始报告路径": record.get("原始报告路径"),
            "周期建议": [period_result(record, period, now, quote_snapshot) for period in periods],
        }
        previews.append(item)

    report = {
        "名称": "股票验证建议预览",
        "版本": "v1.0",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "判断复盘账": str(replay_path),
        "行情快照": str(quote_path),
        "判断复盘记录数": len(replay_records),
        "生成建议数": len(previews),
        "说明": "仅生成验证建议预览，不写入正式验证结果账，不自动修改规则。",
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写正式库": False,
        },
        "建议预览": previews,
    }

    latest_json = out_dir / "验证建议预览_最新.json"
    stamp_json = out_dir / f"验证建议预览_{stamp}.json"
    latest_md = out_dir / "验证建议预览_最新.md"
    stamp_md = out_dir / f"验证建议预览_{stamp}.md"
    write_json(latest_json, report)
    write_json(stamp_json, report)
    markdown = build_markdown(report)
    write_text(latest_md, markdown)
    write_text(stamp_md, markdown)

    print(json.dumps({
        "状态": "完成",
        "判断复盘记录数": len(replay_records),
        "生成建议数": len(previews),
        "输出": str(latest_json),
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
