# -*- coding: utf-8 -*-
"""验收企业微信前台短答影子输入输出样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "企业微信前台短答模拟输入输出样例_最新.json"
RESULT_JSON = DATA_DIR / "企业微信前台短答模拟输入输出样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "企业微信前台短答模拟输入输出样例验收结果_最新.md"
REQUIRED = {
    "002428": "云南锗业",
    "002466": "天齐锂业",
    "688347": "华虹公司",
    "000906": "浙商中拓",
    "300641": "正丹股份",
}
FORBIDDEN_IN_FRONT_ANSWER = ["买入", "卖出", "下单", "仓位", "自动交易", "券商接口"]


def main() -> None:
    errors: list[str] = []
    if not ASSET_PATH.exists():
        errors.append("缺少企业微信前台短答模拟输入输出样例资产")
        asset = {}
    else:
        asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig"))

    if asset.get("asset_identity") != "W1企业微信前台短答影子输入输出样例":
        errors.append("资产身份不是W1企业微信前台短答影子输入输出样例")
    if asset.get("status") != "shadow_io_sample":
        errors.append("状态不是shadow_io_sample")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_service_change"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")

    records = asset.get("records", [])
    codes = {record.get("resolved_stock", {}).get("code") for record in records}
    if codes != set(REQUIRED):
        errors.append(f"样本股票代码不完整：{sorted(codes)}")
    for record in records:
        stock = record.get("resolved_stock", {})
        answer = record.get("simulated_front_answer", "")
        lines = [line for line in answer.splitlines() if line.strip()]
        if len(lines) < 5:
            errors.append(f"{stock.get('code')}前台短答不足5行")
        first = lines[0] if lines else ""
        if stock.get("name") not in first or stock.get("code") not in first:
            errors.append(f"{stock.get('code')}第一行未明确股票名称和代码")
        for required_phrase in ["结论：", "关键缺口：", "置信度："]:
            if required_phrase not in answer:
                errors.append(f"{stock.get('code')}缺少{required_phrase}")
        for phrase in FORBIDDEN_IN_FRONT_ANSWER:
            if phrase in answer:
                errors.append(f"{stock.get('code')}前台答案出现禁止词：{phrase}")
        if record.get("input_channel") != "wecom_shadow":
            errors.append(f"{stock.get('code')}输入通道不是wecom_shadow")
        if record.get("real_wecom_send_allowed") is not False:
            errors.append(f"{stock.get('code')}real_wecom_send_allowed必须为false")
        if record.get("formal_entry_allowed") is not False:
            errors.append(f"{stock.get('code')}formal_entry_allowed必须为false")
        trace = record.get("backend_trace_required", {})
        for key in ["evidence", "missing", "confidence_reason", "next_review_focus", "gate_decisions", "source_assets"]:
            if key not in trace:
                errors.append(f"{stock.get('code')}后台追踪缺少{key}")

    summary = asset.get("summary", {})
    if summary.get("sample_count") != 5:
        errors.append("sample_count必须为5")
    if summary.get("shadow_output_count") != 5:
        errors.append("shadow_output_count必须为5")
    if summary.get("real_wecom_send_allowed") is not False:
        errors.append("summary.real_wecom_send_allowed必须为false")
    if summary.get("formal_entry_allowed") is not False:
        errors.append("summary.formal_entry_allowed必须为false")
    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_formal_config", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界{flag}必须为true")

    result = {
        "name": "企业微信前台短答模拟输入输出样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {
            "sample_count": summary.get("sample_count", 0),
            "object_clear_count": summary.get("object_clear_count", 0),
            "shadow_output_count": summary.get("shadow_output_count", 0),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 企业微信前台短答模拟输入输出样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 样本数：{result['metrics']['sample_count']}",
        f"- 影子输出数：{result['metrics']['shadow_output_count']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
