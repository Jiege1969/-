# -*- coding: utf-8 -*-
"""验收前台短答综合样例二次压缩。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "前台短答综合样例二次压缩验收_最新.json"
RESULT_JSON = DATA_DIR / "前台短答综合样例二次压缩验收结果_最新.json"
RESULT_MD = DATA_DIR / "前台短答综合样例二次压缩验收结果_最新.md"
REQUIRED_CODES = {"002428", "002466", "688347", "000906", "300641"}
FORBIDDEN = ["买入", "卖出", "下单", "仓位", "自动交易", "券商接口"]


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1前台短答综合样例二次压缩验收":
        errors.append("资产身份不正确")
    records = asset.get("records", [])
    codes = {item.get("stock", {}).get("code") for item in records}
    if codes != REQUIRED_CODES:
        errors.append(f"样本股票代码不完整：{sorted(codes)}")
    for item in records:
        stock = item.get("stock", {})
        answer = item.get("compressed_answer", "")
        lines = [line for line in answer.splitlines() if line.strip()]
        if len(lines) > 4:
            errors.append(f"{stock.get('code')}短答超过4行")
        first = lines[0] if lines else ""
        if stock.get("name") not in first or stock.get("code") not in first:
            errors.append(f"{stock.get('code')}第一行未明确对象")
        for phrase in ["结论：", "主因：", "缺口/置信度："]:
            if phrase not in answer:
                errors.append(f"{stock.get('code')}缺少{phrase}")
        for phrase in FORBIDDEN:
            if phrase in answer:
                errors.append(f"{stock.get('code')}出现禁止词：{phrase}")
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
        "name": "前台短答综合样例二次压缩验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {"sample_count": len(records)},
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# 前台短答综合样例二次压缩验收结果", "", f"- 生成时间：{result['generated_at']}", f"- 是否通过：{'是' if result['passed'] else '否'}", f"- 样本数：{result['metrics']['sample_count']}", "", "## 错误", ""]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
