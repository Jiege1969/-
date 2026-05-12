# -*- coding: utf-8 -*-
"""验证三业务正式规则申请人工签收流转与回滚校验包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "90三业务正式规则申请人工签收流转与回滚校验包"
LOG_DIR = ROOT / "04日志" / "三业务正式规则申请人工签收流转与回滚校验包验收"

PACKAGE_JSON = DATA_DIR / "三业务正式规则申请人工签收流转与回滚校验包_最新.json"
FLOW_JSON = DATA_DIR / "人工签收流转定义_最新.json"
FLOW_MD = DATA_DIR / "人工签收流转定义_最新.md"
ROLLBACK_JSON = DATA_DIR / "回滚校验清单_最新.json"
ROLLBACK_MD = DATA_DIR / "回滚校验清单_最新.md"
READONLY_REPORT_JSON = DATA_DIR / "只读校验报告_最新.json"
READONLY_REPORT_MD = DATA_DIR / "只读校验报告_最新.md"
LOG_JSON = LOG_DIR / "three-business-rule-signoff-flow-rollback-verify-最新.json"

REQUIRED_OUTPUTS = [
    PACKAGE_JSON,
    FLOW_JSON,
    FLOW_MD,
    ROLLBACK_JSON,
    ROLLBACK_MD,
    READONLY_REPORT_JSON,
    READONLY_REPORT_MD,
]
REQUIRED_BUSINESSES = {"税收", "股票", "视频"}
REQUIRED_STATES = {"待签收", "需补正", "总管已确认", "可申请正式生效", "已驳回", "回滚待确认"}
REQUIRED_FLAGS = {
    "formal_rule_effective": False,
    "write_formal_rule": False,
    "auto_apply": False,
    "rollback_executed": False,
    "requires_supervisor_confirmation": True,
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_inside_log_dir(path: Path) -> None:
    resolved = path.resolve()
    allowed = LOG_DIR.resolve()
    if resolved != allowed and allowed not in resolved.parents:
        raise ValueError(f"拒绝写入非本包验收日志目录：{resolved}")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    ensure_inside_log_dir(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def require_guard_flags(data: dict[str, Any], name: str, errors: list[str]) -> None:
    flags = data.get("guard_flags", {})
    for key, expected in REQUIRED_FLAGS.items():
        if flags.get(key) is not expected:
            errors.append(f"{name} guard_flags.{key} 必须为 {str(expected).lower()}")


def require_report_flags(report: dict[str, Any], errors: list[str]) -> None:
    for key, expected in REQUIRED_FLAGS.items():
        if report.get(key) is not expected:
            errors.append(f"只读校验报告 {key} 必须为 {str(expected).lower()}")
        if report.get("confirmed_flags", {}).get(key) is not expected:
            errors.append(f"只读校验报告 confirmed_flags.{key} 必须为 {str(expected).lower()}")


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_OUTPUTS:
        if not path.exists():
            errors.append(f"必要产物不存在：{path}")

    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    flow = read_json(FLOW_JSON) if FLOW_JSON.exists() else {}
    rollback = read_json(ROLLBACK_JSON) if ROLLBACK_JSON.exists() else {}
    readonly_report = read_json(READONLY_REPORT_JSON) if READONLY_REPORT_JSON.exists() else {}

    for name, data in [("生成包索引", package), ("人工签收流转定义", flow), ("回滚校验清单", rollback)]:
        require_guard_flags(data, name, errors)
    require_report_flags(readonly_report, errors)

    flow_states = {item.get("state") for item in flow.get("states", [])}
    if not REQUIRED_STATES.issubset(flow_states):
        errors.append("人工签收流转定义状态不完整")
    if set(flow.get("required_states", [])) != REQUIRED_STATES:
        errors.append("人工签收流转定义 required_states 不完整")
    if set(flow.get("businesses", [])) != REQUIRED_BUSINESSES:
        errors.append("人工签收流转定义业务覆盖不完整")

    rollback_rows = rollback.get("checklist", [])
    if {row.get("business") for row in rollback_rows} != REQUIRED_BUSINESSES:
        errors.append("回滚校验清单必须覆盖税收、股票、视频")
    for row in rollback_rows:
        business = row.get("business", "UNKNOWN")
        if not row.get("rollback_entry"):
            errors.append(f"{business} 缺少回滚入口")
        if not row.get("pre_rollback_snapshot"):
            errors.append(f"{business} 缺少回滚前快照")
        if not row.get("post_rollback_acceptance"):
            errors.append(f"{business} 缺少回滚后验收")
        redline = row.get("redline_recheck", [])
        for text in [
            "formal_rule_effective=false",
            "write_formal_rule=false",
            "auto_apply=false",
            "rollback_executed=false",
            "requires_supervisor_confirmation=true",
        ]:
            if text not in redline:
                errors.append(f"{business} 红线复核缺少 {text}")

    if readonly_report.get("passed") is not True:
        errors.append("只读校验报告 passed 必须为 true")
    if readonly_report.get("error_count") != 0:
        errors.append("只读校验报告 error_count 必须为 0")
    if readonly_report.get("read_only") is not True:
        errors.append("只读校验报告 read_only 必须为 true")

    metrics = {
        "flow_states_complete": REQUIRED_STATES.issubset(flow_states),
        "rollback_businesses_complete": {row.get("business") for row in rollback_rows} == REQUIRED_BUSINESSES,
        "readonly_report_error_count_zero": readonly_report.get("error_count") == 0,
        "formal_rule_effective_false": readonly_report.get("formal_rule_effective") is False,
        "write_formal_rule_false": readonly_report.get("write_formal_rule") is False,
        "auto_apply_false": readonly_report.get("auto_apply") is False,
        "rollback_executed_false": readonly_report.get("rollback_executed") is False,
        "requires_supervisor_confirmation_true": readonly_report.get("requires_supervisor_confirmation") is True,
    }
    report = {
        "name": "三业务正式规则申请人工签收流转与回滚校验包验收",
        "verified_at": now_text(),
        "passed": len(errors) == 0,
        "error_count": len(errors),
        "错误数": len(errors),
        "errors": errors,
        "businesses": sorted(REQUIRED_BUSINESSES),
        "states": sorted(REQUIRED_STATES),
        "metrics": metrics,
        "files": {
            "package": str(PACKAGE_JSON),
            "flow_json": str(FLOW_JSON),
            "flow_md": str(FLOW_MD),
            "rollback_json": str(ROLLBACK_JSON),
            "rollback_md": str(ROLLBACK_MD),
            "readonly_report_json": str(READONLY_REPORT_JSON),
            "readonly_report_md": str(READONLY_REPORT_MD),
            "acceptance_log": str(LOG_JSON),
        },
    }

    write_json(LOG_JSON, report)
    print(json.dumps({"通过": report["passed"], "错误数": report["error_count"], "日志": str(LOG_JSON)}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
