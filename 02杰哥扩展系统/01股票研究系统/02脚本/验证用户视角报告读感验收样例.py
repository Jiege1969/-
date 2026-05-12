# -*- coding: utf-8 -*-
"""验收用户视角报告读感样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "用户视角报告读感验收样例_最新.json"
RESULT_JSON = DATA_DIR / "用户视角报告读感验收样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "用户视角报告读感验收样例验收结果_最新.md"
REQUIRED_CODES = {"002428", "002466", "688347", "000906", "300641"}
FORBIDDEN = ["买入", "卖出", "下单", "仓位", "自动交易", "券商接口", "确定收益"]


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1用户视角报告读感验收样例":
        errors.append("资产身份不正确")
    if asset.get("status") != "shadow_readability_acceptance":
        errors.append("状态不是shadow_readability_acceptance")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    checklist = asset.get("checklist", [])
    if len(checklist) != 5:
        errors.append("读感验收清单必须为5项")
    samples = asset.get("samples", [])
    codes = {item.get("stock", {}).get("code") for item in samples}
    if codes != REQUIRED_CODES:
        errors.append(f"样本股票代码不完整：{sorted(codes)}")
    for item in samples:
        stock = item.get("stock", {})
        if item.get("readability_result") not in {"pass", "pass_with_minor_gap"}:
            errors.append(f"{stock.get('code')}读感结果不合规")
        if not item.get("user_view_comment"):
            errors.append(f"{stock.get('code')}缺少用户视角评价")
        combined = json.dumps(item, ensure_ascii=False)
        for forbidden in FORBIDDEN:
            if forbidden in combined:
                errors.append(f"{stock.get('code')}出现禁止表达：{forbidden}")
    summary = asset.get("summary", {})
    if summary.get("real_wecom_send_allowed") is not False:
        errors.append("real_wecom_send_allowed必须为false")
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
        "name": "用户视角报告读感验收样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {"check_count": len(checklist), "sample_count": len(samples)},
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 用户视角报告读感验收样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 清单项：{result['metrics']['check_count']}",
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
