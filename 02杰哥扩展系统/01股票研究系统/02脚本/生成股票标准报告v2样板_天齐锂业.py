# -*- coding: utf-8 -*-
"""
名称：生成股票标准报告v2样板_天齐锂业.py
作用：基于现有股票系统数据，生成“结论驱动版”前台标准报告 v2 样板和数据源差距清单。
触发方式：python 生成股票标准报告v2样板_天齐锂业.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读03数据与本地股票助手HTTP接口；只写03数据/165标准报告v2样板；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-standard-report-v2-sample-tianqi
"""

from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


STOCK_CODE = "sz002466"
STOCK_NAME = "天齐锂业"


def module_root() -> Path:
    # 本脚本约定放在 股票研究系统/02脚本 下，因此 parents[1] 为股票研究系统根目录。
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def find_stock(items: list[dict[str, Any]], code: str, name: str) -> dict[str, Any]:
    for item in items:
        if item.get("代码") == code or item.get("名称") == name:
            return item
    return {}


def pct(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}%"
    except (TypeError, ValueError):
        return "-"


def money_yi(value: Any) -> str:
    try:
        return f"{float(value) / 100000000:.2f}亿元"
    except (TypeError, ValueError):
        return "-"


def score_5(value: Any) -> str:
    try:
        return f"{float(value):.2f}/5"
    except (TypeError, ValueError):
        return "-"


def format_value(value: Any, suffix: str = "", digits: int = 2) -> str:
    try:
        if value is None or value == "":
            return "-"
        return f"{float(value):.{digits}f}{suffix}"
    except (TypeError, ValueError):
        return str(value)


def fetch_single_report_text(root_url: str = "http://127.0.0.1:19302") -> str:
    query = urllib.parse.urlencode({"ask": f"分析{STOCK_NAME}"})
    url = f"{root_url}/wecom-bot/message?{query}"
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return f"【单股问答接口读取失败】{exc}"

    raw = html.unescape(raw)
    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", "", raw)
    return raw.strip()


def extract(pattern: str, text: str, default: str = "-") -> str:
    match = re.search(pattern, text, flags=re.S)
    if not match:
        return default
    return match.group(1).strip()


def extract_ai_summary(text: str) -> str:
    if not text:
        return "-"
    match = re.search(r"8\.\s*研究小结\s*([\s\S]+)$", text)
    if not match:
        return "-"
    summary = match.group(1).strip()
    summary = re.sub(r"\s+", " ", summary)
    return summary or "-"


def build_front_report(root: Path, now: datetime) -> tuple[str, str]:
    data_dir = root / "03数据"
    l5 = load_json(data_dir / "134深度研究池" / "L5深度研究池_最新.json")
    l6 = load_json(data_dir / "133行业主题观察池" / "L6行业主题观察池_最新.json")
    ai = load_json(data_dir / "135分层日报" / "AI分析报告_最新.json")
    company_snapshot = load_json(data_dir / "166公司经营快照" / "公司经营快照_最新.json")
    industry_prosperity = load_json(data_dir / "167行业景气结论" / "行业景气结论_最新.json")

    l5_stock = find_stock(l5.get("股票池", []), STOCK_CODE, STOCK_NAME)
    l6_stock = find_stock(l6.get("股票池", []), STOCK_CODE, STOCK_NAME)
    ai_stock = find_stock(ai.get("分析结果", []), STOCK_CODE, STOCK_NAME)
    snapshot_stock = find_stock(company_snapshot.get("股票快照", []), STOCK_CODE, STOCK_NAME)
    single_text = fetch_single_report_text()

    single_industry = extract(r"行业：([^\n]+)", single_text)
    system_score = extract(r"系统评分：([0-9.]+)分", single_text)
    realtime = extract(r"实时行情：([^\n]+)", single_text)
    trend_basis = extract(r"趋势结构：([^\n]+)", single_text)
    risk_basis = extract(r"主要风险：([^\n]+)", single_text)
    system_judgement = extract(r"系统判断：([^\n]+)", single_text)
    ai_summary = extract_ai_summary(ai_stock.get("analysis_text", ""))

    industry = l5_stock.get("行业") or l6_stock.get("行业") or "-"
    sub_field = l5_stock.get("细分领域") or single_industry or "-"
    industry_row = {}
    for row in industry_prosperity.get("行业景气结论", []):
        if row.get("行业") == industry:
            industry_row = row
            break
    industry_sentence = industry_row.get("前台结论") or "行业景气结论待接入。"
    report_date = l5.get("数据日期") or ai.get("数据日期") or now.strftime("%Y-%m-%d")
    close = l5_stock.get("收盘价")
    change = l5_stock.get("涨跌幅")
    vol_ratio = l5_stock.get("资金放量率")
    adjusted_score = l5_stock.get("调整分")
    source_flags = []
    if l5_stock.get("是否用户增强"):
        source_flags.append("用户关注")
    if l5_stock.get("是否战略样本"):
        source_flags.append("战略样本")
    if l5_stock.get("是否指数基底"):
        source_flags.append("指数基底")
    source_label = " / ".join(source_flags) or "普通样本"

    evidence_level = "中"
    if single_text.startswith("【单股问答接口读取失败】"):
        evidence_level = "低"

    conclusion = (
        "该股当前属于常规跟踪对象。公司处于锂资源/能源金属链条，受锂价周期影响较大；"
        "短线价格和成交额活跃度提升，财报关键指标已初步接入，但行业价格和公告事件仍需补齐后再确认基本面质量。"
    )

    industry_line = (
        f"行业景气：{industry_sentence}"
        "但锂价、库存、供需价格指数尚未接入，因此行业判断仍标记为“部分接入”。"
    )
    finance = snapshot_stock.get("财报快照", {}) if snapshot_stock else {}
    finance_status = snapshot_stock.get("证据状态", {}).get("财报指标", "待接入") if snapshot_stock else "待接入"
    if finance_status == "已接入":
        fundamental_line = (
            f"基本面：最新报告期{finance.get('最新报告期', '-')}，"
            f"营业收入{format_value(finance.get('营业收入_亿元'), '亿元')}，同比{format_value(finance.get('营业收入同比'), '%')}；"
            f"归母净利润{format_value(finance.get('归母净利润_亿元'), '亿元')}，扣非净利润{format_value(finance.get('扣非净利润_亿元'), '亿元')}；"
            f"毛利率{format_value(finance.get('毛利率'), '%')}，ROE{format_value(finance.get('ROE'), '%')}。"
            "以上为公开财务摘要字段，仍需结合正式财报正文核验。"
        )
        finance_front_status = "财报关键指标已接入；正式财报正文待核验。"
    else:
        fundamental_line = (
            "基本面：公司经营快照骨架已建立，但营业收入、扣非利润、毛利率、ROE、现金流等财报字段仍为待接入，需继续补齐。"
        )
        finance_front_status = "公司财务待接入。"

    tech_line = (
        f"走势结论：{trend_basis if trend_basis != '-' else '短线走势活跃，但均线数据不完整，仍需下一轮技术指标刷新确认。'}"
    )
    money_line = (
        f"资金状态：近5/20日成交额放量率约 {pct((vol_ratio or 0) * 100)}，"
        f"近5日日均成交额 {money_yi(l5_stock.get('近5日日均成交额'))}，短期关注度上升，持续性待观察。"
    )

    risk_line = (
        f"主要风险：{risk_basis if risk_basis != '-' else '当前未发现单日行情层面的突出风险，但公告、财报和行业价格未完全接入。'}"
    )
    pending_line = (
        "待核验项：最新完整财报、锂价与库存变化、公告/减持/解禁信息、行业口径（有色金属 vs 能源金属）统一。"
    )

    follow_line = (
        "后续重点：观察价格能否维持在系统技术观察线附近并继续放量，同时补齐财报质量和锂价周期数据；"
        "建议在财报数据接入后重新生成标准报告 v2。"
    )

    report = f"""# {STOCK_NAME}({STOCK_CODE}) 股票标准报告 v2 前台样板

生成时间：{now.strftime("%Y-%m-%d %H:%M:%S")}  
报告日期：{report_date}  
报告版本：标准研究版 v2（结论驱动样板）  
所属行业：{industry}（当前L6/L5口径） / {single_industry}（单股问答口径）  
系统评分：{system_score}/100  
分层状态：L5深度研究池，分层排序分 {score_5(adjusted_score)}  
用户标记：{source_label}  
证据完整度：{evidence_level}

> 本报告仅提供研究信息参考，不构成任何交易指令。用户需独立判断并承担风险。

## 1. 结论

{conclusion}

- 关注等级：常规跟踪对象
- 证据完整度：{evidence_level}（行情、分层、AI摘要、财报关键指标已接入；公告、行业价格待接入）

## 2. 公司概况

{STOCK_NAME}属于锂资源和锂化工相关公司，现有系统将其归入“{industry} / {sub_field}”。公司分析的关键不只是短线走势，还要结合锂价周期、资源成本、产能与新能源电池产业链需求进行复核。

数据状态：部分接入。当前已有行业和细分标签，并已建立公司经营快照骨架；行业地位、主营构成、资源储量、产能规划等仍需后续填充或人工核验。

## 3. 行业与基本面

{industry_line}

{fundamental_line}

数据状态：行业景气部分接入；{finance_front_status}

## 4. 走势与资金状态

{tech_line}

{money_line}

当前行情摘要：{realtime}

系统判断：{system_judgement}

数据状态：行情和量价已接入；均线/指标部分字段仍不完整。

## 5. 风险与待核验

{risk_line}

{pending_line}

数据状态：风险提示部分接入；公告、减持、解禁、行业价格风险待接入。

## 6. 后续跟踪重点

{follow_line}

- 下次复核触发：财报快照接入后、锂价数据接入后、或该股再次进入L5且系统评分变化超过5分。
- 后台保留：L5入选理由为“{l5_stock.get('L5入选原因', '-') or '-'}”；AI小结为“{ai_summary}”。
- 经营快照状态：公司概况={snapshot_stock.get('证据状态', {}).get('公司概况', '待接入')}，财报指标={finance_status}。

## 样板结论

这份样板说明：现有系统已经能支撑“走势与资金状态”和“财报关键指标”的结论化展示，但要让报告真正达到“看懂公司概况、经营情况、未来方向”的要求，下一步必须优先补齐公司经营描述、行业价格和公告事件数据源。
"""

    gap = f"""# 股票标准报告 v2 数据源差距清单（天齐锂业样板）

生成时间：{now.strftime("%Y-%m-%d %H:%M:%S")}  
样板股票：{STOCK_NAME}({STOCK_CODE})  
目标：把“后台深分析、前台给结论”落到现有股票系统中。

## 一、现有系统已能提供

| 模块 | 当前来源 | 可用于前台报告 | 状态 |
|---|---|---|---|
| 股票身份与样本来源 | L8X/L5：指数基底、用户增强、战略样本标记 | 用户标记、样本来源说明 | 已接入 |
| 分层状态 | L5深度研究池 | L5/L6/L7/L8状态、分层排序分 | 已接入 |
| 行情数据 | L7/L6/L5公开行情字段 | 收盘价、涨跌幅、成交额、近5/20日表现 | 已接入 |
| 资金活跃 | L6/L5资金放量率、资金活跃度分 | “短期关注度上升/持续性待观察” | 已接入 |
| AI结构化摘要 | AI分析报告_最新.json | 入选原因、风险提示、研究小结 | 已接入 |
| 单股即时评分 | 股票助手入口/桥接入口 | 系统评分、星级、即时行情摘要 | 已接入 |
| 财报关键指标 | 公司经营快照 + AKShare公开财务摘要 | 营业收入、利润、毛利率、ROE、现金流 | 已接入当前L5 |

## 二、部分接入但需要统一口径

| 字段 | 当前情况 | 问题 | 建议 |
|---|---|---|---|
| 行业口径 | L5显示“{industry}”，单股问答显示“{single_industry}” | 一级行业与细分行业混用 | 前台显示“申万一级/细分行业”两栏 |
| 技术面结论 | 单股问答已有趋势、量比、观察线 | 均线、MACD等字段有缺失 | 前台只保留1-2句结论，后台继续补指标 |
| 分层排序分与系统评分 | L5为{score_5(adjusted_score)}，单股评分为{system_score}/100 | 容易被误解成同一套推荐等级 | 报告和企微摘要继续明确口径说明 |
| 行业景气 | 已生成行业景气结论，{industry}为“{industry_row.get('景气状态', '待接入')}” | 基于L6等权估算，尚未接入正式申万行业指数/行业价格 | 继续作为部分接入字段使用 |

## 三、P0优先补齐

| 数据源 | 用途 | 推荐落地方式 |
|---|---|---|
| 公司经营快照 | 公司概况、经营情况、财务质量 | 已建立 `03数据/166公司经营快照/公司经营快照_最新.json` 骨架；财报指标已补当前L5，核心业务/行业地位仍待补 |
| 财报关键指标 | 营收、利润、毛利率、ROE、现金流 | 当前L5已接AKShare公开财务摘要；后续扩展到用户增强池并核验正式财报 |
| 行业景气结论 | 行业与基本面一段话 | 基于L6行业强度、近1/5/20日涨跌幅、相对沪深300生成 |
| 数据状态表 | 证据完整度 | 每份报告输出字段状态：已接入/部分接入/待接入/人工核验 |

## 四、P1后续增强

| 数据源 | 用途 | 说明 |
|---|---|---|
| 公告事件 | 风险与催化剂 | 只做标题/日期/来源台账，不直接替用户下结论 |
| 解禁减持 | 风险提示 | 接入后进入“待核验”区 |
| 行业价格数据 | 锂价、库存、资源周期判断 | 天齐锂业这类周期股优先需要 |
| 融资融券/北向资金 | 资金面补充 | 先不作为P0，避免数据依赖过重 |

## 五、对现有脚本的改造建议

1. `股票助手入口.py`：新增标准报告 v2 前台输出模式，保留原即时问答作为简版。
2. `生成L5AI分析报告.py`：后台继续保留8维度，但额外输出前台六段摘要字段。
3. `生成股票企微推送草案.py`：企微只推结论摘要，点击后进入标准报告 v2。
4. `公司经营快照_最新.json`：下一步接入真实财报/人工维护字段。
5. `行业景气结论_最新.json`：下一步升级为正式申万行业指数和行业价格数据。

## 六、安全边界

- 未真实发送企业微信。
- 未触发n8n。
- 未调用券商接口。
- 未自动交易。
- 未修改旧系统。
"""

    return report, gap


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    output_dir = root / "03数据" / "165标准报告v2样板"

    report, gap = build_front_report(root, now)

    report_path = output_dir / "天齐锂业_股票标准报告v2前台样板.md"
    report_ts_path = output_dir / f"天齐锂业_股票标准报告v2前台样板_{stamp}.md"
    gap_path = output_dir / "股票标准报告v2_数据源差距清单.md"
    gap_ts_path = output_dir / f"股票标准报告v2_数据源差距清单_{stamp}.md"

    write_text(report_path, report)
    write_text(report_ts_path, report)
    write_text(gap_path, gap)
    write_text(gap_ts_path, gap)

    print(json.dumps({
        "状态": "完成",
        "报告": str(report_path),
        "差距清单": str(gap_path),
        "安全边界": {
            "是否真实发送企业微信": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
