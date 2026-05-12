# -*- coding: utf-8 -*-
"""执行低风险只读调度器本地值守摘要预演。

这里的“执行”仅表示读取本地模板并登记预演结果；不真实发送企业微信，
不触发 n8n，不发起网络请求，不连接任何外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "109低风险只读调度器本地值守摘要与不发送通知包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器本地值守摘要与不发送通知包验收"

BRIEF_JSON = DATA_DIR / "本地值守摘要模板_最新.json"
DRAFT_JSON = DATA_DIR / "通知草稿_最新.json"
PROOF_JSON = DATA_DIR / "不发送证明_最新.json"
PREVIEW_JSON = DATA_DIR / "本地值守摘要预演结果_最新.json"
PREVIEW_MD = DATA_DIR / "本地值守摘要预演结果_最新.md"
PREVIEW_LOG = LOG_DIR / "low-risk-readonly-scheduler-local-brief-no-send-preview-最新.json"


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


def require_false(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not False:
        errors.append(f"{scope}.{key} 必须为 false")


def require_true(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) is not True:
        errors.append(f"{scope}.{key} 必须为 true")


def preview_md(report: dict[str, Any]) -> str:
    lines = [
        "# 低风险只读调度器本地值守摘要预演结果",
        "",
        f"- 生成时间: {report['generated_at']}",
        f"- pass: {str(report['pass']).lower()}",
        f"- error_count: {report['error_count']}",
        f"- draft_count: {report['draft_count']}",
        "- real_send: false",
        "- network_request: false",
        "- trigger_n8n: false",
        "",
        "## 本地值守摘要",
        "",
    ]
    for section in report["brief_sections"]:
        lines.append(f"- {section}")
    lines.extend(["", "## 草稿登记", ""])
    for draft in report["draft_results"]:
        lines.append(f"- {draft['draft_name']}: {draft['preview_status']}, real_send=false")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    generated_at = now()
    errors: list[str] = []
    required_files = [BRIEF_JSON, DRAFT_JSON, PROOF_JSON]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少输入文件: {path}")

    brief = read_json(BRIEF_JSON) if BRIEF_JSON.exists() else {"sections": {}}
    drafts_package = read_json(DRAFT_JSON) if DRAFT_JSON.exists() else {"drafts": []}
    proof = read_json(PROOF_JSON) if PROOF_JSON.exists() else {}

    for scope, data in [("brief", brief), ("drafts_package", drafts_package), ("proof", proof)]:
        require_false(errors, data, "real_send", scope)
        require_false(errors, data, "network_request", scope)
        require_false(errors, data, "trigger_n8n", scope)
        require_true(errors, data, "no_network_request", scope)
        require_true(errors, data, "no_n8n_trigger", scope)
        require_true(errors, data, "no_wecom_send", scope)

    required_sections = ["今日总览", "通过项", "暂停项", "需总管确认项", "下一轮建议"]
    section_names = list(brief.get("sections", {}).keys())
    for section_name in required_sections:
        if section_name not in section_names:
            errors.append(f"本地值守摘要缺少章节: {section_name}")

    drafts = drafts_package.get("drafts", [])
    draft_names = [item.get("draft_name") for item in drafts]
    for required_draft in ["企业微信草稿", "总管本地摘要草稿", "异常升级草稿"]:
        if required_draft not in draft_names:
            errors.append(f"通知草稿缺少: {required_draft}")

    draft_results: list[dict[str, Any]] = []
    for draft in drafts:
        scope = f"draft.{draft.get('draft_name', '<missing>')}"
        require_false(errors, draft, "send_allowed", scope)
        require_false(errors, draft, "real_send", scope)
        require_false(errors, draft, "network_request", scope)
        require_false(errors, draft, "trigger_n8n", scope)
        draft_results.append(
            {
                "draft_id": draft.get("draft_id"),
                "draft_name": draft.get("draft_name"),
                "channel": draft.get("channel"),
                "preview_status": "local_draft_registered_not_sent",
                "send_allowed": False,
                "real_send": False,
                "network_request": False,
                "trigger_n8n": False,
            }
        )

    report = {
        "name": "低风险只读调度器本地值守摘要预演结果",
        "generated_at": generated_at,
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "preview_only": True,
        "local_file_only": True,
        "brief_section_count": len(section_names),
        "brief_sections": section_names,
        "draft_count": len(drafts),
        "draft_results": draft_results,
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
        "scope_statement": "只读读取本地摘要模板和草稿并登记预演结果，不发送、不触发、不联网。",
    }
    write_json(PREVIEW_JSON, report)
    write_text(PREVIEW_MD, preview_md(report))
    write_json(PREVIEW_LOG, report)
    print(
        json.dumps(
            {
                "pass": report["pass"],
                "error_count": report["error_count"],
                "draft_count": report["draft_count"],
                "real_send": False,
                "network_request": False,
                "trigger_n8n": False,
                "output": str(PREVIEW_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
