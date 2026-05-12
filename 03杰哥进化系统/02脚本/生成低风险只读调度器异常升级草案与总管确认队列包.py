# -*- coding: utf-8 -*-
"""生成低风险只读调度器异常升级草案与总管确认队列包。

本脚本只读取第106包本地证据并写入草案、确认队列和索引材料。
不真实发送企业微信、不接n8n、不接券商、不交易、不登录税局、
不接财税软件、不自动转正式规则、不改总管面板、不改一键接续包、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = EVOLUTION_ROOT / "03数据" / "106低风险只读调度红线失败注入与自动暂停演练包"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "110低风险只读调度器异常升级草案与总管确认队列包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器异常升级草案与总管确认队列包验收"

SOURCE_INJECTION_JSON = SOURCE_DIR / "失败注入样例_最新.json"
SOURCE_PAUSE_REPORT_JSON = SOURCE_DIR / "自动暂停演练报告_最新.json"

RULE_JSON = DATA_DIR / "异常升级规则_最新.json"
RULE_MD = DATA_DIR / "异常升级规则_最新.md"
QUEUE_JSON = DATA_DIR / "总管确认队列_最新.json"
QUEUE_MD = DATA_DIR / "总管确认队列_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器异常升级草案与总管确认队列包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器异常升级草案与总管确认队列包_最新.md"
GENERATE_LOG = LOG_DIR / "low-risk-readonly-scheduler-escalation-confirmation-queue-generate-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safety_flags() -> dict[str, bool]:
    return {
        "executed": False,
        "auto_resume": False,
        "commands_executed": False,
        "external_call": False,
        "reload_service": False,
        "real_wecom_send": False,
        "connect_n8n": False,
        "connect_broker": False,
        "trade": False,
        "login_tax_bureau": False,
        "connect_finance_tax_software": False,
        "promote_to_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
    }


def build_rules(generated_at: str, source_injections: dict[str, Any], source_report: dict[str, Any]) -> dict[str, Any]:
    source_types = sorted({item.get("redline_type", "") for item in source_injections.get("samples", []) if item.get("redline_type")})
    common_decision = {
        "pause_required": True,
        "continue_allowed": False,
        "requires_supervisor_confirmation": True,
        "executed": False,
        "auto_resume": False,
        "external_call": False,
        "reload_service": False,
        "only_draft": True,
    }
    rules = [
        {
            "id": "ESC-RULE-001",
            "category": "红线命中",
            "trigger": "第106包任一失败注入样例命中红线词或红线动作意图。",
            "source_evidence": source_types,
            "draft_action": "登记异常升级草案并进入总管确认队列。",
            **common_decision,
        },
        {
            "id": "ESC-RULE-002",
            "category": "服务重载需求",
            "trigger": "出现重载、reload、19310重载、刷新服务状态等请求。",
            "source_evidence": ["19310重载"],
            "draft_action": "仅标记为服务重载需求异常，不重载任何服务。",
            **common_decision,
        },
        {
            "id": "ESC-RULE-003",
            "category": "正式规则影响",
            "trigger": "出现自动写入正式规则、自动生效、自动固化等影响正式规则的请求。",
            "source_evidence": ["正式规则写入"],
            "draft_action": "改写为正式规则影响确认事项，等待人工签收。",
            **common_decision,
        },
        {
            "id": "ESC-RULE-004",
            "category": "外部接口需求",
            "trigger": "出现企业微信真实发送、n8n webhook、券商连接、税局登录、财税软件连接等外部接口需求。",
            "source_evidence": ["企业微信真实发送", "n8n webhook", "券商交易"],
            "draft_action": "登记外部接口需求异常，禁止外呼与连接。",
            **common_decision,
        },
        {
            "id": "ESC-RULE-005",
            "category": "证据缺失",
            "trigger": "调度器无法找到来源证据、验收报告、暂停记录或确认队列证据。",
            "source_evidence": [str(SOURCE_INJECTION_JSON), str(SOURCE_PAUSE_REPORT_JSON)],
            "draft_action": "登记证据缺失异常，暂停续跑并请求总管确认补证。",
            **common_decision,
        },
        {
            "id": "ESC-RULE-006",
            "category": "连续失败",
            "trigger": "同类低风险只读调度连续失败、连续暂停或重复命中红线。",
            "source_evidence": {
                "source_injection_count": source_injections.get("injection_count", 0),
                "pause_required_count": source_report.get("pause_required_count", 0),
                "continue_allowed_count": source_report.get("continue_allowed_count", 0),
            },
            "draft_action": "登记连续失败异常，禁止自动恢复，等待总管确认。",
            **common_decision,
        },
    ]
    return {
        "name": "低风险只读调度器异常升级规则草案",
        "generated_at": generated_at,
        "source_package": str(SOURCE_DIR),
        "readonly_draft_only": True,
        "rule_count": len(rules),
        "required_categories": [rule["category"] for rule in rules],
        "safety_confirmation": safety_flags(),
        "rules": rules,
    }


def build_queue(generated_at: str, rules: dict[str, Any]) -> dict[str, Any]:
    items = []
    for index, rule in enumerate(rules["rules"], start=1):
        items.append(
            {
                "id": f"ESC-Q-{index:03d}",
                "source_rule_id": rule["id"],
                "category": rule["category"],
                "title": f"确认低风险只读调度器异常升级：{rule['category']}",
                "status": "需总管确认",
                "priority": "P1-暂停后人工确认",
                "pause_required": True,
                "continue_allowed": False,
                "requires_supervisor_confirmation": True,
                "executed": False,
                "auto_resume": False,
                "external_call": False,
                "reload_service": False,
                "draft_action": rule["draft_action"],
                "confirmation_question": "是否允许后续仅以人工签收后的只读草案方式处理，不自动执行升级动作？",
            }
        )
    return {
        "name": "低风险只读调度器异常升级总管确认队列",
        "generated_at": generated_at,
        "queue_count": len(items),
        "default_status": "需总管确认",
        "executed": False,
        "auto_resume": False,
        "continue_allowed": False,
        "requires_supervisor_confirmation": True,
        "safety_confirmation": safety_flags(),
        "items": items,
    }


def rules_md(rules: dict[str, Any]) -> str:
    rows = [
        "| {id} | {category} | {pause_required} | {continue_allowed} | {requires_supervisor_confirmation} | {executed} | {auto_resume} | {trigger} |".format(**rule)
        for rule in rules["rules"]
    ]
    return "\n".join(
        [
            "# 低风险只读调度器异常升级规则草案",
            "",
            f"- 生成时间: {rules['generated_at']}",
            "- 性质: 只读草案，不执行升级动作。",
            "- 覆盖: 红线命中、服务重载需求、正式规则影响、外部接口需求、证据缺失、连续失败。",
            "",
            "| ID | 类别 | pause_required | continue_allowed | requires_supervisor_confirmation | executed | auto_resume | 触发条件 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def queue_md(queue: dict[str, Any]) -> str:
    rows = [
        "| {id} | {category} | {status} | {pause_required} | {continue_allowed} | {requires_supervisor_confirmation} | {executed} | {auto_resume} |".format(**item)
        for item in queue["items"]
    ]
    return "\n".join(
        [
            "# 总管确认队列",
            "",
            f"- 生成时间: {queue['generated_at']}",
            f"- queue_count: {queue['queue_count']}",
            "- 默认状态: 需总管确认",
            "- executed: false",
            "- auto_resume: false",
            "",
            "| ID | 类别 | status | pause_required | continue_allowed | requires_supervisor_confirmation | executed | auto_resume |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def package_md(package: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 低风险只读调度器异常升级草案与总管确认队列包",
            "",
            f"- 生成时间: {package['generated_at']}",
            f"- rule_count: {package['metrics']['rule_count']}",
            f"- queue_count: {package['metrics']['queue_count']}",
            "- executed: false",
            "- auto_resume: false",
            "- external_call: false",
            "- reload_service: false",
            "",
            "## 产物",
            "",
            f"- {RULE_JSON.name}",
            f"- {RULE_MD.name}",
            f"- {QUEUE_JSON.name}",
            f"- {QUEUE_MD.name}",
            "",
        ]
    )


def main() -> int:
    generated_at = now()
    source_injections = read_json(SOURCE_INJECTION_JSON)
    source_report = read_json(SOURCE_PAUSE_REPORT_JSON)
    rules = build_rules(generated_at, source_injections, source_report)
    queue = build_queue(generated_at, rules)
    package = {
        "name": "低风险只读调度器异常升级草案与总管确认队列包",
        "generated_at": generated_at,
        "readonly_draft_only": True,
        "source_files": {
            "source_injection_json": str(SOURCE_INJECTION_JSON),
            "source_pause_report_json": str(SOURCE_PAUSE_REPORT_JSON),
        },
        "metrics": {
            "rule_count": rules["rule_count"],
            "queue_count": queue["queue_count"],
        },
        "executed": False,
        "auto_resume": False,
        "external_call": False,
        "reload_service": False,
        "safety_confirmation": safety_flags(),
        "artifacts": {
            "rule_json": str(RULE_JSON),
            "rule_md": str(RULE_MD),
            "queue_json": str(QUEUE_JSON),
            "queue_md": str(QUEUE_MD),
        },
    }

    write_json(RULE_JSON, rules)
    write_text(RULE_MD, rules_md(rules))
    write_json(QUEUE_JSON, queue)
    write_text(QUEUE_MD, queue_md(queue))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))
    write_json(GENERATE_LOG, package)
    print(json.dumps({"pass": True, "error_count": 0, "rule_count": rules["rule_count"], "queue_count": queue["queue_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
