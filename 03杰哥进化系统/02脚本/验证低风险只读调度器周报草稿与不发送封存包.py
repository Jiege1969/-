# -*- coding: utf-8 -*-
"""验证低风险只读调度器周报草稿与不发送封存包。"""

from __future__ import annotations

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
PREVIEW_JSON = DATA_DIR / "周报草稿预演结果_最新.json"
PREVIEW_MD = DATA_DIR / "周报草稿预演结果_最新.md"
VERIFY_JSON = LOG_DIR / "low-risk-readonly-scheduler-weekly-report-no-send-verify-最新.json"


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
    for key in ["send_allowed", "real_send", "real_wecom_send", "network_request", "connect_n8n", "trigger_n8n"]:
        require_false(errors, data, key, scope)
    for key in ["no_wecom_send", "no_n8n_trigger", "no_network_request"]:
        require_true(errors, data, key, scope)


def validate_red_lines(errors: list[str], data: dict[str, Any], scope: str) -> None:
    for key in [
        "broker_connection",
        "trade_order",
        "tax_bureau_login",
        "finance_tax_software_connection",
        "auto_promote_formal_rule",
        "write_formal_rule",
        "modify_supervisor_panel",
        "modify_one_click_continuation_package",
        "reload_service",
    ]:
        require_false(errors, data, key, scope)


def main() -> int:
    generated_at = now()
    errors: list[str] = []
    required_files = [
        TEMPLATE_JSON,
        TEMPLATE_MD,
        SAMPLE_JSON,
        SAMPLE_MD,
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

    template = read_json(TEMPLATE_JSON) if TEMPLATE_JSON.exists() else {"sections": {}, "required_sections": []}
    sample = read_json(SAMPLE_JSON) if SAMPLE_JSON.exists() else {"sections": {}}
    proof = read_json(PROOF_JSON) if PROOF_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    preview = read_json(PREVIEW_JSON) if PREVIEW_JSON.exists() else {}

    for scope, data in [
        ("template", template),
        ("sample", sample),
        ("proof", proof),
        ("package", package),
        ("preview", preview),
    ]:
        validate_no_send(errors, data, scope)
        validate_red_lines(errors, data, scope)
        if scope in {"proof", "package", "preview"}:
            require_true(errors, data, "sealed_locally", scope)

    required_sections = ["本周总览", "通过趋势", "暂停/确认队列", "证据留存", "下周建议"]
    template_sections = template.get("required_sections", [])
    sample_sections = list(sample.get("sections", {}).keys())
    for section in required_sections:
        if section not in template_sections:
            errors.append(f"周报草稿模板缺少章节: {section}")
        if section not in sample_sections:
            errors.append(f"周报草稿样本缺少章节: {section}")

    report_count = int(sample.get("report_count", 0) or 0)
    if report_count < 1:
        errors.append("report_count 必须不少于 1")
    if sample.get("send_allowed") is not False:
        errors.append("周报草稿样本 send_allowed 必须为 false")
    if sample.get("real_send") is not False:
        errors.append("周报草稿样本 real_send 必须为 false")
    if sample.get("modify_supervisor_panel") is not False:
        errors.append("周报草稿样本 modify_supervisor_panel 必须为 false")

    for key in ["no_wecom_send", "no_n8n_trigger", "no_network_request", "sealed_locally"]:
        if proof.get(key) is not True:
            errors.append(f"不发送封存证明 {key} 必须为 true")

    if preview.get("pass") is not True:
        errors.append("预演结果 pass 必须为 true")
    if preview.get("error_count") != 0:
        errors.append("预演结果 error_count 必须为 0")
    if preview.get("report_count", 0) < 1:
        errors.append("预演结果 report_count 必须不少于 1")

    verification = {
        "name": "低风险只读调度器周报草稿与不发送封存包验收",
        "generated_at": generated_at,
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "fixed_log_path": str(VERIFY_JSON),
        "target_data_dir": str(DATA_DIR),
        "log_dir": str(LOG_DIR),
        "required_file_count": len(required_files),
        "existing_file_count": sum(1 for path in required_files if path.exists()),
        "required_sections": required_sections,
        "template_sections_present": all(section in template_sections for section in required_sections),
        "sample_sections_present": all(section in sample_sections for section in required_sections),
        "report_count": report_count,
        "proof_checked": proof.get("no_wecom_send") is True
        and proof.get("no_n8n_trigger") is True
        and proof.get("no_network_request") is True
        and proof.get("sealed_locally") is True,
        "preview_checked": preview.get("pass") is True and preview.get("error_count") == 0,
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
        "scope_statement": "仅验收本地周报草稿模板、样本和不发送封存证明；不发送企业微信，不触发 n8n，不联网，不写总管面板。",
    }
    write_json(VERIFY_JSON, verification)
    print(
        json.dumps(
            {
                "pass": verification["pass"],
                "error_count": verification["error_count"],
                "report_count": verification["report_count"],
                "real_send": verification["real_send"],
                "network_request": verification["network_request"],
                "modify_supervisor_panel": verification["modify_supervisor_panel"],
                "log": str(VERIFY_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if verification["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
