#!/usr/bin/env python3
"""Read-only frontend-message contract check for stock reports.

This gate preserves the settled user-facing report contract:
- reports should state conclusions and computed conditions;
- strong-focus should reuse the star/graphic-report expression layer;
- technical indicators come from the stock-system method kernel, not from
  example wording in the user's template;
- WeCom bots remain input/output terminals, not business-decision layers.

It does not write project files, start services, call external systems, send
messages, touch n8n/Webhook paths, or inspect live brokers.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STOCK_ROOT = ROOT / "02杰哥扩展系统" / "01股票研究系统"
CONTRACT_PATH = STOCK_ROOT / "01配置" / "股票前台报告表达定稿规则_v1.0.json"
DOC_PATH = STOCK_ROOT / "07文档" / "股票前台报告表达定稿与推送消息标准_v1.0.md"
OUTPUT_STANDARD_PATH = STOCK_ROOT / "01配置" / "股票前台输出标准_v2.json"
LAYER_RULE_PATH = STOCK_ROOT / "01配置" / "股票前后台表达分层与杰哥推荐前台规则_v1.0.json"

REQUIRED_TOP_LEVEL_KEYS = [
    "最高口径",
    "前台报告硬原则",
    "计算结果直出规则",
    "强烈关注表达",
    "消息类型",
    "每日推送总表要求",
    "禁止退化",
    "规则收口治理",
    "安全边界",
]

REQUIRED_CONTRACT_PHRASES = [
    "少讲分析过程，但必须给明确判断和可执行观察条件。",
    "不能把计算题留给使用者",
    "技术指标和分析方法以股票分析系统现有方法内核为准",
    "企业微信机器人只是输入输出终端",
]

REQUIRED_DOC_PHRASES = [
    "前台报告不是后台分析过程的复述",
    "不能把计算题留给使用者",
    "强烈关注沿用星级表达体系",
    "技术指标以系统方法内核为准",
    "企业微信机器人只是输入输出终端",
    "不是新增一层规则",
    "旧文件不得再作为前台报告现行规则源",
]

REQUIRED_NUMERIC_OUTPUTS = [
    "最近5日平均成交量",
    "放量达标线",
    "明显活跃线",
    "当前成交量",
    "企稳区间上下沿",
    "转强价",
    "风险线",
    "底线价",
    "连续入选天数",
]

REQUIRED_MESSAGE_TYPES = [
    "单股主动询问",
    "短线主动推送",
    "专家主动推送",
    "详细分析报告",
]

REQUIRED_BOTS = [
    "杰哥股票短线分析助手",
    "杰哥股票分析专家",
]

GUARDRAILS = [
    "read_only_frontend_message_contract",
    "conclusion_and_computed_conditions_first",
    "reuse_star_expression_for_strong_focus",
    "stock_method_kernel_over_user_indicator_examples",
    "single_current_rule_source_and_legacy_cleanup",
    "no_external_service_call",
    "no_real_send_or_n8n_or_webhook",
    "no_auto_trade_or_broker_interface",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def text_contains_all(text: str, phrases: list[str]) -> list[str]:
    return [phrase for phrase in phrases if phrase not in text]


def load_referenced_texts() -> dict[str, str]:
    texts: dict[str, str] = {}
    for path in [DOC_PATH, OUTPUT_STANDARD_PATH, LAYER_RULE_PATH]:
        if path.exists():
            texts[rel(path)] = read_text(path)
    return texts


def stock_legacy_backup_files() -> list[str]:
    return sorted(
        rel(path)
        for path in STOCK_ROOT.rglob("*before-rename-stock-advisor-20260510-2220*")
        if path.is_file()
    )


def build_report() -> dict[str, Any]:
    files = {
        "contract": {
            "path": rel(CONTRACT_PATH),
            "exists": CONTRACT_PATH.exists(),
        },
        "document": {
            "path": rel(DOC_PATH),
            "exists": DOC_PATH.exists(),
        },
        "output_standard": {
            "path": rel(OUTPUT_STANDARD_PATH),
            "exists": OUTPUT_STANDARD_PATH.exists(),
        },
        "layer_rule": {
            "path": rel(LAYER_RULE_PATH),
            "exists": LAYER_RULE_PATH.exists(),
        },
    }

    contract: dict[str, Any] = {}
    contract_text = ""
    if CONTRACT_PATH.exists():
        contract = read_json(CONTRACT_PATH)
        contract_text = read_text(CONTRACT_PATH)

    referenced_texts = load_referenced_texts()
    references = {
        name: {
            "mentions_contract": "股票前台报告表达定稿规则_v1.0.json" in text,
            "mentions_document": "股票前台报告表达定稿与推送消息标准_v1.0.md" in text,
        }
        for name, text in referenced_texts.items()
    }

    message_types = contract.get("消息类型", {}) if contract else {}
    hard_principles = contract.get("前台报告硬原则", {}) if contract else {}
    strong_focus = contract.get("强烈关注表达", {}) if contract else {}
    safety = contract.get("安全边界", {}) if contract else {}
    governance = contract.get("规则收口治理", {}) if contract else {}

    report = {
        "name": "stock_frontend_message_contract",
        "scope": "stock_analysis_sample_room_frontend_messages",
        "files": files,
        "contract_version": contract.get("版本") if contract else None,
        "required_key_coverage": {
            key: key in contract
            for key in REQUIRED_TOP_LEVEL_KEYS
        },
        "required_contract_phrase_missing": text_contains_all(contract_text, REQUIRED_CONTRACT_PHRASES),
        "required_doc_phrase_missing": text_contains_all(
            read_text(DOC_PATH) if DOC_PATH.exists() else "",
            REQUIRED_DOC_PHRASES,
        ),
        "numeric_output_coverage": {
            item: item in json.dumps(hard_principles, ensure_ascii=False)
            for item in REQUIRED_NUMERIC_OUTPUTS
        },
        "message_type_coverage": {
            item: item in message_types
            for item in REQUIRED_MESSAGE_TYPES
        },
        "bot_coverage": {
            bot: bot in contract_text
            for bot in REQUIRED_BOTS
        },
        "strong_focus": {
            "uses_star_expression": "五星" in json.dumps(strong_focus, ensure_ascii=False)
            or "星级" in json.dumps(strong_focus, ensure_ascii=False),
            "not_trade_instruction": "不是买卖指令" in json.dumps(strong_focus, ensure_ascii=False),
        },
        "method_kernel_over_template": "不以用户模板举例为准" in contract_text,
        "governance": {
            "single_current_contract": governance.get("唯一现行规则源") == "01配置/股票前台报告表达定稿规则_v1.0.json",
            "single_current_document": governance.get("唯一现行说明文档") == "07文档/股票前台报告表达定稿与推送消息标准_v1.0.md",
            "mentions_absorb_replace_or_deprecate": "吸收" in json.dumps(governance, ensure_ascii=False)
            and "替换" in json.dumps(governance, ensure_ascii=False)
            and "废止" in json.dumps(governance, ensure_ascii=False),
            "legacy_backup_files": stock_legacy_backup_files(),
        },
        "references": references,
        "safety": safety,
        "guardrails": GUARDRAILS,
    }
    problems = validate_report(report)
    report["ci_gate_status"] = "fail" if problems else "pass"
    report["blocking_problems"] = problems
    return report


def validate_report(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    for name, info in report["files"].items():
        if not info["exists"]:
            problems.append(f"missing_file:{name}:{info['path']}")

    for key, present in report["required_key_coverage"].items():
        if not present:
            problems.append(f"missing_contract_key:{key}")

    for phrase in report["required_contract_phrase_missing"]:
        problems.append(f"missing_contract_phrase:{phrase}")
    for phrase in report["required_doc_phrase_missing"]:
        problems.append(f"missing_doc_phrase:{phrase}")

    for item, present in report["numeric_output_coverage"].items():
        if not present:
            problems.append(f"missing_numeric_output_requirement:{item}")

    for item, present in report["message_type_coverage"].items():
        if not present:
            problems.append(f"missing_message_type:{item}")

    for bot, present in report["bot_coverage"].items():
        if not present:
            problems.append(f"missing_bot_coverage:{bot}")

    if not report["strong_focus"]["uses_star_expression"]:
        problems.append("strong_focus_does_not_reuse_star_expression")
    if not report["strong_focus"]["not_trade_instruction"]:
        problems.append("strong_focus_trade_boundary_missing")
    if not report["method_kernel_over_template"]:
        problems.append("method_kernel_over_template_missing")

    governance = report["governance"]
    if not governance["single_current_contract"]:
        problems.append("governance_single_current_contract_missing")
    if not governance["single_current_document"]:
        problems.append("governance_single_current_document_missing")
    if not governance["mentions_absorb_replace_or_deprecate"]:
        problems.append("governance_absorb_replace_deprecate_missing")
    for path in governance["legacy_backup_files"]:
        problems.append(f"legacy_frontend_backup_file_remaining:{path}")

    for name, info in report["references"].items():
        if name.endswith("股票前台输出标准_v2.json") and not info["mentions_contract"]:
            problems.append(f"output_standard_not_referencing_contract:{name}")
        if name.endswith("股票前后台表达分层与杰哥推荐前台规则_v1.0.json") and not info["mentions_contract"]:
            problems.append(f"layer_rule_not_referencing_contract:{name}")

    safety = report["safety"]
    for key in ["真实发送企业微信", "触发n8n", "调用券商接口", "自动交易"]:
        if safety.get(key) is not False:
            problems.append(f"safety_boundary_not_false:{key}")

    for guardrail in GUARDRAILS:
        if guardrail not in report.get("guardrails", []):
            problems.append(f"missing_guardrail:{guardrail}")
    return problems


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stock Frontend Message Contract",
        "",
        f"- CI gate: `{report['ci_gate_status']}`",
        f"- Scope: `{report['scope']}`",
        f"- Contract version: `{report['contract_version']}`",
        "",
        "## Files",
    ]
    for name, info in report["files"].items():
        lines.append(f"- `{name}`: exists={str(info['exists']).lower()}; path=`{info['path']}`")

    lines.extend(["", "## Message Types"])
    for name, present in report["message_type_coverage"].items():
        lines.append(f"- `{name}`: {str(present).lower()}")

    lines.extend(["", "## Computed Conditions"])
    for name, present in report["numeric_output_coverage"].items():
        lines.append(f"- `{name}`: {str(present).lower()}")

    lines.extend(["", "## Guardrails"])
    for guardrail in report["guardrails"]:
        lines.append(f"- `{guardrail}`")

    lines.extend(["", "## Legacy Cleanup"])
    lines.append(f"- single current contract: {str(report['governance']['single_current_contract']).lower()}")
    lines.append(f"- single current document: {str(report['governance']['single_current_document']).lower()}")
    lines.append(f"- remaining old backup files: {len(report['governance']['legacy_backup_files'])}")

    if report["blocking_problems"]:
        lines.extend(["", "## Blocking Problems"])
        for problem in report["blocking_problems"]:
            lines.append(f"- `{problem}`")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))

    if report["ci_gate_status"] != "pass":
        print("FAIL: stock frontend message contract found blocking problems", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
