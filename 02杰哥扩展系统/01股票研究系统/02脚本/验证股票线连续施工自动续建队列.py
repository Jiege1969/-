# -*- coding: utf-8 -*-
"""
验证股票线连续施工自动续建队列。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "股票线连续施工自动续建队列_最新.json"
RESULT_JSON = DATA_DIR / "股票线连续施工自动续建队列验收_最新.json"
RESULT_MD = DATA_DIR / "股票线连续施工自动续建队列验收_最新.md"


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1连续施工节奏资产":
        errors.append("资产身份必须是 W1连续施工节奏资产")
    if asset.get("status") != "active_for_shadow_construction":
        errors.append("状态必须是 active_for_shadow_construction")
    if asset.get("allowed_write_root") != str(BASE_DIR):
        errors.append("allowed_write_root 必须限制在股票分析系统目录")

    role = asset.get("role_boundary", {})
    for flag in ["not_general_manager", "only_stock_line", "research_analysis_positioning", "not_trading_robot"]:
        if role.get(flag) is not True:
            errors.append(f"角色边界 {flag} 必须为 true")

    readonly = asset.get("mandatory_readonly_before_each_round", [])
    if len(readonly) != 2:
        errors.append("每轮开始前只读文件必须为2项")
    if not any("当前施工面板.md" in item for item in readonly):
        errors.append("缺少当前施工面板只读项")
    if not any("一键接续施工包_最新.md" in item for item in readonly):
        errors.append("缺少一键接续施工包只读项")

    auto = asset.get("auto_continue_rule", {})
    if "不等待用户确认" not in auto.get("w1_w2_low_risk", ""):
        errors.append("W1/W2自动续建规则必须明确不等待用户确认")
    if "不把下一步建议当成请求确认" not in auto.get("final_response_is_report_not_pause", ""):
        errors.append("汇报口径必须纠正下一步建议等于暂停的问题")
    if auto.get("must_self_validate_each_round") is not True:
        errors.append("必须每轮自验收")
    if auto.get("must_write_alignment_record_each_round") is not True:
        errors.append("必须每轮写对齐回传记录")

    queue = asset.get("construction_queue", [])
    if len(queue) < 5:
        errors.append("连续施工队列至少应有5项")
    for item in queue:
        if item.get("risk_level") not in {"W1", "W2"}:
            errors.append(f"{item.get('id')} 风险等级必须为W1/W2")
        if item.get("requires_user_confirmation") is not False:
            errors.append(f"{item.get('id')} 低风险项不得要求用户确认")

    blocked = asset.get("blocked_queue", [])
    if not blocked:
        errors.append("必须登记红线阻断队列")
    for item in blocked:
        if item.get("risk_level") != "W3":
            errors.append(f"{item.get('id')} 阻断项必须为W3")
        if item.get("status") != "blocked_register_only":
            errors.append(f"{item.get('id')} 阻断项只能登记")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_formal_config", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "股票线连续施工自动续建队列验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "queue_count": len(queue),
            "blocked_count": len(blocked),
            "completed_count": len([item for item in queue if item.get("status") == "completed"]),
            "queued_count": len([item for item in queue if item.get("status") == "queued"]),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 股票线连续施工自动续建队列验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 队列数量：{result['metrics'].get('queue_count', 0)}",
        f"- 阻断数量：{result['metrics'].get('blocked_count', 0)}",
        f"- 已完成：{result['metrics'].get('completed_count', 0)}",
        f"- 待续建：{result['metrics'].get('queued_count', 0)}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in result["errors"]] or ["- 无"])
    lines.extend(["", "## 警告", ""])
    lines.extend([f"- {item}" for item in result["warnings"]] or ["- 无"])
    lines.append("")
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
