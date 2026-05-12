# -*- coding: utf-8 -*-
"""验收股票线第四批统一影子验收总表。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "股票线第四批统一影子验收总表_最新.json"
RESULT_JSON = DATA_DIR / "股票线第四批统一影子验收总表验收_最新.json"
RESULT_MD = DATA_DIR / "股票线第四批统一影子验收总表验收_最新.md"


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W2第四批统一影子验收总表":
        errors.append("资产身份不正确")
    if asset.get("status") != "shadow_acceptance_summary":
        errors.append("状态不是shadow_acceptance_summary")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_score_write"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    records = asset.get("records", [])
    if len(records) != 5:
        errors.append("验收检查项必须为5项")
    if not all(item.get("exists") for item in records):
        errors.append("存在缺失验收文件")
    if not all(item.get("passed") for item in records):
        errors.append("存在未通过验收项")
    summary = asset.get("summary", {})
    if summary.get("failed_count") != 0:
        errors.append("failed_count必须为0")
    if summary.get("allow_real_wecom_send") is not False:
        errors.append("allow_real_wecom_send必须为false")
    if summary.get("allow_formal_entry") is not False:
        errors.append("allow_formal_entry必须为false")
    if summary.get("allow_formal_score_update") is not False:
        errors.append("allow_formal_score_update必须为false")
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
    ]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界{flag}必须为true")
    result = {
        "name": "股票线第四批统一影子验收总表验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {
            "check_count": summary.get("check_count", 0),
            "passed_count": summary.get("passed_count", 0),
            "failed_count": summary.get("failed_count", 0),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票线第四批统一影子验收总表验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 通过项：{result['metrics']['passed_count']}/{result['metrics']['check_count']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
