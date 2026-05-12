# -*- coding: utf-8 -*-
"""验证股票提问对象识别与别名映射验收。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "股票提问对象识别与别名映射验收_最新.json"
RESULT_JSON = DATA_DIR / "股票提问对象识别与别名映射验收结果_最新.json"
RESULT_MD = DATA_DIR / "股票提问对象识别与别名映射验收结果_最新.md"
REQUIRED_CODES = {"sz002428", "sz002466", "sh688347", "sz000906", "sz300641"}


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1股票对象识别验收":
        errors.append("资产身份必须是 W1股票对象识别验收")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")
    records = asset.get("records", [])
    codes = {item.get("matched_stock", {}).get("code") for item in records}
    if codes != REQUIRED_CODES:
        errors.append(f"股票代码不完整：{sorted(codes)}")
    for item in records:
        first = item.get("first_line_required", "")
        stock = item.get("matched_stock", {})
        if stock.get("name") not in first or stock.get("code") not in first:
            errors.append(f"{stock.get('code')} 第一行对象不完整")
        if item.get("object_clear") is not True:
            errors.append(f"{stock.get('code')} object_clear必须true")
        if item.get("ambiguous") is not False:
            errors.append(f"{stock.get('code')} ambiguous必须false")
    rules = "\n".join(asset.get("rules", []))
    for phrase in ["第一行必须明确", "不得输出分析结论", "先澄清", "不写正式路由"]:
        if phrase not in rules:
            errors.append(f"规则缺少：{phrase}")
    summary = asset.get("summary", {})
    if summary.get("formal_route_write_allowed") is not False:
        errors.append("formal_route_write_allowed必须false")
    if summary.get("real_wecom_send_allowed") is not False:
        errors.append("real_wecom_send_allowed必须false")
    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_formal_config", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")
    result = {
        "name": "股票提问对象识别与别名映射验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": [],
        "metrics": summary,
        "auto_continue_policy": "通过后继续执行第三批下一小闭环；不等待用户确认。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票提问对象识别与别名映射验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 样本数：{summary.get('sample_count', 0)}",
        f"- 对象明确：{summary.get('object_clear_count', 0)}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
