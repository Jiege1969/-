# -*- coding: utf-8 -*-
"""
验证股票 L3 统一刷新验收执行记录样例。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "股票L3统一刷新验收执行记录样例_最新.json"
RESULT_JSON = DATA_DIR / "股票L3统一刷新验收执行记录样例验收_最新.json"
RESULT_MD = DATA_DIR / "股票L3统一刷新验收执行记录样例验收_最新.md"


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1影子执行记录样例":
        errors.append("资产身份必须是 W1影子执行记录样例")
    if asset.get("status") != "shadow_record":
        errors.append("状态必须是 shadow_record")

    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write", "not_real_refresh"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    header = asset.get("execution_header", {})
    for flag in ["real_refresh_performed", "external_send_performed", "formal_database_write_performed"]:
        if header.get(flag) is not False:
            errors.append(f"execution_header.{flag} 必须为 false")

    records = asset.get("asset_check_records", [])
    if len(records) < 7:
        errors.append("资产检查记录不得少于 7 条")
    for item in records:
        if item.get("actual_exists") is not True:
            errors.append(f"{item.get('display_name')} actual_exists 不是 true")
        if item.get("check_result") != "pass":
            errors.append(f"{item.get('display_name')} check_result 不是 pass")

    decision = asset.get("decision_section", {})
    if decision.get("all_required_assets_ready") is not True:
        errors.append("all_required_assets_ready 应为 true")
    if decision.get("allow_front_answer_generation") is not True:
        errors.append("allow_front_answer_generation 应为 true")
    if decision.get("allow_l3_complete_claim") is not False:
        errors.append("allow_l3_complete_claim 必须为 false，因未真实刷新")
    if "未执行真实数据刷新" not in str(decision.get("missing_summary")):
        errors.append("missing_summary 必须说明未执行真实数据刷新")

    prohibited = "\n".join(asset.get("prohibited_actions", []))
    for phrase in ["真实发送企业微信", "触发 n8n", "写正式库", "买入", "自动交易"]:
        if phrase not in prohibited:
            errors.append(f"禁止动作缺少：{phrase}")

    result = {
        "name": "股票L3统一刷新验收执行记录样例验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": asset.get("summary", {}),
        "next_step": "继续生成影子前台短答刷新验收样例；仍不得真实刷新、外发或写正式库。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 股票L3统一刷新验收执行记录样例验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 资产记录数：{result['metrics'].get('asset_record_count', 0)}",
        f"- 通过数：{result['metrics'].get('pass_count', 0)}",
        f"- 阻断数：{result['metrics'].get('blocked_count', 0)}",
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
