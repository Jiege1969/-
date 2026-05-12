# -*- coding: utf-8 -*-
"""
验证五样本财报/资金证据补齐路线图。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "五样本财报资金证据补齐路线图_最新.json"
RESULT_JSON = DATA_DIR / "五样本财报资金证据补齐路线图验收_最新.json"
RESULT_MD = DATA_DIR / "五样本财报资金证据补齐路线图验收_最新.md"

EXPECTED_CODES = {"sz002428", "sz002466", "sh688347", "sz000906", "sz300641"}
REQUIRED_GROUPS = {"financial_report", "valuation", "capital_flow", "institution_holding", "unlock_reduction"}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1证据补齐路线图":
        errors.append("资产身份必须是 W1证据补齐路线图")
    if asset.get("status") != "draft":
        errors.append("状态必须保持 draft")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_adapter_write", "not_score_write", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    routes = asset.get("stock_routes", [])
    codes = {route.get("stock", {}).get("code") for route in routes}
    if codes != EXPECTED_CODES:
        errors.append(f"样本代码不完整：{sorted(codes)}")
    if len(routes) != 5:
        errors.append(f"样本数量应为5，实际{len(routes)}")

    global_groups = {group.get("field_group") for group in asset.get("global_evidence_groups", [])}
    if global_groups != REQUIRED_GROUPS:
        errors.append(f"全局证据组不完整：{sorted(global_groups)}")

    for group in asset.get("global_evidence_groups", []):
        if not group.get("fields"):
            errors.append(f"{group.get('field_group')} 缺少字段清单")
        if not group.get("minimum_ready_condition"):
            errors.append(f"{group.get('field_group')} 缺少 ready 条件")
        if not group.get("front_gap_wording"):
            errors.append(f"{group.get('field_group')} 缺少前台缺口话术")
        if group.get("priority") not in {"P0", "P1"}:
            errors.append(f"{group.get('field_group')} 优先级非法")

    for route in routes:
        stock = route.get("stock", {})
        groups = route.get("evidence_groups", [])
        route_groups = {group.get("field_group") for group in groups}
        if route_groups != REQUIRED_GROUPS:
            errors.append(f"{stock.get('name')} 证据组不完整：{sorted(route_groups)}")
        if not route.get("stock_specific_fields"):
            warnings.append(f"{stock.get('name')} 缺少股票特有字段")
        for group in groups:
            if group.get("score_status") != "not_scored_until_evidence_ready":
                errors.append(f"{stock.get('name')} {group.get('field_group')} score_status 未保持未评分")
            if "写正式库" not in group.get("blocked_action", ""):
                errors.append(f"{stock.get('name')} {group.get('field_group')} 未登记正式库阻断")

    gate_text = "\n".join(asset.get("quality_gates", []))
    for phrase in ["财报摘要", "估值位置", "资金流向", "机构持仓", "解禁/减持", "不得自动抓取"]:
        if phrase not in gate_text:
            errors.append(f"质量闸口缺少：{phrase}")

    blockers = asset.get("formalization_blockers", [])
    if len(blockers) < 3:
        errors.append("正式化阻断登记不足")
    if not all(item.get("risk_level") == "W3" for item in blockers):
        errors.append("正式化阻断必须全部标注 W3")

    result = {
        "name": "五样本财报资金证据补齐路线图验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "sample_count": len(routes),
            "global_group_count": len(global_groups),
            "total_route_items": asset.get("summary", {}).get("total_route_items", 0),
            "warning_count": len(warnings),
        },
        "next_step": "继续生成财报资金证据采集模板草案；仍不得抓取真实数据或写正式库。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 五样本财报资金证据补齐路线图验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 样本数量：{result['metrics']['sample_count']}",
        f"- 全局证据组数量：{result['metrics']['global_group_count']}",
        f"- 路线项总数：{result['metrics']['total_route_items']}",
        f"- 警告数量：{result['metrics']['warning_count']}",
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
