# -*- coding: utf-8 -*-
"""验证政策事件库字段化补齐样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "政策事件库字段化补齐样例_最新.json"
RESULT_JSON = DATA_DIR / "政策事件库字段化补齐样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "政策事件库字段化补齐样例验收结果_最新.md"
REQUIRED_FIELDS = {
    "event_id",
    "source_name",
    "source_url_status",
    "publish_date",
    "impact_direction",
    "impact_strength",
    "stock_exposure",
    "decay_status",
    "confidence",
    "frontend_effect",
    "missing_reason",
}


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1政策事件字段化样例":
        errors.append("资产身份不正确")
    for flag in ["not_real_policy_database", "not_external_send", "not_formal_entry", "not_score_write"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    samples = asset.get("samples", [])
    if len(samples) < 3:
        errors.append("政策事件样本不得少于3条")
    for sample in samples:
        name = sample.get("stock_name", "")
        event = sample.get("policy_event", {})
        if not REQUIRED_FIELDS.issubset(event.keys()):
            errors.append(f"{name}政策事件字段不完整")
        for field in ["impact_strength", "stock_exposure"]:
            value = event.get(field)
            if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                errors.append(f"{name}.{field}必须在0-1")
        if event.get("source_url_status") != "ready" and not event.get("missing_reason"):
            errors.append(f"{name}来源未ready时必须说明缺口原因")
        if not event.get("frontend_effect"):
            errors.append(f"{name}必须说明前台影响")
    safety = asset.get("safety_boundary", {})
    for flag in [
        "not_n8n",
        "not_external_send",
        "not_service_restart",
        "not_19310",
        "not_real_account",
        "not_formal_database_write",
        "not_formal_config",
        "not_entrypoint",
        "not_broker_interface",
        "not_auto_trade",
        "not_order",
        "not_position_adjustment",
    ]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界{flag}必须为true")
    result = {
        "name": "政策事件库字段化补齐样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {"sample_count": len(samples), "ready_source_count": asset.get("summary", {}).get("ready_source_count", 0)},
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 政策事件库字段化补齐样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 样本数：{result['metrics']['sample_count']}",
        f"- 来源ready数：{result['metrics']['ready_source_count']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
