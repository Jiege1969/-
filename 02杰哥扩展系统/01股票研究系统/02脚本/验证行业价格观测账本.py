# -*- coding: utf-8 -*-
"""
名称：验证行业价格观测账本.py
作用：验收行业价格观测账本与行业价格证据卡是否一致，防止单点观测被误写成连续趋势。
触发方式：python 验证行业价格观测账本.py
安全边界：只读本地账本和证据卡；只写验收报告；不抓取外部价格；不发送企业微信；不触发n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_OBSERVATION_FIELDS = [
    "product_code",
    "product_name",
    "price_date",
    "price_mid",
    "unit",
    "currency",
    "source_name",
    "source_url",
    "checked_at",
    "authorization_status",
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


def check_observation(item: dict[str, Any], index: int) -> list[str]:
    problems: list[str] = []
    for field in REQUIRED_OBSERVATION_FIELDS:
        value = item.get(field)
        if value in (None, ""):
            problems.append(f"第{index}条观测缺少字段：{field}")
    price = item.get("price_mid")
    if not isinstance(price, (int, float)) or price <= 0:
        problems.append(f"第{index}条观测 price_mid 非正数")
    source_url = str(item.get("source_url") or "")
    if source_url and not source_url.startswith(("http://", "https://")):
        problems.append(f"第{index}条观测 source_url 不是可复核URL")
    return problems


def expected_status(observation_count: int, has_source: bool) -> str:
    if observation_count >= 5:
        return "trend_ready"
    if observation_count > 0:
        return "single_observation"
    if has_source:
        return "source_registered"
    return "missing_source"


def card_product_codes(card: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    for item in card.get("tracked_products", []) if isinstance(card.get("tracked_products"), list) else []:
        code = str(item.get("product_code") or "").strip()
        if code:
            codes.append(code)
    return codes


def validate_cards(root: Path, observations_by_product: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    rows: list[dict[str, Any]] = []
    blocking: list[str] = []
    warnings: list[str] = []
    for path in sorted(base_dir(root).glob("*_行业价格证据卡_本地观测_latest.json")):
        card = load_json(path, {}) or {}
        stock = card.get("stock", {}) if isinstance(card.get("stock"), dict) else {}
        product_codes = card_product_codes(card)
        observation_count = sum(len(observations_by_product.get(code, [])) for code in product_codes)
        has_source = bool(card.get("sources"))
        actual_status = str(card.get("状态") or card.get("status") or "")
        should_be = expected_status(observation_count, has_source)
        source_status = card.get("source_status", {}) if isinstance(card.get("source_status"), dict) else {}

        row = {
            "card": str(path),
            "stock_name": stock.get("name"),
            "display_code": stock.get("display_code"),
            "product_codes": product_codes,
            "observation_count": observation_count,
            "actual_status": actual_status,
            "expected_status_floor": should_be,
            "trend_available": source_status.get("trend_available"),
            "price_value_available": source_status.get("price_value_available"),
        }
        rows.append(row)

        if actual_status == "trend_ready" and observation_count < 5:
            blocking.append(f"{path.name} 只有{observation_count}个观测点，却标记为trend_ready")
        if observation_count == 0 and actual_status not in {"source_registered", "missing_source"}:
            blocking.append(f"{path.name} 没有入账价格，却标记为{actual_status}")
        if 0 < observation_count < 5 and actual_status != "single_observation":
            blocking.append(f"{path.name} 有{observation_count}个观测点，应保持single_observation，当前为{actual_status}")
        if observation_count >= 5 and actual_status != "trend_ready":
            warnings.append(f"{path.name} 已达到{observation_count}个观测点，可升级为trend_ready")
        if bool(source_status.get("trend_available")) and observation_count < 5:
            blocking.append(f"{path.name} trend_available=True 但观测点不足5个")
        if bool(source_status.get("price_value_available")) != (observation_count > 0):
            blocking.append(f"{path.name} price_value_available 与账本观测数量不一致")
    return rows, blocking, warnings


def build_markdown(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['stock_name']} | {item['display_code']} | {','.join(item['product_codes'])} | {item['observation_count']} | {item['actual_status']} | {item['expected_status_floor']} |"
        for item in report["cards"]
    ]
    lines = [
        "# 行业价格观测账本验收",
        "",
        f"生成时间：{report['generated_at']}",
        f"总体状态：{report['status']}",
        "",
        "## 账本",
        "",
        f"- 观测点数量：{report['ledger']['observation_count']}",
        f"- 产品数量：{report['ledger']['product_count']}",
        f"- 字段问题：{len(report['ledger']['field_problems'])}",
        "",
        "## 证据卡一致性",
        "",
        "| 股票 | 代码 | 产品 | 观测点 | 当前状态 | 状态下限 |",
        "|---|---|---|---:|---|---|",
        *rows,
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
        "- 不抓取外部价格",
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
    ledger_path = out_dir / "industry_price_observations_ledger_v1.0.json"
    ledger = load_json(ledger_path, {}) or {}
    observations = ledger.get("observations", []) if isinstance(ledger.get("observations"), list) else []

    observations_by_product: dict[str, list[dict[str, Any]]] = defaultdict(list)
    field_problems: list[str] = []
    for index, item in enumerate(observations, start=1):
        if not isinstance(item, dict):
            field_problems.append(f"第{index}条观测不是对象")
            continue
        observations_by_product[str(item.get("product_code") or "")].append(item)
        field_problems.extend(check_observation(item, index))

    cards, blocking, warnings = validate_cards(root, observations_by_product)
    blocking.extend(field_problems)
    status = "passed" if not blocking else "failed"
    report = {
        "名称": "行业价格观测账本验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "自动验收报告",
        "status": status,
        "ledger": {
            "path": str(ledger_path),
            "observation_count": len(observations),
            "product_count": len([key for key in observations_by_product if key]),
            "field_problems": field_problems,
        },
        "cards": cards,
        "blocking": blocking,
        "warnings": warnings,
        "rule": {
            "trend_ready_min_observations": 5,
            "single_observation_range": "1-4",
            "zero_observation_status": "source_registered",
        },
        "safety_boundary": {
            "not_external_fetch": True,
            "not_external_send": True,
            "not_n8n": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }
    json_path = out_dir / "行业价格观测账本验收_最新.json"
    md_path = out_dir / "行业价格观测账本验收_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({"status": status, "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
