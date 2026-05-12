# -*- coding: utf-8 -*-
"""生成低风险只读调度干跑结果漂移复核与幂等校验包。

只生成本地漂移规则与包索引；不真实发送企业微信、不接 n8n、不接券商、
不交易、不登录税局、不接财税软件、不自动转正式规则、不改总管面板、
不改一键接续包、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "105低风险只读调度干跑结果漂移复核与幂等校验包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度干跑结果漂移复核与幂等校验包验收"

RULES_JSON = DATA_DIR / "漂移规则_最新.json"
RULES_MD = DATA_DIR / "漂移规则_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度干跑结果漂移复核与幂等校验包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度干跑结果漂移复核与幂等校验包_最新.md"
GENERATE_LOG = LOG_DIR / "low-risk-readonly-scheduler-drift-idempotency-generate-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safety_flags() -> dict[str, bool]:
    return {
        "real_wecom_send": False,
        "trigger_n8n": False,
        "external_call": False,
        "broker_connection": False,
        "trade_order": False,
        "tax_bureau_login": False,
        "finance_tax_software_connection": False,
        "auto_promote_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
        "reload_service": False,
        "actual_execution": False,
        "copy_source_files": False,
        "move_source_files": False,
        "source_files_modified": False,
    }


def build_rules(generated_at: str) -> dict[str, Any]:
    return {
        "name": "低风险只读调度干跑结果漂移复核规则",
        "generated_at": generated_at,
        "scope": "readonly_compare_only_no_source_mutation",
        "source_priority": [
            "第104包安全边界与低风险台账摘要",
            "本地低风险只读调度预演台账作为三轮干跑样例",
        ],
        "source_files": {
            "package104": str(
                EVOLUTION_ROOT
                / "03数据"
                / "104完全交付使用版低风险续建第二批复核包"
                / "完全交付使用版低风险续建第二批复核包_最新.json"
            ),
            "readonly_ledger": str(
                EVOLUTION_ROOT
                / "03数据"
                / "100低风险只读调度运行台账与证据归档预演包"
                / "调度预演台账_最新.json"
            ),
            "ledger_field_definition": str(
                EVOLUTION_ROOT
                / "03数据"
                / "100低风险只读调度运行台账与证据归档预演包"
                / "运行台账字段定义_最新.json"
            ),
            "readonly_run_report": str(
                EVOLUTION_ROOT
                / "03数据"
                / "100低风险只读调度运行台账与证据归档预演包"
                / "调度运行台账归档预演执行报告_最新.json"
            ),
        },
        "checks": [
            {
                "id": "task_count",
                "name": "任务数量",
                "method": "三轮 normalized_plan.task_count 必须完全一致，且不少于 1。",
                "pass_when": "drift_count=0",
            },
            {
                "id": "task_order",
                "name": "任务顺序",
                "method": "比较 task_id 顺序与每条任务 normalized hash 顺序。",
                "pass_when": "diff_count=0",
            },
            {
                "id": "redline_scan_summary",
                "name": "红线扫描摘要",
                "method": "扫描源包和三轮计划中的企业微信、n8n、券商、交易、税局、财税、正式规则、总管面板、一键接续、重载字段。",
                "pass_when": "redline_regression_count=0",
            },
            {
                "id": "safety_boundary_fields",
                "name": "安全边界字段",
                "method": "关键安全字段必须存在于复核结果并固定为 false。",
                "pass_when": "missing_count=0 and redline_regression_count=0",
            },
            {
                "id": "ledger_fields",
                "name": "台账字段",
                "method": "每条任务必须包含 task_id、task_name、plan_time、preview_status、pause_required、evidence_path、hash、operator_mode。",
                "pass_when": "missing_count=0",
            },
        ],
        "required_ledger_fields": [
            "task_id",
            "task_name",
            "plan_time",
            "preview_status",
            "pause_required",
            "evidence_path",
            "hash",
            "operator_mode",
        ],
        "required_false_fields": list(safety_flags().keys()),
        "expected_results": {
            "repeated_preview_same_plan": True,
            "source_files_modified": False,
            "diff_count": 0,
            "drift_count": 0,
            "missing_count": 0,
            "redline_regression_count": 0,
            "external_call": False,
        },
        "actual_execution": False,
        "copy_source_files": False,
        "move_source_files": False,
        "source_files_modified": False,
        "external_call": False,
        "reload_service": False,
        "hard_red_line_confirmation": safety_flags(),
    }


def rules_md(rules: dict[str, Any]) -> str:
    rows = [
        f"| {item['id']} | {item['name']} | {item['method']} | {item['pass_when']} |"
        for item in rules["checks"]
    ]
    fields = "、".join(rules["required_ledger_fields"])
    false_fields = "、".join(rules["required_false_fields"])
    return "\n".join(
        [
            "# 漂移规则",
            "",
            f"- 生成时间：{rules['generated_at']}",
            f"- 范围：{rules['scope']}",
            "- 复核动作：只读比对，不改源产物。",
            "",
            "| id | 检查项 | 方法 | 通过条件 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
            "## 必需台账字段",
            "",
            fields,
            "",
            "## 必须为 false 的安全字段",
            "",
            false_fields,
        ]
    )


def package_md(package: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 低风险只读调度干跑结果漂移复核与幂等校验包",
            "",
            f"- 生成时间：{package['generated_at']}",
            f"- pass: {package['pass']}",
            f"- error_count: {package['error_count']}",
            "- 范围：对第104包安全边界和本地只读调度样例做漂移复核与幂等校验。",
            "- 红线：不真实发送企业微信、不接 n8n、不接券商、不交易、不登录税局、不接财税软件、不自动转正式规则、不改总管面板、不改一键接续包、不重载服务。",
            "",
            "## 输出",
            "",
            f"- 漂移规则 JSON：{package['outputs']['rules_json']}",
            f"- 漂移规则 MD：{package['outputs']['rules_md']}",
            f"- 幂等校验报告 JSON：{package['outputs']['idempotency_json']}",
            f"- 漂移复核报告 JSON：{package['outputs']['drift_json']}",
            f"- 固定验收日志：{package['fixed_verify_log']}",
        ]
    )


def main() -> int:
    generated_at = now()
    rules = build_rules(generated_at)
    package = {
        "name": "低风险只读调度干跑结果漂移复核与幂等校验包",
        "generated_at": generated_at,
        "pass": True,
        "error_count": 0,
        "errors": [],
        "outputs": {
            "rules_json": str(RULES_JSON),
            "rules_md": str(RULES_MD),
            "idempotency_json": str(DATA_DIR / "幂等校验报告_最新.json"),
            "idempotency_md": str(DATA_DIR / "幂等校验报告_最新.md"),
            "drift_json": str(DATA_DIR / "漂移复核报告_最新.json"),
            "drift_md": str(DATA_DIR / "漂移复核报告_最新.md"),
            "package_json": str(PACKAGE_JSON),
            "package_md": str(PACKAGE_MD),
        },
        "fixed_verify_log": str(LOG_DIR / "low-risk-readonly-scheduler-drift-idempotency-verify-最新.json"),
        "actual_execution": False,
        "copy_source_files": False,
        "move_source_files": False,
        "source_files_modified": False,
        "external_call": False,
        "reload_service": False,
        "hard_red_line_confirmation": safety_flags(),
    }
    write_json(RULES_JSON, rules)
    write_text(RULES_MD, rules_md(rules))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))
    write_json(GENERATE_LOG, package | {"log_type": "generate"})
    print(json.dumps({"pass": True, "error_count": 0, "rules": str(RULES_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
