# -*- coding: utf-8 -*-
"""验证标准股票分析格式前台短答范本样例。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "标准股票分析格式前台短答范本样例_最新.json"
RESULT_JSON = DATA_DIR / "标准股票分析格式前台短答范本样例验收结果_最新.json"
RESULT_MD = DATA_DIR / "标准股票分析格式前台短答范本样例验收结果_最新.md"
FORBIDDEN = ["买入", "卖出", "下单", "仓位", "自动交易", "券商接口"]
REQUIRED_NAMES = {"云南锗业", "三花智控", "上纬新材", "浙商中拓", "正丹股份"}


def main() -> None:
    errors: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if asset.get("asset_identity") != "W1前台短答格式样例":
        errors.append("资产身份不正确")
    for flag in ["not_real_market_report", "not_external_send", "not_formal_entry", "not_trade_advice"]:
        if asset.get(flag) is not True:
            errors.append(f"{flag}必须为true")
    samples = asset.get("samples", [])
    if len(samples) != 5:
        errors.append("样本数量必须为5")
    names = {item.get("stock_name") for item in samples}
    if names != REQUIRED_NAMES:
        errors.append("样本股票必须包含云南锗业、三花智控、上纬新材、浙商中拓、正丹股份")
    allowed = set(asset.get("allowed_conclusions", []))
    for item in samples:
        name = item.get("stock_name", "")
        code = item.get("stock_code", "")
        first_line = item.get("first_line", "")
        if not first_line.startswith(f"{name}（{code}）："):
            errors.append(f"{name}第一行未明确对象和代码")
        if item.get("conclusion") not in allowed:
            errors.append(f"{name}结论词不在允许范围")
        if not item.get("one_sentence"):
            errors.append(f"{name}缺少一句话判断")
        reasons = item.get("main_reasons", [])
        if not reasons or len(reasons) > 3:
            errors.append(f"{name}主要依据必须为1-3条")
        missing = item.get("key_missing", [])
        if not missing:
            errors.append(f"{name}必须显式列出关键缺口")
        if not any(str(m).startswith("P0") for m in missing):
            errors.append(f"{name}关键缺口必须至少包含P0")
        text = json.dumps(item, ensure_ascii=False)
        for word in FORBIDDEN:
            if word in text:
                errors.append(f"{name}包含禁止交易/执行词：{word}")
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
        "name": "标准股票分析格式前台短答范本样例验收结果",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": len(errors) == 0,
        "errors": errors,
        "metrics": {
            "sample_count": len(samples),
            "included_new_samples": sorted(list(names & {"浙商中拓", "正丹股份"})),
            "forbidden_word_count": len([err for err in errors if "禁止交易/执行词" in err]),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 标准股票分析格式前台短答范本样例验收结果",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 样本数：{result['metrics']['sample_count']}",
        f"- 新增样本：{', '.join(result['metrics']['included_new_samples'])}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
