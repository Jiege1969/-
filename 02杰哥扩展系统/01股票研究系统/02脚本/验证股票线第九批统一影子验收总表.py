# -*- coding: utf-8 -*-
"""验证股票线第九批统一影子验收总表。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_JSON = DATA_DIR / "股票线第九批统一影子验收总表_最新.json"
RESULT_JSON = DATA_DIR / "股票线第九批统一影子验收总表验收结果_最新.json"
RESULT_MD = DATA_DIR / "股票线第九批统一影子验收总表验收结果_最新.md"


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_JSON.read_text(encoding="utf-8-sig")) if ASSET_JSON.exists() else {}
    summary = asset.get("summary", {})
    if asset.get("status") != "shadow_batch_acceptance":
        errors.append("总表状态必须为 shadow_batch_acceptance")
    if summary.get("failed_count") != 0:
        errors.append("总表检查项不得失败")
    if summary.get("passed_count") != summary.get("check_count"):
        errors.append("通过数必须等于检查项总数")
    if summary.get("real_system_triggered") is not False:
        errors.append("不得触发真实系统")
    for flag in [
        "not_n8n",
        "not_external_send",
        "not_formal_config",
        "not_broker_interface",
        "not_auto_trade",
        "not_order",
        "not_position_adjustment",
    ]:
        if asset.get("safety_boundary", {}).get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")
    result = {
        "name": "股票线第九批统一影子验收总表验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": summary,
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    RESULT_MD.write_text(
        "\n".join([
            "# 股票线第九批统一影子验收总表验收结果",
            "",
            f"- 生成时间：{result['generated_at']}",
            f"- 是否通过：{'是' if result['passed'] else '否'}",
            f"- 检查项：{summary.get('check_count', 0)}",
            f"- 通过：{summary.get('passed_count', 0)}",
            f"- 失败：{summary.get('failed_count', 0)}",
            "",
            "## 错误",
            "",
            *([f"- {item}" for item in errors] or ["- 无"]),
        ]),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
