# -*- coding: utf-8 -*-
"""生成 n8n 禁用态导入草案人工签收与回滚演练包。

本脚本只读承接第87包本地材料；不连接 n8n，不触发 webhook，不请求网络，
不真实发送企业微信，不修改运行配置，不重载服务，不写正式规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "91n8n禁用态导入草案人工签收与回滚演练包"
SOURCE_87_DIR = ROOT / "03数据" / "87n8n离线导入包静态扫描与禁用态导出草案包"
SOURCE_87_PACKAGE = SOURCE_87_DIR / "n8n离线导入包静态扫描与禁用态导出草案包_最新.json"
SOURCE_87_DRAFT = SOURCE_87_DIR / "n8n禁用态离线导入包草案_最新.json"
SOURCE_87_SCAN = SOURCE_87_DIR / "n8n离线导入包静态扫描报告_最新.json"

PACKAGE_JSON = DATA_DIR / "n8n禁用态导入草案人工签收与回滚演练包_最新.json"
PACKAGE_MD = DATA_DIR / "n8n禁用态导入草案人工签收与回滚演练包_最新.md"
SOURCE_SUMMARY_JSON = DATA_DIR / "第87包承接摘要_最新.json"
SIGNOFF_JSON = DATA_DIR / "n8n禁用态导入草案人工签收单_最新.json"
SIGNOFF_MD = DATA_DIR / "n8n禁用态导入草案人工签收单_最新.md"
ROLLBACK_JSON = DATA_DIR / "n8n禁用态导入草案禁用态回滚演练_最新.json"
ROLLBACK_MD = DATA_DIR / "n8n禁用态导入草案禁用态回滚演练_最新.md"

MODE = "offline/disabled_import_signoff_rollback_drill"

GLOBAL_GUARD = {
    "mode": MODE,
    "offline": True,
    "read_only": True,
    "dry_run": True,
    "simulation_only": True,
    "disabled": True,
    "active": False,
    "webhook_enabled": False,
    "real_trigger": False,
    "credential_values_present": False,
    "network_request": False,
    "rollback_executed": False,
    "import_allowed": False,
    "activation_allowed": False,
    "requires_supervisor_confirmation": True,
    "n8n_connection_allowed": False,
    "n8n_config_write_allowed": False,
    "service_reload_allowed": False,
    "enterprise_wechat_send_allowed": False,
    "formal_rule_write_allowed": False,
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def guard_copy(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    data = dict(GLOBAL_GUARD)
    if extra:
        data.update(extra)
    return data


def build_source_summary() -> dict[str, Any]:
    package87 = read_json_if_exists(SOURCE_87_PACKAGE)
    draft87 = read_json_if_exists(SOURCE_87_DRAFT)
    scan87 = read_json_if_exists(SOURCE_87_SCAN)
    return guard_copy(
        {
            "name": "第87包承接摘要",
            "generated_at": now_text(),
            "source_package": str(SOURCE_87_PACKAGE),
            "source_draft": str(SOURCE_87_DRAFT),
            "source_scan_report": str(SOURCE_87_SCAN),
            "source_package_exists": SOURCE_87_PACKAGE.exists(),
            "source_draft_exists": SOURCE_87_DRAFT.exists(),
            "source_scan_report_exists": SOURCE_87_SCAN.exists(),
            "source_status": package87.get("status", "source_not_found"),
            "source_scan_status": scan87.get("status", "source_not_found"),
            "source_error_count": package87.get("error_count", 0) if package87 else 0,
            "source_scan_error_count": scan87.get("scan_error_count", scan87.get("error_count", 0)) if scan87 else 0,
            "source_disabled": draft87.get("disabled", True),
            "source_active": draft87.get("active", False),
            "source_webhook_enabled": draft87.get("webhook_enabled", False),
            "source_real_trigger": draft87.get("real_trigger", False),
            "source_credential_values_present": draft87.get("credential_values_present", False),
            "carry_forward_scope": "仅承接第87包禁用态导入草案的静态结论，不承接任何运行时连接、导入或激活动作。",
            "error_count": 0,
        }
    )


def build_signoff(source_summary: dict[str, Any]) -> dict[str, Any]:
    return guard_copy(
        {
            "name": "n8n禁用态导入草案人工签收单",
            "version": "disabled-import-signoff-v1",
            "generated_at": now_text(),
            "status": "unsigned",
            "unsigned": True,
            "signed": False,
            "signer": None,
            "signed_at": None,
            "import_allowed": False,
            "activation_allowed": False,
            "requires_supervisor_confirmation": True,
            "supervisor_confirmation_status": "required_not_provided",
            "confirmation_channels": ["人工复核记录", "主管二次确认记录"],
            "scope": {
                "source_package": "第87包：n8n离线导入包静态扫描与禁用态导出草案包",
                "draft_state": "disabled_import_draft_only",
                "allowed_use": "人工审阅与离线演练",
                "forbidden_use": [
                    "导入 n8n",
                    "激活工作流",
                    "触发 webhook",
                    "请求网络",
                    "发送企业微信",
                    "写入正式规则",
                    "修改运行配置",
                    "重载服务",
                ],
            },
            "required_manual_checks": [
                {
                    "item": "确认导入草案保持 disabled=true 且 active=false",
                    "checked": False,
                    "required_before_import": True,
                },
                {
                    "item": "确认 webhook_enabled=false 且 real_trigger=false",
                    "checked": False,
                    "required_before_import": True,
                },
                {
                    "item": "确认 credential_values_present=false",
                    "checked": False,
                    "required_before_import": True,
                },
                {
                    "item": "主管明确签收前 import_allowed 与 activation_allowed 必须为 false",
                    "checked": False,
                    "required_before_import": True,
                },
            ],
            "source_summary": source_summary,
            "error_count": 0,
        }
    )


def scenario(scenario_id: str, title: str, objective: str, steps: list[str], stop_conditions: list[str]) -> dict[str, Any]:
    return guard_copy(
        {
            "scenario_id": scenario_id,
            "title": title,
            "objective": objective,
            "simulation_only": True,
            "rollback_executed": False,
            "network_request": False,
            "import_allowed": False,
            "activation_allowed": False,
            "preconditions": [
                "仅使用本地 JSON/MD 演练材料",
                "不连接 n8n",
                "不导入草案",
                "不激活任何工作流",
            ],
            "steps": steps,
            "expected_result": {
                "disabled": True,
                "active": False,
                "webhook_enabled": False,
                "real_trigger": False,
                "credential_values_present": False,
                "network_request": False,
                "rollback_executed": False,
            },
            "stop_conditions": stop_conditions,
            "evidence_required": "只读演练报告记录该场景通过，且 error_count=0。",
            "error_count": 0,
        }
    )


def build_rollback_drill(signoff: dict[str, Any]) -> dict[str, Any]:
    scenarios = [
        scenario(
            "DRILL-01",
            "导入前备份",
            "演练在允许导入之前必须存在备份清单与人工签收拦截点。",
            [
                "读取第87包草案路径与本包签收单路径。",
                "记录需备份对象名称、哈希占位和保管责任人字段。",
                "保持签收单 unsigned，import_allowed=false。",
            ],
            ["签收单不是 unsigned", "import_allowed 不是 false", "备份清单字段缺失"],
        ),
        scenario(
            "DRILL-02",
            "导入失败回滚",
            "演练导入失败时的只读回滚剧本，不执行真实导入或回滚。",
            [
                "模拟导入失败状态为 blocked_before_import。",
                "确认禁用态草案仍为 disabled=true、active=false。",
                "记录人工复核应恢复到导入前备份，但 rollback_executed=false。",
            ],
            ["出现真实导入动作", "rollback_executed 变为 true", "network_request 变为 true"],
        ),
        scenario(
            "DRILL-03",
            "误激活回滚",
            "演练误激活时的人工处置顺序，材料层保持 active=false。",
            [
                "模拟误激活发现信号，不访问 n8n。",
                "要求人工确认先禁用工作流，再复核 webhook 和凭据隔离。",
                "本包仅记录演练结论，不修改任何运行配置。",
            ],
            ["activation_allowed 不是 false", "active 不是 false", "service_reload_allowed 不是 false"],
        ),
        scenario(
            "DRILL-04",
            "凭据泄露阻断",
            "演练发现凭据泄露迹象时的阻断清单，草案中不得出现真实凭据值。",
            [
                "扫描签收单、回滚演练与报告字段。",
                "确认 credential_values_present=false。",
                "记录阻断：停止导入、主管确认、重新生成脱敏草案。",
            ],
            ["credential_values_present 不是 false", "出现明文凭据字段值", "network_request 变为 true"],
        ),
    ]
    return guard_copy(
        {
            "name": "n8n禁用态导入草案禁用态回滚演练",
            "version": "disabled-import-rollback-drill-v1",
            "generated_at": now_text(),
            "status": "simulation_ready",
            "simulation_only": True,
            "rollback_executed": False,
            "signoff_status": signoff.get("status"),
            "signoff_required": True,
            "scenarios": scenarios,
            "scenario_count": len(scenarios),
            "acceptance_requirements": {
                "all_scenarios_simulation_only": True,
                "rollback_executed": False,
                "network_request": False,
                "disabled": True,
                "active": False,
                "webhook_enabled": False,
                "real_trigger": False,
                "credential_values_present": False,
                "error_count": 0,
            },
            "error_count": 0,
        }
    )


def build_signoff_md(signoff: dict[str, Any]) -> str:
    checks = "\n".join(f"- [ ] {item['item']}" for item in signoff["required_manual_checks"])
    return "\n".join(
        [
            "# n8n禁用态导入草案人工签收单",
            "",
            f"- 生成时间：{signoff['generated_at']}",
            f"- 状态：{signoff['status']}",
            "- unsigned=true",
            "- import_allowed=false",
            "- activation_allowed=false",
            "- requires_supervisor_confirmation=true",
            "- disabled=true",
            "- active=false",
            "- webhook_enabled=false",
            "- real_trigger=false",
            "- credential_values_present=false",
            "",
            "## 人工签收项",
            checks,
            "",
            "签收结论：未签收，禁止导入，禁止激活。",
            "",
        ]
    )


def build_rollback_md(drill: dict[str, Any]) -> str:
    lines = [
        "# n8n禁用态导入草案禁用态回滚演练",
        "",
        f"- 生成时间：{drill['generated_at']}",
        "- simulation_only=true",
        "- rollback_executed=false",
        "- network_request=false",
        "- disabled=true",
        "- active=false",
        "- webhook_enabled=false",
        "- real_trigger=false",
        "- credential_values_present=false",
        "",
        "| 场景 | simulation_only | rollback_executed | 目标 |",
        "| --- | --- | --- | --- |",
    ]
    for item in drill["scenarios"]:
        lines.append(f"| {item['title']} | {item['simulation_only']} | {item['rollback_executed']} | {item['objective']} |")
    lines.append("")
    return "\n".join(lines)


def build_package_md(package: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# n8n禁用态导入草案人工签收与回滚演练包",
            "",
            f"- 生成时间：{package['generated_at']}",
            f"- 状态：{package['status']}",
            "- read_only=true",
            "- simulation_only=true",
            "- import_allowed=false",
            "- activation_allowed=false",
            "- network_request=false",
            "- rollback_executed=false",
            "- error_count=0",
            "",
            "## 产物",
            f"- 人工签收单：{SIGNOFF_JSON.name} / {SIGNOFF_MD.name}",
            f"- 禁用态回滚演练：{ROLLBACK_JSON.name} / {ROLLBACK_MD.name}",
            "",
        ]
    )


def build_package(source_summary: dict[str, Any], signoff: dict[str, Any], rollback_drill: dict[str, Any]) -> dict[str, Any]:
    return guard_copy(
        {
            "name": "n8n禁用态导入草案人工签收与回滚演练包",
            "version": "disabled-import-signoff-rollback-package-v1",
            "generated_at": now_text(),
            "status": "ready_for_read_only_drill",
            "source_summary": source_summary,
            "signoff": {
                "path": str(SIGNOFF_JSON),
                "status": signoff["status"],
                "unsigned": signoff["unsigned"],
                "import_allowed": False,
                "activation_allowed": False,
                "requires_supervisor_confirmation": True,
            },
            "rollback_drill": {
                "path": str(ROLLBACK_JSON),
                "simulation_only": True,
                "scenario_count": rollback_drill["scenario_count"],
                "rollback_executed": False,
            },
            "acceptance_requirements": {
                "signoff_unsigned": True,
                "import_allowed": False,
                "activation_allowed": False,
                "requires_supervisor_confirmation": True,
                "all_rollback_scenarios_simulation_only": True,
                "disabled": True,
                "active": False,
                "webhook_enabled": False,
                "real_trigger": False,
                "credential_values_present": False,
                "network_request": False,
                "rollback_executed": False,
                "error_count": 0,
            },
            "outputs": {
                "package_json": str(PACKAGE_JSON),
                "package_markdown": str(PACKAGE_MD),
                "source_summary_json": str(SOURCE_SUMMARY_JSON),
                "signoff_json": str(SIGNOFF_JSON),
                "signoff_markdown": str(SIGNOFF_MD),
                "rollback_json": str(ROLLBACK_JSON),
                "rollback_markdown": str(ROLLBACK_MD),
            },
            "error_count": 0,
        }
    )


def main() -> int:
    source_summary = build_source_summary()
    signoff = build_signoff(source_summary)
    rollback_drill = build_rollback_drill(signoff)
    package = build_package(source_summary, signoff, rollback_drill)

    write_json(SOURCE_SUMMARY_JSON, source_summary)
    write_json(SIGNOFF_JSON, signoff)
    write_text(SIGNOFF_MD, build_signoff_md(signoff))
    write_json(ROLLBACK_JSON, rollback_drill)
    write_text(ROLLBACK_MD, build_rollback_md(rollback_drill))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, build_package_md(package))

    print(json.dumps({"status": package["status"], "error_count": 0, "data_dir": str(DATA_DIR)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
