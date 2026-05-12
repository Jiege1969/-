# -*- coding: utf-8 -*-
"""生成低风险只读调度器周报草稿与不发送封存包。

本脚本只写入 122 数据包和固定验收日志目录内的本地 JSON/MD 草稿；不发送企业微信，
不触发 n8n，不发起网络请求，不连接券商、税局或财税软件，不修改总管面板和一键接续包。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "122低风险只读调度器周报草稿与不发送封存包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器周报草稿与不发送封存包验收"

TEMPLATE_JSON = DATA_DIR / "周报草稿模板_最新.json"
TEMPLATE_MD = DATA_DIR / "周报草稿模板_最新.md"
SAMPLE_JSON = DATA_DIR / "周报草稿样本_最新.json"
SAMPLE_MD = DATA_DIR / "周报草稿样本_最新.md"
PROOF_JSON = DATA_DIR / "不发送封存证明_最新.json"
PROOF_MD = DATA_DIR / "不发送封存证明_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器周报草稿与不发送封存包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器周报草稿与不发送封存包_最新.md"
GENERATE_LOG = LOG_DIR / "low-risk-readonly-scheduler-weekly-report-no-send-generate-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safety_flags() -> dict[str, Any]:
    return {
        "preview_only": True,
        "local_file_only": True,
        "readonly_scheduler": True,
        "send_allowed": False,
        "real_send": False,
        "real_wecom_send": False,
        "network_request": False,
        "no_network_request": True,
        "connect_n8n": False,
        "trigger_n8n": False,
        "no_n8n_trigger": True,
        "no_wecom_send": True,
        "sealed_locally": True,
        "broker_connection": False,
        "trade_order": False,
        "tax_bureau_login": False,
        "finance_tax_software_connection": False,
        "auto_promote_formal_rule": False,
        "write_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
        "reload_service": False,
    }


def build_template(generated_at: str) -> dict[str, Any]:
    sections = {
        "本周总览": {
            "section_order": 1,
            "fields": ["周期", "只读调度器状态", "本地草稿结论", "红线确认"],
            "template_items": [
                "汇总本周只读调度器本地预演、值守、证据留存与异常队列状态。",
                "说明本周只产出本地草稿，不发送企业微信，不触发 n8n。",
            ],
        },
        "通过趋势": {
            "section_order": 2,
            "fields": ["预演批次", "通过数", "暂停数", "待确认数", "趋势备注"],
            "template_items": [
                "记录本周只读预演通过趋势。",
                "趋势仅来自本地草稿样本，不作为正式运行指标自动生效。",
            ],
        },
        "暂停/确认队列": {
            "section_order": 3,
            "fields": ["队列编号", "事项", "状态", "是否需要总管人工确认"],
            "template_items": [
                "登记需要暂停或人工确认的事项。",
                "所有待确认事项保持本地封存，不自动推进正式规则。",
            ],
        },
        "证据留存": {
            "section_order": 4,
            "fields": ["证据类型", "本地路径占位", "留存状态", "封存说明"],
            "template_items": [
                "记录周报草稿、预演结果和不发送证明的本地留存状态。",
                "证据留存只写 122 数据包和固定验收日志目录。",
            ],
        },
        "下周建议": {
            "section_order": 5,
            "fields": ["建议编号", "建议内容", "执行前置条件", "仍需人工确认"],
            "template_items": [
                "仅提出低风险只读完善建议。",
                "任何发送、触发、交易、登录、面板修改或服务重载建议均标记为禁止。",
            ],
        },
    }
    return {
        "name": "低风险只读调度器周报草稿模板",
        "generated_at": generated_at,
        "template_version": "v1-local-weekly-report-no-send",
        "report_type": "weekly_report_draft_template",
        "required_sections": list(sections.keys()),
        "sections": sections,
        "hard_red_line_confirmation": safety_flags(),
        **safety_flags(),
    }


def build_sample(generated_at: str) -> dict[str, Any]:
    return {
        "name": "低风险只读调度器周报草稿样本",
        "generated_at": generated_at,
        "report_id": "LR-RO-SCHED-WEEKLY-LOCAL-001",
        "report_count": 1,
        "report_period": {
            "week_label": "本周本地预演样本",
            "start_date": "2026-05-04",
            "end_date": "2026-05-08",
            "timezone": "Asia/Shanghai",
        },
        "sections": {
            "本周总览": [
                "本周仅汇总低风险只读调度器本地草稿与预演结果。",
                "周报处于草稿封存状态，不发送企业微信，不触发 n8n，不写总管面板。",
            ],
            "通过趋势": [
                {"batch": "本地值守摘要", "passed": 1, "paused": 0, "pending_confirmation": 1},
                {"batch": "证据留存到期检查", "passed": 1, "paused": 0, "pending_confirmation": 1},
                {"batch": "周报草稿封存", "passed": 1, "paused": 0, "pending_confirmation": 0},
            ],
            "暂停/确认队列": [
                {
                    "queue_id": "WEEKLY-CONFIRM-001",
                    "item": "是否继续保持企业微信与 n8n 禁用态",
                    "status": "待总管人工确认",
                    "requires_supervisor_confirmation": True,
                    "auto_execute": False,
                },
                {
                    "queue_id": "WEEKLY-PAUSE-001",
                    "item": "真实发送、网络请求、服务重载、面板写入",
                    "status": "已暂停且封存",
                    "requires_supervisor_confirmation": True,
                    "auto_execute": False,
                },
            ],
            "证据留存": [
                {
                    "evidence_id": "WEEKLY-EVD-001",
                    "type": "周报草稿样本 JSON/MD",
                    "retention": "本地 122 数据包封存",
                },
                {
                    "evidence_id": "WEEKLY-EVD-002",
                    "type": "不发送封存证明 JSON/MD",
                    "retention": "本地 122 数据包封存",
                },
                {
                    "evidence_id": "WEEKLY-EVD-003",
                    "type": "固定验收日志",
                    "retention": "固定验收目录封存",
                },
            ],
            "下周建议": [
                "继续只读汇总通过趋势和暂停/确认队列。",
                "如需扩大来源，先补充人工确认清单，不接入真实发送或外部触发。",
                "保持 send_allowed=false、real_send=false、modify_supervisor_panel=false。",
            ],
        },
        "hard_red_line_confirmation": safety_flags(),
        **safety_flags(),
    }


def build_proof(generated_at: str) -> dict[str, Any]:
    return {
        "name": "低风险只读调度器周报草稿不发送封存证明",
        "generated_at": generated_at,
        "proof_type": "local_no_send_seal",
        "proof_scope": "证明周报草稿与样本只落本地文件，不发送企业微信，不触发 n8n，不发起网络请求。",
        "no_wecom_send": True,
        "no_n8n_trigger": True,
        "no_network_request": True,
        "sealed_locally": True,
        "seal_items": [
            "周报草稿模板 JSON/MD 已落本地 122 数据包。",
            "周报草稿样本 JSON/MD 已落本地 122 数据包。",
            "不发送封存证明 JSON/MD 已落本地 122 数据包。",
            "脚本仅使用 json、datetime、pathlib、hashlib 等本地标准库。",
        ],
        "hard_red_line_confirmation": safety_flags(),
        **safety_flags(),
    }


def template_md(template: dict[str, Any]) -> str:
    lines = [
        "# 低风险只读调度器周报草稿模板",
        "",
        f"- 生成时间: {template['generated_at']}",
        "- send_allowed: false",
        "- real_send: false",
        "- modify_supervisor_panel: false",
        "- no_network_request: true",
        "",
    ]
    for section_name in template["required_sections"]:
        section = template["sections"][section_name]
        lines.extend([f"## {section_name}", "", f"- 字段: {', '.join(section['fields'])}"])
        lines.extend(f"- {item}" for item in section["template_items"])
        lines.append("")
    return "\n".join(lines)


def sample_md(sample: dict[str, Any]) -> str:
    lines = [
        "# 低风险只读调度器周报草稿样本",
        "",
        f"- 生成时间: {sample['generated_at']}",
        f"- report_id: {sample['report_id']}",
        "- send_allowed: false",
        "- real_send: false",
        "- modify_supervisor_panel: false",
        "- network_request: false",
        "",
    ]
    for section_name, content in sample["sections"].items():
        lines.extend([f"## {section_name}", ""])
        for item in content:
            if isinstance(item, dict):
                lines.append("- " + json.dumps(item, ensure_ascii=False, sort_keys=True))
            else:
                lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def proof_md(proof: dict[str, Any]) -> str:
    lines = [
        "# 低风险只读调度器周报草稿不发送封存证明",
        "",
        f"- 生成时间: {proof['generated_at']}",
        "- no_wecom_send: true",
        "- no_n8n_trigger: true",
        "- no_network_request: true",
        "- sealed_locally: true",
        "- real_send: false",
        "- network_request: false",
        "",
        "## 封存项",
        "",
    ]
    lines.extend(f"- {item}" for item in proof["seal_items"])
    lines.append("")
    return "\n".join(lines)


def build_package(generated_at: str) -> dict[str, Any]:
    files = [
        TEMPLATE_JSON,
        TEMPLATE_MD,
        SAMPLE_JSON,
        SAMPLE_MD,
        PROOF_JSON,
        PROOF_MD,
    ]
    artifacts = [{"name": path.name, "path": str(path), "sha256": sha256_file(path)} for path in files]
    return {
        "name": "低风险只读调度器周报草稿与不发送封存包",
        "generated_at": generated_at,
        "target_data_dir": str(DATA_DIR),
        "log_dir": str(LOG_DIR),
        "file_count": len(artifacts),
        "report_count": 1,
        "artifacts": artifacts,
        "template_json": str(TEMPLATE_JSON),
        "sample_json": str(SAMPLE_JSON),
        "proof_json": str(PROOF_JSON),
        "hard_red_line_confirmation": safety_flags(),
        **safety_flags(),
    }


def package_md(package: dict[str, Any]) -> str:
    lines = [
        "# 低风险只读调度器周报草稿与不发送封存包",
        "",
        f"- 生成时间: {package['generated_at']}",
        f"- file_count: {package['file_count']}",
        f"- report_count: {package['report_count']}",
        "- send_allowed: false",
        "- real_send: false",
        "- network_request: false",
        "- modify_supervisor_panel: false",
        "- sealed_locally: true",
        "",
        "| 文件 | sha256 |",
        "| --- | --- |",
    ]
    for artifact in package["artifacts"]:
        lines.append(f"| {artifact['name']} | {artifact['sha256']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    generated_at = now()
    template = build_template(generated_at)
    sample = build_sample(generated_at)
    proof = build_proof(generated_at)

    write_json(TEMPLATE_JSON, template)
    write_text(TEMPLATE_MD, template_md(template))
    write_json(SAMPLE_JSON, sample)
    write_text(SAMPLE_MD, sample_md(sample))
    write_json(PROOF_JSON, proof)
    write_text(PROOF_MD, proof_md(proof))

    package = build_package(generated_at)
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))

    log = {
        "name": "低风险只读调度器周报草稿与不发送封存包生成日志",
        "generated_at": generated_at,
        "pass": True,
        "error_count": 0,
        "output_dir": str(DATA_DIR),
        "report_count": 1,
        "real_send": False,
        "network_request": False,
        "modify_supervisor_panel": False,
        "hard_red_line_confirmation": safety_flags(),
    }
    write_json(GENERATE_LOG, log)
    print(
        json.dumps(
            {
                "pass": True,
                "error_count": 0,
                "report_count": 1,
                "real_send": False,
                "network_request": False,
                "modify_supervisor_panel": False,
                "output": str(PACKAGE_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
