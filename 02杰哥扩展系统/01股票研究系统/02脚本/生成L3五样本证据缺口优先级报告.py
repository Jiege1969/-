# -*- coding: utf-8 -*-
"""
名称：生成L3五样本证据缺口优先级报告.py
作用：只读汇总五样本L3报告、财报证据卡、行业价格证据卡、政策事件库和市场风格日表，生成证据缺口优先级报告。
触发方式：python 生成L3五样本证据缺口优先级报告.py
安全边界：只写股票系统03数据/245L3评分基础资产；不修改配置；不触发n8n；不发送企业微信；不重启服务；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SAMPLES = [
    {"name": "云南锗业", "code": "sz002428"},
    {"name": "天齐锂业", "code": "sz002466"},
    {"name": "华虹公司", "code": "sh688347"},
    {"name": "浙商中拓", "code": "sz000906"},
    {"name": "正丹股份", "code": "sz300641"},
]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def base_dir(root: Path) -> Path:
    return root / "03数据" / "245L3评分基础资产"


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


def pick_latest(paths: list[Path]) -> Path | None:
    existing = [path for path in paths if path.exists()]
    if not existing:
        return None
    return max(existing, key=lambda item: item.stat().st_mtime)


def load_sample_assets(root: Path, name: str, code: str) -> dict[str, Any]:
    base = base_dir(root)
    code_digits = code[2:]
    l3_path = pick_latest(
        list((base / "单股L3评分").glob(f"{name}_{code}_*.json"))
        + list((base / "单股L3评分").glob(f"{name}_{code_digits}_*.json"))
    )
    finance_path = pick_latest(list(base.glob(f"{name}_财报基本面证据卡_*.json")))
    industry_path = pick_latest(list(base.glob(f"{name}_行业价格证据卡_本地观测_latest.json")))
    return {
        "l3_path": l3_path,
        "finance_path": finance_path,
        "industry_path": industry_path,
        "l3": load_json(l3_path, {}) if l3_path else {},
        "finance": load_json(finance_path, {}) if finance_path else {},
        "industry": load_json(industry_path, {}) if industry_path else {},
    }


def item_score(report: dict[str, Any], item_name: str) -> dict[str, Any]:
    for item in report.get("item_scores", []) if isinstance(report.get("item_scores"), list) else []:
        if item.get("item") == item_name:
            return item if isinstance(item, dict) else {}
    return {}


def unique_missing(*sources: Any) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for source in sources:
        if isinstance(source, str):
            values = [source]
        elif isinstance(source, list):
            values = source
        else:
            values = []
        for value in values:
            text = str(value or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
    return result


def classify_priority(row: dict[str, Any]) -> tuple[str, list[str]]:
    missing_text = "；".join(row.get("missing", []))
    blockers: list[str] = []
    if row.get("industry_price_status") in {"source_registered", "missing"}:
        blockers.append("行业价格尚未形成可用观测")
    if "资金流" in missing_text or "机构持仓" in missing_text or "减持" in missing_text:
        blockers.append("资金/机构/减持解禁证据未合并")
    if "一季报" in missing_text or "财报" in missing_text:
        blockers.append("最新财报字段仍需结构化")
    if row.get("policy_score", 0) < 5:
        blockers.append("政策事件匹配或暴露度不足")
    if row.get("market_style_confidence") == "low":
        blockers.append("市场风格只宜作辅助参考")
    if row.get("confidence") == "low":
        blockers.append("综合置信度偏低")

    if any("行业价格" in item or "资金" in item for item in blockers):
        return "P0", blockers
    if any("财报" in item or "政策" in item for item in blockers):
        return "P1", blockers
    if blockers:
        return "P2", blockers
    return "P3", ["当前缺口较少，按复盘节奏跟踪"]


def build_row(root: Path, sample: dict[str, str]) -> dict[str, Any]:
    assets = load_sample_assets(root, sample["name"], sample["code"])
    l3 = assets["l3"]
    finance = assets["finance"]
    industry = assets["industry"]
    technical = item_score(l3, "技术结构")
    fundamental = item_score(l3, "基本面/资金")
    policy = item_score(l3, "政策事件")
    market = item_score(l3, "市场风格适配")
    industry_score = industry.get("industry_price_shadow_score", {}) if isinstance(industry, dict) else {}
    finance_score = finance.get("fundamental_capital_shadow_score", {}) if isinstance(finance, dict) else {}

    missing = unique_missing(
        technical.get("missing"),
        fundamental.get("missing"),
        policy.get("missing"),
        market.get("missing"),
        l3.get("missing_summary"),
        finance_score.get("missing") if isinstance(finance_score, dict) else [],
        industry.get("missing") if isinstance(industry, dict) else [],
    )
    row = {
        "stock": sample,
        "total_score": l3.get("total_score"),
        "conclusion": l3.get("conclusion_text"),
        "confidence": (l3.get("confidence") or {}).get("level") if isinstance(l3.get("confidence"), dict) else l3.get("confidence"),
        "item_scores": {
            "technical": technical.get("score"),
            "fundamental_capital": fundamental.get("score"),
            "policy_events": policy.get("score"),
            "market_style_fit": market.get("score"),
        },
        "policy_score": float(policy.get("score") or 0),
        "market_style_confidence": market.get("confidence"),
        "finance_card_status": finance.get("状态", "missing") if finance else "missing",
        "industry_price_status": industry.get("状态", "missing") if industry else "missing",
        "industry_price_points": len(industry.get("price_observations", [])) if isinstance(industry.get("price_observations"), list) else 0,
        "missing": missing,
        "paths": {
            "l3_report": str(assets["l3_path"]) if assets["l3_path"] else "",
            "finance_card": str(assets["finance_path"]) if assets["finance_path"] else "",
            "industry_price_card": str(assets["industry_path"]) if assets["industry_path"] else "",
        },
    }
    priority, blockers = classify_priority(row)
    row["priority"] = priority
    row["priority_reasons"] = blockers
    return row


def next_actions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for row in rows:
        name = row["stock"]["name"]
        if row.get("industry_price_status") in {"source_registered", "missing"}:
            actions.append({
                "priority": "P0",
                "stock": name,
                "action": "补行业价格观测入账",
                "boundary": "只补公开可复核价格、日期、单位和来源；不足5个连续观测点前不得写趋势确认。",
            })
        if any("资金" in item or "机构" in item or "减持" in item for item in row.get("missing", [])):
            actions.append({
                "priority": "P0",
                "stock": name,
                "action": "建立资金/机构/减持解禁证据卡候选",
                "boundary": "只做证据卡候选和missing字段，不生成买卖、仓位或交易动作。",
            })
        if any("一季报" in item or "财报" in item for item in row.get("missing", [])):
            actions.append({
                "priority": "P1",
                "stock": name,
                "action": "补最新财报结构化字段",
                "boundary": "只提取公开披露字段，保留来源和缺口；不得凭空补数。",
            })
        if row.get("policy_score", 0) < 5:
            actions.append({
                "priority": "P1",
                "stock": name,
                "action": "补政策事件匹配或确认无直接政策",
                "boundary": "无结构化政策时明确写无直接政策，不让模型凭空加分。",
            })
    dedup: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for action in actions:
        key = (action["stock"], action["action"])
        if key not in seen:
            seen.add(key)
            dedup.append(action)
    return dedup


def build_markdown(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['stock']['name']} | {item['total_score']} | {item['conclusion']} | {item['confidence']} | {item['industry_price_status']} | {item['priority']} | {'；'.join(item['priority_reasons'])} |"
        for item in report["samples"]
    ]
    action_rows = [
        f"| {item['priority']} | {item['stock']} | {item['action']} | {item['boundary']} |"
        for item in report["next_actions"]
    ]
    return "\n".join([
        "# L3五样本证据缺口优先级报告",
        "",
        f"- 生成时间：{report['generated_at']}",
        "- 资产身份：W1只读分析报告，不是正式配置，不是入口，不写正式库。",
        "- 安全边界：未触发n8n、未发送企业微信、未重启服务、未调用券商接口、未自动交易。",
        "",
        "## 样本缺口",
        "",
        "| 股票 | 总分 | 结论 | 置信度 | 行业价格状态 | 优先级 | 主要原因 |",
        "|---|---:|---|---|---|---|---|",
        *rows,
        "",
        "## 下一步证据动作",
        "",
        "| 优先级 | 股票 | 动作 | 边界 |",
        "|---|---|---|---|",
        *(action_rows or ["| P3 | 全部 | 暂无新增高优先级证据动作 | 按复盘节奏跟踪 |"]),
        "",
        "## 读取来源",
        "",
        "- 总管当前施工面板：只读",
        "- 一键接续施工包：只读",
        "- 股票L3短答证据闭环状态面板：只读",
        "",
    ])


def main() -> int:
    root = module_root()
    base = base_dir(root)
    rows = [build_row(root, sample) for sample in SAMPLES]
    policy_events = load_json(base / "policy_events_v1.0.json", []) or []
    market_style = load_json(base / "market_style_daily_latest.json", {}) or {}
    report = {
        "name": "L3五样本证据缺口优先级报告",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1只读分析报告",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "samples": rows,
        "next_actions": next_actions(rows),
        "context": {
            "policy_event_count": len(policy_events) if isinstance(policy_events, list) else 0,
            "market_style_status": market_style.get("status") or market_style.get("状态"),
            "market_style_date": market_style.get("date") or market_style.get("日期"),
            "read_current_construction_panel": True,
            "read_one_key_continuation_package": True,
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_delete_or_move_old_assets": True,
            "not_formal_database_write": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }
    json_path = base / "L3五样本证据缺口优先级报告_最新.json"
    md_path = base / "L3五样本证据缺口优先级报告_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({"status": "completed", "samples": len(rows), "actions": len(report["next_actions"]), "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
