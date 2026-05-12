# -*- coding: utf-8 -*-
"""
名称：生成单股L3评分报告.py
作用：按L3评分契约，为任意已能解析的单股生成结构化L3评分报告。
触发方式：python 生成单股L3评分报告.py --stock 云南锗业
安全边界：只读本地股票研究数据；只写03数据/245L3评分基础资产/单股L3评分；不联网；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text[-6:]
    digits = "".join(ch for ch in text if ch.isdigit())
    return digits[-6:] if len(digits) >= 6 else text


def market_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text[:2] + normalize_code(text)
    pure = normalize_code(text)
    if pure.startswith(("6", "9")):
        return "sh" + pure
    if pure.startswith(("4", "8")):
        return "bj" + pure
    return "sz" + pure


def load_stock_candidates(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pool = load_json(root / "01配置" / "重点关注股票池.json", {"股票池": []})
    for item in pool.get("股票池", []):
        code = market_code(item.get("代码"))
        rows.append({**item, "代码": code, "名称": item.get("名称") or item.get("name")})
    mapping = load_json(root / "01配置" / "股票简称补充映射.json", {"映射": []})
    for item in mapping.get("映射", []):
        code = market_code(item.get("代码"))
        aliases = item.get("别名", [])
        rows.append({**item, "代码": code, "名称": item.get("名称"), "别名": aliases})
    return rows


def resolve_stock(root: Path, keyword: str) -> dict[str, str]:
    text = str(keyword or "").strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    candidates = load_stock_candidates(root)
    for item in candidates:
        code = market_code(item.get("代码"))
        name = str(item.get("名称") or "")
        aliases = [str(alias) for alias in item.get("别名", [])]
        if text == name or (name and text in name) or (name and name in text):
            return {"代码": code, "纯代码": normalize_code(code), "名称": name}
        if digits and normalize_code(code) == digits[-6:]:
            return {"代码": code, "纯代码": normalize_code(code), "名称": name or digits[-6:]}
        if text in aliases:
            return {"代码": code, "纯代码": normalize_code(code), "名称": name}
    if len(digits) >= 6:
        code = market_code(digits[-6:])
        return {"代码": code, "纯代码": normalize_code(code), "名称": digits[-6:]}
    raise ValueError(f"未识别股票：{keyword}")


def latest_report_path(root: Path, stock: dict[str, str]) -> Path:
    data_dir = root / "03数据" / "135分层日报"
    code = stock["代码"]
    name = stock["名称"]
    patterns = [
        f"单股标准报告v2_{name}_{code}_*.md",
        f"单股标准报告v2_*_{code}_*.md",
        f"单股标准报告v2_{stock['纯代码']}_{code}_*.md",
    ]
    candidates: list[Path] = []
    for pattern in patterns:
        candidates.extend(data_dir.glob(pattern))
    unique = sorted(set(candidates), key=lambda p: p.stat().st_mtime, reverse=True)
    return unique[0] if unique else data_dir / "单股标准报告v2_最新.md"


def find_quote(root: Path, pure_code: str) -> dict[str, Any]:
    data = load_json(root / "03数据" / "04数据快照" / "重点关注池公开行情快照_最新.json", {"行情": []})
    for row in data.get("行情", []):
        if normalize_code(row.get("代码")) == pure_code:
            return row
    return {}


def extract_float(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def extract_strength(report_text: str) -> int:
    match = re.search(r"强度：([0-5])/5", report_text)
    return int(match.group(1)) if match else 0


def conclusion_from_score(score: float) -> str:
    if score >= 80:
        return "重点关注"
    if score >= 60:
        return "可纳入观察"
    return "暂不建议关注"


def policy_decay_factor(event: dict[str, Any], today: date) -> float:
    if event.get("status") == "retired":
        return 0.0
    valid_until = event.get("valid_until")
    if not valid_until:
        return 1.0
    try:
        valid_date = date.fromisoformat(valid_until)
    except ValueError:
        return 0.5
    if today <= valid_date:
        return 1.0
    decay_days = max(int(event.get("decay_days") or 180), 1)
    passed = (today - valid_date).days
    return max(0.0, 1.0 - passed / decay_days)


def build_technical_score(report_text: str, quote: dict[str, Any]) -> dict[str, Any]:
    strength = extract_strength(report_text)
    current = quote.get("最新价") or extract_float(r"当前价：([0-9.]+)元", report_text)
    support_low = extract_float(r"承接区：([0-9.]+)元-[0-9.]+元", report_text)
    support_high = extract_float(r"承接区：[0-9.]+元-([0-9.]+)元", report_text)
    turn_strong = extract_float(r"转强线：([0-9.]+)元", report_text)
    risk_line = extract_float(r"风险线：([0-9.]+)元", report_text)
    volume_ratio = quote.get("量比")

    score = 8 + strength * 6
    evidence = [f"现有单股报告给出强度{strength}/5。"]
    missing: list[str] = []

    if all(value is not None for value in [current, support_low, support_high, turn_strong, risk_line]):
        score += 5
        evidence.append(f"当前价{current}元，承接区{support_low}-{support_high}元，转强线{turn_strong}元，风险线{risk_line}元均已给出。")
    else:
        missing.append("承接区/转强线/风险线或当前价不完整")

    if isinstance(volume_ratio, (int, float)):
        if volume_ratio >= 1.10:
            score += 3
            evidence.append(f"量比{volume_ratio}，达到成交活跃标准。")
        else:
            evidence.append(f"量比{volume_ratio}，尚未达到1.10倍成交活跃标准。")
    else:
        missing.append("量比缺失")

    if "观察等待" in report_text:
        evidence.append("原单股报告结论为观察等待，技术面未给出强转强确认。")
    if "待核验" in report_text:
        missing.append("原报告包含待核验证据")

    if current is not None and risk_line is not None and current < risk_line:
        score = min(score, 18)
        evidence.append("当前价低于风险线，技术结构评分上限降至18分。")
    elif current is not None and support_low is not None and current < support_low:
        score = min(score, 30)
        evidence.append("当前价低于承接区下沿，承接尚未成立，技术结构评分上限降至30分。")
    elif current is not None and turn_strong is not None and current < turn_strong:
        score = min(score, 34)
        evidence.append("当前价尚未站上转强线，技术结构评分不得打满。")
    if "观察等待" in report_text:
        score = min(score, 30)

    return {
        "item": "技术结构",
        "score": min(40, max(0, int(round(score)))),
        "max_score": 40,
        "evidence": evidence,
        "missing": missing,
        "confidence": "medium" if missing else "high",
    }


def build_fundamentals_score(quote: dict[str, Any], report_text: str) -> dict[str, Any]:
    evidence: list[str] = []
    missing: list[str] = []
    score = 0
    pe = quote.get("市盈率")
    industry = quote.get("行业")
    amount = quote.get("成交额")
    turnover = quote.get("换手率")
    if pe is not None:
        score += 2
        evidence.append(f"行情快照已有市盈率{pe}。")
    else:
        missing.append("市盈率缺失")
    if industry:
        score += 1
        evidence.append(f"行情快照已有行业标签：{industry}。")
    else:
        missing.append("行业标签缺失")
    if amount is not None or turnover is not None:
        score += 2
        evidence.append(f"行情快照已有成交额/换手率：成交额={amount}，换手率={turnover}。")
    else:
        missing.append("成交额或换手率缺失")
    if "财报：关键指标待接入" in report_text or "财报关键指标未完整接入" in report_text:
        missing.append("近三年营收、净利润、现金流、ROE等财报关键指标未结构化接入")
    if "公告、行业价格、解禁减持、财报正文" in report_text:
        missing.append("公告、行业价格、解禁减持和财报正文仍待核验")
    return {
        "item": "基本面/资金",
        "score": min(20, score),
        "max_score": 20,
        "evidence": evidence,
        "missing": missing,
        "confidence": "low" if missing else "medium",
    }


def build_policy_score(events: list[dict[str, Any]], exposures: list[dict[str, Any]], pure_code: str) -> dict[str, Any]:
    today = date.today()
    by_event = {event.get("event_id"): event for event in events}
    evidence: list[str] = []
    missing: list[str] = []
    total = 0.0
    for exposure in exposures:
        if normalize_code(exposure.get("stock_code")) != pure_code:
            continue
        event = by_event.get(exposure.get("event_id"))
        if not event:
            missing.append(f"暴露度记录{exposure.get('event_id')}未匹配到政策事件")
            continue
        if event.get("status") == "draft":
            missing.append(f"{event.get('event_id')}仍为draft，未进入正式评分")
            continue
        decay = policy_decay_factor(event, today)
        event_score = 20 * float(event.get("impact_strength", 0)) * float(exposure.get("exposure", 0)) * decay * float(event.get("event_confidence", 0))
        total += event_score
        evidence.append(
            f"{event.get('event_id')}：{event.get('title')}；方向={event.get('impact_direction')}，强度={event.get('impact_strength')}，暴露度={exposure.get('exposure')}，时效={round(decay, 2)}。"
        )
        evidence.append(str(exposure.get("exposure_reason", "")))
    if not evidence:
        missing.append("未匹配到该股票的政策事件暴露度")
    return {
        "item": "政策事件",
        "score": round(min(20, total), 1),
        "max_score": 20,
        "evidence": evidence,
        "missing": missing,
        "confidence": "high" if evidence and not missing else "low",
    }


def industry_matches(industry: str, sector_name: str) -> bool:
    industry_text = str(industry or "")
    sector_text = str(sector_name or "")
    if not industry_text or not sector_text:
        return False
    if industry_text in sector_text or sector_text in industry_text:
        return True
    resource_words = ["小金属", "能源金属", "有色金属", "稀有金属", "稀土", "煤炭"]
    tech_words = ["半导体", "电子", "通信", "计算机", "AI", "算力"]
    consumer_words = ["食品饮料", "家电", "商贸", "旅游", "酿酒"]
    for words in [resource_words, tech_words, consumer_words]:
        if any(word in industry_text for word in words) and any(word in sector_text for word in words):
            return True
    return False


def build_market_style_score(style: dict[str, Any], quote: dict[str, Any]) -> dict[str, Any]:
    score = int(style.get("final_adaptation_score") or 0)
    stock_industry = str(quote.get("行业") or "")
    top_sectors = style.get("sector_heat", {}).get("top_sectors", [])
    bottom_sectors = style.get("sector_heat", {}).get("bottom_sectors", [])
    evidence = [
        style.get("overall_summary", ""),
        f"风险偏好={style.get('risk_appetite', {}).get('score')}，热门主题={style.get('sector_heat', {}).get('hot_theme')}，大小盘风格={style.get('size_style', {}).get('dominant')}，流动性={style.get('liquidity', {}).get('total_amount_rank_percentile')}。",
        style.get("notes_for_stock_type", ""),
    ]
    evidence = [item for item in evidence if item]
    missing: list[str] = []
    if stock_industry:
        top_match = [item.get("name") for item in top_sectors if industry_matches(stock_industry, str(item.get("name", "")))]
        bottom_match = [item.get("name") for item in bottom_sectors if industry_matches(stock_industry, str(item.get("name", "")))]
        if top_match:
            score += 2
            evidence.append(f"个股行业{stock_industry}与强势板块{top_match[:2]}匹配，市场风格适配加分。")
        if bottom_match:
            score -= 2
            evidence.append(f"个股行业{stock_industry}与弱势板块{bottom_match[:2]}匹配，市场风格适配降分。")
        if not top_match and not bottom_match:
            evidence.append(f"个股行业{stock_industry}未与当日强弱板块形成明确匹配，按中性处理。")
    else:
        missing.append("个股行业标签缺失，无法计算行业适配")
    for key in ["risk_appetite", "sector_heat", "size_style", "liquidity"]:
        missing.extend(style.get(key, {}).get("missing", []))
    if style.get("status") != "confirmed":
        missing.append(f"市场风格状态为{style.get('status')}，尚不能作为高置信度证据")
        score = min(score, 13)
    return {
        "item": "市场风格适配",
        "score": min(20, max(0, score)),
        "max_score": 20,
        "evidence": evidence,
        "missing": missing,
        "confidence": "low" if missing else "high",
    }


def confidence_from_missing(item_scores: list[dict[str, Any]], market_status: str) -> dict[str, str]:
    critical_missing: list[str] = []
    for item in item_scores:
        if item["item"] in {"基本面/资金", "政策事件", "市场风格适配"} and item.get("missing"):
            critical_missing.extend(item["missing"])
    if market_status in {"draft", "partial"}:
        critical_missing.append("市场风格日表尚未确认为confirmed")
    if critical_missing:
        return {
            "level": "low",
            "reason": "仍存在关键证据缺口：" + "；".join(critical_missing[:5]),
        }
    return {"level": "medium", "reason": "四项证据均可读取，但仍需盘后复核确认。"}


def safe_name(text: str) -> str:
    return re.sub(r'[\\/:*?"<>|\\s]+', "_", text).strip("_") or "unknown"


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# {result['stock_name']}L3评分报告",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 分析对象：{result['stock_name']}（{result['stock_code']}）",
        f"- 综合得分：{result['total_score']}/100",
        f"- 结论：{result['conclusion_text']}",
        f"- 置信度：{result['confidence']['level']}；{result['confidence']['reason']}",
        "",
        "## 分项评分",
        "",
    ]
    for item in result["item_scores"]:
        lines.append(f"### {item['item']}：{item['score']}/{item['max_score']}")
        lines.append(f"- 置信度：{item['confidence']}")
        for evidence in item["evidence"]:
            lines.append(f"- 证据：{evidence}")
        if item["missing"]:
            for missing in item["missing"]:
                lines.append(f"- 缺口：{missing}")
        else:
            lines.append("- 缺口：无")
        lines.append("")
    lines.extend([
        "## 总结",
        "",
        f"- 证据摘要：{result['evidence_summary']}",
        f"- 缺口摘要：{result['missing_summary']}",
        f"- 下次复核：{result['next_review_date']}",
        "",
        "说明：本文件用于L3评分链路和复盘，不构成投资建议，不作为买卖指令。",
        "",
    ])
    return "\n".join(lines)


def build_l3_report(root: Path, stock_keyword: str) -> dict[str, Any]:
    stock = resolve_stock(root, stock_keyword)
    data = root / "03数据" / "245L3评分基础资产"
    contract = load_json(root / "01配置" / "L3_scoring_contract_v1.0.json", {})
    events = load_json(data / "policy_events_v1.0.json", [])
    exposures = load_json(data / "stock_policy_exposures_v1.0.json", [])
    style = load_json(data / "market_style_daily_latest.json", {})
    report_path = latest_report_path(root, stock)
    report_text = read_text(report_path)
    quote = find_quote(root, stock["纯代码"])

    item_scores = [
        build_technical_score(report_text, quote),
        build_fundamentals_score(quote, report_text),
        build_policy_score(events, exposures, stock["纯代码"]),
        build_market_style_score(style, quote),
    ]
    total_score = round(sum(float(item["score"]) for item in item_scores), 1)
    confidence = confidence_from_missing(item_scores, str(style.get("status")))
    conclusion = conclusion_from_score(total_score)
    if confidence["level"] == "low" and conclusion == "重点关注":
        conclusion = "可纳入观察"
    missing_points: list[str] = []
    for item in item_scores:
        for missing in item.get("missing", []):
            if missing and missing not in missing_points:
                missing_points.append(str(missing))
    if missing_points:
        missing_summary = "更高分的主要约束来自：" + "；".join(missing_points[:6]) + "。"
    else:
        missing_summary = "未发现关键结构化证据缺口，仍需按复盘节奏跟踪证据是否变化。"

    return {
        "version": contract.get("version", "1.0"),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stock_code": stock["代码"],
        "stock_name": stock["名称"],
        "source_report": str(report_path),
        "total_score": total_score,
        "item_scores": item_scores,
        "evidence_summary": f"技术面来自现有单股报告和行情快照；政策面来自结构化政策事件库和暴露度表；市场风格使用market_style_daily_latest.json，当前状态为{style.get('status', 'unknown')}。",
        "missing_summary": missing_summary,
        "confidence": confidence,
        "conclusion_text": conclusion,
        "next_review_date": (date.today() + timedelta(days=7)).isoformat(),
        "safety_boundary": "仅供研究参考，不构成投资建议，不作为买卖指令；不调用券商接口，不自动交易。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="生成单股L3评分报告")
    parser.add_argument("--stock", required=True, help="股票名称、代码或别名，例如 云南锗业 / 002428 / sz002428")
    args = parser.parse_args()

    root = module_root()
    data = root / "03数据" / "245L3评分基础资产" / "单股L3评分"
    result = build_l3_report(root, args.stock)
    stem = f"{safe_name(result['stock_name'])}_{result['stock_code']}"
    write_json(data / f"{stem}_最新.json", result)
    write_text(data / f"{stem}_最新.md", build_markdown(result))
    write_json(data / "单股L3评分_最新.json", result)
    write_text(data / "单股L3评分_最新.md", build_markdown(result))
    print(json.dumps({"状态": "完成", "股票": result["stock_name"], "综合得分": result["total_score"], "结论": result["conclusion_text"], "输出": str(data)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
