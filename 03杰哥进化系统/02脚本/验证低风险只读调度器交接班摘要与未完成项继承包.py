# -*- coding: utf-8 -*-
"""验证低风险只读调度器交接班摘要与未完成项继承包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "117低风险只读调度器交接班摘要与未完成项继承包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器交接班摘要与未完成项继承包验收"

SUMMARY_JSON = DATA_DIR / "交接班摘要_最新.json"
SUMMARY_MD = DATA_DIR / "交接班摘要_最新.md"
INHERIT_JSON = DATA_DIR / "未完成项继承清单_最新.json"
INHERIT_MD = DATA_DIR / "未完成项继承清单_最新.md"
NO_ACTION_JSON = DATA_DIR / "不发送不恢复证明_最新.json"
NO_ACTION_MD = DATA_DIR / "不发送不恢复证明_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器交接班摘要与未完成项继承包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器交接班摘要与未完成项继承包_最新.md"
VERIFY_JSON = LOG_DIR / "low-risk-readonly-scheduler-handoff-inheritance-verify-最新.json"


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


def validate_safety(errors: list[str], data: dict[str, Any], scope: str) -> None:
    for key in [
        "send_allowed",
        "real_send",
        "real_wecom_send",
        "network_request",
        "connect_n8n",
        "trigger_n8n",
        "auto_resume_task",
        "auto_schedule_task",
        "write_formal_rule",
        "auto_promote_formal_rule",
        "modify_supervisor_panel",
        "modify_one_click_continuation_package",
        "reload_service",
        "delete_business_artifact",
        "broker_connection",
        "trade_order",
        "tax_bureau_login",
        "finance_tax_software_connection",
    ]:
        require_false(errors, data, key, scope)
    for key in [
        "readonly_only",
        "local_file_only",
        "handoff_summary_only",
        "inheritance_preview_only",
        "no_network_request",
        "no_n8n_trigger",
    ]:
        require_true(errors, data, key, scope)


def main() -> int:
    errors: list[str] = []
    required_files = [
        SUMMARY_JSON,
        SUMMARY_MD,
        INHERIT_JSON,
        INHERIT_MD,
        NO_ACTION_JSON,
        NO_ACTION_MD,
        PACKAGE_JSON,
        PACKAGE_MD,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件：{path}")

    summary = read_json(SUMMARY_JSON) if SUMMARY_JSON.exists() else {}
    inheritance = read_json(INHERIT_JSON) if INHERIT_JSON.exists() else {"继承项": []}
    proof = read_json(NO_ACTION_JSON) if NO_ACTION_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}

    for scope, data in [
        ("summary", summary),
        ("inheritance", inheritance),
        ("proof", proof),
        ("package", package),
    ]:
        validate_safety(errors, data, scope)

    if package.get("状态") != "low_risk_readonly_scheduler_handoff_inheritance_ready":
        errors.append("总包状态不正确")
    if package.get("数据目录") != str(DATA_DIR):
        errors.append("总包数据目录不是 117 目录")
    if "113" in str(package.get("数据目录", "")):
        errors.append("总包数据目录误指向 113")
    if package.get("历史目录保护", {}).get("本次写入113目录") is not False:
        errors.append("历史目录保护字段未证明本次不写入 113")

    items = inheritance.get("继承项", [])
    if len(items) < 4:
        errors.append("继承项数量不足 4")
    if not any(item.get("需总管确认") is False for item in items):
        errors.append("缺少低风险只读可继续项")
    for item in items:
        if item.get("允许自动恢复") is not False:
            errors.append(f"{item.get('编号', '<missing>')} 允许自动恢复必须为 false")

    required_summary_sections = ["本班已完成", "本班暂停项", "接班关注", "验收口径"]
    for section in required_summary_sections:
        if not summary.get(section):
            errors.append(f"交接班摘要缺少章节：{section}")

    proof_evidence = proof.get("证据", [])
    if len(proof_evidence) < 4:
        errors.append("不发送不恢复证明证据不足")

    verification = {
        "名称": "低风险只读调度器交接班摘要与未完成项继承包验收",
        "生成时间": now(),
        "通过": len(errors) == 0,
        "错误数": len(errors),
        "错误": errors,
        "数据目录": str(DATA_DIR),
        "日志目录": str(LOG_DIR),
        "验证日志": str(VERIFY_JSON),
        "required_file_count": len(required_files),
        "existing_file_count": sum(1 for path in required_files if path.exists()),
        "继承项数量": len(items),
        "低风险只读可继续项数量": sum(1 for item in items if item.get("需总管确认") is False),
        "需总管确认项数量": sum(1 for item in items if item.get("需总管确认") is True),
        "未写入113目录": True,
        "最终验收以117目录为准": True,
        "send_allowed": False,
        "real_send": False,
        "real_wecom_send": False,
        "network_request": False,
        "connect_n8n": False,
        "trigger_n8n": False,
        "auto_resume_task": False,
        "auto_schedule_task": False,
        "write_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
        "reload_service": False,
    }
    write_json(VERIFY_JSON, verification)
    print(
        json.dumps(
            {
                "通过": verification["通过"],
                "错误数": verification["错误数"],
                "数据目录": verification["数据目录"],
                "验证日志": verification["验证日志"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if verification["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
