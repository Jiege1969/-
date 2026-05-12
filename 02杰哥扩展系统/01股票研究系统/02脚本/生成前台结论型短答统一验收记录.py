# -*- coding: utf-8 -*-
"""
生成前台结论型短答统一验收记录。

把已有前台短答样例与财报资金、行业价格、政策事件、市场风格四类证据闸口
合并验收，确保企业微信前台口径是结论型短答，而不是后台指标堆叠。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
SOURCE_FRONT = DATA_DIR / "影子前台短答刷新验收样例_最新.json"
JSON_OUT = DATA_DIR / "前台结论型短答统一验收记录_最新.json"
MD_OUT = DATA_DIR / "前台结论型短答统一验收记录_最新.md"

GATE_ASSETS = [
    ("financial_capital", DATA_DIR / "财报资金证据人工填写回执模板验收_最新.json"),
    ("industry_price", DATA_DIR / "行业价格观测人工填报回执模板验收_最新.json"),
    ("policy_event_exposure", DATA_DIR / "政策事件单股暴露度人工复核回执模板验收_最新.json"),
    ("market_style_fit", DATA_DIR / "市场风格单股适配人工复核回执模板验收_最新.json"),
]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return default


def gate_check(name: str, path: Path) -> dict[str, Any]:
    data = load_json(path, {})
    return {
        "name": name,
        "path": str(path),
        "exists": path.exists(),
        "passed": data.get("passed") is True,
        "errors": data.get("errors", []),
        "metrics": data.get("metrics", {}),
    }


def build_asset() -> dict[str, Any]:
    front = load_json(SOURCE_FRONT, {})
    sample_checks = front.get("sample_checks", [])
    gates = [gate_check(name, path) for name, path in GATE_ASSETS]
    return {
        "name": "前台结论型短答统一验收记录",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1前台短答统一验收记录",
        "status": "shadow_acceptance",
        "source_assets": {
            "front_shadow_acceptance": str(SOURCE_FRONT),
            "front_shadow_acceptance_exists": SOURCE_FRONT.exists(),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "not_real_wecom_send": True,
        "front_answer_contract": {
            "required_lines": ["对象行", "结论行", "主要原因", "关键缺口", "置信度/复核重点"],
            "user_view_rule": "前台给结论和少量原因，后台保留证据链、缺口和复盘字段。",
            "missing_rule": "财报资金、行业价格、政策事件或市场风格证据缺失时，必须显式标注缺口，不能强行补分。",
            "forbidden": ["买入", "卖出", "下单", "仓位调整", "自动交易", "券商接口"],
        },
        "evidence_gate_checks": gates,
        "sample_checks": sample_checks,
        "summary": {
            "sample_count": len(sample_checks),
            "sample_passed_count": len([item for item in sample_checks if item.get("passed") is True]),
            "gate_count": len(gates),
            "gate_passed_count": len([item for item in gates if item.get("passed") is True]),
            "allow_shadow_front_answer": bool(sample_checks) and all(item.get("passed") is True for item in sample_checks),
            "allow_real_wecom_send": False,
            "allow_formal_entry": False,
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_adapter_write": True,
            "not_score_write": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }


def write_markdown(asset: dict[str, Any]) -> None:
    summary = asset["summary"]
    lines = [
        "# 前台结论型短答统一验收记录",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：影子验收，不真实发送企业微信，不改正式入口。",
        "",
        "## 汇总",
        "",
        f"- 样本通过：{summary['sample_passed_count']}/{summary['sample_count']}",
        f"- 证据闸口通过：{summary['gate_passed_count']}/{summary['gate_count']}",
        f"- 允许影子前台短答：{summary['allow_shadow_front_answer']}",
        f"- 允许真实企微发送：{summary['allow_real_wecom_send']}",
        "",
        "## 证据闸口",
        "",
    ]
    for gate in asset["evidence_gate_checks"]:
        lines.append(f"- {gate['name']}：exists={gate['exists']}，passed={gate['passed']}")
    lines.extend(["", "## 样本验收", ""])
    for item in asset["sample_checks"]:
        stock = item.get("stock", {})
        lines.append(f"- {stock.get('name')}（{stock.get('code')}）：passed={item.get('passed')}")
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    asset = build_asset()
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({"status": "ok", "json": str(JSON_OUT), "md": str(MD_OUT), "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
