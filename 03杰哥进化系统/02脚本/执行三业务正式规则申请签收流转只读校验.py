# -*- coding: utf-8 -*-
"""执行三业务正式规则申请签收流转只读校验。

只读取第90包材料与第86包只读产物，生成只读校验报告。
不写正式规则，不自动生效，不执行回滚，不触发任何外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "90三业务正式规则申请人工签收流转与回滚校验包"
SOURCE_86_DIR = ROOT / "03数据" / "86三业务正式规则申请草案冲突扫描与签收台账包"

PACKAGE_JSON = DATA_DIR / "三业务正式规则申请人工签收流转与回滚校验包_最新.json"
FLOW_JSON = DATA_DIR / "人工签收流转定义_最新.json"
FLOW_MD = DATA_DIR / "人工签收流转定义_最新.md"
ROLLBACK_JSON = DATA_DIR / "回滚校验清单_最新.json"
ROLLBACK_MD = DATA_DIR / "回滚校验清单_最新.md"
READONLY_REPORT_JSON = DATA_DIR / "只读校验报告_最新.json"
READONLY_REPORT_MD = DATA_DIR / "只读校验报告_最新.md"

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


def ensure_inside_allowed(path: Path) -> None:
    resolved = path.resolve()
    allowed = DATA_DIR.resolve()
    if resolved != allowed and allowed not in resolved.parents:
        raise ValueError(f"拒绝写入非本包数据目录：{resolved}")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    ensure_inside_allowed(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    ensure_inside_allowed(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def existing_source_86_files() -> list[str]:
    if not SOURCE_86_DIR.exists():
        return []
    return [str(path) for path in sorted(SOURCE_86_DIR.glob("*_最新.json"))]


def check_flags(data: dict[str, Any], name: str, errors: list[str]) -> None:
    flags = data.get("guard_flags", {})
    for key, expected in REQUIRED_FLAGS.items():
        actual = flags.get(key)
        if actual is not expected:
            errors.append(f"{name} guard_flags.{key} 必须为 {str(expected).lower()}")


def report_md(report: dict[str, Any]) -> str:
    flags = report["confirmed_flags"]
    lines = [
        "# 三业务正式规则申请签收流转只读校验报告",
        "",
        f"- 校验时间：{report['checked_at']}",
        f"- 通过：{str(report['passed']).lower()}",
        f"- 错误数：{report['error_count']}",
        f"- formal_rule_effective：{str(flags['formal_rule_effective']).lower()}",
        f"- write_formal_rule：{str(flags['write_formal_rule']).lower()}",
        f"- auto_apply：{str(flags['auto_apply']).lower()}",
        f"- rollback_executed：{str(flags['rollback_executed']).lower()}",
        f"- requires_supervisor_confirmation：{str(flags['requires_supervisor_confirmation']).lower()}",
        "",
        "| 校验项 | 结果 |",
        "| --- | --- |",
    ]
    for key, value in report["checks"].items():
        lines.append(f"| {key} | {str(value).lower()} |")
    if report["errors"]:
        lines.extend(["", "## 错误", ""])
        for error in report["errors"]:
            lines.append(f"- {error}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    errors: list[str] = []
    required_files = [PACKAGE_JSON, FLOW_JSON, FLOW_MD, ROLLBACK_JSON, ROLLBACK_MD]
    for path in required_files:
        if not path.exists():
            errors.append(f"必要输入不存在：{path}")

    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    flow = read_json(FLOW_JSON) if FLOW_JSON.exists() else {}
    rollback = read_json(ROLLBACK_JSON) if ROLLBACK_JSON.exists() else {}

    for name, data in [("生成包索引", package), ("人工签收流转定义", flow), ("回滚校验清单", rollback)]:
        check_flags(data, name, errors)

    flow_states = {item.get("state") for item in flow.get("states", [])}
    if not REQUIRED_STATES.issubset(flow_states):
        errors.append("人工签收流转定义必须包含：待签收、需补正、总管已确认、可申请正式生效、已驳回、回滚待确认")

    flow_businesses = set(flow.get("businesses", []))
    rollback_businesses = {item.get("business") for item in rollback.get("checklist", [])}
    if flow_businesses != REQUIRED_BUSINESSES:
        errors.append("人工签收流转定义必须覆盖税收、股票、视频")
    if rollback_businesses != REQUIRED_BUSINESSES:
        errors.append("回滚校验清单必须覆盖税收、股票、视频")

    for row in rollback.get("checklist", []):
        business = row.get("business", "UNKNOWN")
        for key in ["rollback_entry", "pre_rollback_snapshot", "post_rollback_acceptance", "redline_recheck"]:
            if not row.get(key):
                errors.append(f"{business} 回滚校验缺少 {key}")
        if row.get("rollback_executed") is not False:
            errors.append(f"{business} rollback_executed 必须为 false")
        if row.get("requires_supervisor_confirmation") is not True:
            errors.append(f"{business} requires_supervisor_confirmation 必须为 true")

    source_86_files = existing_source_86_files()
    checks = {
        "package_86_referenced": bool(package.get("based_on_package_86")) and bool(flow.get("based_on_package_86")),
        "source_86_files_exist": bool(source_86_files),
        "flow_states_complete": REQUIRED_STATES.issubset(flow_states),
        "rollback_businesses_complete": rollback_businesses == REQUIRED_BUSINESSES,
        "formal_rule_effective_false": all(
            data.get("guard_flags", {}).get("formal_rule_effective") is False
            for data in [package, flow, rollback]
        ),
        "write_formal_rule_false": all(
            data.get("guard_flags", {}).get("write_formal_rule") is False
            for data in [package, flow, rollback]
        ),
        "auto_apply_false": all(
            data.get("guard_flags", {}).get("auto_apply") is False
            for data in [package, flow, rollback]
        ),
        "rollback_executed_false": all(
            data.get("guard_flags", {}).get("rollback_executed") is False
            for data in [package, flow, rollback]
        ),
        "requires_supervisor_confirmation_true": all(
            data.get("guard_flags", {}).get("requires_supervisor_confirmation") is True
            for data in [package, flow, rollback]
        ),
    }
    for key, ok in checks.items():
        if not ok:
            errors.append(f"只读校验未通过：{key}")

    confirmed_flags = dict(REQUIRED_FLAGS)
    report = {
        "name": "三业务正式规则申请签收流转只读校验报告",
        "checked_at": now_text(),
        "passed": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "read_only": True,
        "based_on_package_86": True,
        "source_86_files": source_86_files,
        "checked_files": [str(path) for path in required_files],
        "businesses": sorted(REQUIRED_BUSINESSES),
        "states": sorted(REQUIRED_STATES),
        "confirmed_flags": confirmed_flags,
        "formal_rule_effective": False,
        "write_formal_rule": False,
        "auto_apply": False,
        "rollback_executed": False,
        "requires_supervisor_confirmation": True,
        "external_actions": {
            "send_wecom": False,
            "connect_n8n": False,
            "connect_broker": False,
            "trade": False,
            "login_tax_bureau": False,
            "connect_tax_software": False,
            "change_supervisor_panel": False,
            "change_one_click_continuation_package": False,
            "reload_service": False,
        },
        "checks": checks,
    }

    write_json(READONLY_REPORT_JSON, report)
    write_text(READONLY_REPORT_MD, report_md(report))
    print(json.dumps({"通过": report["passed"], "错误数": report["error_count"], "报告": str(READONLY_REPORT_JSON)}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
