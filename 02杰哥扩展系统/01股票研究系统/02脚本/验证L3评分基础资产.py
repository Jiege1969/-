# -*- coding: utf-8 -*-
"""
名称：验证L3评分基础资产.py
作用：验证L3评分契约、政策事件库、股票政策暴露度表、市场风格日表是否具备可读取、可评分、可复盘的最小条件。
触发方式：python 验证L3评分基础资产.py
安全边界：只读01配置和03数据/245L3评分基础资产；只写03数据/245L3评分基础资产/验证结果；不联网；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False, "ok": False, "message": "文件不存在"}
    try:
        load_json(path)
        return {"path": str(path), "exists": True, "ok": True, "message": "JSON可解析"}
    except Exception as exc:
        return {"path": str(path), "exists": True, "ok": False, "message": f"JSON解析失败：{exc}"}


def validate_contract(contract: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    items = contract.get("scoring_items", [])
    names = {item.get("name") for item in items}
    expected = {"technical_structure", "fundamentals_capital", "policy_events", "market_style_fit"}
    if names != expected:
        issues.append(f"评分项不完整：当前={sorted(names)}")
    total_weight = sum(int(item.get("weight", 0)) for item in items)
    if total_weight != 100:
        issues.append(f"评分权重合计不是100：{total_weight}")
    thresholds = contract.get("conclusion_thresholds", {})
    if not {"重点关注", "可纳入观察", "暂不建议关注"}.issubset(thresholds):
        issues.append("结论阈值缺少重点关注/可纳入观察/暂不建议关注")
    if "missing_handling" not in contract.get("scoring_rules", {}):
        issues.append("缺少missing_handling规则")
    return issues


def validate_policy_events(events: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    seen: set[str] = set()
    required = {
        "event_id",
        "title",
        "publish_date",
        "status",
        "source_url",
        "source_level",
        "impact_direction",
        "impact_strength",
        "event_confidence",
        "industry_tags",
    }
    for event in events:
        event_id = str(event.get("event_id", ""))
        missing = sorted(required - set(event))
        if missing:
            issues.append(f"{event_id or 'unknown'} 缺字段：{missing}")
        if event_id in seen:
            issues.append(f"重复event_id：{event_id}")
        seen.add(event_id)
        if event.get("status") in {"active", "superseded_active"} and event.get("source_level") not in {"official", "exchange", "company_filing"}:
            issues.append(f"{event_id} 是正式事件但source_level不够高")
        strength = event.get("impact_strength")
        confidence = event.get("event_confidence")
        if not isinstance(strength, (int, float)) or not 0 <= strength <= 1:
            issues.append(f"{event_id} impact_strength不在0-1")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            issues.append(f"{event_id} event_confidence不在0-1")
    return issues


def validate_exposures(exposures: list[dict[str, Any]], event_ids: set[str]) -> list[str]:
    issues: list[str] = []
    required = {"event_id", "stock_code", "stock_name", "exposure", "exposure_reason"}
    for row in exposures:
        key = f"{row.get('event_id', 'unknown')}/{row.get('stock_code', 'unknown')}"
        missing = sorted(required - set(row))
        if missing:
            issues.append(f"{key} 缺字段：{missing}")
        if row.get("event_id") not in event_ids:
            issues.append(f"{key} 找不到对应政策事件")
        exposure = row.get("exposure")
        if not isinstance(exposure, (int, float)) or not 0 <= exposure <= 1:
            issues.append(f"{key} exposure不在0-1")
    return issues


def validate_market_style(style: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    required = {
        "date",
        "market",
        "status",
        "risk_appetite",
        "sector_heat",
        "size_style",
        "liquidity",
        "final_adaptation_score",
        "moderate_coefficient",
        "missing_summary",
    }
    missing = sorted(required - set(style))
    if missing:
        issues.append(f"市场风格日表缺字段：{missing}")
    score = style.get("final_adaptation_score")
    if not isinstance(score, int) or not 0 <= score <= 20:
        issues.append("final_adaptation_score必须是0-20整数")
    coefficient = style.get("moderate_coefficient")
    if not isinstance(coefficient, (int, float)) or not 0.85 <= coefficient <= 1.15:
        issues.append("moderate_coefficient必须在0.85-1.15")
    if style.get("status") in {"draft", "partial"}:
        issues.append("市场风格日表仍为draft/partial，只能作为低或中置信度证据")
    return issues


def markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# L3评分基础资产验证结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 总体状态：{result['status']}",
        "",
        "## 文件检查",
        "",
    ]
    for item in result["files"]:
        lines.append(f"- {item['path']}：{item['message']}")
    lines.extend(["", "## 规则检查", ""])
    for section, issues in result["issues"].items():
        if issues:
            lines.append(f"### {section}")
            for issue in issues:
                lines.append(f"- {issue}")
            lines.append("")
        else:
            lines.append(f"- {section}：通过")
    lines.extend(["", "## 下一步", ""])
    lines.append(result["next_step"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    config = root / "01配置"
    data = root / "03数据" / "245L3评分基础资产"
    out = data / "验证结果"

    paths = {
        "contract": config / "L3_scoring_contract_v1.0.json",
        "policy_schema": config / "policy_events_schema_v1.0.json",
        "market_style_schema": config / "market_style_daily_schema_v1.0.json",
        "policy_events": data / "policy_events_v1.0.json",
        "stock_policy_exposures": data / "stock_policy_exposures_v1.0.json",
        "market_style_latest": data / "market_style_daily_latest.json",
    }
    files = [file_status(path) for path in paths.values()]
    issues: dict[str, list[str]] = {
        "L3评分契约": [],
        "政策事件主表": [],
        "股票政策暴露度": [],
        "市场风格日表": [],
    }

    if all(item["ok"] for item in files):
        contract = load_json(paths["contract"])
        events = load_json(paths["policy_events"])
        exposures = load_json(paths["stock_policy_exposures"])
        style = load_json(paths["market_style_latest"])
        event_ids = {event.get("event_id") for event in events}
        issues["L3评分契约"] = validate_contract(contract)
        issues["政策事件主表"] = validate_policy_events(events)
        issues["股票政策暴露度"] = validate_exposures(exposures, event_ids)
        issues["市场风格日表"] = validate_market_style(style)

    blocking = [item for item in files if not item["ok"]]
    issue_count = sum(len(value) for value in issues.values())
    status = "PASS" if not blocking and issue_count == 0 else "PASS_WITH_NOTES" if not blocking else "FAIL"
    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "files": files,
        "issues": issues,
        "next_step": "将market_style_daily_latest.json从draft升级为confirmed，并补齐上涨/下跌家数、大小盘指数涨跌幅后，可进入更高置信度L3评分。",
    }
    write_json(out / "L3评分基础资产验证结果_最新.json", result)
    write_text(out / "L3评分基础资产验证结果_最新.md", markdown_report(result))
    print(json.dumps({"状态": status, "输出": str(out)}, ensure_ascii=False))
    return 0 if status in {"PASS", "PASS_WITH_NOTES"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
