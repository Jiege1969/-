# -*- coding: utf-8 -*-
"""验证低风险自主命令白名单与红线静态扫描包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "101低风险自主命令白名单与红线静态扫描包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险自主命令白名单与红线静态扫描包验收"

WHITELIST_JSON = DATA_DIR / "低风险自主命令白名单_最新.json"
WHITELIST_MD = DATA_DIR / "低风险自主命令白名单_最新.md"
REDLINE_JSON = DATA_DIR / "低风险自主命令红线静态扫描规则_最新.json"
REDLINE_MD = DATA_DIR / "低风险自主命令红线静态扫描规则_最新.md"
SAMPLE_COMMANDS_JSON = DATA_DIR / "本包样例候选命令_最新.json"
SAMPLE_COMMANDS_MD = DATA_DIR / "本包样例候选命令_最新.md"
REPORT_JSON = DATA_DIR / "低风险自主命令红线静态扫描报告_最新.json"
REPORT_MD = DATA_DIR / "低风险自主命令红线静态扫描报告_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险自主命令白名单与红线静态扫描包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险自主命令白名单与红线静态扫描包_最新.md"
VERIFY_JSON = LOG_DIR / "low-risk-autonomous-command-whitelist-redline-scan-verify-最新.json"


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


def require_zero(errors: list[str], data: dict[str, Any], key: str, scope: str) -> None:
    if data.get(key) != 0:
        errors.append(f"{scope}.{key} 必须为 0")


def main() -> int:
    generated_at = now()
    errors: list[str] = []
    required_files = [
        WHITELIST_JSON,
        WHITELIST_MD,
        REDLINE_JSON,
        REDLINE_MD,
        SAMPLE_COMMANDS_JSON,
        SAMPLE_COMMANDS_MD,
        REPORT_JSON,
        REPORT_MD,
        PACKAGE_JSON,
        PACKAGE_MD,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件: {path}")

    whitelist = read_json(WHITELIST_JSON) if WHITELIST_JSON.exists() else {}
    redline = read_json(REDLINE_JSON) if REDLINE_JSON.exists() else {}
    samples = read_json(SAMPLE_COMMANDS_JSON) if SAMPLE_COMMANDS_JSON.exists() else {}
    report = read_json(REPORT_JSON) if REPORT_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}

    allowed_ids = {item.get("id") for item in whitelist.get("allowed_command_families", [])}
    required_allowed = {
        "python_readonly_acceptance_script",
        "python_snapshot_generator",
        "python_status_package_generator",
    }
    missing_allowed = sorted(required_allowed - allowed_ids)
    if missing_allowed:
        errors.append(f"白名单缺少允许族: {missing_allowed}")

    for key in ["redline_terms", "path_redlines", "port_reload_redlines", "external_interface_redlines"]:
        if not redline.get(key):
            errors.append(f"红线规则缺少或为空: {key}")

    explicit_denies = "\n".join(str(item) for item in whitelist.get("explicit_denies", []))
    for phrase in ["Start-Process", "企业微信", "n8n", "券商", "税局", "财税软件", "正式规则", "总管面板", "一键接续包"]:
        if phrase not in explicit_denies and phrase not in json.dumps(redline, ensure_ascii=False):
            errors.append(f"禁止项未覆盖: {phrase}")

    if samples.get("candidate_count", 0) < 4:
        errors.append("样例候选命令数量不足 4")

    if report.get("pass") is not True:
        errors.append("扫描报告必须 pass=true")
    require_zero(errors, report, "error_count", "report")
    require_zero(errors, report, "violation_count", "report")
    require_false(errors, report, "commands_executed", "report")
    require_false(errors, report, "external_call", "report")
    require_false(errors, report, "reload_service", "report")

    for item in report.get("scan_results", []):
        item_id = item.get("id", "<missing>")
        require_zero(errors, item, "violation_count", item_id)
        require_false(errors, item, "command_executed", item_id)
        if item.get("decision") != "allow":
            errors.append(f"{item_id}.decision 必须为 allow")

    for scope, data in [("package", package), ("samples", samples), ("report", report)]:
        require_false(errors, data, "commands_executed", scope)
        require_false(errors, data, "external_call", scope)
        require_false(errors, data, "reload_service", scope)

    verification = {
        "name": "低风险自主命令白名单与红线静态扫描包验收",
        "generated_at": generated_at,
        "pass": len(errors) == 0,
        "error_count": len(errors),
        "violation_count": report.get("violation_count", -1),
        "errors": errors,
        "fixed_log_path": str(VERIFY_JSON),
        "required_file_count": len(required_files),
        "existing_file_count": sum(1 for path in required_files if path.exists()),
        "allowed_family_count": len(allowed_ids),
        "candidate_count": report.get("candidate_count", 0),
        "commands_executed": False,
        "external_call": False,
        "reload_service": False,
        "real_wecom_send": False,
        "connect_n8n": False,
        "connect_broker": False,
        "trade_order": False,
        "login_tax_bureau": False,
        "connect_finance_tax_software": False,
        "write_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
        "scope_statement": "仅静态扫描草案命令文本，未执行候选命令，未调用外部接口，未重载服务。",
    }
    write_json(VERIFY_JSON, verification)
    print(json.dumps({"pass": verification["pass"], "error_count": verification["error_count"], "violation_count": verification["violation_count"], "log": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if verification["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
