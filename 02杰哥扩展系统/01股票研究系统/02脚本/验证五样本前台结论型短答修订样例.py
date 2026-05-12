# -*- coding: utf-8 -*-
"""
验证五样本前台结论型短答修订样例。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "五样本前台结论型短答修订样例_最新.json"
RESULT_JSON = DATA_DIR / "五样本前台结论型短答修订样例验收_最新.json"
RESULT_MD = DATA_DIR / "五样本前台结论型短答修订样例验收_最新.md"

EXPECTED = {
    "云南锗业": "sz002428",
    "天齐锂业": "sz002466",
    "华虹公司": "sh688347",
    "浙商中拓": "sz000906",
    "正丹股份": "sz300641",
}
FORBIDDEN = ["买入", "卖出", "加仓", "减仓", "下单", "仓位调整", "自动交易", "券商接口", "重点推荐", "强烈推荐"]


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig")) if ASSET_PATH.exists() else {}
    if not asset:
        errors.append(f"缺少资产文件：{ASSET_PATH}")

    if asset.get("asset_identity") != "W1样本修订草案":
        errors.append("资产身份必须是 W1样本修订草案")
    if asset.get("status") != "draft":
        errors.append("状态必须保持 draft")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    safety = asset.get("safety_boundary", {})
    for flag in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    samples = asset.get("samples", [])
    if len(samples) != 5:
        errors.append(f"样本数量应为5，实际{len(samples)}")

    seen = {}
    for sample in samples:
        stock = sample.get("stock", {})
        name = stock.get("name")
        code = stock.get("code")
        seen[name] = code
        answer_lines = sample.get("front_answer", [])
        answer = "\n".join(answer_lines)
        if not answer_lines:
            errors.append(f"{name} 缺少前台短答")
            continue
        if answer_lines[0].strip() != f"{name}（{code}）":
            errors.append(f"{name} 第一行未明确对象和代码")
        for phrase in ["结论", "主要原因", "关键缺口", "置信度"]:
            if phrase not in answer:
                errors.append(f"{name} 缺少 {phrase}")
        if not any(term in answer for term in ["待采集", "未匹配", "尚未结构化", "观测点不足", "尚未入账", "证据待补"]):
            errors.append(f"{name} 未显式标注证据缺口")
        bad_terms = [term for term in FORBIDDEN if term in answer]
        if bad_terms:
            errors.append(f"{name} 出现禁用词：{bad_terms}")
        if len(answer) > 520:
            warnings.append(f"{name} 短答偏长，可继续压缩")

    if seen != EXPECTED:
        errors.append(f"样本对象不完整：{seen}")

    result = {
        "name": "五样本前台结论型短答修订样例验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "sample_count": len(samples),
            "warning_count": len(warnings),
        },
        "next_step": "可继续做后台证据链到前台短答字段映射草案；仍不得写正式企业微信入口。",
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    print(json.dumps(result, ensure_ascii=False))


def write_markdown(result: dict) -> None:
    lines = [
        "# 五样本前台结论型短答修订样例验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 样本数量：{result['metrics']['sample_count']}",
        f"- 警告数量：{result['metrics']['warning_count']}",
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
