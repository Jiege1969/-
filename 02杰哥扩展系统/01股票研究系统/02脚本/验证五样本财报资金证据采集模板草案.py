# -*- coding: utf-8 -*-
"""
验证五样本财报/资金证据采集模板草案。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "五样本财报资金证据采集模板草案_最新.json"
RESULT_JSON = DATA_DIR / "五样本财报资金证据采集模板草案验收_最新.json"
RESULT_MD = DATA_DIR / "五样本财报资金证据采集模板草案验收_最新.md"

EXPECTED_CODES = {"sz002428", "sz002466", "sh688347", "sz000906", "sz300641"}
REQUIRED_GROUPS = {"financial_report", "valuation", "capital_flow", "institution_holding", "unlock_reduction"}
REQUIRED_FIELD_KEYS = {"value", "source_name", "source_url", "as_of_date", "evidence_status", "review_status", "note"}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1空白采集模板草案":
        errors.append("资产身份必须是 W1空白采集模板草案")
    if asset.get("status") != "draft":
        errors.append("状态必须保持 draft")

    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write", "not_real_data_fetch", "not_formal_database_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_adapter_write", "not_score_write", "not_entrypoint", "not_broker_interface", "not_auto_trade", "not_real_data_fetch"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    templates = asset.get("templates", [])
    codes = {item.get("stock", {}).get("code") for item in templates}
    if codes != EXPECTED_CODES:
        errors.append(f"样本代码不完整：{sorted(codes)}")
    if len(templates) != 5:
        errors.append(f"样本数量应为5，实际{len(templates)}")

    for item in templates:
        stock = item.get("stock", {})
        if item.get("overall_ready") is not False:
            errors.append(f"{stock.get('name')} overall_ready 必须为 false")
        if item.get("overall_score_status") != "not_scored_until_evidence_ready":
            errors.append(f"{stock.get('name')} overall_score_status 非法")
        groups = item.get("evidence_groups", [])
        group_ids = {group.get("field_group") for group in groups}
        if group_ids != REQUIRED_GROUPS:
            errors.append(f"{stock.get('name')} 证据组不完整：{sorted(group_ids)}")
        for group in groups:
            if group.get("score_status") != "not_scored_until_evidence_ready":
                errors.append(f"{stock.get('name')} {group.get('field_group')} score_status 非法")
            if group.get("ready_check", {}).get("ready") is not False:
                errors.append(f"{stock.get('name')} {group.get('field_group')} ready_check 必须为 false")
            for field_name, field in group.get("fields", {}).items():
                if set(field) != REQUIRED_FIELD_KEYS:
                    errors.append(f"{stock.get('name')} {field_name} 字段结构不完整")
                if field.get("value") is not None:
                    errors.append(f"{stock.get('name')} {field_name} 不得预填 value")
                if field.get("evidence_status") != "missing":
                    errors.append(f"{stock.get('name')} {field_name} 默认 evidence_status 必须 missing")
                if field.get("review_status") != "pending_review":
                    errors.append(f"{stock.get('name')} {field_name} 默认 review_status 必须 pending_review")

    gate_text = "\n".join(asset.get("quality_gates", []))
    for phrase in ["五个样本", "财报摘要", "估值位置", "资金流向", "机构持仓", "解禁/减持", "默认 missing", "不得写企业微信入口"]:
        if phrase not in gate_text:
            errors.append(f"质量闸口缺少：{phrase}")

    result = {
        "name": "五样本财报资金证据采集模板草案验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "sample_count": len(templates),
            "group_count": asset.get("summary", {}).get("group_count", 0),
            "blank_field_count": asset.get("summary", {}).get("blank_field_count", 0),
            "ready_count": asset.get("summary", {}).get("ready_count", 0),
        },
        "next_step": "继续生成统一刷新验收清单或资金证据人工填写回执模板；仍不得抓取真实数据或写正式库。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 五样本财报资金证据采集模板草案验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 样本数量：{result['metrics']['sample_count']}",
        f"- 证据组数量：{result['metrics']['group_count']}",
        f"- 空白字段数量：{result['metrics']['blank_field_count']}",
        f"- ready 数量：{result['metrics']['ready_count']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in result["errors"]] or ["- 无"])
    lines.extend(["", "## 警告", ""])
    lines.extend([f"- {item}" for item in result["warnings"]] or ["- 无"])
    lines.extend(["", "## 下一步", "", f"- {result['next_step']}", ""])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
