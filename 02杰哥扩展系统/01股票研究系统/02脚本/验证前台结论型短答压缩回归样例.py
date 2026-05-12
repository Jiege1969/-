# -*- coding: utf-8 -*-
"""验证前台结论型短答压缩回归样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "前台结论型短答压缩回归样例_最新.json"
RESULT_JSON = DATA_DIR / "前台结论型短答压缩回归样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "前台结论型短答压缩回归样例验收结果_最新.md"
PROHIBITED = ["买入", "卖出", "下单", "仓位", "自动交易", "保证收益"]


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1 前台结论型短答压缩回归样例":
        errors.append("资产身份不正确")
    if asset.get("status") != "shadow_frontend_regression":
        errors.append("状态必须为 shadow_frontend_regression")
    for flag in ["not_formal_entry", "not_external_send", "not_formal_config", "not_trade"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag} 必须为 true")
    samples = asset.get("samples", [])
    if len(samples) < 5:
        errors.append("样本不得少于5只股票")
    for sample in samples:
        name = sample.get("stock_name", "")
        code = sample.get("stock_code", "")
        text = sample.get("frontend_answer", "")
        if name not in text or code not in text:
            errors.append(f"{name} 前台短答必须包含名称和代码")
        if sample.get("conclusion") not in text:
            errors.append(f"{name} 前台短答必须包含结论词")
        if not any(word in text for word in ["缺口", "没补齐", "未补齐", "等待证据"]):
            errors.append(f"{name} 前台短答必须提示关键缺口")
        if len(text) > 180:
            errors.append(f"{name} 前台短答过长：{len(text)} 字")
        for word in PROHIBITED:
            if word in text:
                errors.append(f"{name} 前台短答不得出现交易/承诺词：{word}")
    summary = asset.get("summary", {})
    if summary.get("real_external_send_allowed") is not False:
        errors.append("不得允许真实外发")
    if summary.get("trade_action_allowed") is not False:
        errors.append("不得允许交易动作")
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
            errors.append(f"安全边界 {flag} 必须为 true")
    result = {
        "name": "前台结论型短答压缩回归样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {
            "sample_count": len(samples),
            "real_external_send_allowed": summary.get("real_external_send_allowed"),
            "trade_action_allowed": summary.get("trade_action_allowed"),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 前台结论型短答压缩回归样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 样本数：{result['metrics']['sample_count']}",
        f"- 真实外发允许：{result['metrics']['real_external_send_allowed']}",
        f"- 交易动作允许：{result['metrics']['trade_action_allowed']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
