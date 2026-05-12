# -*- coding: utf-8 -*-
"""
生成影子前台短答刷新验收样例。

只验证本地前台短答样例是否可在影子层输出，不真实外发。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
EXECUTION_PATH = DATA_DIR / "股票L3统一刷新验收执行记录样例_最新.json"
FRONT_SAMPLE_PATH = DATA_DIR / "五样本前台结论型短答修订样例_最新.json"
JSON_OUT = DATA_DIR / "影子前台短答刷新验收样例_最新.json"
MD_OUT = DATA_DIR / "影子前台短答刷新验收样例_最新.md"

FORBIDDEN = ["买入", "卖出", "加仓", "减仓", "下单", "仓位调整", "自动交易", "券商接口", "强烈推荐"]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_front_answer(sample: dict[str, Any]) -> dict[str, Any]:
    stock = sample.get("stock", {})
    lines = sample.get("front_answer", [])
    text = "\n".join(lines)
    checks = {
        "object_line": bool(lines and lines[0] == f"{stock.get('name')}（{stock.get('code')}）"),
        "conclusion_line": "结论：" in text,
        "main_reason_line": "主要原因：" in text,
        "key_gap_line": "关键缺口：" in text,
        "confidence_line": "置信度：" in text,
        "missing_explicit": any(term in text for term in ["待补", "待采集", "未匹配", "尚未", "不足", "不能"]),
        "no_forbidden_terms": not any(term in text for term in FORBIDDEN),
    }
    return {
        "stock": stock,
        "checks": checks,
        "passed": all(checks.values()),
        "front_answer": lines,
        "blocked_reason": None if all(checks.values()) else "前台短答字段或边界未通过影子验收。",
    }


def build_asset() -> dict[str, Any]:
    execution = load_json(EXECUTION_PATH)
    front_samples = load_json(FRONT_SAMPLE_PATH)
    allow_shadow_front = execution.get("decision_section", {}).get("allow_front_answer_generation") is True
    sample_checks = [check_front_answer(item) for item in front_samples.get("samples", [])]
    return {
        "name": "影子前台短答刷新验收样例",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1影子前台短答验收样例",
        "status": "shadow_acceptance",
        "source_assets": {
            "execution_record": str(EXECUTION_PATH),
            "front_answer_samples": str(FRONT_SAMPLE_PATH),
            "execution_record_exists": bool(execution),
            "front_answer_samples_exists": bool(front_samples),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "not_real_refresh": True,
        "shadow_generation_gate": {
            "allow_shadow_front_answer_generation": allow_shadow_front,
            "allow_real_wecom_send": False,
            "allow_formal_l3_complete_claim": False,
            "reason": "影子执行记录允许生成前台短答样例，但未真实刷新，不能真实外发或声称正式 L3 完整。",
        },
        "sample_checks": sample_checks,
        "summary": {
            "sample_count": len(sample_checks),
            "pass_count": sum(1 for item in sample_checks if item["passed"]),
            "blocked_count": sum(1 for item in sample_checks if not item["passed"]),
            "allow_real_wecom_send": False,
            "allow_formal_l3_complete_claim": False,
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
            "not_real_refresh": True,
        },
    }


def write_markdown(asset: dict[str, Any]) -> None:
    lines = [
        "# 影子前台短答刷新验收样例",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：W1 影子验收，不真实外发，不接企业微信入口，不声称正式 L3 完整。",
        "",
        "## 生成闸口",
        "",
    ]
    for key, value in asset["shadow_generation_gate"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 汇总", ""])
    for key, value in asset["summary"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 样本检查", ""])
    for item in asset["sample_checks"]:
        stock = item["stock"]
        lines.extend([f"### {stock.get('name')}（{stock.get('code')}）", "", f"- passed：{item['passed']}"])
        for key, value in item["checks"].items():
            lines.append(f"- {key}：{value}")
        lines.append("")
    lines.extend(["## 下一步自动推进", ""])
    lines.append("- 继续生成“股票线连续施工状态快照”，汇总当前前台短答、证据模板、刷新验收和剩余旧债。")
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
