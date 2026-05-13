# -*- coding: utf-8 -*-
"""
名称：L3企业微信短答适配器.py
作用：把L3评分、财报证据卡、行业价格证据卡、市场风格和技术观察条件压缩成企业微信单股结论型短答。
审计说明：本脚本实现《L3企业微信短答旧链路对照方案》中的“技术只保留一句结论和明确观察条件”“明细留后台，前台只保留用户可观察条件”部分。
触发方式：由股票助手入口.py调用；也可命令行dry-run。
安全边界：只读股票系统本地证据资产；不发送企业微信；不触发n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any


FORBIDDEN_TRADE_WORDS = (
    "买入",
    "卖出",
    "下单",
    "加仓",
    "减仓",
    "满仓",
    "半仓",
    "止盈",
    "目标价",
)


def load_caliber_module() -> Any:
    path = module_root() / "02脚本" / "stock_frontend_caliber.py"
    spec = importlib.util.spec_from_file_location("stock_frontend_caliber", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载股票前台口径模块：{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        suffix = suffix.lower()
        if suffix in {"sh", "sz", "bj"}:
            return suffix + num.zfill(6)
    if text.isdigit():
        if text.startswith(("6", "9")):
            return "sh" + text.zfill(6)
        if text.startswith(("4", "8")):
            return "bj" + text.zfill(6)
        return "sz" + text.zfill(6)
    return text


def display_code(stock: dict[str, Any]) -> str:
    code = stock.get("代码") or stock.get("code") or stock.get("display_code") or ""
    return normalize_code(code)


def clean_name(stock: dict[str, Any]) -> str:
    return str(stock.get("名称") or stock.get("name") or stock.get("stock_name") or stock.get("股票") or "").strip()


def l3_dir(root: Path) -> Path:
    return root / "03数据" / "245L3评分基础资产"


def file_score(path: Path, name: str, code: str, preferred_tokens: tuple[str, ...]) -> int:
    text = path.name
    score = 0
    if name and name in text:
        score += 10
    if code and code in text.lower():
        score += 10
    for token in preferred_tokens:
        if token in text:
            score += 3
    return score


def pick_json_file(paths: list[Path], name: str, code: str, preferred_tokens: tuple[str, ...]) -> Path | None:
    candidates = [p for p in paths if p.exists() and p.suffix.lower() == ".json"]
    if not candidates:
        return None
    candidates.sort(key=lambda p: (file_score(p, name, code, preferred_tokens), p.stat().st_mtime), reverse=True)
    best = candidates[0]
    return best if file_score(best, name, code, preferred_tokens) > 0 else None


def load_l3_report(root: Path, stock: dict[str, Any]) -> tuple[dict[str, Any], str]:
    name = clean_name(stock)
    code = display_code(stock)
    paths = list((l3_dir(root) / "单股L3评分").glob("*.json"))
    path = pick_json_file(paths, name, code, ("财报补证", "最新", "L3"))
    if not path:
        return {}, ""
    return load_json(path, {}) or {}, str(path)


def load_named_card(root: Path, stock: dict[str, Any], pattern: str, preferred_tokens: tuple[str, ...]) -> tuple[dict[str, Any], str]:
    name = clean_name(stock)
    code = display_code(stock)
    paths = list(l3_dir(root).glob(pattern))
    path = pick_json_file(paths, name, code, preferred_tokens)
    if not path:
        return {}, ""
    return load_json(path, {}) or {}, str(path)


def item_score(report: dict[str, Any], item_name: str) -> dict[str, Any]:
    for item in report.get("item_scores", []) if isinstance(report.get("item_scores"), list) else []:
        if str(item.get("item") or "") == item_name:
            return item if isinstance(item, dict) else {}
    return {}


def first_sentence(text: Any, fallback: str = "证据仍待补齐。", limit: int = 86) -> str:
    value = re.sub(r"\s+", " ", str(text or "").strip())
    if not value:
        value = fallback
    parts = re.split(r"[。；;]\s*", value)
    value = parts[0].strip() if parts and parts[0].strip() else value
    if len(value) > limit:
        value = value[: limit - 1] + "…"
    return value.rstrip("。；;") + "。"


def short_clause(text: Any, limit: int = 54) -> str:
    value = first_sentence(text, "", limit=limit).rstrip("。")
    return value or "证据仍待补齐"


def policy_industry_clause(policy_line: str, industry_price_line: str) -> str:
    policy = short_clause(policy_line, 28)
    industry = short_clause(industry_price_line, 34)
    if "未匹配" in policy or "不能靠政策" in policy:
        policy = "政策未形成强支撑"
    elif "政策事件分" in policy or "政策有" in policy or policy.startswith("POL-"):
        policy = "政策有辅助支撑"
    return f"{policy}，{industry}"


def fundamental_brief(fundamental_line: str) -> str:
    text = str(fundamental_line or "")
    if any(token in text for token in ("下滑", "偏风险", "不支持提高关注", "仍弱")):
        return "基本面偏弱"
    if any(token in text for token in ("修复", "增长", "改善", "支撑")):
        return "基本面有支撑但不充分"
    if any(token in text for token in ("不是空白", "不再是空白")):
        return "基本面已有证据"
    return "基本面证据待补"


def policy_industry_brief(policy_line: str, industry_price_line: str) -> str:
    policy = "政策有辅助" if any(token in str(policy_line) for token in ("政策事件分", "政策有", "POL-")) else "政策不强"
    industry_text = str(industry_price_line or "")
    if "单点" in industry_text:
        industry = "行业价仅单点"
    elif any(token in industry_text for token in ("来源已登记", "价格尚未入账", "仍待入账")):
        industry = "行业价未入账"
    else:
        industry = "行业价待补"
    return f"{policy}，{industry}"


def market_brief(root: Path) -> str:
    data = load_json(l3_dir(root) / "market_style_daily_latest.json", {}) or {}
    score = data.get("final_adaptation_score")
    if score not in (None, ""):
        return f"市场适配{score}/20"
    risk = data.get("risk_appetite", {}) if isinstance(data.get("risk_appetite"), dict) else {}
    if risk.get("score") not in (None, ""):
        return f"市场风险偏好{risk.get('score')}"
    return "市场风格待补"


def conclusion_from_l3(report: dict[str, Any], fallback_level: str) -> str:
    text = str(report.get("conclusion_text") or "").strip()
    allowed = {"重点关注", "可纳入观察", "暂不建议关注", "风险复核"}
    if text in allowed:
        return text
    if fallback_level in {"重点研究", "常规研究", "重点推荐", "常规推荐", "重点关注"}:
        return "可纳入观察"
    if fallback_level in {"风险复核", "离场观望", "回避"}:
        return "风险复核"
    return "暂不建议关注"


def confidence_text(report: dict[str, Any]) -> str:
    confidence = report.get("confidence", {})
    if isinstance(confidence, dict):
        return str(confidence.get("level") or "low")
    return str(confidence or "low")


def concise_missing(report: dict[str, Any], fundamental: dict[str, Any], price_card: dict[str, Any]) -> list[str]:
    raw: list[str] = []
    if isinstance(report.get("missing_summary"), str) and report.get("missing_summary"):
        raw.append(str(report["missing_summary"]))
    for card in (fundamental, price_card):
        missing = card.get("missing") if isinstance(card, dict) else []
        if isinstance(missing, list):
            raw.extend(str(item) for item in missing if str(item).strip())
    result: list[str] = []
    seen: set[str] = set()
    for item in raw:
        text = re.sub(r"\s+", "", str(item).strip("。；; "))
        text = text.replace("更高分的主要约束来自各分项missing字段；", "")
        text = text.replace("更高分的主要约束来自各分项missing字段", "")
        text = text.replace("当前市场风格已确认，后续按复盘节奏跟踪市场环境是否变化；", "")
        text = text.replace("当前市场风格已确认，后续按复盘节奏跟踪市场环境是否变化", "")
        for stale in (
            "、市场风格partial",
            "市场风格partial、",
            "市场风格partial",
            "、市场风格未结构化",
            "市场风格未结构化、",
            "市场风格未结构化",
            "和市场风格完整性",
            "、市场风格完整性",
            "市场风格完整性",
        ):
            text = text.replace(stale, "")
        text = text.replace("、、", "、").strip("、，,")
        text = text.replace("和。", "。").replace("和；", "；").replace("和", "")
        text = text.rstrip("、，,和")
        if text.endswith("政策事件"):
            text = text + "仍需结构化补强"
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
        if len(result) >= 3:
            break
    return result or ["政策、市场风格、行业价格或资金流仍需继续核验"]


def market_sentence(root: Path) -> str:
    data = load_json(l3_dir(root) / "market_style_daily_latest.json", {}) or {}
    status = str(data.get("status") or data.get("状态") or "").lower()
    score = data.get("final_adaptation_score")
    risk = data.get("risk_appetite", {}) if isinstance(data.get("risk_appetite"), dict) else {}
    risk_score = risk.get("score")
    if score not in (None, ""):
        if "partial" in status:
            return f"市场风格得分{score}/20，但仍是partial，只能低置信参考。"
        return f"市场风格得分{score}/20，可作为环境适配参考。"
    if risk_score not in (None, ""):
        return f"市场风险偏好{risk_score}，但完整风格日表仍待补齐。"
    return "市场风格日表仍待补齐，不能作为强结论依据。"


def policy_sentence(report: dict[str, Any]) -> str:
    policy = item_score(report, "政策事件")
    score = policy.get("score")
    if score not in (None, "") and float(score or 0) > 0:
        ev = policy.get("evidence") if isinstance(policy.get("evidence"), list) else []
        return first_sentence(ev[0] if ev else f"政策事件分{score}/20，作为辅助支撑。")
    return "未匹配到足够强的结构化政策事件，不能靠政策单独提高结论。"


def technical_sentence(context: dict[str, Any]) -> str:
    price_state = str(context.get("price_state") or "").strip()
    volume_state = str(context.get("volume_state") or "").strip()
    if price_state or volume_state:
        return first_sentence(f"{price_state}；{volume_state}".strip("；"), "技术上仍以观察条件是否成立为准。")
    return "技术上仍以承接区、转强线、成交活跃度和风险线为准。"


def build_watch_text(context: dict[str, Any]) -> str:
    def compact_condition(value: Any, prefer_current: bool = False) -> str:
        text = str(value or "").strip()
        if not text or text == "-":
            return ""
        pieces = [item.strip("，,；。 ") for item in re.split(r"[；。]", text) if item.strip("，,；。 ")]
        if prefer_current:
            current = next((item for item in pieces if "当前成交额" in item or "当前成交量" in item), "")
            threshold = next((item for item in pieces if "1.10倍" in item or "活跃线" in item), "")
            if current and threshold:
                return f"{current}，{threshold}"
            for item in pieces:
                if "当前" in item:
                    return item
        return pieces[0] if pieces else text

    support = compact_condition(context.get("support_condition"))
    strength = compact_condition(context.get("strength_condition"))
    volume = compact_condition(context.get("volume_condition"), prefer_current=True)
    parts = [part for part in (support, strength, volume) if part and part != "-"]
    if not parts:
        return "关键价格、成交或时间条件未完整生成，本次不输出价位型强结论。"
    text = "；".join(parts[:3])
    if len(text) > 240:
        text = text[:239] + "…"
    return text.rstrip("。") + "。"


def build_risk_text(context: dict[str, Any]) -> str:
    risk = str(context.get("risk_condition") or "").strip()
    if risk and risk != "-":
        return risk.rstrip("。") + "。"
    return "风险线未完整生成，本次结论降级处理。"


def sanitize(text: str) -> str:
    safe = str(text or "")
    replacements = {
        "买入": "提高研究优先级",
        "卖出": "降低研究优先级",
        "买点": "转强观察点",
        "下单": "执行动作",
        "加仓": "提高研究优先级",
        "减仓": "降低研究优先级",
        "满仓": "高优先级",
        "半仓": "中等优先级",
        "止盈": "风险复核",
        "目标价": "转强观察位",
    }
    for old, new in replacements.items():
        safe = safe.replace(old, new)
    safe = safe.replace("。。", "。").replace("；。", "。").replace("。；", "；")
    return safe


def build_l3_wecom_short_answer(root: Path, stock: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    name = clean_name(stock) or str(context.get("name") or "待确认股票")
    code = display_code(stock) or str(context.get("code") or "")
    report, report_path = load_l3_report(root, {"名称": name, "代码": code})
    fundamental, fundamental_path = load_named_card(root, {"名称": name, "代码": code}, f"{name}_财报基本面证据卡_*.json", ("财报", "证据卡"))
    price_card, price_path = load_named_card(root, {"名称": name, "代码": code}, f"{name}_行业价格证据卡_*.json", ("本地观测", "latest", "价格观测", "来源登记"))

    conclusion = conclusion_from_l3(report, str(context.get("level") or ""))
    confidence = confidence_text(report)
    fundamental_line = first_sentence(
        ((fundamental.get("front_output_compression") or {}).get("one_sentence") if isinstance(fundamental, dict) else ""),
        "财报证据卡未形成，基本面置信度下调。",
    )
    industry_price_line = first_sentence(
        ((price_card.get("front_output_compression") or {}).get("one_sentence") if isinstance(price_card, dict) else ""),
        "行业价格仍待入账，暂不能作为提高关注等级的依据。",
    )
    tech_line = technical_sentence(context)
    policy_line = policy_sentence(report)
    market_line = market_sentence(root)
    missing = concise_missing(report, fundamental, price_card)

    policy_industry_line = f"{policy_line.rstrip('。')}；{industry_price_line.rstrip('。')}。"

    if conclusion == "重点关注" and (confidence != "high" or missing):
        conclusion = "可纳入观察"
    if conclusion in {"重点关注", "可纳入观察"} and not report:
        conclusion = "暂不建议关注"
    caliber = load_caliber_module().normalize_frontend_caliber(
        raw_level=conclusion,
        score=report.get("total_score") if isinstance(report, dict) else None,
        confidence=confidence,
        risk_text="；".join([
            str(context.get("risk_summary") or ""),
            str(context.get("decision_risks") or ""),
            str(context.get("decision_signal") or ""),
            build_risk_text(context),
        ]),
    )
    research_level = caliber["研究等级"]
    current_status = caliber["当前状态"]

    reason_parts = [
        "技术部分接近" if research_level in {"重点研究", "常规研究"} and current_status not in {"风险复核", "回避"} else "技术未确认",
        fundamental_brief(fundamental_line),
        policy_industry_brief(policy_line, industry_price_line),
        market_brief(root),
    ]
    why_joined = "；".join(reason_parts) + "。"
    evidence_summary = str(report.get("evidence_summary") or "") if isinstance(report, dict) else ""
    if any(token in evidence_summary for token in ("沿用原L3样例", "技术来自现有单股报告", "技术面来自现有单股报告", "技术报告已给风险复核")):
        evidence_summary = ""
    one_sentence = first_sentence(
        evidence_summary or f"{fundamental_line.rstrip('。')}；{industry_price_line.rstrip('。')}",
        "证据未形成多因素共振，当前按观察或风险复核处理。",
        limit=96,
    )
    action = str(context.get("action_text") or "").strip() or "当前只作为研究观察，不执行任何交易动作。"
    if current_status in {"风险复核", "回避"}:
        action = load_caliber_module().current_status_action(current_status)

    lines = [
        f"分析对象：{name}（{code}）",
        f"结论：研究等级={research_level}；当前状态={current_status}。",
        f"研究等级：{research_level}。",
        f"当前状态：{current_status}。",
        f"一句话：{one_sentence.rstrip('。')}。",
        f"现在怎么处理：{action.rstrip('。')}。",
        f"观察条件：{build_watch_text(context)}",
        f"风险线：{build_risk_text(context)}",
        f"为什么：{why_joined}",
        "缺口：" + "；".join(missing[:3]) + "。",
        "说明：仅供研究参考，不构成投资建议，不作为买卖指令。",
    ]
    text = sanitize("\n".join(lines))
    return {
        "状态": "完成",
        "短答": text,
        "来源": {
            "l3_score_report": report_path,
            "fundamental_evidence_card": fundamental_path,
            "industry_price_evidence_card": price_path,
        },
        "结论": caliber["口径"],
        "研究等级": research_level,
        "当前状态": current_status,
        "原始结论": conclusion,
        "置信度": confidence,
        "阻断项": [word for word in FORBIDDEN_TRADE_WORDS if word in text],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock", required=True)
    parser.add_argument("--code", default="")
    args = parser.parse_args()
    root = module_root()
    stock = {"名称": args.stock, "代码": args.code}
    result = build_l3_wecom_short_answer(root, stock, {
        "level": "",
        "support_condition": "承接区、转强线和成交阈值需由股票助手入口传入。",
        "strength_condition": "",
        "volume_condition": "",
        "risk_condition": "风险线需由股票助手入口传入。",
        "action_text": "本命令行模式只验证证据压缩，不生成正式价位条件",
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
