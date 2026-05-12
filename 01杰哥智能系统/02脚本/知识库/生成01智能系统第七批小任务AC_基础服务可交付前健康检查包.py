# -*- coding: utf-8 -*-
"""
生成 01 智能系统第七批小任务 AC：
基础服务可交付前健康检查包。

边界：
- 只生成本地 JSON/Markdown 健康检查包与验收材料。
- 不调用真实外部 API，不触发 n8n，不发送企业微信真实消息。
- 不写正式库，不调用券商接口，不自动交易，不触碰本职工作系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path("D:/杰哥智能化系统")
SMART_ROOT = SYSTEM_ROOT / "01杰哥智能系统"
DATA_DIR = SMART_ROOT / "03数据" / "知识库" / "18第七批小任务AC基础服务可交付前健康检查包"
DOC_PATH = SMART_ROOT / "07文档" / "API契约" / "01智能系统第七批小任务AC_基础服务可交付前健康检查包_最新.md"

PACKAGE_JSON = DATA_DIR / "01智能系统第七批小任务AC_基础服务可交付前健康检查包_最新.json"
SAMPLES_JSON = DATA_DIR / "01智能系统第七批小任务AC_健康检查样本_最新.json"
ACCEPTANCE_MD = DATA_DIR / "01智能系统第七批小任务AC_验收报告_最新.md"

SAFETY_BOUNDARY = {
    "mode": "local_shadow_health_check_only",
    "allowed_input_source": "local_shadow_contract_and_knowledge_index",
    "call_external_api": False,
    "trigger_n8n": False,
    "send_wecom_real_message": False,
    "write_production_db": False,
    "write_formal_knowledge_db": False,
    "write_formal_vector_db": False,
    "call_broker_api": False,
    "auto_trade": False,
    "place_order": False,
    "touch_primary_work_system": False,
    "dry_run_required": True,
}

ERROR_CODES = {
    "OK": {
        "status": "ok",
        "severity": "info",
        "delivery_gate": "pass",
        "message": "基础服务健康检查通过，可进入后续人工准入评审。",
    },
    "AC_CONTRACT_MISMATCH": {
        "status": "blocked",
        "severity": "error",
        "delivery_gate": "stop",
        "message": "API 契约字段或枚举不一致，本轮阻断交付，请先补齐契约。",
    },
    "AC_ERROR_CODE_GAP": {
        "status": "blocked",
        "severity": "error",
        "delivery_gate": "stop",
        "message": "错误码或固定降级语缺口未闭合，本轮阻断交付。",
    },
    "AC_KNOWLEDGE_LINK_DEGRADED": {
        "status": "degraded",
        "severity": "warning",
        "delivery_gate": "manual_review",
        "message": "知识检索联动证据不足，本轮只允许返回降级说明和人工复核提示。",
    },
    "AC_LOG_FIELD_MISSING": {
        "status": "blocked",
        "severity": "error",
        "delivery_gate": "stop",
        "message": "日志字段缺失，无法形成可追踪交付证据，本轮阻断交付。",
    },
    "AC_EXCEPTION_UNHANDLED": {
        "status": "blocked",
        "severity": "critical",
        "delivery_gate": "stop",
        "message": "异常处理路径未覆盖或可能外扩真实动作，本轮硬阻断。",
    },
    "AC_SAFETY_BOUNDARY_VIOLATION": {
        "status": "blocked",
        "severity": "critical",
        "delivery_gate": "stop",
        "message": "安全边界未闭合，本轮只保留本地 dry_run 记录并要求人工复核。",
    },
}

REQUIRED_LOG_FIELDS = [
    "trace_id",
    "request_id",
    "service_name",
    "operation",
    "health_check_item",
    "status",
    "error_code",
    "degrade_reason",
    "fallback_action",
    "knowledge_query_id",
    "evidence_ids",
    "evidence_count",
    "safe_to_show_user",
    "requires_human_review",
    "external_effect",
    "formal_store_write",
    "latency_ms",
    "timestamp",
]

HEALTH_ITEMS = [
    {
        "id": "AC-H01",
        "name": "API契约",
        "objective": "交付前确认请求字段、响应字段、枚举、dry_run 和安全边界字段齐全。",
        "required_evidence": ["第六批 V API影子契约", "第五批 P 知识库证据索引联动样本"],
        "pass_rule": "request_fields、response_fields、error_codes、safety_boundary 均存在且字段含义明确。",
        "fallback_on_fail": "返回 AC_CONTRACT_MISMATCH，阻断交付，列入人工补契约清单。",
    },
    {
        "id": "AC-H02",
        "name": "错误码",
        "objective": "交付前确认成功、契约不一致、错误码缺口、知识检索降级、日志缺失、异常未处理、安全边界违规均有固定错误码。",
        "required_evidence": ["第六批 V 错误码与降级标准"],
        "pass_rule": "所有错误码具备 status、severity、delivery_gate、message。",
        "fallback_on_fail": "返回 AC_ERROR_CODE_GAP，阻断交付。",
    },
    {
        "id": "AC-H03",
        "name": "降级",
        "objective": "证据不足、系统异常、字段缺失、越权真实动作时只返回固定降级语，不补写索引，不调用外部服务。",
        "required_evidence": ["第六批 V 降级标准", "小任务 B 异常处理闭环"],
        "pass_rule": "每个阻断或降级错误码都有固定 message 和 fallback_action。",
        "fallback_on_fail": "返回 AC_ERROR_CODE_GAP 或 AC_EXCEPTION_UNHANDLED。",
    },
    {
        "id": "AC-H04",
        "name": "知识检索联动",
        "objective": "健康检查能读取本地知识检索索引口径，并在证据不足时降级。",
        "required_evidence": ["知识库全文索引_最新.json", "知识库检索增强链路报告_最新.json"],
        "pass_rule": "health_check_item 中记录 knowledge_query_id、evidence_ids、evidence_count。",
        "fallback_on_fail": "返回 AC_KNOWLEDGE_LINK_DEGRADED，进入人工复核，不编造证据。",
    },
    {
        "id": "AC-H05",
        "name": "日志字段",
        "objective": "交付前确认每个检查项都能产出可追踪日志字段。",
        "required_evidence": ["本 AC 健康检查包 REQUIRED_LOG_FIELDS"],
        "pass_rule": "每条样本日志包含 REQUIRED_LOG_FIELDS 全量字段。",
        "fallback_on_fail": "返回 AC_LOG_FIELD_MISSING，阻断交付。",
    },
    {
        "id": "AC-H06",
        "name": "异常处理",
        "objective": "本地异常、字段缺失、证据不足、安全边界违规都能转入降级或阻断路径。",
        "required_evidence": ["第六批 V 四类契约样本", "本 AC 异常处理矩阵"],
        "pass_rule": "异常矩阵覆盖 contract_missing、no_evidence、local_exception、safety_violation。",
        "fallback_on_fail": "返回 AC_EXCEPTION_UNHANDLED，硬阻断。",
    },
]

EXCEPTION_MATRIX = [
    {
        "exception": "contract_missing",
        "detect_at": "request_validation",
        "error_code": "AC_CONTRACT_MISMATCH",
        "fallback_action": "block_delivery_and_request_contract_fix",
        "external_effect": "none",
    },
    {
        "exception": "no_evidence",
        "detect_at": "knowledge_link_check",
        "error_code": "AC_KNOWLEDGE_LINK_DEGRADED",
        "fallback_action": "return_degraded_message_and_manual_review",
        "external_effect": "none",
    },
    {
        "exception": "local_exception",
        "detect_at": "health_check_runtime",
        "error_code": "AC_EXCEPTION_UNHANDLED",
        "fallback_action": "block_delivery_keep_local_trace",
        "external_effect": "none",
    },
    {
        "exception": "safety_violation",
        "detect_at": "safety_boundary_guard",
        "error_code": "AC_SAFETY_BOUNDARY_VIOLATION",
        "fallback_action": "hard_block_and_manual_review",
        "external_effect": "blocked",
    },
]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def log_record(
    *,
    trace_id: str,
    request_id: str,
    item: str,
    status: str,
    error_code: str,
    evidence_ids: list[str],
    timestamp: str,
    fallback_action: str = "none",
    degrade_reason: str = "",
    external_effect: str = "none",
    requires_human_review: bool = False,
) -> dict[str, Any]:
    return {
        "trace_id": trace_id,
        "request_id": request_id,
        "service_name": "01-intelligence-base-service",
        "operation": "pre_delivery_health_check",
        "health_check_item": item,
        "status": status,
        "error_code": error_code,
        "degrade_reason": degrade_reason,
        "fallback_action": fallback_action,
        "knowledge_query_id": f"kq-{request_id}",
        "evidence_ids": evidence_ids,
        "evidence_count": len(evidence_ids),
        "safe_to_show_user": True,
        "requires_human_review": requires_human_review,
        "external_effect": external_effect,
        "formal_store_write": False,
        "latency_ms": 0,
        "timestamp": timestamp,
    }


def build_package(generated_at: str) -> dict[str, Any]:
    return {
        "task": "01智能系统第七批小任务AC_基础服务可交付前健康检查包",
        "version": "shadow-ac-2026-05-05",
        "generated_at": generated_at,
        "execution_mode": "local_shadow_health_check_only",
        "delivery_gate": "pre_delivery_manual_acceptance",
        "health_items": HEALTH_ITEMS,
        "api_contract": {
            "endpoint_shadow": "POST /shadow/v1/intelligence/base-service/health-check",
            "request_fields": [
                {"name": "request_id", "type": "string", "required": True},
                {"name": "caller", "type": "string", "required": True},
                {"name": "health_scope", "type": "array[string]", "required": True},
                {"name": "knowledge_query", "type": "object", "required": True},
                {"name": "dry_run", "type": "boolean", "required": True, "must_be": True},
                {"name": "safety_boundary", "type": "object", "required": True},
            ],
            "response_fields": [
                {"name": "request_id", "type": "string", "required": True},
                {"name": "status", "type": "enum", "required": True, "allowed": ["ok", "degraded", "blocked"]},
                {"name": "error_code", "type": "enum", "required": True, "allowed": list(ERROR_CODES)},
                {"name": "health_result", "type": "array[object]", "required": True},
                {"name": "degrade_message", "type": "string", "required": True},
                {"name": "fallback_action", "type": "string", "required": True},
                {"name": "log_fields", "type": "object", "required": True},
                {"name": "knowledge_link", "type": "object", "required": True},
                {"name": "safe_to_show_user", "type": "boolean", "required": True},
                {"name": "requires_human_review", "type": "boolean", "required": True},
                {"name": "external_effect", "type": "string", "required": True, "allowed": ["none", "blocked"]},
                {"name": "formal_store_write", "type": "boolean", "required": True, "must_be": False},
            ],
        },
        "error_codes": ERROR_CODES,
        "degradation_policy": {
            "no_evidence": "返回 AC_KNOWLEDGE_LINK_DEGRADED；不编造证据，不补写索引，不调用外部检索。",
            "contract_mismatch": "返回 AC_CONTRACT_MISMATCH；阻断交付，保留本地检查结果。",
            "log_missing": "返回 AC_LOG_FIELD_MISSING；阻断交付，要求补齐日志字段。",
            "local_exception": "返回 AC_EXCEPTION_UNHANDLED；不外扩重试真实服务。",
            "safety_violation": "返回 AC_SAFETY_BOUNDARY_VIOLATION；硬阻断并人工复核。",
        },
        "knowledge_link": {
            "mode": "local_readonly_index_reference",
            "index_candidates": [
                str(SMART_ROOT / "03数据" / "知识库" / "03索引清单" / "知识库全文索引_最新.json"),
                str(SMART_ROOT / "03数据" / "知识库" / "04检索缓存" / "知识库检索增强链路报告_最新.json"),
            ],
            "required_response_fields": ["knowledge_query_id", "evidence_ids", "evidence_count", "degrade_reason"],
            "no_evidence_policy": "return_degraded_message_only",
        },
        "required_log_fields": REQUIRED_LOG_FIELDS,
        "exception_matrix": EXCEPTION_MATRIX,
        "safety_boundary": SAFETY_BOUNDARY,
    }


def build_samples(generated_at: str) -> dict[str, Any]:
    logs = [
        log_record(
            trace_id="ac-trace-001",
            request_id="ac-health-001",
            item="API契约",
            status="ok",
            error_code="OK",
            evidence_ids=["V-CONTRACT-LOCAL", "P-KNOWLEDGE-LINK-LOCAL"],
            timestamp=generated_at,
        ),
        log_record(
            trace_id="ac-trace-002",
            request_id="ac-health-002",
            item="知识检索联动",
            status="degraded",
            error_code="AC_KNOWLEDGE_LINK_DEGRADED",
            evidence_ids=[],
            timestamp=generated_at,
            fallback_action="return_degraded_message_and_manual_review",
            degrade_reason="local_evidence_missing",
            requires_human_review=True,
        ),
        log_record(
            trace_id="ac-trace-003",
            request_id="ac-health-003",
            item="日志字段",
            status="blocked",
            error_code="AC_LOG_FIELD_MISSING",
            evidence_ids=["AC-LOG-SPEC"],
            timestamp=generated_at,
            fallback_action="block_delivery_and_fix_log_schema",
            degrade_reason="required_log_field_missing",
            requires_human_review=True,
        ),
        log_record(
            trace_id="ac-trace-004",
            request_id="ac-health-004",
            item="异常处理",
            status="blocked",
            error_code="AC_SAFETY_BOUNDARY_VIOLATION",
            evidence_ids=["AC-EXCEPTION-MATRIX"],
            timestamp=generated_at,
            fallback_action="hard_block_and_manual_review",
            degrade_reason="safety_boundary_open",
            external_effect="blocked",
            requires_human_review=True,
        ),
    ]
    return {
        "task": "01智能系统第七批小任务AC_健康检查样本",
        "generated_at": generated_at,
        "samples": [
            {
                "id": "AC-S01",
                "case": "健康通过",
                "input": "基础服务交付前检查 API 契约、错误码、降级、知识检索联动、日志字段、异常处理。",
                "expected": "OK",
                "log": logs[0],
            },
            {
                "id": "AC-S02",
                "case": "知识检索证据不足降级",
                "input": "健康检查需要知识库证据，但本地证据为空。",
                "expected": "AC_KNOWLEDGE_LINK_DEGRADED",
                "log": logs[1],
            },
            {
                "id": "AC-S03",
                "case": "日志字段缺失阻断",
                "input": "健康检查日志缺少必需字段。",
                "expected": "AC_LOG_FIELD_MISSING",
                "log": logs[2],
            },
            {
                "id": "AC-S04",
                "case": "安全边界异常阻断",
                "input": "健康检查发现真实动作开关存在打开风险。",
                "expected": "AC_SAFETY_BOUNDARY_VIOLATION",
                "log": logs[3],
            },
        ],
    }


def render_markdown(generated_at: str, package: dict[str, Any], samples: dict[str, Any]) -> str:
    lines = [
        "# 01智能系统第七批小任务AC：基础服务可交付前健康检查包",
        "",
        f"- 生成时间：{generated_at}",
        "- 执行模式：local_shadow_health_check_only",
        "- 交付门禁：pre_delivery_manual_acceptance",
        "- 安全边界：不调用真实外部API，不触发 n8n，不发企业微信真实消息，不写正式库，不调用券商接口，不自动交易，不触碰本职工作系统。",
        "",
        "## 检查项",
    ]
    for item in package["health_items"]:
        lines.extend(
            [
                f"### {item['id']} {item['name']}",
                f"- 目标：{item['objective']}",
                f"- 通过规则：{item['pass_rule']}",
                f"- 失败降级：{item['fallback_on_fail']}",
            ]
        )
    lines.extend(["", "## API契约"])
    lines.append("- 影子端点：POST /shadow/v1/intelligence/base-service/health-check")
    lines.append("- 请求字段：" + "、".join(field["name"] for field in package["api_contract"]["request_fields"]))
    lines.append("- 响应字段：" + "、".join(field["name"] for field in package["api_contract"]["response_fields"]))
    lines.extend(["", "## 错误码与降级"])
    for code, spec in package["error_codes"].items():
        lines.append(f"- {code}：status={spec['status']}；severity={spec['severity']}；gate={spec['delivery_gate']}；{spec['message']}")
    lines.extend(["", "## 知识检索联动"])
    lines.append("- 模式：local_readonly_index_reference")
    lines.append("- 证据字段：knowledge_query_id、evidence_ids、evidence_count、degrade_reason")
    lines.append("- 无证据策略：返回 AC_KNOWLEDGE_LINK_DEGRADED，不编造证据，不补写索引，不调用外部检索。")
    lines.extend(["", "## 日志字段"])
    lines.append("- " + "、".join(package["required_log_fields"]))
    lines.extend(["", "## 异常处理矩阵"])
    for row in package["exception_matrix"]:
        lines.append(f"- {row['exception']}：detect_at={row['detect_at']}；error_code={row['error_code']}；fallback={row['fallback_action']}；external_effect={row['external_effect']}")
    lines.extend(["", "## 样本"])
    for sample in samples["samples"]:
        log = sample["log"]
        lines.append(f"- {sample['id']} {sample['case']}：status={log['status']}；error_code={log['error_code']}；fallback={log['fallback_action']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    package = build_package(generated_at)
    samples = build_samples(generated_at)

    write_json(PACKAGE_JSON, package)
    write_json(SAMPLES_JSON, samples)
    markdown = render_markdown(generated_at, package, samples)
    write_text(DOC_PATH, markdown)
    write_text(ACCEPTANCE_MD, markdown.replace("基础服务可交付前健康检查包", "基础服务可交付前健康检查包验收报告"))

    print(json.dumps({"result": "generated", "package_json": str(PACKAGE_JSON), "samples_json": str(SAMPLES_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
