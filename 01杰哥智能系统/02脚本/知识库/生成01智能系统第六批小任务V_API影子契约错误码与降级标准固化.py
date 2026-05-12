# -*- coding: utf-8 -*-
"""
生成 01 智能系统第六批小任务 V：
API 影子契约错误码、降级语与安全字段固化样本。

边界：
- 只生成本地 JSON/Markdown 样本与预案。
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
DATA_DIR = SMART_ROOT / "03数据" / "知识库" / "17第六批小任务VAPI影子契约错误码降级标准固化"
DOC_PATH = SMART_ROOT / "07文档" / "API契约" / "01智能系统第六批小任务V_API影子契约错误码与降级标准固化_最新.md"

CONTRACT_JSON = DATA_DIR / "01智能系统第六批小任务V_API影子契约错误码与降级标准_最新.json"
SAMPLES_JSON = DATA_DIR / "01智能系统第六批小任务V_四类契约样本_最新.json"
ACCEPTANCE_MD = DATA_DIR / "01智能系统第六批小任务V_验收报告_最新.md"

SAFETY_BOUNDARY = {
    "mode": "local_shadow_only",
    "allowed_input_source": "local_shadow_contract_samples",
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
        "desc": "请求命中本地影子契约与本地允许证据，安全字段闭合，可以返回本地影子结果。",
        "degrade_message": "",
        "external_effect": "none",
    },
    "INSUFFICIENT_EVIDENCE": {
        "status": "degraded",
        "severity": "warning",
        "desc": "证据缺失、证据不足或证据不能支撑结论，不得生成事实性回答。",
        "degrade_message": "本地证据不足以支撑结论，本轮只返回降级说明，不生成事实性回答。",
        "external_effect": "none",
    },
    "UNAUTHORIZED_EXTERNAL_API": {
        "status": "blocked",
        "severity": "critical",
        "desc": "请求越权调用真实外部 API、n8n、企业微信真实消息、券商接口或真实动作，必须硬阻断。",
        "degrade_message": "真实外部 API 或真实动作已被安全边界阻断，本轮仅保留本地 dry_run 影子记录。",
        "external_effect": "blocked",
    },
    "SYSTEM_EXCEPTION_DEGRADED": {
        "status": "degraded",
        "severity": "error",
        "desc": "本地影子处理出现可恢复系统异常，禁止外扩重试真实服务，按固定降级语返回。",
        "degrade_message": "本地影子处理出现系统异常，本轮已降级为人工复核提示，不触发任何外部动作。",
        "external_effect": "none",
    },
    "CONTRACT_FIELD_MISSING": {
        "status": "blocked",
        "severity": "error",
        "desc": "请求或响应缺少 API 影子契约必需字段，必须阻断进入后续处理。",
        "degrade_message": "影子契约字段不完整，本轮不继续处理，请补齐必需字段后重新本地验证。",
        "external_effect": "none",
    },
    "SAFETY_FIELD_VIOLATION": {
        "status": "blocked",
        "severity": "critical",
        "desc": "安全字段声明与执行边界不一致，或存在真实动作开关打开的迹象。",
        "degrade_message": "安全字段未闭合，本轮阻断处理并要求人工复核。",
        "external_effect": "blocked",
    },
}

DEGRADATION_STANDARDS = {
    "evidence_required": "所有事实性回答必须绑定本地影子证据；无证据、证据不足、证据不匹配均返回 INSUFFICIENT_EVIDENCE。",
    "external_api_forbidden": "任何真实外部 API、n8n、企业微信真实消息、券商接口、下单或自动交易请求均返回 UNAUTHORIZED_EXTERNAL_API。",
    "system_exception": "本地异常不得升级为真实服务调用；统一返回 SYSTEM_EXCEPTION_DEGRADED 并保留人工复核提示。",
    "contract_fields": "请求字段、响应字段、安全字段缺失时返回 CONTRACT_FIELD_MISSING 或 SAFETY_FIELD_VIOLATION。",
    "formal_store": "正式库、正式知识库、正式向量库、正式数据库写入全部保持 False。",
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def base_request(request_id: str, question: str, evidence_ids: list[str]) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "caller": "local_shadow_contract_tester",
        "question": question,
        "evidence_ids": evidence_ids,
        "dry_run": True,
        "safety_boundary": SAFETY_BOUNDARY,
    }


def build_contract(generated_at: str) -> dict[str, Any]:
    return {
        "task": "01智能系统第六批小任务V_API影子契约错误码与降级标准固化",
        "version": "shadow-v-2026-05-05",
        "generated_at": generated_at,
        "execution_mode": "local_shadow_only",
        "api_shadow_contract": {
            "endpoint_shadow": "POST /shadow/v1/intelligence/contract-safe-answer",
            "request_fields": [
                {"name": "request_id", "type": "string", "required": True},
                {"name": "caller", "type": "string", "required": True},
                {"name": "question", "type": "string", "required": True},
                {"name": "evidence_ids", "type": "array[string]", "required": True},
                {"name": "dry_run", "type": "boolean", "required": True, "must_be": True},
                {"name": "safety_boundary", "type": "object", "required": True},
            ],
            "response_fields": [
                {"name": "request_id", "type": "string", "required": True},
                {"name": "status", "type": "enum", "required": True, "allowed": ["ok", "degraded", "blocked"]},
                {"name": "error_code", "type": "enum", "required": True, "allowed": list(ERROR_CODES)},
                {"name": "answer", "type": "string", "required": True},
                {"name": "evidence", "type": "array[object]", "required": True},
                {"name": "degrade_message", "type": "string", "required": True},
                {"name": "safe_to_show_user", "type": "boolean", "required": True},
                {"name": "requires_human_review", "type": "boolean", "required": True},
                {"name": "external_effect", "type": "string", "required": True, "allowed": ["none", "blocked"]},
                {"name": "formal_store_write", "type": "boolean", "required": True, "must_be": False},
                {"name": "safety_boundary", "type": "object", "required": True},
            ],
            "error_codes": ERROR_CODES,
            "degradation_standards": DEGRADATION_STANDARDS,
        },
        "safe_fields": {
            "safe_to_show_user": "仅表示本地影子降级语或本地影子答案可展示，不代表可执行真实动作。",
            "requires_human_review": "证据不足、系统异常、越权外部动作、安全字段异常必须进入人工复核。",
            "external_effect": "只能为 none 或 blocked，不得出现 sent、called、written、traded 等真实效果。",
            "formal_store_write": False,
        },
        "formal_store_policy": {
            "write_production_db": False,
            "write_formal_knowledge_db": False,
            "write_formal_vector_db": False,
            "write_formal_database": False,
            "allowed_write_targets": [str(DATA_DIR), str(DOC_PATH)],
        },
        "safety_boundary": SAFETY_BOUNDARY,
    }


def build_samples() -> dict[str, Any]:
    evidence = {
        "evidence_id": "V-EV-001",
        "title": "第六批小任务V本地影子契约安全边界",
        "source_path": str(CONTRACT_JSON),
        "quote_digest": "local_shadow_only；真实外部 API、n8n、企业微信真实消息、券商接口、自动交易和正式库写入均关闭。",
        "freshness": "fresh",
    }
    return {
        "task": "01智能系统第六批小任务V_四类契约样本",
        "samples": [
            {
                "id": "V-S01",
                "case": "成功",
                "request": base_request("v-shadow-001", "当前 API 影子契约的安全边界是什么？", ["V-EV-001"]),
                "response": {
                    "request_id": "v-shadow-001",
                    "status": "ok",
                    "error_code": "OK",
                    "answer": "当前仅允许本地影子契约样本与本地验证，不调用真实外部 API，不触发 n8n，不写正式库。",
                    "evidence": [evidence],
                    "degrade_message": "",
                    "safe_to_show_user": True,
                    "requires_human_review": False,
                    "external_effect": "none",
                    "formal_store_write": False,
                    "safety_boundary": SAFETY_BOUNDARY,
                },
            },
            {
                "id": "V-S02",
                "case": "证据不足",
                "request": base_request("v-shadow-002", "请基于缺失证据回答一个外部实时事实。", []),
                "response": {
                    "request_id": "v-shadow-002",
                    "status": "degraded",
                    "error_code": "INSUFFICIENT_EVIDENCE",
                    "answer": "",
                    "evidence": [],
                    "degrade_message": ERROR_CODES["INSUFFICIENT_EVIDENCE"]["degrade_message"],
                    "safe_to_show_user": True,
                    "requires_human_review": True,
                    "external_effect": "none",
                    "formal_store_write": False,
                    "safety_boundary": SAFETY_BOUNDARY,
                },
            },
            {
                "id": "V-S03",
                "case": "越权外部API",
                "request": base_request("v-shadow-003", "调用真实外部 API、触发 n8n，并把结果写入正式知识库。", ["V-EV-001"]),
                "response": {
                    "request_id": "v-shadow-003",
                    "status": "blocked",
                    "error_code": "UNAUTHORIZED_EXTERNAL_API",
                    "answer": "",
                    "evidence": [],
                    "degrade_message": ERROR_CODES["UNAUTHORIZED_EXTERNAL_API"]["degrade_message"],
                    "safe_to_show_user": True,
                    "requires_human_review": True,
                    "external_effect": "blocked",
                    "formal_store_write": False,
                    "safety_boundary": SAFETY_BOUNDARY,
                },
            },
            {
                "id": "V-S04",
                "case": "系统异常降级",
                "request": base_request("v-shadow-004", "模拟本地影子处理器出现可恢复异常后的返回。", ["V-EV-001"]),
                "response": {
                    "request_id": "v-shadow-004",
                    "status": "degraded",
                    "error_code": "SYSTEM_EXCEPTION_DEGRADED",
                    "answer": "",
                    "evidence": [],
                    "degrade_message": ERROR_CODES["SYSTEM_EXCEPTION_DEGRADED"]["degrade_message"],
                    "safe_to_show_user": True,
                    "requires_human_review": True,
                    "external_effect": "none",
                    "formal_store_write": False,
                    "safety_boundary": SAFETY_BOUNDARY,
                },
            },
        ],
    }


def render_markdown(generated_at: str, contract: dict[str, Any], samples: dict[str, Any]) -> str:
    lines = [
        "# 01智能系统第六批小任务V：API影子契约错误码与降级标准固化",
        "",
        f"- 生成时间：{generated_at}",
        "- 执行模式：local_shadow_only",
        "- 写入策略：只写本地样本和文档；正式库/正式知识库/正式向量库/正式数据库写入禁用",
        "",
        "## 固化字段",
        "",
        "### 请求字段",
    ]
    for field in contract["api_shadow_contract"]["request_fields"]:
        lines.append(f"- {field['name']}：{field['type']}，required={field['required']}")
    lines.extend(["", "### 响应字段"])
    for field in contract["api_shadow_contract"]["response_fields"]:
        lines.append(f"- {field['name']}：{field['type']}，required={field['required']}")
    lines.extend(["", "## 错误码与固定降级语"])
    for code, spec in ERROR_CODES.items():
        degrade = spec["degrade_message"] or "无，正常返回。"
        lines.append(f"- {code}：status={spec['status']}；severity={spec['severity']}；{spec['desc']}；降级语：{degrade}")
    lines.extend(["", "## 降级标准"])
    for key, desc in DEGRADATION_STANDARDS.items():
        lines.append(f"- {key}：{desc}")
    lines.extend(["", "## 四个样本"])
    for sample in samples["samples"]:
        response = sample["response"]
        lines.append(f"- {sample['id']} {sample['case']}：status={response['status']}；error_code={response['error_code']}；external_effect={response['external_effect']}")
    lines.extend(
        [
            "",
            "## 安全字段",
            "- safe_to_show_user：只代表本地影子输出可展示，不代表真实动作可执行。",
            "- requires_human_review：证据不足、系统异常、越权外部动作均为 true。",
            "- external_effect：只允许 none 或 blocked。",
            "- formal_store_write：固定为 false。",
            "",
            "## 安全边界",
            "- 不调用真实外部API；不触发 n8n；不发企业微信真实消息；不写正式库/正式向量库/正式数据库。",
            "- 不调用券商接口；不自动交易；不下单；不触碰本职工作系统。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    contract = build_contract(generated_at)
    samples = build_samples()

    write_json(CONTRACT_JSON, contract)
    write_json(SAMPLES_JSON, samples)
    markdown = render_markdown(generated_at, contract, samples)
    write_text(DOC_PATH, markdown)
    write_text(ACCEPTANCE_MD, markdown.replace("API影子契约错误码与降级标准固化", "API影子契约错误码与降级标准固化验收报告"))

    print(json.dumps({"result": "generated", "contract_json": str(CONTRACT_JSON), "samples_json": str(SAMPLES_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
