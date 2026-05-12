# -*- coding: utf-8 -*-
"""
名称：生成股票正式成交额源补齐预演.py
作用：对照当前行情、历史K线和220条件口径，生成正式成交额源补齐预演报告。
安全边界：只读本地快照和影子口径；只写 03数据/223正式成交额源补齐预演；不联网、不改正式入口、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "223正式成交额源补齐预演"
QUOTE_JSON = DATA / "04数据快照" / "重点关注池公开行情快照_最新.json"
HISTORY_JSON = DATA / "11历史行情" / "重点关注池历史K线快照_最新.json"
CONDITION_JSON = DATA / "220价位成交额条件口径" / "股票价位成交额条件口径预览_最新.json"
SHORT_TEXT_JSON = DATA / "221微信短文条件口径影子预览" / "股票微信短文条件口径影子预览_最新.json"
SHADOW_BRANCH_JSON = DATA / "222微信短文正式生成器影子分支接入预演" / "微信短文正式生成器影子分支接入预演_最新.json"
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


def normalize_code(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text.startswith(("sz", "sh")):
        text = text[2:]
    return text


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


def find_quote(quote: dict[str, Any], code: str, name: str) -> dict[str, Any]:
    target = normalize_code(code)
    for item in quote.get("行情", []) or []:
        if normalize_code(item.get("代码")) == target or item.get("名称") == name:
            return item
    return {}


def find_history(history: dict[str, Any], code: str, name: str) -> dict[str, Any]:
    target = normalize_code(code)
    for item in history.get("历史K线", []) or []:
        if normalize_code(item.get("代码")) == target or item.get("名称") == name:
            return item
    return {}


def formal_amount_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        amount = to_float(row.get("成交额"))
        result.append({
            "日期": row.get("日期", ""),
            "收盘": row.get("收盘"),
            "成交量": row.get("成交量"),
            "正式成交额": amount,
            "正式成交额显示": yuan_text(amount),
            "是否有正式成交额": amount is not None and amount > 0,
        })
    return result


def summarize_history_sources(history: dict[str, Any]) -> dict[str, Any]:
    items = history.get("历史K线", []) or []
    eastmoney = 0
    tencent = 0
    with_formal_amount = 0
    without_formal_amount = 0
    for item in items:
        source = str(item.get("数据源", ""))
        rows = item.get("K线", []) or []
        has_amount = any((to_float(row.get("成交额")) or 0) > 0 for row in rows)
        if "东方财富" in source:
            eastmoney += 1
        if "腾讯" in source:
            tencent += 1
        if has_amount:
            with_formal_amount += 1
        else:
            without_formal_amount += 1
    return {
        "股票数": len(items),
        "东方财富历史K线数量": eastmoney,
        "腾讯历史K线数量": tencent,
        "含正式成交额数量": with_formal_amount,
        "成交额缺失数量": without_formal_amount,
    }


def compare_recent_five(condition: dict[str, Any], history_item: dict[str, Any]) -> list[dict[str, Any]]:
    estimated_rows = condition.get("近5日明细", []) or []
    history_by_date = {str(row.get("日期", "")): row for row in history_item.get("K线", []) or []}
    result = []
    for row in estimated_rows:
        date = str(row.get("日期", ""))
        history_row = history_by_date.get(date, {})
        formal_amount = to_float(history_row.get("成交额"))
        estimated_amount = to_float(row.get("成交额"))
        delta = None
        if formal_amount is not None and estimated_amount is not None:
            delta = formal_amount - estimated_amount
        result.append({
            "日期": date,
            "估算成交额": estimated_amount,
            "估算成交额显示": yuan_text(estimated_amount),
            "正式成交额": formal_amount,
            "正式成交额显示": yuan_text(formal_amount),
            "差额": delta,
            "差额显示": yuan_text(delta) if delta is not None else "无法对照",
            "当前可替换估算": formal_amount is not None and formal_amount > 0,
        })
    return result


def build_candidate_text(status: str, condition: dict[str, Any], current_amount: str) -> str:
    base = condition.get("基准数据", {})
    avg_amount = base.get("截至昨日近5日均额", "缺失")
    threshold = base.get("截至昨日近5日均额1.2倍", "缺失")
    if status == "历史成交额正式可用":
        return (
            f"成交额口径：当前成交额{current_amount}来自东方财富公开行情快照；"
            f"截至昨日近5日均额{avg_amount}来自东方财富历史K线成交额字段，1.2倍阈值{threshold}。"
        )
    return (
        f"成交额口径：当前成交额{current_amount}来自东方财富公开行情快照；"
        f"截至昨日近5日均额{avg_amount}仍为成交量×收盘价×100估算，"
        "待 `生成重点关注池历史K线快照.py` 东方财富历史K线分支成功回补后再解除降级。"
    )


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票正式成交额源补齐预演",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 样本股票：{report['样本股票'].get('名称')}（{report['样本股票'].get('市场代码')}）",
        "",
        "## 一、源状态",
        "",
    ]
    for key, value in report["正式成交额源状态"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 二、当前行情成交额", ""])
    for key, value in report["当前行情成交额"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、近5日成交额对照", ""])
    for item in report["近5日成交额对照"]:
        lines.append(
            f"- {item['日期']}：估算 {item['估算成交额显示']}；"
            f"正式 {item['正式成交额显示']}；可替换={item['当前可替换估算']}"
        )
    lines.extend(["", "## 四、回补路径", ""])
    for item in report["正式回补路径"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、微信短文候选替换句", "", report["微信短文候选替换句"], "", "## 六、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 七、下一步计划", "", report["下一步计划"], ""])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    quote = load_json(QUOTE_JSON)
    history = load_json(HISTORY_JSON)
    condition = load_json(CONDITION_JSON)
    short_text = load_json(SHORT_TEXT_JSON)
    shadow_branch = load_json(SHADOW_BRANCH_JSON)
    sample = condition.get("样本股票") or short_text.get("样本股票") or {"名称": "新易盛", "代码": "300502", "市场代码": "sz300502"}
    code = sample.get("代码") or sample.get("市场代码") or "300502"
    name = sample.get("名称", "")
    quote_item = find_quote(quote, code, name)
    history_item = find_history(history, code, name)
    recent_rows = history_item.get("K线", []) or []
    recent_five_compare = compare_recent_five(condition, history_item)
    formal_recent = [item for item in recent_five_compare if item["当前可替换估算"]]
    quote_amount = to_float(quote_item.get("成交额"))
    quote_source = str(quote.get("数据源", ""))
    history_source = str(history_item.get("数据源", ""))
    current_status = "当前成交额正式可用" if quote_amount and quote_amount > 0 and "东方财富" in quote_source else "当前成交额缺失"
    history_status = (
        "历史成交额正式可用"
        if len(formal_recent) == len(recent_five_compare) and len(formal_recent) >= 5 and "东方财富" in history_source
        else "历史成交额仍需回补"
    )
    source_status = {
        "当前成交额": current_status,
        "历史成交额": history_status,
        "样本历史K线来源": history_source or "缺失",
        "近5日正式成交额可替换天数": f"{len(formal_recent)}/{len(recent_five_compare)}",
        "是否解除估算降级": history_status == "历史成交额正式可用",
    }
    current_amount_text = yuan_text(quote_amount)
    report = {
        "名称": "股票正式成交额源补齐预演",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "样本股票": sample,
        "当前结论": (
            "当前行情成交额已有东方财富正式快照支撑；样本历史K线当前为腾讯兜底，近5日正式成交额仍缺失，暂不能解除估算降级。"
            if history_status != "历史成交额正式可用"
            else "当前行情成交额和历史近5日成交额均已有正式来源，可进入微信短文小样本替换对照。"
        ),
        "读取文件": {
            "当前公开行情快照": str(QUOTE_JSON),
            "历史K线快照": str(HISTORY_JSON),
            "220价位成交额条件口径": str(CONDITION_JSON),
            "221微信短文影子预览": str(SHORT_TEXT_JSON),
            "222正式生成器影子分支": str(SHADOW_BRANCH_JSON),
            "历史K线生成脚本": str(HISTORY_SCRIPT),
        },
        "正式成交额源状态": source_status,
        "全局历史K线源统计": summarize_history_sources(history),
        "当前行情成交额": {
            "数据源": quote_source,
            "快照生成时间": quote.get("生成时间", ""),
            "最新价": quote_item.get("最新价"),
            "成交量": quote_item.get("成交量"),
            "成交额": quote_amount,
            "成交额显示": current_amount_text,
            "是否正式可用": current_status == "当前成交额正式可用",
        },
        "样本历史K线摘要": {
            "数据源": history_source,
            "快照生成时间": history.get("生成时间", ""),
            "状态": history_item.get("状态", "缺失"),
            "错误": history_item.get("错误", ""),
            "记录数": history_item.get("记录数", len(recent_rows)),
            "最近8日正式成交额状态": formal_amount_rows(recent_rows[-8:]),
        },
        "近5日成交额对照": recent_five_compare,
        "220原始口径": {
            "近5日成交额口径": condition.get("基准数据", {}).get("近5日成交额口径", ""),
            "阈值可信度": condition.get("基准数据", {}).get("阈值可信度", ""),
            "当前结论": condition.get("当前结论", ""),
        },
        "微信短文候选替换句": build_candidate_text(history_status, condition, current_amount_text),
        "正式回补路径": [
            "`生成重点关注池历史K线快照.py` 已包含东方财富历史K线分支，并从 Eastmoney `parts[6]` 解析成交额。",
            "当前样本新易盛历史K线为腾讯兜底，`成交额` 字段为空；因此 220/221/222 仍必须保留估算降级说明。",
            "后续回补应先让东方财富历史K线分支稳定产出样本近5日 `成交额`，再重跑 220、221、222 和本 223 验收。",
            "回补完成前，不把估算阈值升级为强结论，不接入真实发送。"
        ],
        "上游衔接": {
            "221短文是否仍含估算降级": "估算" in json.dumps(short_text, ensure_ascii=False),
            "222影子分支是否存在": bool(shadow_branch),
        },
        "安全边界": {
            "联网刷新行情": False,
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
        "下一步计划": "先做正式成交额源验收；通过后进入小样本对照包。若要解除估算降级，需先稳定回补东方财富历史K线成交额并重跑 220/221/222。",
    }

    latest_json = OUT_DIR / "股票正式成交额源补齐预演_最新.json"
    latest_md = OUT_DIR / "股票正式成交额源补齐预演_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "样本": name,
        "当前成交额": current_amount_text,
        "历史成交额状态": history_status,
        "近5日正式可替换": source_status["近5日正式成交额可替换天数"],
        "输出": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
