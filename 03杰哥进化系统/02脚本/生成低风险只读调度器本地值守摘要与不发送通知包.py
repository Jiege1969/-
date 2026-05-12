# -*- coding: utf-8 -*-
"""生成低风险只读调度器本地值守摘要与不发送通知包。

本脚本只写入本地 JSON/MD 模板和证明文件；不发送企业微信，不触发 n8n，
不发起网络请求，不连接券商、税局或财税软件，不改正式规则和运行面板。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "109低风险只读调度器本地值守摘要与不发送通知包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器本地值守摘要与不发送通知包验收"

BRIEF_JSON = DATA_DIR / "本地值守摘要模板_最新.json"
BRIEF_MD = DATA_DIR / "本地值守摘要模板_最新.md"
DRAFT_JSON = DATA_DIR / "通知草稿_最新.json"
DRAFT_MD = DATA_DIR / "通知草稿_最新.md"
PROOF_JSON = DATA_DIR / "不发送证明_最新.json"
PROOF_MD = DATA_DIR / "不发送证明_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器本地值守摘要与不发送通知包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器本地值守摘要与不发送通知包_最新.md"
GENERATE_LOG = LOG_DIR / "low-risk-readonly-scheduler-local-brief-no-send-generate-最新.json"


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
        "send_allowed": False,
        "real_send": False,
        "real_wecom_send": False,
        "network_request": False,
        "no_network_request": True,
        "connect_n8n": False,
        "trigger_n8n": False,
        "no_n8n_trigger": True,
        "no_wecom_send": True,
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


def build_brief(generated_at: str) -> dict[str, Any]:
    return {
        "name": "低风险只读调度器本地值守摘要模板",
        "generated_at": generated_at,
        "template_version": "v1-local-readonly-no-send",
        "summary_scope": "本地值守摘要模板，仅用于总管本地查看和下一轮人工确认参考",
        "readonly_scheduler": True,
        "template_only": True,
        "sections": {
            "今日总览": {
                "section_order": 1,
                "items": [
                    "只读调度器处于本地值守摘要预演状态",
                    "本包仅登记摘要字段、通知草稿和不发送证明",
                    "全部外部通知与接口触发保持禁用",
                ],
            },
            "通过项": {
                "section_order": 2,
                "items": [
                    "本地摘要模板已生成",
                    "通知草稿仅保存为本地文件",
                    "不发送证明已显式记录 no_wecom_send/no_n8n_trigger/no_network_request",
                ],
            },
            "暂停项": {
                "section_order": 3,
                "items": [
                    "企业微信真实发送暂停",
                    "n8n 触发和消息接口接入暂停",
                    "任何交易、税局登录、财税软件连接和正式规则自动生效均暂停",
                ],
            },
            "需总管确认项": {
                "section_order": 4,
                "items": [
                    "是否允许下一轮继续只读本地值守摘要完善",
                    "是否需要人工补充今日总览中的业务口径",
                    "是否仍保持企业微信与 n8n 的不发送/不触发状态",
                ],
            },
            "下一轮建议": {
                "section_order": 5,
                "items": [
                    "继续只读汇总调度器本地值守结果",
                    "仅在总管明确授权后再讨论通知通道接入",
                    "下一轮优先补齐异常分级口径和人工确认清单",
                ],
            },
        },
        "section_names_required": ["今日总览", "通过项", "暂停项", "需总管确认项", "下一轮建议"],
        "hard_red_line_confirmation": safety_flags(),
        **safety_flags(),
    }


def build_drafts(generated_at: str) -> dict[str, Any]:
    drafts = [
        {
            "draft_id": "wecom-local-draft",
            "draft_name": "企业微信草稿",
            "channel": "企业微信",
            "target": "总管企业微信占位",
            "body_md": "【只读值守摘要草稿】今日仅生成本地摘要和不发送证明，未真实发送企业微信。",
        },
        {
            "draft_id": "supervisor-local-brief-draft",
            "draft_name": "总管本地摘要草稿",
            "channel": "本地摘要",
            "target": "总管本地查看",
            "body_md": "【总管本地摘要】通过项、暂停项、需确认项已写入本地模板，等待人工查看。",
        },
        {
            "draft_id": "exception-escalation-draft",
            "draft_name": "异常升级草稿",
            "channel": "本地异常升级占位",
            "target": "人工确认队列占位",
            "body_md": "【异常升级草稿】若后续发现红线或接口误触发迹象，仅登记本地升级草稿，不外发。",
        },
    ]
    for draft in drafts:
        draft.update(
            {
                "delivery_mode": "local_draft_only",
                "send_allowed": False,
                "real_send": False,
                "real_wecom_send": False,
                "network_request": False,
                "trigger_n8n": False,
                "connect_n8n": False,
                "requires_supervisor_confirmation_before_any_future_send": True,
            }
        )
    return {
        "name": "低风险只读调度器通知草稿",
        "generated_at": generated_at,
        "draft_count": len(drafts),
        "draft_names_required": ["企业微信草稿", "总管本地摘要草稿", "异常升级草稿"],
        "drafts": drafts,
        "hard_red_line_confirmation": safety_flags(),
        **safety_flags(),
    }


def build_no_send_proof(generated_at: str) -> dict[str, Any]:
    return {
        "name": "低风险只读调度器不发送证明",
        "generated_at": generated_at,
        "proof_scope": "证明本包只生成本地文件，不发送企业微信，不触发 n8n，不发起网络请求",
        "no_wecom_send": True,
        "no_n8n_trigger": True,
        "no_network_request": True,
        "real_send": False,
        "real_wecom_send": False,
        "send_allowed": False,
        "network_request": False,
        "trigger_n8n": False,
        "connect_n8n": False,
        "evidence": [
            "通知内容仅写入通知草稿 JSON/MD",
            "脚本仅使用 json、datetime、pathlib、hashlib 等本地标准库",
            "未读取或写入任何消息通道密钥、券商、税局或财税软件凭据",
            "验收脚本只检查本地文件字段并写固定验收日志",
        ],
        "hard_red_line_confirmation": safety_flags(),
        **safety_flags(),
    }


def brief_md(brief: dict[str, Any]) -> str:
    lines = [
        "# 低风险只读调度器本地值守摘要模板",
        "",
        f"- 生成时间: {brief['generated_at']}",
        "- readonly_scheduler: true",
        "- send_allowed: false",
        "- real_send: false",
        "- network_request: false",
        "- trigger_n8n: false",
        "",
    ]
    for section_name in brief["section_names_required"]:
        lines.extend([f"## {section_name}", ""])
        for item in brief["sections"][section_name]["items"]:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def drafts_md(drafts_package: dict[str, Any]) -> str:
    lines = [
        "# 低风险只读调度器通知草稿",
        "",
        f"- 生成时间: {drafts_package['generated_at']}",
        f"- draft_count: {drafts_package['draft_count']}",
        "- send_allowed: false",
        "- real_send: false",
        "- network_request: false",
        "- trigger_n8n: false",
        "",
    ]
    for draft in drafts_package["drafts"]:
        lines.extend(
            [
                f"## {draft['draft_name']}",
                "",
                f"- channel: {draft['channel']}",
                f"- delivery_mode: {draft['delivery_mode']}",
                "- send_allowed: false",
                "- real_send: false",
                "- network_request: false",
                "- trigger_n8n: false",
                "",
                draft["body_md"],
                "",
            ]
        )
    return "\n".join(lines)


def proof_md(proof: dict[str, Any]) -> str:
    lines = [
        "# 低风险只读调度器不发送证明",
        "",
        f"- 生成时间: {proof['generated_at']}",
        "- no_wecom_send: true",
        "- no_n8n_trigger: true",
        "- no_network_request: true",
        "- real_send: false",
        "- network_request: false",
        "- trigger_n8n: false",
        "",
        "## 证明项",
        "",
    ]
    lines.extend(f"- {item}" for item in proof["evidence"])
    lines.append("")
    return "\n".join(lines)


def package_md(package: dict[str, Any]) -> str:
    lines = [
        "# 低风险只读调度器本地值守摘要与不发送通知包",
        "",
        f"- 生成时间: {package['generated_at']}",
        f"- file_count: {package['file_count']}",
        f"- draft_count: {package['draft_count']}",
        "- no_wecom_send: true",
        "- no_n8n_trigger: true",
        "- no_network_request: true",
        "",
        "| 文件 | sha256 |",
        "| --- | --- |",
    ]
    for item in package["files"]:
        lines.append(f"| {item['name']} | {item['sha256']} |")
    lines.append("")
    return "\n".join(lines)


def build_package(generated_at: str, brief: dict[str, Any], drafts: dict[str, Any], proof: dict[str, Any]) -> dict[str, Any]:
    files = [
        {"name": BRIEF_JSON.name, "path": str(BRIEF_JSON), "sha256": sha256_file(BRIEF_JSON)},
        {"name": BRIEF_MD.name, "path": str(BRIEF_MD), "sha256": sha256_file(BRIEF_MD)},
        {"name": DRAFT_JSON.name, "path": str(DRAFT_JSON), "sha256": sha256_file(DRAFT_JSON)},
        {"name": DRAFT_MD.name, "path": str(DRAFT_MD), "sha256": sha256_file(DRAFT_MD)},
        {"name": PROOF_JSON.name, "path": str(PROOF_JSON), "sha256": sha256_file(PROOF_JSON)},
        {"name": PROOF_MD.name, "path": str(PROOF_MD), "sha256": sha256_file(PROOF_MD)},
    ]
    return {
        "name": "低风险只读调度器本地值守摘要与不发送通知包",
        "generated_at": generated_at,
        "file_count": len(files),
        "files": files,
        "brief_section_count": len(brief["section_names_required"]),
        "draft_count": drafts["draft_count"],
        "proof_ready": True,
        "brief_json": str(BRIEF_JSON),
        "draft_json": str(DRAFT_JSON),
        "proof_json": str(PROOF_JSON),
        "hard_red_line_confirmation": safety_flags(),
        **safety_flags(),
    }


def main() -> int:
    generated_at = now()
    brief = build_brief(generated_at)
    drafts = build_drafts(generated_at)
    proof = build_no_send_proof(generated_at)

    write_json(BRIEF_JSON, brief)
    write_text(BRIEF_MD, brief_md(brief))
    write_json(DRAFT_JSON, drafts)
    write_text(DRAFT_MD, drafts_md(drafts))
    write_json(PROOF_JSON, proof)
    write_text(PROOF_MD, proof_md(proof))

    package = build_package(generated_at, brief, drafts, proof)
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))

    log = {
        "name": "低风险只读调度器本地值守摘要与不发送通知包生成日志",
        "generated_at": generated_at,
        "pass": True,
        "error_count": 0,
        "output_dir": str(DATA_DIR),
        "file_count": package["file_count"] + 2,
        "draft_count": drafts["draft_count"],
        "real_send": False,
        "network_request": False,
        "trigger_n8n": False,
        "hard_red_line_confirmation": safety_flags(),
    }
    write_json(GENERATE_LOG, log)
    print(
        json.dumps(
            {
                "pass": True,
                "error_count": 0,
                "draft_count": drafts["draft_count"],
                "real_send": False,
                "network_request": False,
                "trigger_n8n": False,
                "output": str(PACKAGE_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
