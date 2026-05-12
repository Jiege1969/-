# -*- coding: utf-8 -*-
"""
名称：生成华虹公司v21影子样板.py
作用：基于现有本地股票研究数据，生成华虹公司股票报告 v2.1 三层影子样板与微信短文本地预览。
触发方式：python 生成华虹公司v21影子样板.py
所属系统：02 杰哥扩展系统 / 01 股票研究系统；复盘字段预演归入 03 进化系统。
安全边界：只读本地研究数据；只写 03数据/186报告v21影子样板；不改正式入口；不重启 19300/19302；
不发送企业微信；不触发 n8n；不写正式库；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


STOCK_CODE = "sh688347"
DISPLAY_CODE = "688347.SH"
STOCK_NAME = "华虹公司"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def find_stock(items: Any, code: str = STOCK_CODE, name: str = STOCK_NAME) -> dict[str, Any]:
    if not isinstance(items, list):
        return {}
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("代码") == code or item.get("展示代码") == DISPLAY_CODE or item.get("名称") == name:
            return item
    return {}


def num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "待核验"


def pct(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}%"
    except (TypeError, ValueError):
        return "待核验"


def yi(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value) / 100000000:.{digits}f}亿元"
    except (TypeError, ValueError):
        return "待核验"


def build_markdown(report: dict[str, Any]) -> str:
    short_text = report["微信短文层"]["短文"]
    backend = report["后台完整分析层"]
    judgement = report["研究判断层"]
    review = report["复盘字段预演"]
    lines = [
        f"# {STOCK_NAME}（{DISPLAY_CODE}）股票报告 v2.1 影子样板",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 样板模式：{report['样板模式']}",
        f"- 结论可信度：{judgement['结论可信度']}",
        f"- 运行边界：{report['运行边界说明']}",
        "",
        "## 微信短文层",
        "",
        short_text,
        "",
        "## 研究判断层",
        "",
        f"- 关注级别：{judgement['关注级别']}",
        f"- 财务支持度：{judgement['财务支持度']}",
        f"- 估值状态：{judgement['估值状态']}",
        f"- 结论可信度：{judgement['结论可信度']}",
        f"- 验证周期：{judgement['验证周期']}",
        f"- 成功条件：{judgement['成功条件']}",
        f"- 失败条件：{judgement['失败条件']}",
        f"- 降级原因：{judgement['降级原因']}",
        "",
        "## 后台完整分析层",
        "",
        "### 公司与行业",
        "",
        f"- 公司定位：{backend['公司与行业']['公司定位']}",
        f"- 行业口径：{backend['公司与行业']['行业口径']}",
        f"- 数据来源：{'; '.join(backend['公司与行业']['数据来源'])}",
        "",
        "### 财务与估值",
        "",
    ]
    for key, value in backend["财务与估值"].items():
        lines.append(f"- {key}：{value}")
    lines.extend([
        "",
        "### 价位与成交额",
        "",
    ])
    for key, value in backend["价位与成交额"].items():
        lines.append(f"- {key}：{value}")
    lines.extend([
        "",
        "### 数据缺口",
        "",
    ])
    for gap in backend["数据缺口"]:
        lines.append(f"- {gap}")
    lines.extend([
        "",
        "## 复盘字段预演",
        "",
    ])
    for key, value in review.items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    data_dir = root / "03数据"
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    l7 = load_json(data_dir / "132可交易过滤池" / "L7可交易过滤池_最新.json")
    l6 = load_json(data_dir / "133行业主题观察池" / "L6行业主题观察池_最新.json")
    l5 = load_json(data_dir / "134深度研究池" / "L5深度研究池_最新.json")
    ai_daily = load_json(data_dir / "135分层日报" / "AI分析报告_最新.json")
    company_snapshot = load_json(data_dir / "166公司经营快照" / "公司经营快照_最新.json")

    l7_stock = find_stock(l7.get("股票池"))
    l6_stock = find_stock(l6.get("股票池"))
    l5_stock = find_stock(l5.get("股票池"))
    ai_stock = find_stock(ai_daily.get("分析结果"))
    snapshot_stock = find_stock(company_snapshot.get("股票快照"))

    finance = snapshot_stock.get("财报快照", {}) if snapshot_stock else {}
    company_profile = snapshot_stock.get("公司概况", {}) if snapshot_stock else {}
    evidence_status = snapshot_stock.get("证据状态", {}) if snapshot_stock else {}
    source_list = snapshot_stock.get("数据来源", []) if snapshot_stock else []

    close = num(l7_stock.get("收盘价") or l6_stock.get("收盘价") or l5_stock.get("收盘价") or 141.0)
    observation_low = 138.18
    observation_high = 139.56
    risk_line = 132.54
    turn_line = 152.28
    middle_line = 145.00
    avg5_amount = num(l7_stock.get("近5日日均成交额") or l6_stock.get("近5日日均成交额") or l5_stock.get("近5日日均成交额"))
    avg20_amount = num(l7_stock.get("近20日日均成交额") or l6_stock.get("近20日日均成交额") or l5_stock.get("近20日日均成交额"))
    avg5_yi = avg5_amount / 100000000
    down_amount_limit_yi = avg5_yi * 1.2
    amount_is_estimated = bool(l7_stock.get("成交额是否估算") or l6_stock.get("成交额是否估算") or l5_stock.get("成交额是否估算"))
    amount_source_note = "本地腾讯复权日线估算口径，待原始行情源核验" if amount_is_estimated else "本地行情口径"

    revenue = num(finance.get("营业收入_亿元"))
    net_profit = num(finance.get("归母净利润_亿元"))
    attributable_margin = net_profit / revenue * 100 if revenue else 0.0
    system_net_margin = finance.get("净利率")
    pe_status = "PE超600倍（来自当前v2标准样例口径，正式报告需接入估值源复核）"
    pb_status = "PB待接入，行业均值/历史分位待核验"

    gaps = []
    if not finance:
        gaps.append("财报快照未接入，结论可信度必须降级。")
    if "2026Q1营业收入_亿元" not in finance:
        gaps.append("最新季度营收、净利润未接入：当前只用2025年报口径，需补2026Q1或最新季报。")
    if pb_status.startswith("PB待"):
        gaps.append("PB、行业估值均值、历史分位未接入：估值判断只能写偏高风险，不能写安全边际。")
    if amount_is_estimated:
        gaps.append("成交额为本地估算口径：微信阈值可展开数字，但必须标注待原始行情源核验。")
    gaps.append("利润下滑主因待核验：不能自行归因于折旧、研发或毛利变化。")

    observation_condition = (
        f"{observation_low:.2f}-{observation_high:.2f}元区间；未来3个交易日内至少2个交易日收盘价 >= {observation_low:.2f}元；"
        f"任一下跌日成交额 <= 截至昨日近5日均额1.2倍，即 <= {down_amount_limit_yi:.2f}亿元。"
        f"近5日均额不含当日 = {avg5_yi:.2f}亿元，{amount_source_note}。"
    )
    turn_condition = (
        f"连续2个交易日收盘价 >= {turn_line:.2f}元，且这2天成交额均 >= 截至昨日近5日均额，即 >= {avg5_yi:.2f}亿元。"
        f"成交额口径：不含当日，{amount_source_note}。"
    )
    fail_condition = (
        f"收盘价 < {risk_line:.2f}元；或收盘价 < {observation_low:.2f}元后2个交易日内未重新收回{observation_low:.2f}元；"
        f"或触发观察区后5个交易日内仍未收上{middle_line:.2f}元。"
    )

    short_text = "\n\n".join([
        f"【{STOCK_NAME}】可观察，不追高。",
        "逻辑：半导体国产化和特色晶圆代工卡位有研究价值；但利润弱、ROE极低，估值已经透支，不能按强推荐处理。",
        (
            f"财务：2025年营收{revenue:.2f}亿元，同比{pct(finance.get('营业收入同比'))}；"
            f"归母净利{net_profit:.2f}亿元，同比{pct(finance.get('利润同比'))}；"
            f"毛利率{pct(finance.get('毛利率'))}，ROE{pct(finance.get('ROE'))}；"
            f"系统净利率口径{pct(system_net_margin)}，归母净利/营收约{attributable_margin:.2f}%，口径差异先记为待核验。"
        ),
        f"观察条件：{observation_condition}",
        f"转强条件：{turn_condition}",
        f"失败条件：{fail_condition}",
        "风险：PE超600倍，PB和行业分位未接入；盈利效率尚未证明，不适合价值配置，只能作为研究样本跟踪。",
    ])

    backend_layer = {
        "公司与行业": {
            "公司定位": company_profile.get("核心业务", "待核验"),
            "行业地位": company_profile.get("行业地位", "待核验"),
            "行业口径": l6_stock.get("行业") or l5_stock.get("行业") or snapshot_stock.get("申万一级行业", "待核验"),
            "数据来源": source_list or ["当前L5/L6/L7本地研究池", "公司经营快照"],
            "证据状态": evidence_status,
        },
        "财务与估值": {
            "近三年营收与净利润": "当前系统仅接入2025年报关键值；2023-2024逐年序列待补齐。",
            "2025营业收入": f"{revenue:.2f}亿元，同比{pct(finance.get('营业收入同比'))}",
            "2025归母净利润": f"{net_profit:.2f}亿元，同比{pct(finance.get('利润同比'))}",
            "2025扣非净利润": f"{fmt(finance.get('扣非净利润_亿元'))}亿元",
            "2025毛利率": pct(finance.get("毛利率")),
            "2025净利率": f"系统口径{pct(system_net_margin)}；归母净利/营收约{attributable_margin:.2f}%，口径差异待财报正文核验",
            "2025ROE": pct(finance.get("ROE")),
            "2025经营现金流净额": f"{fmt(finance.get('经营现金流净额_亿元'))}亿元",
            "现金流质量说明": finance.get("现金流质量说明", "待核验"),
            "最新季度营收净利": "待接入",
            "利润下滑主因": "待核验，报告不得自行归因",
            "PE": pe_status,
            "PB与估值对比": pb_status,
        },
        "价位与成交额": {
            "报告基准日": l7.get("数据日期") or l6.get("数据日期") or l5.get("数据日期") or "2026-04-30",
            "当前价": f"{close:.2f}元",
            "观察区": f"{observation_low:.2f}-{observation_high:.2f}元",
            "风险线": f"{risk_line:.2f}元",
            "转强线": f"{turn_line:.2f}元",
            "弱势震荡降级线": f"{middle_line:.2f}元",
            "截至昨日近5日均额": f"{avg5_yi:.2f}亿元（不含当日，{amount_source_note}）",
            "下跌日成交额上限": f"{down_amount_limit_yi:.2f}亿元（近5日均额1.2倍）",
            "近20日均额": yi(avg20_amount),
            "资金活跃度分": fmt(l6_stock.get("资金活跃度分") or l5_stock.get("资金活跃度分")),
            "行业强度分": fmt(l6_stock.get("行业强度分") or l5_stock.get("行业强度分")),
            "技术面分": fmt(l5_stock.get("技术面分")),
            "AI研究小结": ai_stock.get("analysis_text", "待核验"),
        },
        "数据缺口": gaps,
    }

    judgement_layer = {
        "关注级别": "可观察，不追高",
        "判断主因": "行业与公司卡位有研究价值；短期资金与价格强度较高；财务与估值不支持强结论。",
        "财务支持度": "部分支持偏弱：营收增长和经营现金流为正，但净利润、ROE、估值不支持强推荐。",
        "估值状态": "严重偏高：PE超600倍，PB与行业分位待接入。",
        "结论可信度": "中偏低：财报关键项已接入，但最新季度、估值对比、成交额原始口径仍待核验。",
        "验证周期": "价格条件按未来3个交易日/5个交易日验证；财务条件等最新季报或估值源补齐后复核。",
        "成功条件": observation_condition + "；" + turn_condition,
        "失败条件": fail_condition,
        "降级原因": "成交额为估算口径、PB/行业估值缺失、最新季度缺失、利润下滑主因待核验。",
    }

    output_dir = data_dir / "186报告v21影子样板"
    detail_path = output_dir / "华虹公司v21影子样板_最新.md"
    review_layer = {
        "股票": f"{STOCK_NAME}({DISPLAY_CODE})",
        "原始结论": "可观察，不追高",
        "判断主因": judgement_layer["判断主因"],
        "财务支持度": judgement_layer["财务支持度"],
        "估值状态": judgement_layer["估值状态"],
        "观察条件": observation_condition,
        "转强条件": turn_condition,
        "失败条件": fail_condition,
        "验证周期": judgement_layer["验证周期"],
        "详情路径": str(detail_path),
        "验证结果": "待人工确认；本阶段只生成影子预览，不自动确认验证结果，不自动修改规则。",
    }

    report = {
        "名称": "华虹公司股票报告v2.1影子样板",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "样板模式": "shadow_preview_only",
        "涉及系统": ["02扩展系统/股票研究系统", "03进化系统/复盘字段预演", "00总管系统/边界记录"],
        "股票": {"代码": STOCK_CODE, "展示代码": DISPLAY_CODE, "名称": STOCK_NAME},
        "后台完整分析层": backend_layer,
        "研究判断层": judgement_layer,
        "微信短文层": {
            "格式": "6+1段式",
            "短文": short_text,
            "长度": len(short_text),
            "阈值展开": {
                "近5日均额_亿元": round(avg5_yi, 2),
                "下跌日1点2倍阈值_亿元": round(down_amount_limit_yi, 2),
                "观察区下沿": observation_low,
                "观察区上沿": observation_high,
                "风险线": risk_line,
                "转强线": turn_line,
            },
        },
        "复盘字段预演": review_layer,
        "安全边界": {
            "是否修改运行入口": False,
            "是否重启19300": False,
            "是否重启19302": False,
            "是否发送企业微信": False,
            "是否触发n8n": False,
            "是否写正式库": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
        "运行边界说明": "本阶段只生成本地影子样板和微信短文预览，不替换正式19300/19302入口，不发送企业微信真实消息。",
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"华虹公司v21影子样板_{stamp}.json"
    md_path = output_dir / f"华虹公司v21影子样板_{stamp}.md"
    short_path = output_dir / f"华虹公司v21微信短文预览_{stamp}.md"
    review_path = output_dir / f"华虹公司v21复盘字段预演_{stamp}.json"

    latest_json = output_dir / "华虹公司v21影子样板_最新.json"
    latest_md = output_dir / "华虹公司v21影子样板_最新.md"
    latest_short = output_dir / "华虹公司v21微信短文预览_最新.md"
    latest_review = output_dir / "华虹公司v21复盘字段预演_最新.json"

    markdown = build_markdown(report)
    short_markdown = "# 华虹公司 v2.1 微信短文预览\n\n" + short_text + "\n"

    for path in (json_path, latest_json):
        write_json(path, report)
    for path in (md_path, latest_md):
        write_text(path, markdown)
    for path in (short_path, latest_short):
        write_text(path, short_markdown)
    for path in (review_path, latest_review):
        write_json(path, review_layer)

    print(json.dumps({
        "状态": "完成",
        "样板": str(latest_md),
        "微信短文预览": str(latest_short),
        "复盘字段预演": str(latest_review),
        "未改正式入口": True,
        "未发送企业微信": True,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
