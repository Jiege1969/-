# -*- coding: utf-8 -*-
"""执行低风险只读调度器周报草稿预演。

这里的“执行”只表示读取 122 本地草稿并生成本地预演结果；不发送企业微信，
不触发 n8n，不发起网络请求，不修改总管面板。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "122低风险只读调度器周报草稿与不发送封存包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器周报草稿与不发送封存包验收"

TEMPLATE_JSON = DATA_DIR / "周报草稿模板_最新.json"
SAMPLE_JSON = DATA_DIR / "周报草稿样本_最新.json"
PROOF_JSON = DATA_DIR / "不发送封存证明_最新.json"
PREVIEW_JSON = DATA_DIR / "周报草稿预演结果_最新.json"
PREVIEW_MD = DATA_DIR / "周报草稿预演结果_最新.md"
PREVIEW_LOG = LOG_DIR / "low-risk-readonly-scheduler-weekly-report-no-send-preview-最新.json"


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


def validate_no_send(errors: list[str], data: dict[str, Any], scope: str) -> None:
    for key in ["send_allowed", "real_send", "real_wecom_send", "network_request", "connect_n8n", "trigger_n8n", "modify_supervisor_panel"]:
        require_false(errors, data, key, scope)
    for key in ["no_wecom_send", "no_n8n_trigger", "no_network_request", "sealed_locally"]:
        require_true(errors, data, key, scope)


def preview_md(report: dict[str, Any]) -> str:
    lines = [
        "# 低风险只读调度器周报草稿预演结果",
        "",
        f"- 生成时间: {report['generated_at']}",
        f"- pass: {str(report['pass']).lower()}",
        f"- error_count: {report['error_count']}",
        f"- report_count: {report['report_count']}",
        "- real_send: false",
        "- network_request: false",
        "- modify_supervisor_panel: false",
        "- sealed_locally: true",
        "",
        "## 章节检查",
        "",
    ]
    lines.extend(f"- {section}" for section in report["sections_checked"])
    lines.extend(["", "## 预演结论", ""])
    lines.extend(f"- {item}" for item in report["preview_conclusions"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    generated_at = now()
    errors: list[str] = []
    for path in [TEMPLATE_JSON, SAMPLE_JSON, PROOF_JSON]:
        if not path.exists():
            errors.append(f"缺少输入文件: {path}")

    template = read_json(TEMPLATE_JSON) if TEMPLATE_JSON.exists() else {"required_sections": []}
    sample = read_json(SAMPLE_JSON) if SAMPLE_JSON.exists() else {"sections": {}}
    proof = read_json(PROOF_JSON) if PROOF_JSON.exists() else {}

    for scope, data in [("template", template), ("sample", sample), ("proof", proof)]:
        validate_no_send(errors, data, scope)

    required_sections = ["本周总览", "通过趋势", "暂停/确认队列", "证据留存", "下周建议"]
    template_sections = template.get("required_sections", [])
    sample_sections = list(sample.get("sections", {}).keys())
    for section in required_sections:
        if section not in template_sections:
            errors.append(f"周报草稿模板缺少章节: {section}")
        if section not in sample_sections:
            errors.append(f"周报草稿样本缺少章节: {section}")

    if sample.get("report_count", 0) < 1:
        errors.append("report_count 必须不少于 1")
    if proof.get("no_wecom_send") is not True:
        errors.append("不发送封存证明 no_wecom_send 必须为 true")
    if proof.get("no_n8n_trigger") is not True:
        errors.append("不发送封存证明 no_n8n_trigger 必须为 true")
    if proof.get("no_network_request") is not True:
        errors.append("不发送封存证明 no_network_request 必须为 true")
    if proof.get("sealed_locally") is not True:
        errors.append("不发送封存证明 sealed_locally 必须为 true")

    report = {
        "name": "低风险只读调度器周报草稿预演结果",
        "generated_at": generated_at,
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "preview_only": True,
        "local_file_only": True,
        "report_count": sample.get("report_count", 0),
        "sections_checked": required_sections,
        "template_sections_present": all(section in template_sections for section in required_sections),
        "sample_sections_present": all(section in sample_sections for section in required_sections),
        "proof_checked": proof.get("no_wecom_send") is True
        and proof.get("no_n8n_trigger") is True
        and proof.get("no_network_request") is True
        and proof.get("sealed_locally") is True,
        "preview_conclusions": [
            "周报草稿模板已按必需章节进行本地只读检查。",
            "周报草稿样本已确认至少 1 份，且保持 send_allowed=false、real_send=false。",
            "不发送封存证明已确认 no_wecom_send=true、no_n8n_trigger=true、no_network_request=true、sealed_locally=true。",
            "预演仅落本地 JSON/MD 和验收日志，不触发外部系统。",
        ],
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
        "scope_statement": "仅读取 122 本地周报草稿与封存证明并写入本地预演结果，不发送、不触发、不联网、不改面板。",
    }
    write_json(PREVIEW_JSON, report)
    write_text(PREVIEW_MD, preview_md(report))
    write_json(PREVIEW_LOG, report)
    print(
        json.dumps(
            {
                "pass": report["pass"],
                "error_count": report["error_count"],
                "report_count": report["report_count"],
                "real_send": False,
                "network_request": False,
                "modify_supervisor_panel": False,
                "output": str(PREVIEW_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
