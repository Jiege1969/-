# -*- coding: utf-8 -*-
"""
验证影子前台短答刷新验收样例。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "影子前台短答刷新验收样例_最新.json"
RESULT_JSON = DATA_DIR / "影子前台短答刷新验收样例验收_最新.json"
RESULT_MD = DATA_DIR / "影子前台短答刷新验收样例验收_最新.md"

EXPECTED_CODES = {"sz002428", "sz002466", "sh688347", "sz000906", "sz300641"}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1影子前台短答验收样例":
        errors.append("资产身份必须是 W1影子前台短答验收样例")
    if asset.get("status") != "shadow_acceptance":
        errors.append("状态必须是 shadow_acceptance")

    gate = asset.get("shadow_generation_gate", {})
    if gate.get("allow_shadow_front_answer_generation") is not True:
        errors.append("影子前台短答生成闸口未开启")
    if gate.get("allow_real_wecom_send") is not False:
        errors.append("真实企业微信发送必须为 false")
    if gate.get("allow_formal_l3_complete_claim") is not False:
        errors.append("正式 L3 完整声明必须为 false")

    samples = asset.get("sample_checks", [])
    codes = {item.get("stock", {}).get("code") for item in samples}
    if codes != EXPECTED_CODES:
        errors.append(f"样本代码不完整：{sorted(codes)}")
    for item in samples:
        if item.get("passed") is not True:
            errors.append(f"{item.get('stock', {}).get('name')} 未通过前台短答影子验收")

    summary = asset.get("summary", {})
    if summary.get("pass_count") != 5 or summary.get("blocked_count") != 0:
        errors.append("样本通过/阻断计数异常")
    if summary.get("allow_real_wecom_send") is not False:
        errors.append("summary.allow_real_wecom_send 必须 false")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_adapter_write", "not_score_write", "not_entrypoint", "not_broker_interface", "not_auto_trade", "not_real_refresh"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    result = {
        "name": "影子前台短答刷新验收样例验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": summary,
        "next_step": "继续生成股票线连续施工状态快照；仍不得真实外发或写正式库。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 影子前台短答刷新验收样例验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 样本数：{result['metrics'].get('sample_count', 0)}",
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
