# -*- coding: utf-8 -*-
"""验证企业微信模拟问答回归验收样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "企业微信模拟问答回归验收样例_最新.json"
RESULT_JSON = DATA_DIR / "企业微信模拟问答回归验收样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "企业微信模拟问答回归验收样例验收结果_最新.md"
ALLOWED_CONCLUSIONS = ["重点关注", "可纳入观察", "暂不建议关注"]
FORBIDDEN = ["MACD", "RSI", "K线", "量比", "均线排列", "计算过程", "item_scores", "买入", "卖出", "下单", "仓位", "自动交易", "券商接口"]


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W2本地模拟问答回归样例":
        errors.append("资产身份不正确")
    for flag in ["not_real_wecom_send", "not_external_send", "not_formal_entry", "not_trade_advice"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    qa = asset.get("simulated_qa", [])
    if len(qa) != 5:
        errors.append("模拟问答必须覆盖5个样本")
    for item in qa:
        name = item.get("stock_name", "")
        code = item.get("stock_code", "")
        ans = item.get("answer", {})
        first_line = ans.get("first_line", "")
        if not first_line.startswith(f"{name}（{code}）："):
            errors.append(f"{name}第一行未明确对象和代码")
        if not any(conclusion in first_line for conclusion in ALLOWED_CONCLUSIONS):
            errors.append(f"{name}缺少标准结论词")
        if len(ans.get("main_reasons", [])) > 3:
            errors.append(f"{name}主要依据超过3条")
        if not ans.get("key_missing"):
            errors.append(f"{name}缺少关键缺口")
        if not ans.get("confidence_text"):
            errors.append(f"{name}缺少置信度表达")
        if not ans.get("review_hint"):
            errors.append(f"{name}缺少复核提醒")
        text = json.dumps(ans, ensure_ascii=False)
        for word in FORBIDDEN:
            if word in text:
                errors.append(f"{name}前台包含禁止词：{word}")
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
        "name": "企业微信模拟问答回归验收样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {"qa_count": len(qa), "forbidden_word_count": len([err for err in errors if "禁止词" in err])},
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 企业微信模拟问答回归验收样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 问答数：{result['metrics']['qa_count']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
