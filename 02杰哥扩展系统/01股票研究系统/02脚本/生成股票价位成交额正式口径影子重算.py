# -*- coding: utf-8 -*-
"""
名称：生成股票价位成交额正式口径影子重算.py
作用：基于227东方财富增强影子快照，重算220价位成交额条件口径中的正式成交额阈值影子预览。
安全边界：只读220和227；只写 03数据/228价位成交额正式口径影子重算；不覆盖220、不改221/222、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "228价位成交额正式口径影子重算"
CONDITION_220_JSON = DATA / "220价位成交额条件口径" / "股票价位成交额条件口径预览_最新.json"
SHADOW_HISTORY_227_JSON = DATA / "227历史K线东方财富增强影子快照" / "历史K线东方财富增强影子快照_最新.json"
SHADOW_HISTORY_227_VERIFY = DATA / "227历史K线东方财富增强影子快照" / "历史K线东方财富增强影子快照验收_最新.json"


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


def find_history_item(history: dict[str, Any], sample: dict[str, Any]) -> dict[str, Any]:
    code = sample.get("代码") or sample.get("市场代码") or ""
    name = sample.get("名称", "")
    for item in history.get("历史K线", []) or []:
        if normalize_code(item.get("代码")) == normalize_code(code) or item.get("名称") == name:
            return item
    return {}


def build_recent_rows(condition: dict[str, Any], history_item: dict[str, Any]) -> list[dict[str, Any]]:
    by_date = {str(row.get("日期", "")): row for row in history_item.get("K线", []) or []}
    rows = []
    for old in condition.get("近5日明细", []) or []:
        date = str(old.get("日期", ""))
        formal = by_date.get(date, {})
        old_amount = to_float(old.get("成交额"))
        new_amount = to_float(formal.get("成交额"))
        rows.append({
            "日期": date,
            "收盘": formal.get("收盘", old.get("收盘")),
            "成交量": formal.get("成交量", old.get("成交量")),
            "原估算成交额": old_amount,
            "原估算成交额显示": yuan_text(old_amount),
            "正式成交额": new_amount,
            "正式成交额显示": yuan_text(new_amount),
            "差额": None if old_amount is None or new_amount is None else new_amount - old_amount,
            "口径": "东方财富历史K线正式成交额" if new_amount else "缺失",
        })
    return rows


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def replace_condition_text(text: str, old_avg: str, old_threshold: str, new_avg: str, new_threshold: str) -> str:
    result = text.replace(old_avg, new_avg).replace(old_threshold, new_threshold)
    result = result.replace("估算口径，待正式成交额源回补", "东方财富历史K线正式成交额口径")
    result = result.replace("估算口径", "东方财富历史K线正式成交额口径")
    result = result.replace("待正式成交额源回补", "正式成交额源已影子回补")
    result = result.replace(
        "若历史成交额来自估算，微信端必须写明“成交额阈值为估算，正式成交额源已影子回补”。",
        "历史成交额来自东方财富历史K线正式成交额，微信端可写明“成交额阈值已接入正式历史成交额影子口径”。",
    )
    return result


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票价位成交额正式口径影子重算",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 样本股票：{report['样本股票'].get('名称')}（{report['样本股票'].get('市场代码')}）",
        "",
        "## 一、阈值对照",
        "",
    ]
    for key, value in report["阈值对照"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 二、近5日正式成交额明细", ""])
    for item in report["近5日正式成交额明细"]:
        lines.append(f"- {item['日期']}：正式 {item['正式成交额显示']}；原估算 {item['原估算成交额显示']}；口径={item['口径']}")
    lines.extend(["", "## 三、条件口径正式影子版", ""])
    for item in report["条件口径正式影子版"]:
        lines.append(f"- {item['条件名称']}：{item['可执行表述']}")
    lines.extend(["", "## 四、微信短文可用表达正式影子版", ""])
    for item in report["微信短文可用表达正式影子版"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 六、下一步计划", "", report["下一步计划"], ""])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    condition = load_json(CONDITION_220_JSON)
    history = load_json(SHADOW_HISTORY_227_JSON)
    history_verify = load_json(SHADOW_HISTORY_227_VERIFY)
    sample = condition.get("样本股票", {})
    history_item = find_history_item(history, sample)
    rows = build_recent_rows(condition, history_item)
    formal_values = [to_float(row.get("正式成交额")) for row in rows if to_float(row.get("正式成交额")) is not None]
    formal_values = [value for value in formal_values if value is not None]
    formal_avg = average(formal_values)
    formal_threshold = formal_avg * 1.2 if formal_avg is not None else None
    base = condition.get("基准数据", {})
    old_avg = str(base.get("截至昨日近5日均额", ""))
    old_threshold = str(base.get("截至昨日近5日均额1.2倍", ""))
    new_avg = yuan_text(formal_avg)
    new_threshold = yuan_text(formal_threshold)
    formal_ready = history_verify.get("结论") == "通过" and len(formal_values) == 5
    formal_conditions = []
    for item in condition.get("条件口径", []) or []:
        copied = dict(item)
        copied["可执行表述"] = replace_condition_text(str(item.get("可执行表述", "")), old_avg, old_threshold, new_avg, new_threshold)
        copied["数据依据"] = replace_condition_text(str(item.get("数据依据", "")), old_avg, old_threshold, new_avg, new_threshold)
        formal_conditions.append(copied)
    formal_wechat = [
        replace_condition_text(str(item), old_avg, old_threshold, new_avg, new_threshold)
        for item in condition.get("微信短文可用表达", []) or []
    ]
    report = {
        "名称": "股票价位成交额正式口径影子重算",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "样本股票": sample,
        "当前结论": (
            "已基于227东方财富增强影子快照重算正式成交额阈值；可进入221微信短文正式口径影子重跑。"
            if formal_ready
            else "正式成交额明细不足，继续保留估算降级。"
        ),
        "读取文件": {
            "220原条件口径": str(CONDITION_220_JSON),
            "227东方财富增强影子快照": str(SHADOW_HISTORY_227_JSON),
            "227验收": str(SHADOW_HISTORY_227_VERIFY),
        },
        "阈值对照": {
            "原近5日均额": old_avg,
            "正式近5日均额": new_avg,
            "原近5日均额1.2倍": old_threshold,
            "正式近5日均额1.2倍": new_threshold,
            "口径变化": "按成交量×收盘价×100估算 -> 东方财富历史K线正式成交额",
            "是否可解除估算降级": formal_ready,
        },
        "基准数据正式影子版": {
            **base,
            "截至昨日近5日均额": new_avg,
            "截至昨日近5日均额1.2倍": new_threshold,
            "近5日成交额口径": "东方财富历史K线正式成交额",
            "阈值可信度": "正式成交额影子口径，待220/221/222联动验收后替换",
        },
        "近5日正式成交额明细": rows,
        "条件口径正式影子版": formal_conditions,
        "微信短文可用表达正式影子版": formal_wechat,
        "安全边界": {
            "联网请求": False,
            "覆盖220原文件": False,
            "覆盖历史K线最新快照": False,
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
        "下一步计划": "基于本228正式口径影子重算结果，生成221微信短文正式口径影子重跑；仍不替换正式企业微信入口。",
    }
    latest_json = OUT_DIR / "股票价位成交额正式口径影子重算_最新.json"
    latest_md = OUT_DIR / "股票价位成交额正式口径影子重算_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "正式近5日均额": new_avg,
        "正式1.2倍": new_threshold,
        "是否可解除估算降级": formal_ready,
        "输出": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
