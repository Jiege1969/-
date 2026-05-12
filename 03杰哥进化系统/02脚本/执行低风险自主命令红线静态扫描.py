# -*- coding: utf-8 -*-
"""执行低风险自主命令红线静态扫描。

只扫描草案命令文本，不执行候选命令，不访问网络，不重载服务。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = EVOLUTION_ROOT / "02脚本"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "101低风险自主命令白名单与红线静态扫描包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险自主命令白名单与红线静态扫描包验收"

WHITELIST_JSON = DATA_DIR / "低风险自主命令白名单_最新.json"
REDLINE_JSON = DATA_DIR / "低风险自主命令红线静态扫描规则_最新.json"
SAMPLE_COMMANDS_JSON = DATA_DIR / "本包样例候选命令_最新.json"
REPORT_JSON = DATA_DIR / "低风险自主命令红线静态扫描报告_最新.json"
REPORT_MD = DATA_DIR / "低风险自主命令红线静态扫描报告_最新.md"
RUN_LOG = LOG_DIR / "low-risk-autonomous-command-redline-static-scan-run-最新.json"


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


def norm(text: str) -> str:
    return text.replace("/", "\\").lower()


def extract_python_target(command: str) -> tuple[str | None, str | None]:
    pattern = re.compile(r"^\s*(python|python3|py)(?:\s+-3|\s+-X\s+utf8)?\s+[\"']?(.+?\.py)[\"']?\s*$", re.IGNORECASE)
    match = pattern.match(command.strip())
    if not match:
        return None, None
    return match.group(1).lower(), match.group(2)


def whitelist_category(command: str) -> str | None:
    _runner, target = extract_python_target(command)
    if not target:
        return None
    target_path = Path(target)
    filename = target_path.name
    normalized_target = norm(str(target_path))
    normalized_script_dir = norm(str(SCRIPT_DIR))
    if not normalized_target.startswith(normalized_script_dir):
        return None
    if filename.endswith(".py") and (filename.startswith("验证") or filename.startswith("只读验证")):
        return "python_readonly_acceptance_script"
    if filename.endswith(".py") and filename.startswith("生成") and "快照" in filename:
        return "python_snapshot_generator"
    if filename.endswith(".py") and filename.startswith("生成") and "状态包" in filename:
        return "python_status_package_generator"
    return None


def scan_hits(command: str, rules: dict[str, Any]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    command_lower = command.lower()
    command_norm = norm(command)
    for key in ["redline_terms", "path_redlines", "port_reload_redlines", "external_interface_redlines"]:
        for item in rules.get(key, []):
            needle = str(item)
            haystack = command_norm if "\\" in needle or "/" in needle else command_lower
            normalized_needle = norm(needle) if "\\" in needle or "/" in needle else needle.lower()
            if normalized_needle in haystack:
                hits.append({"rule_group": key, "matched": needle})
    shape_checks = {
        "pipeline": "|",
        "redirect": ">",
        "chain_and": "&&",
        "semicolon": ";",
    }
    for name, token in shape_checks.items():
        if token in command:
            hits.append({"rule_group": "command_shape_denies", "matched": name})
    return hits


def build_report_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['id']} | {item['source_hint']} | {item['whitelist_category'] or 'none'} | {item['redline_hit_count']} | {item['decision']} | `{item['draft_command']}` |"
        for item in report["scan_results"]
    ]
    return "\n".join(
        [
            "# 低风险自主命令红线静态扫描报告",
            "",
            f"- 生成时间: {report['generated_at']}",
            f"- pass: {report['pass']}",
            f"- violation_count: {report['violation_count']}",
            "- commands_executed: false",
            "- external_call: false",
            "- reload_service: false",
            "",
            "| id | source | whitelist_category | redline_hit_count | decision | draft_command |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def main() -> int:
    generated_at = now()
    errors: list[str] = []
    for path in [WHITELIST_JSON, REDLINE_JSON, SAMPLE_COMMANDS_JSON]:
        if not path.exists():
            errors.append(f"缺少输入文件: {path}")

    whitelist = read_json(WHITELIST_JSON) if WHITELIST_JSON.exists() else {}
    redline_rules = read_json(REDLINE_JSON) if REDLINE_JSON.exists() else {}
    sample_commands = read_json(SAMPLE_COMMANDS_JSON) if SAMPLE_COMMANDS_JSON.exists() else {"candidates": []}
    allowed_ids = {item.get("id") for item in whitelist.get("allowed_command_families", [])}

    scan_results: list[dict[str, Any]] = []
    violation_count = 0
    for item in sample_commands.get("candidates", []):
        command = str(item.get("draft_command", ""))
        hits = scan_hits(command, redline_rules)
        category = whitelist_category(command)
        not_whitelisted = category not in allowed_ids
        item_violations = len(hits) + (1 if not_whitelisted else 0)
        violation_count += item_violations
        scan_results.append(
            {
                "id": item.get("id"),
                "source_hint": item.get("source_hint"),
                "draft_command": command,
                "expected_decision": item.get("expected_decision"),
                "whitelist_category": category,
                "not_whitelisted": not_whitelisted,
                "redline_hit_count": len(hits),
                "redline_hits": hits,
                "violation_count": item_violations,
                "decision": "allow" if item_violations == 0 else "block",
                "command_executed": False,
            }
        )

    if not scan_results:
        errors.append("候选命令为空")
    report = {
        "name": "低风险自主命令红线静态扫描报告",
        "generated_at": generated_at,
        "scan_scope": sample_commands.get("source_strategy", "本包内样例命令"),
        "pass": len(errors) == 0 and violation_count == 0,
        "error_count": len(errors),
        "errors": errors,
        "candidate_count": len(scan_results),
        "violation_count": violation_count,
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
        "scan_results": scan_results,
    }
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, build_report_md(report))
    write_json(RUN_LOG, report)
    print(json.dumps({"pass": report["pass"], "error_count": report["error_count"], "violation_count": report["violation_count"], "output": str(REPORT_JSON)}, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
