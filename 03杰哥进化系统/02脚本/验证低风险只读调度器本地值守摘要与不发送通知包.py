# -*- coding: utf-8 -*-
"""验证低风险只读调度器本地值守摘要与不发送通知包。"""

from __future__ import annotations

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
PREVIEW_JSON = DATA_DIR / "本地值守摘要预演结果_最新.json"
PREVIEW_MD = DATA_DIR / "本地值守摘要预演结果_最新.md"
VERIFY_JSON = LOG_DIR / "low-risk-readonly-scheduler-local-brief-no-send-verify-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def require_false(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not False:
        errors.append(f"{scope}.{key} 必须为 false")


def require_true(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not True:
        errors.append(f"{scope}.{key} 必须为 true")


def validate_no_send(errors: list[str], data: dict[str, Any], scope: str) -> None:
    for key in ["send_allowed", "real_send", "network_request", "trigger_n8n", "connect_n8n"]:
        require_false(errors, data, key, scope)
    for key in ["no_wecom_send", "no_n8n_trigger", "no_network_request"]:
        require_true(errors, data, key, scope)


def main() -> int:
    generated_at = now()
    errors: list[str] = []
    required_files = [
        BRIEF_JSON,
        BRIEF_MD,
        DRAFT_JSON,
        DRAFT_MD,
        PROOF_JSON,
        PROOF_MD,
        PACKAGE_JSON,
        PACKAGE_MD,
        PREVIEW_JSON,
        PREVIEW_MD,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件: {path}")

    brief = read_json(BRIEF_JSON) if BRIEF_JSON.exists() else {"sections": {}}
    drafts_package = read_json(DRAFT_JSON) if DRAFT_JSON.exists() else {"drafts": []}
    proof = read_json(PROOF_JSON) if PROOF_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    preview = read_json(PREVIEW_JSON) if PREVIEW_JSON.exists() else {}

    for scope, data in [
        ("brief", brief),
        ("drafts_package", drafts_package),
        ("proof", proof),
        ("package", package),
        ("preview", preview),
    ]:
        validate_no_send(errors, data, scope)
        require_false(errors, data, "broker_connection", scope)
        require_false(errors, data, "trade_order", scope)
        require_false(errors, data, "tax_bureau_login", scope)
        require_false(errors, data, "finance_tax_software_connection", scope)
        require_false(errors, data, "auto_promote_formal_rule", scope)
        require_false(errors, data, "write_formal_rule", scope)
        require_false(errors, data, "modify_supervisor_panel", scope)
        require_false(errors, data, "modify_one_click_continuation_package", scope)
        require_false(errors, data, "reload_service", scope)

    required_sections = ["今日总览", "通过项", "暂停项", "需总管确认项", "下一轮建议"]
    section_names = list(brief.get("sections", {}).keys())
    for section_name in required_sections:
        if section_name not in section_names:
            errors.append(f"摘要模板缺少章节: {section_name}")

    drafts = drafts_package.get("drafts", [])
    draft_names = [draft.get("draft_name") for draft in drafts]
    for required_draft in ["企业微信草稿", "总管本地摘要草稿", "异常升级草稿"]:
        if required_draft not in draft_names:
            errors.append(f"通知草稿缺少: {required_draft}")

    if len(drafts) < 3:
        errors.append("draft_count 必须不少于 3")
    if drafts_package.get("draft_count") != len(drafts):
        errors.append("drafts_package.draft_count 必须等于 drafts 数量")
    for draft in drafts:
        scope = f"draft.{draft.get('draft_name', '<missing>')}"
        require_false(errors, draft, "send_allowed", scope)
        require_false(errors, draft, "real_send", scope)
        require_false(errors, draft, "real_wecom_send", scope)
        require_false(errors, draft, "network_request", scope)
        require_false(errors, draft, "trigger_n8n", scope)
        require_false(errors, draft, "connect_n8n", scope)

    if proof.get("no_wecom_send") is not True:
        errors.append("不发送证明 no_wecom_send 必须为 true")
    if proof.get("no_n8n_trigger") is not True:
        errors.append("不发送证明 no_n8n_trigger 必须为 true")
    if proof.get("no_network_request") is not True:
        errors.append("不发送证明 no_network_request 必须为 true")

    if preview.get("pass") is not True:
        errors.append("预演结果 pass 必须为 true")
    if preview.get("error_count") != 0:
        errors.append("预演结果 error_count 必须为 0")
    if preview.get("draft_count", 0) < 3:
        errors.append("预演结果 draft_count 必须不少于 3")

    verification = {
        "name": "低风险只读调度器本地值守摘要与不发送通知包验收",
        "generated_at": generated_at,
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "fixed_log_path": str(VERIFY_JSON),
        "required_file_count": len(required_files),
        "existing_file_count": sum(1 for path in required_files if path.exists()),
        "brief_section_count": len(section_names),
        "required_sections_present": all(section in section_names for section in required_sections),
        "draft_count": len(drafts),
        "required_drafts_present": all(name in draft_names for name in ["企业微信草稿", "总管本地摘要草稿", "异常升级草稿"]),
        "proof_checked": proof.get("no_wecom_send") is True
        and proof.get("no_n8n_trigger") is True
        and proof.get("no_network_request") is True,
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
        "scope_statement": "仅验收本地值守摘要模板、通知草稿和不发送证明；不发送企业微信，不触发 n8n，不联网。",
    }
    write_json(VERIFY_JSON, verification)
    print(
        json.dumps(
            {
                "pass": verification["pass"],
                "error_count": verification["error_count"],
                "draft_count": verification["draft_count"],
                "real_send": verification["real_send"],
                "network_request": verification["network_request"],
                "trigger_n8n": verification["trigger_n8n"],
                "log": str(VERIFY_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if verification["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
