# -*- coding: utf-8 -*-
"""
验证前台缺口话术规则草案。

只验证股票线 W1 草案资产是否完整、边界是否清楚，不触发任何真实系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
ASSET_PATH = DATA_DIR / "前台缺口话术规则草案_最新.json"
RESULT_JSON = DATA_DIR / "前台缺口话术规则草案验收_最新.json"
RESULT_MD = DATA_DIR / "前台缺口话术规则草案验收_最新.md"

REQUIRED_RULE_IDS = {
    "FRONT_GAP_WORDING_001",
    "FRONT_GAP_WORDING_002",
    "FRONT_GAP_WORDING_003",
    "FRONT_GAP_WORDING_004",
}

FORBIDDEN_TERMS = [
    "买入",
    "卖出",
    "加仓",
    "减仓",
    "下单",
    "自动交易",
    "仓位调整",
    "券商接口",
]


def validate() -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if not ASSET_PATH.exists():
        errors.append(f"缺少资产文件：{ASSET_PATH}")
        asset = {}
    else:
        asset = json.loads(ASSET_PATH.read_text(encoding="utf-8-sig"))

    rules = asset.get("rules", [])
    rule_ids = {rule.get("rule_id") for rule in rules}
    missing_ids = REQUIRED_RULE_IDS - rule_ids
    if missing_ids:
        errors.append(f"缺少规则：{sorted(missing_ids)}")

    if asset.get("asset_identity") != "W1规则草案":
        errors.append("资产身份必须是 W1规则草案")
    if asset.get("status") != "draft":
        errors.append("状态必须保持 draft")

    for flag in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write"]:
        if asset.get(flag) is not True:
            errors.append(f"边界字段 {flag} 必须为 true")

    safety = asset.get("safety_boundary", {})
    for flag in [
        "not_n8n",
        "not_external_send",
        "not_service_restart",
        "not_19310",
        "not_real_account",
        "not_formal_database_write",
        "not_adapter_write",
        "not_score_write",
        "not_entrypoint",
        "not_broker_interface",
        "not_auto_trade",
    ]:
        if safety.get(flag) is not True:
            errors.append(f"安全边界 {flag} 必须为 true")

    required_phrases = [
        "资金/机构/解禁证据仍待采集",
        "未匹配直接结构化政策",
        "政策背景存在，但尚未结构化到单股事件",
        "价格/景气观测点不足",
    ]
    all_wording = "\n".join(
        [rule.get("recommended_wording", "") for rule in rules]
        + [variant.get("wording", "") for rule in rules for variant in rule.get("variants", [])]
    )
    for phrase in required_phrases:
        if phrase not in all_wording:
            errors.append(f"缺少关键话术：{phrase}")

    for rule in rules:
        if not rule.get("do_not_say"):
            errors.append(f"{rule.get('rule_id')} 缺少 do_not_say")
        if "W3" not in rule.get("blocked_if_formalized", ""):
            errors.append(f"{rule.get('rule_id')} 未写明正式化 W3 阻断")
        if "模型凭空" in rule.get("evidence_requirement", "") or "必须读取" in rule.get("evidence_requirement", ""):
            pass
        else:
            warnings.append(f"{rule.get('rule_id')} 证据要求可继续加强")

    serialized = json.dumps(asset, ensure_ascii=False)
    for term in FORBIDDEN_TERMS:
        if term in serialized and term not in ["自动交易", "券商接口"]:
            # 允许在禁止事项、红线登记中出现这些词，但不允许作为能力表达。
            if "禁止新增" not in serialized and "不新增" not in serialized:
                errors.append(f"出现交易相关词但未作为禁止边界表达：{term}")

    if "正式结论" in serialized and "不把草案说成正式结论" not in serialized:
        errors.append("出现正式结论表述但未声明草案边界")

    result = {
        "name": "前台缺口话术规则草案验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_path": str(ASSET_PATH),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "rule_count": len(rules),
            "required_rule_count": len(REQUIRED_RULE_IDS),
            "formalization_blocker_count": len(asset.get("formalization_blockers", [])),
        },
        "safety_boundary_confirmed": {
            "not_n8n": safety.get("not_n8n") is True,
            "not_external_send": safety.get("not_external_send") is True,
            "not_service_restart": safety.get("not_service_restart") is True,
            "not_19310": safety.get("not_19310") is True,
            "not_entrypoint": safety.get("not_entrypoint") is True,
            "not_broker_interface": safety.get("not_broker_interface") is True,
            "not_auto_trade": safety.get("not_auto_trade") is True,
        },
        "next_step": "可继续生成前台结论型短答样例验收清单；不得直接写正式适配器或企业微信入口。",
    }

    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)
    return result


def write_markdown(result: dict) -> None:
    lines = [
        "# 前台缺口话术规则草案验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 验收结论：{'通过' if result['passed'] else '不通过'}",
        f"- 规则数量：{result['metrics']['rule_count']}",
        f"- 正式化阻断数量：{result['metrics']['formalization_blocker_count']}",
        "",
        "## 错误",
        "",
    ]
    if result["errors"]:
        lines.extend([f"- {item}" for item in result["errors"]])
    else:
        lines.append("- 无")

    lines.extend(["", "## 警告", ""])
    if result["warnings"]:
        lines.extend([f"- {item}" for item in result["warnings"]])
    else:
        lines.append("- 无")

    lines.extend(
        [
            "",
            "## 边界确认",
            "",
        ]
    )
    for key, value in result["safety_boundary_confirmed"].items():
        lines.append(f"- {key}：{value}")

    lines.extend(["", "## 下一步", "", f"- {result['next_step']}", ""])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False))
