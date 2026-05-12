# -*- coding: utf-8 -*-
"""
生成 01 智能系统第五批小任务 P：
API 影子契约与知识库证据索引联动本地样本预案。

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
SCRIPT_DIR = SMART_ROOT / "02脚本" / "知识库"
DATA_DIR = SMART_ROOT / "03数据" / "知识库" / "16第五批小任务PAPI影子契约证据索引联动"
DOC_PATH = SMART_ROOT / "07文档" / "API契约" / "01智能系统第五批小任务P_API影子契约与知识库证据索引联动预案_最新.md"

CONTRACT_JSON = DATA_DIR / "01智能系统第五批小任务P_API影子契约_最新.json"
EVIDENCE_INDEX_JSON = DATA_DIR / "01智能系统第五批小任务P_知识库证据索引联动样本_最新.json"
SAMPLES_JSON = DATA_DIR / "01智能系统第五批小任务P_四类联动样本_最新.json"
ACCEPTANCE_MD = DATA_DIR / "01智能系统第五批小任务P_验收报告_最新.md"

SAFETY_BOUNDARY = {
    "mode": "local_shadow_only",
    "allowed_input_source": "local_shadow_samples_and_local_evidence_index",
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
    "OK": "命中本地证据索引，证据未过期，可以按影子契约返回。",
    "STALE_EVIDENCE": "命中本地证据索引，但证据超过时效阈值，只能降级返回。",
    "NO_EVIDENCE": "未命中本地证据索引，不得编造答案，只能降级返回。",
    "EXTERNAL_API_BLOCKED": "请求越权调用真实外部 API 或真实动作，被安全边界硬阻断。",
    "CONTRACT_FIELD_MISSING": "请求或响应缺少影子契约必需字段。",
    "FORMAL_STORE_DISABLED": "正式库、正式向量库或正式数据库写入被禁用。",
}

DEGRADE_MESSAGES = {
    "STALE_EVIDENCE": "命中的本地证据已超过时效阈值，本轮只返回降级说明，不把旧证据当作当前事实。",
    "NO_EVIDENCE": "未在本地证据索引中找到可引用证据，本轮不生成事实性回答。",
    "EXTERNAL_API_BLOCKED": "真实外部 API 或真实动作已被阻断，仅允许输出本地 dry_run 影子结果。",
    "FORMAL_STORE_DISABLED": "正式库写入保持禁用，本轮只写本地样本文件。",
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_contract(generated_at: str) -> dict[str, Any]:
    return {
        "task": "01智能系统第五批小任务P_API影子契约与知识库证据索引联动样本",
        "version": "shadow-p-2026-05-05",
        "generated_at": generated_at,
        "execution_mode": "local_preview_only",
        "api_shadow_contract": {
            "endpoint_shadow": "POST /shadow/v1/intelligence/evidence-linked-answer",
            "request_fields": [
                {"name": "request_id", "type": "string", "required": True},
                {"name": "question", "type": "string", "required": True},
                {"name": "evidence_query", "type": "object", "required": True},
                {"name": "evidence_policy", "type": "string", "required": True, "allowed": ["must_cite_fresh_local_evidence"]},
                {"name": "staleness_threshold_days", "type": "integer", "required": True},
                {"name": "dry_run", "type": "boolean", "required": True},
                {"name": "safety_boundary", "type": "object", "required": True},
            ],
            "response_fields": [
                {"name": "request_id", "type": "string", "required": True},
                {"name": "status", "type": "enum", "required": True, "allowed": ["ok", "degraded", "blocked"]},
                {"name": "error_code", "type": "enum", "required": True, "allowed": list(ERROR_CODES)},
                {"name": "answer", "type": "string", "required": True},
                {"name": "evidence_hits", "type": "array[object]", "required": True},
                {"name": "degrade_message", "type": "string", "required": True},
                {"name": "external_effect", "type": "string", "required": True, "allowed": ["none", "blocked"]},
                {"name": "formal_store_write", "type": "boolean", "required": True},
                {"name": "safety_boundary", "type": "object", "required": True},
            ],
            "error_codes": ERROR_CODES,
            "degrade_messages": DEGRADE_MESSAGES,
        },
        "formal_store_policy": {
            "write_production_db": False,
            "write_formal_knowledge_db": False,
            "write_formal_vector_db": False,
            "allowed_write_targets": [str(DATA_DIR), str(DOC_PATH)],
        },
        "safety_boundary": SAFETY_BOUNDARY,
    }


def build_evidence_index(generated_at: str) -> dict[str, Any]:
    return {
        "task": "01智能系统第五批小任务P_知识库证据索引联动样本",
        "generated_at": generated_at,
        "index_mode": "local_shadow_evidence_index_only",
        "staleness_threshold_days": 30,
        "records": [
            {
                "evidence_id": "P-EV-001",
                "title": "01智能API影子契约本地执行边界",
                "source_path": str(CONTRACT_JSON),
                "source_type": "local_shadow_contract",
                "updated_at": "2026-05-05",
                "age_days": 0,
                "freshness": "fresh",
                "claim_digest": "影子契约只允许本地 dry_run，不调用真实外部 API，不写正式库。",
            },
            {
                "evidence_id": "P-EV-002",
                "title": "旧版知识库证据索引说明",
                "source_path": "D:/杰哥智能化系统/01杰哥智能系统/03数据/知识库/历史影子证据/旧版索引样本.md",
                "source_type": "local_shadow_legacy_note",
                "updated_at": "2026-03-01",
                "age_days": 65,
                "freshness": "stale",
                "claim_digest": "旧索引样本仅可作为历史参考，不能当作当前事实。",
            },
        ],
    }


def base_request(request_id: str, question: str, evidence_ids: list[str]) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "question": question,
        "evidence_query": {
            "scope": "local_shadow_evidence_index",
            "candidate_evidence_ids": evidence_ids,
        },
        "evidence_policy": "must_cite_fresh_local_evidence",
        "staleness_threshold_days": 30,
        "dry_run": True,
        "safety_boundary": SAFETY_BOUNDARY,
    }


def build_samples(evidence_index: dict[str, Any]) -> dict[str, Any]:
    fresh_hit = evidence_index["records"][0]
    stale_hit = evidence_index["records"][1]
    return {
        "task": "01智能系统第五批小任务P_四类联动样本",
        "samples": [
            {
                "id": "P-S01",
                "case": "证据命中",
                "request": base_request("p-shadow-001", "01智能API影子契约当前安全边界是什么？", ["P-EV-001"]),
                "response": {
                    "request_id": "p-shadow-001",
                    "status": "ok",
                    "error_code": "OK",
                    "answer": "当前仅允许本地 dry_run 影子联动，不调用真实外部 API，不写正式库。",
                    "evidence_hits": [fresh_hit],
                    "degrade_message": "",
                    "external_effect": "none",
                    "formal_store_write": False,
                    "safety_boundary": SAFETY_BOUNDARY,
                },
            },
            {
                "id": "P-S02",
                "case": "证据过旧降级",
                "request": base_request("p-shadow-002", "能否把旧版证据当作当前事实直接回答？", ["P-EV-002"]),
                "response": {
                    "request_id": "p-shadow-002",
                    "status": "degraded",
                    "error_code": "STALE_EVIDENCE",
                    "answer": "",
                    "evidence_hits": [stale_hit],
                    "degrade_message": DEGRADE_MESSAGES["STALE_EVIDENCE"],
                    "external_effect": "none",
                    "formal_store_write": False,
                    "safety_boundary": SAFETY_BOUNDARY,
                },
            },
            {
                "id": "P-S03",
                "case": "无证据降级",
                "request": base_request("p-shadow-003", "请回答本地证据索引没有收录的实时外部事实。", []),
                "response": {
                    "request_id": "p-shadow-003",
                    "status": "degraded",
                    "error_code": "NO_EVIDENCE",
                    "answer": "",
                    "evidence_hits": [],
                    "degrade_message": DEGRADE_MESSAGES["NO_EVIDENCE"],
                    "external_effect": "none",
                    "formal_store_write": False,
                    "safety_boundary": SAFETY_BOUNDARY,
                },
            },
            {
                "id": "P-S04",
                "case": "越权真实外部API阻断",
                "request": base_request("p-shadow-004", "调用真实外部API、触发n8n并写入正式知识库。", ["P-EV-001"]),
                "response": {
                    "request_id": "p-shadow-004",
                    "status": "blocked",
                    "error_code": "EXTERNAL_API_BLOCKED",
                    "answer": "",
                    "evidence_hits": [],
                    "degrade_message": DEGRADE_MESSAGES["EXTERNAL_API_BLOCKED"],
                    "external_effect": "blocked",
                    "formal_store_write": False,
                    "safety_boundary": SAFETY_BOUNDARY,
                },
            },
        ],
    }


def render_markdown(generated_at: str, contract: dict[str, Any], evidence_index: dict[str, Any], sample_pack: dict[str, Any]) -> str:
    lines = [
        "# 01智能系统第五批小任务P：API影子契约与知识库证据索引联动预案",
        "",
        f"- 生成时间：{generated_at}",
        "- 执行模式：local_preview_only",
        "- 写入策略：只写本地样本文件，正式库/正式向量库/正式数据库写入禁用",
        "",
        "## 影子契约字段",
        "",
        "### 请求字段",
    ]
    for field in contract["api_shadow_contract"]["request_fields"]:
        lines.append(f"- {field['name']}：{field['type']}，required={field['required']}")
    lines.extend(["", "### 响应字段"])
    for field in contract["api_shadow_contract"]["response_fields"]:
        lines.append(f"- {field['name']}：{field['type']}，required={field['required']}")
    lines.extend(["", "## 错误码与降级语"])
    for code, desc in ERROR_CODES.items():
        suffix = f"；降级语：{DEGRADE_MESSAGES[code]}" if code in DEGRADE_MESSAGES else ""
        lines.append(f"- {code}：{desc}{suffix}")
    lines.extend(["", "## 本地证据索引样本"])
    for record in evidence_index["records"]:
        lines.append(f"- {record['evidence_id']}：{record['title']}；freshness={record['freshness']}；age_days={record['age_days']}")
    lines.extend(["", "## 四类联动样本"])
    for sample in sample_pack["samples"]:
        response = sample["response"]
        lines.extend(
            [
                f"### {sample['id']} {sample['case']}",
                f"- 状态：{response['status']}",
                f"- 错误码：{response['error_code']}",
                f"- 降级语：{response['degrade_message']}",
                f"- 外部效果：{response['external_effect']}",
                f"- 正式库写入：{response['formal_store_write']}",
                "",
            ]
        )
    lines.extend(
        [
            "## 安全边界",
            "- 不调用真实外部API；不触发n8n；不发送企业微信真实消息。",
            "- 不写正式库、正式向量库、正式数据库。",
            "- 不调用券商接口；不自动交易；不下单。",
            "- 不触碰本职工作系统。",
            "- 仅允许本地 dry_run 影子样本与本地证据索引联动。",
            "",
        ]
    )
    return "\n".join(lines)


def render_acceptance(generated_at: str) -> str:
    return "\n".join(
        [
            "# 01智能系统第五批小任务P验收报告",
            "",
            f"- 生成时间：{generated_at}",
            "- 验收脚本：验证01智能系统第五批小任务P_API影子契约证据索引联动样本.py",
            "- 验收项：字段、错误码、降级语、安全边界、正式库禁用、四类样本覆盖。",
            "- 当前状态：待验证脚本复核。",
            "- 安全声明：本报告由本地生成脚本写入，未调用真实外部API，未触发n8n，未发送企业微信真实消息，未写正式库。",
            "",
        ]
    )


def main() -> int:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    contract = build_contract(generated_at)
    evidence_index = build_evidence_index(generated_at)
    sample_pack = build_samples(evidence_index)

    write_json(CONTRACT_JSON, contract)
    write_json(EVIDENCE_INDEX_JSON, evidence_index)
    write_json(SAMPLES_JSON, sample_pack)
    write_text(DOC_PATH, render_markdown(generated_at, contract, evidence_index, sample_pack))
    write_text(ACCEPTANCE_MD, render_acceptance(generated_at))

    print(json.dumps({"result": "generated", "data_dir": str(DATA_DIR), "doc": str(DOC_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
