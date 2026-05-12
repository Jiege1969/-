# -*- coding: utf-8 -*-
"""验收报告缺口优先级排序样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "报告缺口优先级排序样例_最新.json"
RESULT_JSON = DATA_DIR / "报告缺口优先级排序样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "报告缺口优先级排序样例验收结果_最新.md"
REQUIRED_CODES = {"002428", "002466", "688347", "000906", "300641"}
FORBIDDEN = ["买入", "卖出", "下单", "仓位", "自动交易", "券商接口", "正式评分已修改"]


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1报告缺口优先级排序样例":
        errors.append("资产身份不正确")
    if asset.get("status") != "shadow_missing_priority_sample":
        errors.append("状态不是shadow_missing_priority_sample")
    for flag in ["not_formal_config", "not_score_write", "not_entrypoint"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    priority_rules = asset.get("priority_rules", {})
    for priority in ["P0", "P1", "P2"]:
        if priority not in priority_rules:
            errors.append(f"缺少{priority}优先级定义")
    records = asset.get("records", [])
    codes = {item.get("stock", {}).get("code") for item in records}
    if codes != REQUIRED_CODES:
        errors.append(f"样本股票代码不完整：{sorted(codes)}")
    for item in records:
        stock = item.get("stock", {})
        priority = item.get("missing_priority", {})
        for level in ["P0", "P1", "P2"]:
            values = priority.get(level, [])
            if not isinstance(values, list) or len(values) < 2:
                errors.append(f"{stock.get('code')} {level}缺口不足")
        phrase = item.get("front_gap_phrase", "")
        if "关键缺口" not in phrase:
            errors.append(f"{stock.get('code')}前台缺口话术未明确关键缺口")
        combined = json.dumps(item, ensure_ascii=False)
        for forbidden in FORBIDDEN:
            if forbidden in combined:
                errors.append(f"{stock.get('code')}出现禁止表达：{forbidden}")
    summary = asset.get("summary", {})
    if summary.get("sample_count") != 5:
        errors.append("sample_count必须为5")
    if summary.get("formal_score_update_allowed") is not False:
        errors.append("formal_score_update_allowed必须为false")
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
        "name": "报告缺口优先级排序样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {"sample_count": len(records)},
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 报告缺口优先级排序样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 样本数：{result['metrics']['sample_count']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
