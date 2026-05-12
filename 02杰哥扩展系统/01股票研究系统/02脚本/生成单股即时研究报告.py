# -*- coding: utf-8 -*-
"""
名称：生成单股即时研究报告.py
作用：基于本地行情、技术指标、候选池和数据健康度生成单股可读研究报告。
触发方式：python 生成单股即时研究报告.py --stock 新易盛
依赖：Python标准库；重点关注股票池.json；重点关注池公开行情快照_最新.json；重点关注池技术指标_最新.json；重点关注池候选池_最新.json；股票研究系统状态摘要_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地股票研究数据；只写03数据/23单股即时报告和04日志/单股即时报告；不联网；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建单股即时研究报告脚本。
标识：stock-single-instant-report-generate
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_code(code: str) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz")):
        return text[2:]
    return text.zfill(6) if text.isdigit() else text


def code_with_market(code: str) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz")):
        return text
    if text.startswith(("6", "9")):
        return "sh" + text.zfill(6)
    return "sz" + text.zfill(6)


def stock_pool(root: Path) -> list[dict[str, Any]]:
    focus = load_json(root / "01配置" / "重点关注股票池.json", {"股票池": []})
    merged = load_json(root / "01配置" / "股票池模板.json", {"股票池": []})
    items = merged.get("股票池") or focus.get("股票池", [])
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        key = normalize_code(item.get("代码") or item.get("code") or "")
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def find_stock(root: Path, keyword: str) -> dict[str, Any]:
    text = str(keyword or "").strip()
    stocks = stock_pool(root)
    for item in stocks:
        code = str(item.get("代码") or item.get("code") or "")
        name = str(item.get("名称") or item.get("name") or "")
        if text == name or text in name or name in text:
            return item
        if code and (normalize_code(code) in text or code.lower() in text.lower()):
            return item
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 6:
        code = code_with_market(digits[:6])
        return {"代码": code, "名称": digits[:6], "关注原因": "用户输入代码"}
    raise ValueError(f"未识别股票：{keyword}")


def map_by_code(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {normalize_code(item.get("代码", "")): item for item in items}


def load_candidate_map(root: Path) -> dict[str, dict[str, Any]]:
    data = load_json(root / "03数据" / "14候选池" / "重点关注池候选池_最新.json", {"候选池": {}})
    result: dict[str, dict[str, Any]] = {}
    for layer, items in data.get("候选池", {}).items():
        for item in items:
            result[normalize_code(item.get("代码", ""))] = {**item, "候选层级": layer}
    return result


def load_data_health(root: Path) -> dict[str, Any]:
    status = load_json(root / "03数据" / "16状态摘要" / "股票研究系统状态摘要_最新.json", {})
    health = status.get("数据健康度")
    if health:
        return health
    indicators = load_json(root / "03数据" / "12技术指标" / "重点关注池技术指标_最新.json", {"技术指标": []}).get("技术指标", [])
    total = len(indicators)
    success = sum(1 for item in indicators if item.get("状态") == "成功")
    rate = round(success / total * 100, 2) if total else 0
    return {"健康等级": "优秀" if rate >= 95 else "降级", "股票数量": total, "指标成功数量": success, "成功率": rate}


def value_or_dash(value: Any) -> str:
    if value is None or value == "":
        return "-"
    return str(value)


def to_number(value: Any) -> float | None:
    try:
        if value in (None, "", "无", "-"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def build_research_signal(layer: str, score_value: Any, health_level: str, risks: list[str]) -> dict[str, Any]:
    score = to_number(score_value)
    layer_text = str(layer or "")
    risk_text = "；".join(str(item) for item in risks)
    cap = 3 if health_level in {"暂停", "降级"} else 5
    if score is not None and (score >= 75 or layer_text.startswith("L4")):
        stars = 5
        marker = "★" * stars
        direction = "机会研究信号"
        note = "出现较强关注信号，可作为重点研究对象；仍需人工确认，不构成交易指令。"
        color_name = "红色实心星"
        color_value = "#C62828"
    elif score is not None and (score >= 62 or layer_text.startswith("L5")):
        stars = 4
        marker = "★" * stars
        direction = "机会研究信号"
        note = "具备继续深度研究价值；不自动升级到L4，不构成交易指令。"
        color_name = "红色实心星"
        color_value = "#C62828"
    elif score is not None and (score <= 35 or layer_text.startswith("L7")):
        stars = 5
        marker = "☆" * stars
        direction = "风险复核信号"
        note = "风险或弱势特征较明显，适合重点复核是否退出观察；不构成交易指令。"
        color_name = "绿色空心星"
        color_value = "#2E7D32"
    elif (score is not None and score <= 44) or any(word in risk_text for word in ["破位", "利空", "追高", "回撤"]):
        stars = 2
        marker = "☆" * stars
        direction = "风险复核信号"
        note = "存在需要重点核实的风险点；不构成交易指令。"
        color_name = "绿色空心星"
        color_value = "#2E7D32"
    else:
        stars = 0
        marker = "观察"
        direction = "中性观察"
        note = "当前未形成明确机会或风险复核信号，只保留观察。"
        color_name = "不标色"
        color_value = "#374151"
    stars = min(stars, cap)
    if cap < 5:
        note = f"{note} 当前数据健康度为{health_level}，星级上限降为{cap}星。"
        if marker.startswith("★"):
            marker = "★" * stars
        elif marker.startswith("☆"):
            marker = "☆" * stars
    return {"星级": stars, "标记": marker, "方向": direction, "说明": note, "颜色": color_name, "色值": color_value}


def build_assessment(indicator: dict[str, Any], candidate: dict[str, Any], health: dict[str, Any]) -> dict[str, Any]:
    layer = candidate.get("候选层级") or candidate.get("层级") or "未进入候选池"
    score = candidate.get("系统评分", "无")
    health_level = health.get("健康等级", "未知")
    risks = candidate.get("风险", []) or []
    if health_level in {"暂停", "降级"}:
        conclusion = "数据健康度不足，只适合观察和复盘，不强化结论。"
    elif layer == "L5深度研究":
        conclusion = "进入L5深度研究候选，可继续跟踪，但不自动升级到L4。"
    elif str(layer).startswith("L6"):
        conclusion = "处于L6轻度关注，适合观察，不宜直接提高关注级别。"
    elif str(layer).startswith("L7"):
        conclusion = "处于L7系统过滤，当前只保留复盘观察价值。"
    else:
        conclusion = "未进入候选池，需等待更多数据或人工补充基本面。"
    observations = indicator.get("技术观察") or []
    return {"层级": layer, "系统评分": score, "研究信号": build_research_signal(layer, score, health_level, risks), "初步结论": conclusion, "技术观察": observations}


def markdown_report(report: dict[str, Any]) -> str:
    stock = report["股票"]
    quote = report["行情"]
    indicator = report["技术指标"]
    candidate = report["候选信息"]
    health = report["数据健康度"]
    assess = report["研判"]
    basis = "\n".join(f"- {item}" for item in candidate.get("依据", [])[:6]) or "- 暂无候选池依据。"
    risks = "\n".join(f"- {item}" for item in candidate.get("风险", [])[:6]) or "- 未发现候选池突出风险，仍需人工复核。"
    observations = "\n".join(f"- {item}" for item in assess.get("技术观察", [])[:6]) or "- 暂无技术观察。"
    ma = indicator.get("均线", {})
    macd = indicator.get("MACD", {})
    return f"""# 单股即时研究报告：{stock.get('名称')}（{stock.get('代码')}）

生成时间：{report['生成时间']}

声明：本报告只用于研究辅助，不构成投资建议；不连接券商接口，不自动交易。

## 一、数据健康度

- 健康等级：{health.get('健康等级')}
- 指标成功：{health.get('指标成功数量')}/{health.get('股票数量')}
- 成功率：{health.get('成功率')}%

## 二、行情事实

- 最新价：{value_or_dash(quote.get('最新价'))}
- 昨收：{value_or_dash(quote.get('昨收'))}
- 涨跌幅：{value_or_dash(quote.get('涨跌幅'))}%
- 市盈率：{value_or_dash(quote.get('市盈率'))}
- 换手率：{value_or_dash(quote.get('换手率'))}
- 行业：{value_or_dash(quote.get('行业'))}

## 三、技术指标

- 指标状态：{value_or_dash(indicator.get('状态'))}
- 最新日期：{value_or_dash(indicator.get('最新日期'))}
- 最新收盘：{value_or_dash(indicator.get('最新收盘'))}
- MA5/MA10/MA20/MA60：{value_or_dash(ma.get('MA5'))} / {value_or_dash(ma.get('MA10'))} / {value_or_dash(ma.get('MA20'))} / {value_or_dash(ma.get('MA60'))}
- RSI14：{value_or_dash(indicator.get('RSI14'))}
- MACD DIF/DEA/MACD：{value_or_dash(macd.get('DIF'))} / {value_or_dash(macd.get('DEA'))} / {value_or_dash(macd.get('MACD'))}
- 量比5日：{value_or_dash(indicator.get('量比5日'))}

## 四、系统分层

- 当前层级：{assess.get('层级')}
- 系统评分：{assess.get('系统评分')}
- 研究信号：<span style="color:{assess.get('研究信号', {}).get('色值')};font-weight:bold">{assess.get('研究信号', {}).get('标记')} {assess.get('研究信号', {}).get('方向')}（{assess.get('研究信号', {}).get('颜色')}）</span>
- 信号说明：{assess.get('研究信号', {}).get('说明')}
- 动作边界：{value_or_dash(candidate.get('动作'))}
- 初步结论：{assess.get('初步结论')}

## 五、依据

{basis}

## 六、风险

{risks}

## 七、技术观察

{observations}

## 八、反馈入口

- 继续观察：{stock.get('名称')}，原因
- 暂不关注：{stock.get('名称')}，原因
- 无价值：{stock.get('名称')}，原因
- 确认L4：{stock.get('名称')}，原因（必须人工确认）
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock", default="新易盛", help="股票名称或代码")
    args = parser.parse_args()
    root = module_root()
    stock = find_stock(root, args.stock)
    code = normalize_code(stock.get("代码") or "")
    quote_data = load_json(root / "03数据" / "04数据快照" / "重点关注池公开行情快照_最新.json", {"行情": []})
    indicator_data = load_json(root / "03数据" / "12技术指标" / "重点关注池技术指标_最新.json", {"技术指标": []})
    quote = map_by_code(quote_data.get("行情", [])).get(code, {})
    indicator = map_by_code(indicator_data.get("技术指标", [])).get(code, {})
    candidate = load_candidate_map(root).get(code, {})
    health = load_data_health(root)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "股票": stock,
        "行情": quote,
        "技术指标": indicator,
        "候选信息": candidate,
        "数据健康度": health,
        "研判": build_assessment(indicator, candidate, health),
        "安全边界": {
            "是否联网": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否写旧系统": False,
            "是否写正式库": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_name = f"{stock.get('名称', code)}_{stock.get('代码', code)}".replace("/", "")
    output_dir = root / "03数据" / "23单股即时报告"
    log_dir = root / "04日志" / "单股即时报告"
    json_path = output_dir / f"单股即时研究报告_{safe_name}_最新.json"
    latest_json = output_dir / "单股即时研究报告_最新.json"
    md_path = output_dir / f"单股即时研究报告_{safe_name}_最新.md"
    latest_md = output_dir / "单股即时研究报告_最新.md"
    log_path = log_dir / "stock-single-instant-report-generate-最新.json"
    write_json(json_path, report)
    write_json(latest_json, report)
    write_text(md_path, markdown_report(report))
    write_text(latest_md, markdown_report(report))
    write_json(log_path, {"生成时间": report["生成时间"], "股票": stock, "输出": str(md_path)})
    print(json.dumps({"股票": stock.get("名称"), "代码": stock.get("代码"), "输出": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
