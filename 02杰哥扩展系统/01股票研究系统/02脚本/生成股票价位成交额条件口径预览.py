# -*- coding: utf-8 -*-
"""
名称：生成股票价位成交额条件口径预览.py
作用：把股票报告中的“观察、转强、失败、成交额阈值”转成可执行、可复盘、可解释的条件口径。
安全边界：只读报告、行情快照、历史K线和技术指标；只写 03数据/220价位成交额条件口径；不改正式入口，不重启服务，不发送企业微信，不触发 n8n，不调用券商接口，不自动交易。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "220价位成交额条件口径"

REPORT_MD = DATA / "135分层日报" / "单股标准报告v2_最新.md"
MARKET_JSON = DATA / "04数据快照" / "重点关注池公开行情快照_最新.json"
KLINE_JSON = DATA / "11历史行情" / "重点关注池历史K线快照_最新.json"
TECH_JSON = DATA / "12技术指标" / "重点关注池技术指标_最新.json"
EVIDENCE_MAP_JSON = DATA / "219股票报告证据源映射" / "股票报告证据源映射预览_最新.json"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


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


def extract_stock(report_text: str) -> dict[str, str]:
    match = re.search(r"([^\n（）()]+)[（(]([a-z]{2}\d{6})[）)]", report_text, re.I)
    if not match:
        return {"名称": "未知", "市场代码": "未知", "代码": "未知"}
    market_code = match.group(2).lower()
    return {"名称": match.group(1).strip(), "市场代码": market_code, "代码": market_code[-6:]}


def extract_float(pattern: str, text: str, default: float = 0.0) -> float:
    match = re.search(pattern, text)
    if not match:
        return default
    return float(match.group(1))


def find_by_code(rows: list[dict[str, Any]], code: str) -> dict[str, Any]:
    for row in rows:
        raw = str(row.get("代码", "")).lower()
        if raw.endswith(code):
            return row
    return {}


def amount_from_row(row: dict[str, Any]) -> tuple[float | None, str]:
    amount = row.get("成交额")
    if isinstance(amount, (int, float)) and amount > 0:
        return float(amount), "东方财富历史K线正式成交额"
    volume = row.get("成交量")
    close = row.get("收盘")
    if isinstance(volume, (int, float)) and isinstance(close, (int, float)) and volume > 0 and close > 0:
        return float(volume) * float(close) * 100.0, "按成交量×收盘价×100估算"
    return None, "缺成交额且无法估算"


def yuan_to_yi(amount: float | None) -> str:
    if amount is None:
        return "缺失"
    return f"{amount / 100000000:.2f}亿元"


def build_markdown(preview: dict[str, Any]) -> str:
    lines = [
        "# 股票价位成交额条件口径预览",
        "",
        f"- 生成时间：{preview['生成时间']}",
        f"- 样本股票：{preview['样本股票']['名称']}({preview['样本股票']['市场代码']})",
        f"- 当前结论：{preview['当前结论']}",
        "",
        "## 一、基准数据",
        "",
    ]
    base = preview["基准数据"]
    for key, value in base.items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 二、条件口径", ""])
    for item in preview["条件口径"]:
        lines.extend([
            f"### {item['条件名称']}",
            f"- 规则：{item['可执行表述']}",
            f"- 数据依据：{item['数据依据']}",
            f"- 复盘字段：{', '.join(item['复盘字段'])}",
            "",
        ])
    lines.extend(["## 三、微信短文可用表达", ""])
    for item in preview["微信短文可用表达"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、禁用表达", ""])
    for item in preview["禁用表达"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、下一步", "", preview["下一步计划"], ""])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    report_text = read_text(REPORT_MD)
    market = load_json(MARKET_JSON, {})
    kline = load_json(KLINE_JSON, {})
    tech = load_json(TECH_JSON, {})
    evidence = load_json(EVIDENCE_MAP_JSON, {})
    stock = extract_stock(report_text)
    code = stock["代码"]

    market_row = find_by_code(market.get("行情", []), code)
    kline_row = find_by_code(kline.get("历史K线", []), code)
    tech_row = find_by_code(tech.get("技术指标", []), code)
    rows = kline_row.get("K线", []) if isinstance(kline_row, dict) else []
    last_rows = rows[-5:]
    amount_rows: list[dict[str, Any]] = []
    amount_values: list[float] = []
    amount_basis_set: set[str] = set()
    for row in last_rows:
        amount, basis = amount_from_row(row)
        amount_basis_set.add(basis)
        if amount is not None:
            amount_values.append(amount)
        amount_rows.append({
            "日期": row.get("日期"),
            "收盘": row.get("收盘"),
            "成交量": row.get("成交量"),
            "成交额": amount,
            "成交额显示": yuan_to_yi(amount),
            "口径": basis,
        })

    avg5_amount = sum(amount_values) / len(amount_values) if amount_values else None
    avg5_amount_12 = avg5_amount * 1.2 if avg5_amount else None
    current_amount = market_row.get("成交额") if isinstance(market_row.get("成交额"), (int, float)) else None

    low_support = extract_float(r"承接区：([0-9.]+)元-", report_text)
    high_support = extract_float(r"承接区：[0-9.]+元-([0-9.]+)元", report_text)
    turn_strong = extract_float(r"转强线：([0-9.]+)元", report_text)
    risk_line = extract_float(r"风险线：([0-9.]+)元", report_text)
    ma = tech_row.get("均线", {}) if isinstance(tech_row, dict) else {}

    amount_basis = "；".join(sorted(amount_basis_set)) if amount_basis_set else "缺少近5日成交额"
    is_estimated_amount = "估算" in amount_basis or "缺" in amount_basis
    amount_reliability = "估算口径，待正式成交额源回补" if is_estimated_amount else "东方财富历史K线正式成交额口径"
    current_conclusion = (
        "已把观察、转强、失败和成交额阈值转成可执行口径；历史K线成交额已来自东方财富正式字段，近5日成交额阈值可按正式口径使用。"
        if not is_estimated_amount
        else "已把观察、转强、失败和成交额阈值转成可执行口径；因历史K线成交额缺失，近5日成交额阈值使用估算并明确降级。"
    )
    amount_credibility_statement = (
        f"当前快照成交额为{yuan_to_yi(current_amount)}；截至昨日近5日均额为{yuan_to_yi(avg5_amount)}；历史成交额来自东方财富历史K线正式字段，微信端可写明成交额阈值为正式历史成交额口径。"
        if not is_estimated_amount
        else f"当前快照成交额为{yuan_to_yi(current_amount)}；截至昨日近5日均额为{yuan_to_yi(avg5_amount)}；若历史成交额来自估算，微信端必须写明“成交额阈值为估算，待正式成交额源回补”。"
    )

    conditions = [
        {
            "条件名称": "观察条件",
            "可执行表述": f"未来3个有效交易日内，至少2个交易日收盘价不低于{low_support:.2f}元；同时任一交易日收盘价不得低于{risk_line:.2f}元；若出现下跌日，该日成交额不高于截至昨日近5日均额1.2倍（{yuan_to_yi(avg5_amount_12)}，{amount_reliability}）。",
            "数据依据": f"承接区来自报告 {low_support:.2f}-{high_support:.2f}元；截至昨日近5日为{amount_rows[0]['日期'] if amount_rows else '缺失'}至{amount_rows[-1]['日期'] if amount_rows else '缺失'}；近5日均额={yuan_to_yi(avg5_amount)}。",
            "复盘字段": ["观察开始日", "3日内收盘不低于承接下沿天数", "下跌日成交额", "是否触发风险线", "观察结论"],
        },
        {
            "条件名称": "转强条件",
            "可执行表述": f"连续2个有效交易日收盘价高于{turn_strong:.2f}元，且这2个交易日中至少1日成交额不低于截至昨日近5日均额（{yuan_to_yi(avg5_amount)}，{amount_reliability}）。",
            "数据依据": f"转强线来自报告 {turn_strong:.2f}元；成交额基准使用截至昨日、不含当天的近5日均额。",
            "复盘字段": ["连续收盘高于转强线天数", "成交额是否达到近5日均额", "是否形成转强确认"],
        },
        {
            "条件名称": "失败条件",
            "可执行表述": f"任一有效交易日收盘价低于{risk_line:.2f}元，直接判定观察失败；或收盘价低于{low_support:.2f}元后，后续2个有效交易日内仍未重新收回{low_support:.2f}元，降低观察优先级；若5个有效交易日内始终不能收复{high_support:.2f}元，也降低观察优先级。",
            "数据依据": f"风险线来自报告 {risk_line:.2f}元；承接区上下沿来自报告 {low_support:.2f}-{high_support:.2f}元。",
            "复盘字段": ["是否跌破风险线", "跌破承接下沿后2日是否收回", "5日内是否收复承接上沿", "降级原因"],
        },
        {
            "条件名称": "成交额可信度条件",
            "可执行表述": amount_credibility_statement,
            "数据依据": f"当前成交额来自{market.get('数据源', '未知')}；近5日历史来源为{kline_row.get('数据源', '未知')}；近5日成交额口径={amount_basis}。",
            "复盘字段": ["当前成交额", "近5日均额", "成交额口径", "是否需要回补正式成交额源"],
        },
    ]

    wechat_lines = [
        f"观察条件：未来3个有效交易日内，至少2天收盘不低于{low_support:.2f}元；若下跌日成交额高于{yuan_to_yi(avg5_amount_12)}，观察降级。",
        f"转强条件：连续2天收盘高于{turn_strong:.2f}元，且至少1天成交额不低于{yuan_to_yi(avg5_amount)}。",
        f"失败条件：收盘低于{risk_line:.2f}元；或跌破{low_support:.2f}元后2个有效交易日内未收回；或5个有效交易日内不能收复{high_support:.2f}元。",
        f"成交额口径：当前{yuan_to_yi(current_amount)}；近5日均额{yuan_to_yi(avg5_amount)}，当前历史成交额为{amount_reliability}。",
    ]

    preview = {
        "名称": "股票价位成交额条件口径预览",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "样本股票": stock,
        "当前结论": current_conclusion,
        "读取文件": {
            "报告正文": str(REPORT_MD),
            "公开行情快照": str(MARKET_JSON),
            "历史K线": str(KLINE_JSON),
            "技术指标": str(TECH_JSON),
            "证据源映射": str(EVIDENCE_MAP_JSON),
        },
        "基准数据": {
            "当前价": f"{market_row.get('最新价', '缺失')}元",
            "当前成交额": yuan_to_yi(current_amount),
            "承接区": f"{low_support:.2f}元-{high_support:.2f}元",
            "转强线": f"{turn_strong:.2f}元",
            "风险线": f"{risk_line:.2f}元",
            "MA5": ma.get("MA5", "缺失"),
            "MA10": ma.get("MA10", "缺失"),
            "MA20": ma.get("MA20", "缺失"),
            "MA60": ma.get("MA60", "缺失"),
            "截至昨日近5日均额": yuan_to_yi(avg5_amount),
            "截至昨日近5日均额1.2倍": yuan_to_yi(avg5_amount_12),
            "近5日成交额口径": amount_basis,
            "阈值可信度": amount_reliability,
        },
        "近5日明细": amount_rows,
        "条件口径": conditions,
        "微信短文可用表达": wechat_lines,
        "禁用表达": [
            "稳住",
            "有承接",
            "放量",
            "转强",
            "继续观察",
            "资金活跃",
            "趋势不错",
        ],
        "降级规则": [
            "缺少正式成交额源时，成交额阈值必须标为估算，不能作为强结论。",
            "缺少公告、财报、行业景气和人工复核时，不得输出强推荐、长期价值或盈利改善肯定结论。",
            "微信端只输出结论、条件、阈值和风险，不展开复杂技术分析过程。",
        ],
        "继承证据源映射结论": evidence.get("当前结论", "未读取到证据源映射结论"),
        "安全边界": {
            "修改正式入口": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
            "本步骤仅生成口径预览": True,
        },
        "下一步计划": "将本口径模板接入微信短文影子生成器预览；在正式接入前先补正式成交额源、价位公式溯源卡和人工复核字段。",
    }

    latest_json = OUT_DIR / "股票价位成交额条件口径预览_最新.json"
    latest_md = OUT_DIR / "股票价位成交额条件口径预览_最新.md"
    write_json(latest_json, preview)
    write_text(latest_md, build_markdown(preview))

    print(json.dumps({
        "状态": "完成",
        "样本股票": stock,
        "近5日均额": yuan_to_yi(avg5_amount),
        "近5日均额1.2倍": yuan_to_yi(avg5_amount_12),
        "阈值可信度": amount_reliability,
        "输出": {"json": str(latest_json), "markdown": str(latest_md)},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
