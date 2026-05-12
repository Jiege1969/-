# -*- coding: utf-8 -*-
"""
名称：验证政策事件库.py
作用：验收政策事件库与股票暴露度映射是否可用于L3评分，防止缺来源、缺暴露、过期事件被误作强政策证据。
触发方式：python 验证政策事件库.py
安全边界：只读本地政策事件和暴露映射；只写验收报告；不抓取外部政策；不发送企业微信；不触发n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


VALID_DIRECTIONS = {"利好", "利空", "中性"}
VALID_STATUS = {"active", "superseded_active", "draft", "retired", "inactive"}
VALID_SOURCE_LEVEL = {"official", "exchange", "company_announcement", "industry_association", "media", "manual_review"}

REQUIRED_EVENT_FIELDS = [
    "event_id",
    "title",
    "publish_date",
    "source_url",
    "source_name",
    "source_level",
    "impact_direction",
    "impact_strength",
    "event_confidence",
    "industry_tags",
    "description",
    "risk_counterpoint",
]

REQUIRED_EXPOSURE_FIELDS = [
    "event_id",
    "stock_code",
    "stock_name",
    "exposure",
    "exposure_direction",
    "exposure_reason",
    "last_reviewed_at",
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


def parse_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def check_event(event: dict[str, Any], event_ids: set[str]) -> tuple[list[str], list[str], dict[str, Any]]:
    blocking: list[str] = []
    warnings: list[str] = []
    event_id = str(event.get("event_id") or "")
    for field in REQUIRED_EVENT_FIELDS:
        if event.get(field) in (None, "", []):
            blocking.append(f"{event_id or '未知事件'} 缺少字段：{field}")

    if event_id in event_ids:
        blocking.append(f"事件ID重复：{event_id}")
    event_ids.add(event_id)

    publish_date = parse_date(event.get("publish_date"))
    effective_date = parse_date(event.get("effective_date")) if event.get("effective_date") else None
    valid_until = parse_date(event.get("valid_until")) if event.get("valid_until") else None
    if not publish_date:
        blocking.append(f"{event_id} publish_date 不是YYYY-MM-DD")
    if effective_date and publish_date and effective_date < publish_date:
        blocking.append(f"{event_id} effective_date 早于 publish_date")
    if valid_until and publish_date and valid_until < publish_date:
        blocking.append(f"{event_id} valid_until 早于 publish_date")

    status = str(event.get("status") or "")
    if status and status not in VALID_STATUS:
        blocking.append(f"{event_id} status 非法：{status}")
    if status == "retired" and not event.get("retired_reason"):
        blocking.append(f"{event_id} 已retired但缺少retired_reason")

    source_url = str(event.get("source_url") or "")
    if source_url and not source_url.startswith(("http://", "https://")):
        blocking.append(f"{event_id} source_url 不是可复核URL")
    source_level = str(event.get("source_level") or "")
    if source_level and source_level not in VALID_SOURCE_LEVEL:
        blocking.append(f"{event_id} source_level 非法：{source_level}")

    direction = str(event.get("impact_direction") or "")
    if direction and direction not in VALID_DIRECTIONS:
        blocking.append(f"{event_id} impact_direction 非法：{direction}")
    for field in ("impact_strength", "event_confidence"):
        value = event.get(field)
        if not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
            blocking.append(f"{event_id} {field} 必须在0-1之间")

    decay_days = event.get("decay_days")
    if decay_days is not None and (not isinstance(decay_days, int) or decay_days <= 0):
        blocking.append(f"{event_id} decay_days 必须为正整数")
    if len(str(event.get("description") or "")) < 30:
        warnings.append(f"{event_id} description 偏短，后续报告解释可能不足")
    if len(str(event.get("risk_counterpoint") or "")) < 20:
        warnings.append(f"{event_id} risk_counterpoint 偏短，可能弱化风险提示")

    row = {
        "event_id": event_id,
        "title": event.get("title"),
        "status": status,
        "publish_date": event.get("publish_date"),
        "source_level": source_level,
        "impact_direction": direction,
        "impact_strength": event.get("impact_strength"),
        "event_confidence": event.get("event_confidence"),
    }
    return blocking, warnings, row


def check_exposure(item: dict[str, Any], event_index: dict[str, dict[str, Any]], seen: set[tuple[str, str]]) -> tuple[list[str], list[str], dict[str, Any]]:
    blocking: list[str] = []
    warnings: list[str] = []
    event_id = str(item.get("event_id") or "")
    stock_code = str(item.get("stock_code") or "")
    for field in REQUIRED_EXPOSURE_FIELDS:
        if item.get(field) in (None, ""):
            blocking.append(f"{event_id}/{stock_code} 暴露映射缺少字段：{field}")
    key = (event_id, stock_code)
    if key in seen:
        blocking.append(f"暴露映射重复：{event_id}/{stock_code}")
    seen.add(key)
    if event_id not in event_index:
        blocking.append(f"暴露映射引用不存在的事件：{event_id}/{stock_code}")
    if not stock_code.isdigit() or len(stock_code) != 6:
        blocking.append(f"{event_id}/{stock_code} stock_code 必须为6位数字")
    exposure = item.get("exposure")
    if not isinstance(exposure, (int, float)) or not 0 <= float(exposure) <= 1:
        blocking.append(f"{event_id}/{stock_code} exposure 必须在0-1之间")
    if len(str(item.get("exposure_reason") or "")) < 20:
        warnings.append(f"{event_id}/{stock_code} exposure_reason 偏短")
    if not parse_date(item.get("last_reviewed_at")):
        blocking.append(f"{event_id}/{stock_code} last_reviewed_at 不是YYYY-MM-DD")
    row = {
        "event_id": event_id,
        "stock_code": stock_code,
        "stock_name": item.get("stock_name"),
        "exposure": item.get("exposure"),
        "exposure_direction": item.get("exposure_direction"),
        "last_reviewed_at": item.get("last_reviewed_at"),
    }
    return blocking, warnings, row


def build_markdown(report: dict[str, Any]) -> str:
    event_rows = [
        f"| {item['event_id']} | {item['status']} | {item['publish_date']} | {item['source_level']} | {item['impact_direction']} | {item['impact_strength']} |"
        for item in report["events"]
    ]
    exposure_rows = [
        f"| {item['event_id']} | {item['stock_name']} | {item['stock_code']} | {item['exposure']} | {item['exposure_direction']} |"
        for item in report["exposures"]
    ]
    lines = [
        "# 政策事件库验收",
        "",
        f"生成时间：{report['generated_at']}",
        f"总体状态：{report['status']}",
        "",
        "## 事件",
        "",
        "| event_id | 状态 | 发布日 | 来源层级 | 方向 | 强度 |",
        "|---|---|---|---|---|---:|",
        *event_rows,
        "",
        "## 暴露映射",
        "",
        "| event_id | 股票 | 代码 | 暴露度 | 方向 |",
        "|---|---|---|---:|---|",
        *exposure_rows,
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in report["blocking"]] or ["- 无"])
    lines.extend(["", "## 提醒项", ""])
    lines.extend([f"- {item}" for item in report["warnings"]] or ["- 无"])
    lines.extend([
        "",
        "## 边界",
        "",
        "- 不抓取外部政策",
        "- 不真实发送企业微信",
        "- 不触发 n8n",
        "- 不调用券商接口",
        "- 不自动交易",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    out_dir = base_dir(root)
    events_path = out_dir / "policy_events_v1.0.json"
    exposures_path = out_dir / "stock_policy_exposures_v1.0.json"
    events_raw = load_json(events_path, []) or []
    exposures_raw = load_json(exposures_path, []) or []

    blocking: list[str] = []
    warnings: list[str] = []
    event_rows: list[dict[str, Any]] = []
    event_ids: set[str] = set()
    for event in events_raw:
        if not isinstance(event, dict):
            blocking.append("政策事件列表中存在非对象记录")
            continue
        b, w, row = check_event(event, event_ids)
        blocking.extend(b)
        warnings.extend(w)
        event_rows.append(row)

    event_index = {str(event.get("event_id")): event for event in events_raw if isinstance(event, dict)}
    exposure_rows: list[dict[str, Any]] = []
    seen_exposure: set[tuple[str, str]] = set()
    for item in exposures_raw:
        if not isinstance(item, dict):
            blocking.append("股票暴露映射列表中存在非对象记录")
            continue
        b, w, row = check_exposure(item, event_index, seen_exposure)
        blocking.extend(b)
        warnings.extend(w)
        exposure_rows.append(row)

    events_with_exposure = {item["event_id"] for item in exposure_rows}
    for event_id in event_ids:
        if event_id not in events_with_exposure:
            warnings.append(f"{event_id} 暂无股票暴露映射，无法进入单股政策评分")

    status = "passed" if not blocking else "failed"
    report = {
        "名称": "政策事件库验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "自动验收报告",
        "status": status,
        "source_files": {
            "policy_events": str(events_path),
            "stock_policy_exposures": str(exposures_path),
        },
        "summary": {
            "event_count": len(event_rows),
            "exposure_count": len(exposure_rows),
            "events_with_exposure_count": len(events_with_exposure),
            "blocking_count": len(blocking),
            "warning_count": len(warnings),
        },
        "events": event_rows,
        "exposures": exposure_rows,
        "blocking": blocking,
        "warnings": warnings,
        "safety_boundary": {
            "not_external_fetch": True,
            "not_external_send": True,
            "not_n8n": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }
    json_path = out_dir / "政策事件库验收_最新.json"
    md_path = out_dir / "政策事件库验收_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({"status": status, "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
