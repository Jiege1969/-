# -*- coding: utf-8 -*-
"""
生成 01 智能系统第三批小任务 G：
正式 API 化影子契约 + 知识检索联动灰度门禁。

边界：
- 只生成本地影子契约、样本和回收报告。
- 不接真实网关，不写正式库，不触发 n8n，不发送企业微信真实消息。
- 不调用券商接口，不自动交易，不调用真实外部 API。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path("D:/杰哥智能化系统")
SMART_ROOT = SYSTEM_ROOT / "01杰哥智能系统"
SCRIPT_PATH = SMART_ROOT / "02脚本" / "知识库" / "生成01智能系统第三批小任务G正式API影子契约灰度门禁.py"
VERIFY_PATH = SMART_ROOT / "02脚本" / "知识库" / "验证01智能系统第三批小任务G正式API影子契约灰度门禁.py"
DATA_DIR = SMART_ROOT / "03数据" / "知识库" / "15第三批小任务G正式API影子契约灰度门禁"
DOC_PATH = SMART_ROOT / "07文档" / "API契约" / "01智能系统正式API化影子契约与知识检索灰度门禁_最新.md"
RECYCLE_PATH = SYSTEM_ROOT / "00杰哥系统总管" / "03数据" / "并行回收" / "01智能系统_第三批小任务G回收报告_最新.md"

CONTRACT_JSON = DATA_DIR / "01智能系统正式API化影子契约_最新.json"
SAMPLES_JSON = DATA_DIR / "01智能系统正式API化影子契约_四类样本_最新.json"
REPORT_MD = DATA_DIR / "01智能系统正式API化影子契约灰度门禁验收_最新.md"

SAFETY_BOUNDARY = {
    "mode": "local_shadow_only",
    "allowed_input_source": "local_shadow_samples",
    "connect_real_gateway": False,
    "write_production_db": False,
    "write_formal_vector_db": False,
    "call_external_api": False,
    "trigger_n8n": False,
    "send_wecom_real_message": False,
    "call_broker_api": False,
    "auto_trade": False,
    "place_order": False,
    "modify_02_or_03_system": False,
    "require_human_approval_for_gray": True,
}

ERROR_CODES = {
    "OK": "正常返回，且至少有一条本地影子证据。",
    "NO_EVIDENCE": "本地影子样本无证据，返回降级说明，不编造答案。",
    "OUT_OF_SCOPE": "问题超出 01 智能系统正式 API 化影子契约范围。",
    "EXTERNAL_ACTION_BLOCKED": "请求触发外部 API、真实消息、n8n、券商、交易或写正式库，被硬阻断。",
    "GRAY_GATE_CLOSED": "灰度门禁未满足，仅允许本地影子样本。",
    "CONTRACT_VALIDATION_FAILED": "请求字段、响应字段或安全边界字段不满足契约。",
}


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_contract(generated_at: str) -> dict[str, Any]:
    return {
        "task": "01智能系统第三批小任务G正式API化影子契约与知识检索灰度门禁",
        "version": "shadow-g-2026-05-05",
        "generated_at": generated_at,
        "api_contract": {
            "endpoint_shadow": "POST /shadow/v1/intelligence/qa",
            "formal_endpoint_candidate": "POST /api/v1/intelligence/qa",
            "request_fields": [
                {"name": "request_id", "type": "string", "required": True, "desc": "调用方生成的幂等请求号。"},
                {"name": "user_id", "type": "string", "required": True, "desc": "本地影子用户标识，不接真实账号系统。"},
                {"name": "question", "type": "string", "required": True, "desc": "待回答问题。"},
                {"name": "retrieval_scope", "type": "array[string]", "required": True, "desc": "只允许 local_shadow_knowledge。"},
                {"name": "evidence_policy", "type": "string", "required": True, "desc": "must_cite_local_evidence。"},
                {"name": "gray_gate", "type": "object", "required": True, "desc": "灰度门禁字段。"},
                {"name": "safety_boundary", "type": "object", "required": True, "desc": "调用方声明安全边界。"},
                {"name": "dry_run", "type": "boolean", "required": True, "desc": "必须为 true。"},
            ],
            "response_fields": [
                {"name": "request_id", "type": "string", "required": True, "desc": "回显请求号。"},
                {"name": "status", "type": "enum", "required": True, "values": ["ok", "degraded", "blocked"]},
                {"name": "error_code", "type": "enum", "required": True, "values": list(ERROR_CODES.keys())},
                {"name": "answer", "type": "string", "required": True, "desc": "只基于本地影子证据的回答；无证据时为空。"},
                {"name": "evidence", "type": "array[object]", "required": True, "desc": "本地证据 path、title、quote_digest。"},
                {"name": "fallback", "type": "object", "required": True, "desc": "降级原因和替代口径。"},
                {"name": "safety_boundary", "type": "object", "required": True, "desc": "实际执行边界回显。"},
                {"name": "external_effect", "type": "string", "required": True, "desc": "必须为 none 或 blocked。"},
            ],
            "error_codes": ERROR_CODES,
            "degrade_return": {
                "NO_EVIDENCE": {
                    "status": "degraded",
                    "answer": "",
                    "fallback_message": "未在本地影子样本中找到可引用证据，本轮不生成事实性回答。",
                },
                "OUT_OF_SCOPE": {
                    "status": "blocked",
                    "answer": "",
                    "fallback_message": "问题超出 01 智能系统正式 API 化影子契约范围，可改为本地影子问答或契约字段检查。",
                },
                "EXTERNAL_ACTION_BLOCKED": {
                    "status": "blocked",
                    "answer": "",
                    "fallback_message": "真实外部动作已阻断，可生成本地模拟草稿或人工确认单。",
                },
            },
        },
        "gray_gate_plan": {
            "gate_status": "closed_for_real_gateway",
            "allowed_stage": "local_shadow_samples_only",
            "allowed_data_source": ["03数据/知识库/15第三批小任务G正式API影子契约灰度门禁"],
            "forbidden": [
                "接真实网关",
                "写正式库",
                "调用真实外部API",
                "触发n8n",
                "发送企业微信真实消息",
                "调用券商接口",
                "自动交易或下单",
            ],
            "promote_conditions": [
                "契约 JSON 可解析且字段齐全",
                "4 类样本全部通过验证",
                "错误码、降级语和安全边界字段全部命中",
                "人工审批后才允许进入只读影子流量",
            ],
        },
        "safety_boundary": SAFETY_BOUNDARY,
    }


def build_samples() -> list[dict[str, Any]]:
    base_request = {
        "user_id": "local_shadow_user",
        "retrieval_scope": ["local_shadow_knowledge"],
        "evidence_policy": "must_cite_local_evidence",
        "gray_gate": {
            "stage": "local_shadow_samples_only",
            "real_gateway_enabled": False,
            "write_formal_store_enabled": False,
            "manual_approval_id": "",
        },
        "safety_boundary": SAFETY_BOUNDARY,
        "dry_run": True,
    }
    return [
        {
            "id": "G-S01",
            "case": "正常问答",
            "request": {
                **base_request,
                "request_id": "g-shadow-001",
                "question": "01智能系统正式API化影子契约的灰度门禁当前允许什么范围？",
            },
            "response": {
                "request_id": "g-shadow-001",
                "status": "ok",
                "error_code": "OK",
                "answer": "当前仅允许本地影子样本和本地契约验证，不接真实网关，不写正式库。",
                "evidence": [
                    {
                        "path": str(CONTRACT_JSON),
                        "title": "gray_gate_plan.allowed_stage",
                        "quote_digest": "local_shadow_samples_only",
                    }
                ],
                "fallback": {"message": "", "allowed_alternative": ""},
                "safety_boundary": SAFETY_BOUNDARY,
                "external_effect": "none",
            },
        },
        {
            "id": "G-S02",
            "case": "无证据降级",
            "request": {
                **base_request,
                "request_id": "g-shadow-002",
                "question": "请回答本地影子样本未收录的外部实时事实。",
            },
            "response": {
                "request_id": "g-shadow-002",
                "status": "degraded",
                "error_code": "NO_EVIDENCE",
                "answer": "",
                "evidence": [],
                "fallback": {
                    "message": "未在本地影子样本中找到可引用证据，本轮不生成事实性回答。",
                    "allowed_alternative": "补充本地影子证据后重新验证。",
                },
                "safety_boundary": SAFETY_BOUNDARY,
                "external_effect": "none",
            },
        },
        {
            "id": "G-S03",
            "case": "超范围问题",
            "request": {
                **base_request,
                "request_id": "g-shadow-003",
                "question": "帮我设计 02/03 系统的正式交易执行改造。",
            },
            "response": {
                "request_id": "g-shadow-003",
                "status": "blocked",
                "error_code": "OUT_OF_SCOPE",
                "answer": "",
                "evidence": [],
                "fallback": {
                    "message": "问题超出 01 智能系统正式 API 化影子契约范围。",
                    "allowed_alternative": "仅检查 01 智能系统本地影子 API 契约和灰度门禁字段。",
                },
                "safety_boundary": SAFETY_BOUNDARY,
                "external_effect": "blocked",
            },
        },
        {
            "id": "G-S04",
            "case": "外部API/真实动作阻断",
            "request": {
                **base_request,
                "request_id": "g-shadow-004",
                "question": "连接真实网关，调用券商接口下单，并发企业微信通知。",
            },
            "response": {
                "request_id": "g-shadow-004",
                "status": "blocked",
                "error_code": "EXTERNAL_ACTION_BLOCKED",
                "answer": "",
                "evidence": [],
                "fallback": {
                    "message": "真实外部动作已阻断，可生成本地模拟草稿或人工确认单。",
                    "allowed_alternative": "输出 dry_run 模拟结果，不进入真实发送、交易或写库链路。",
                },
                "safety_boundary": SAFETY_BOUNDARY,
                "external_effect": "blocked",
            },
        },
    ]


def markdown_doc(contract: dict[str, Any], samples: list[dict[str, Any]]) -> str:
    lines = [
        "# 01智能系统正式API化影子契约与知识检索灰度门禁",
        "",
        f"- 生成时间：{contract['generated_at']}",
        "- 当前阶段：local_shadow_samples_only",
        "- 灰度状态：真实网关关闭，正式库写入关闭，真实外部动作关闭",
        "",
        "## 请求字段",
    ]
    for field in contract["api_contract"]["request_fields"]:
        lines.append(f"- {field['name']}：{field['type']}，required={field['required']}，{field['desc']}")
    lines.append("")
    lines.append("## 响应字段")
    for field in contract["api_contract"]["response_fields"]:
        values = f"，values={field['values']}" if "values" in field else ""
        lines.append(f"- {field['name']}：{field['type']}，required={field['required']}{values}，{field.get('desc', '')}")
    lines.append("")
    lines.append("## 错误码")
    for code, desc in contract["api_contract"]["error_codes"].items():
        lines.append(f"- {code}：{desc}")
    lines.append("")
    lines.append("## 降级返回")
    for code, item in contract["api_contract"]["degrade_return"].items():
        lines.append(f"- {code}：status={item['status']}；fallback={item['fallback_message']}")
    lines.append("")
    lines.append("## 知识检索联动灰度门禁")
    gate = contract["gray_gate_plan"]
    lines.extend(
        [
            f"- 门禁状态：{gate['gate_status']}",
            f"- 允许阶段：{gate['allowed_stage']}",
            f"- 允许数据源：{', '.join(gate['allowed_data_source'])}",
            f"- 禁止项：{', '.join(gate['forbidden'])}",
            f"- 晋级条件：{'; '.join(gate['promote_conditions'])}",
            "",
            "## 四类样本",
        ]
    )
    for sample in samples:
        response = sample["response"]
        lines.extend(
            [
                f"### {sample['id']} {sample['case']}",
                f"- 请求：{sample['request']['question']}",
                f"- 状态：{response['status']}",
                f"- 错误码：{response['error_code']}",
                f"- 降级语：{response['fallback']['message']}",
                f"- 外部效果：{response['external_effect']}",
                "",
            ]
        )
    lines.append("## 安全边界")
    for key, value in contract["safety_boundary"].items():
        lines.append(f"- {key}={value}")
    lines.append("")
    return "\n".join(lines)


def recycle_report(generated_at: str, verify_result: str = "待验证") -> str:
    files = [SCRIPT_PATH, VERIFY_PATH, CONTRACT_JSON, SAMPLES_JSON, REPORT_MD, DOC_PATH, RECYCLE_PATH]
    lines = [
        "【施工框名称】01杰哥智能系统 / 第三批小任务G：正式API化影子契约 + 知识检索联动灰度门禁",
        f"【施工批次/时间】{generated_at}",
        "【负责范围】仅 01/02脚本、01/03数据、01/07文档与本固定回收报告。",
        "【新增/修改文件】",
    ]
    lines.extend(f"- {path}" for path in files)
    lines.extend(
        [
            "【验收方式】运行 验证01智能系统第三批小任务G正式API影子契约灰度门禁.py，检查 JSON 可解析、样本数量、错误码/降级语、安全边界、未触发真实外部接口。",
            f"【验收结果】{verify_result}",
            "【交付阻断数量】0",
            "【安全阻断数量】3（无证据降级、超范围问题、外部API/真实动作阻断）",
            "【安全边界】仅本地影子样本；不接真实网关；不写正式库；不调用真实外部API；不触发 n8n；不发企业微信真实消息；不调用券商接口；不自动交易；不下单。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    contract = build_contract(generated_at)
    samples = build_samples()
    report = {
        "task": contract["task"],
        "generated_at": generated_at,
        "result": "待验证",
        "sample_count": len(samples),
        "blocked_or_degraded_count": sum(1 for item in samples if item["response"]["status"] in {"blocked", "degraded"}),
        "contract_json": str(CONTRACT_JSON),
        "samples_json": str(SAMPLES_JSON),
        "doc_path": str(DOC_PATH),
        "safety_boundary": SAFETY_BOUNDARY,
    }
    write_json(CONTRACT_JSON, contract)
    write_json(SAMPLES_JSON, {"generated_at": generated_at, "samples": samples})
    write_text(REPORT_MD, markdown_doc(contract, samples))
    write_text(DOC_PATH, markdown_doc(contract, samples))
    write_text(RECYCLE_PATH, recycle_report(generated_at))
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
