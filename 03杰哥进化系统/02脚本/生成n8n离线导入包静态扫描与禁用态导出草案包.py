# -*- coding: utf-8 -*-
"""生成 n8n 离线导入包静态扫描与禁用态导出草案包。

本脚本只读取本地离线样例和内置蓝图；不连接 n8n，不触发 webhook，
不请求网络，不写 n8n 配置，不重载服务，不真实发送企业微信。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "87n8n离线导入包静态扫描与禁用态导出草案包"
SOURCE_84_DIR = ROOT / "03数据" / "84n8n离线导入前凭据隔离与启用禁入包"
SOURCE_84_PACKAGE = SOURCE_84_DIR / "n8n离线导入前凭据隔离与启用禁入包_最新.json"

PACKAGE_JSON = DATA_DIR / "n8n离线导入包静态扫描与禁用态导出草案包_最新.json"
PACKAGE_MD = DATA_DIR / "n8n离线导入包静态扫描与禁用态导出草案包_最新.md"
DRAFT_JSON = DATA_DIR / "n8n禁用态离线导入包草案_最新.json"
DRAFT_MD = DATA_DIR / "n8n禁用态离线导入包草案_最新.md"
SCAN_RULES_JSON = DATA_DIR / "静态扫描规则_最新.json"
SOURCE_SUMMARY_JSON = DATA_DIR / "第84包承接摘要_最新.json"

MODE = "offline/disabled_import_static_scan"

GLOBAL_GUARD = {
    "mode": MODE,
    "offline": True,
    "read_only": True,
    "dry_run": True,
    "disabled": True,
    "active": False,
    "webhook_enabled": False,
    "real_trigger": False,
    "credential_values_present": False,
    "import_allowed": False,
    "activation_allowed": False,
    "external_network_action_allowed": False,
    "n8n_connection_allowed": False,
    "n8n_config_write_allowed": False,
    "service_reload_allowed": False,
    "enterprise_wechat_send_allowed": False,
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
    source84 = read_json_if_exists(SOURCE_84_PACKAGE)
    source_acceptance = source84.get("acceptance_requirements", {})
    return guard_copy(
        {
            "name": "第84包导入前凭据隔离承接摘要",
            "generated_at": now_text(),
            "source_package": str(SOURCE_84_PACKAGE),
            "source_exists": SOURCE_84_PACKAGE.exists(),
            "source_status": source84.get("status", "source_not_found"),
            "source_error_count": source84.get("error_count", 0) if source84 else 0,
            "source_import_allowed": source84.get("import_allowed", False),
            "source_activation_allowed": source84.get("activation_allowed", False),
            "source_credential_values_present": source84.get("credential_values_present", False),
            "source_webhook_enabled": source84.get("webhook_enabled", False),
            "source_real_trigger": source84.get("real_trigger", False),
            "source_acceptance_requirements": {
                "import_allowed": source_acceptance.get("import_allowed", False),
                "activation_allowed": source_acceptance.get("activation_allowed", False),
                "credential_values_present": source_acceptance.get("credential_values_present", False),
                "webhook_enabled": source_acceptance.get("webhook_enabled", False),
                "real_trigger": source_acceptance.get("real_trigger", False),
            },
            "carry_forward_policy": "仅承接禁入与凭据隔离结论，不承接任何运行时连接或真实凭据值",
            "fallback_used_when_missing": "使用本包内置禁用态蓝图草案",
            "error_count": 0,
        }
    )


def build_disabled_node(node_id: str, name: str, purpose: str, operation: str) -> dict[str, Any]:
    return guard_copy(
        {
            "id": node_id,
            "name": name,
            "type": "disabled.placeholder",
            "purpose": purpose,
            "operation": operation,
            "disabled": True,
            "active": False,
            "webhook_enabled": False,
            "real_trigger": False,
            "credential_values_present": False,
            "external_network_action_allowed": False,
            "enterprise_wechat_send_allowed": False,
            "parameters": {
                "contains_real_url": False,
                "contains_real_secret": False,
                "contains_credential_value": False,
                "uses_placeholder_only": True,
                "runtime_effect": "none",
            },
            "error_count": 0,
        }
    )


def build_draft_package(source_summary: dict[str, Any]) -> dict[str, Any]:
    nodes = [
        build_disabled_node("DRAFT-01", "离线入队占位", "展示离线导入形状，不注册触发器", "manual_review_only"),
        build_disabled_node("DRAFT-02", "凭据隔离占位", "仅保留字段名和隔离状态，不保留真实值", "strip_values_before_import"),
        build_disabled_node("DRAFT-03", "业务处理占位", "保留人工复核步骤草案，不执行自动动作", "disabled_noop"),
        build_disabled_node("DRAFT-04", "企业微信通知占位", "仅标记通知需求，不执行发送动作", "manual_note_only"),
        build_disabled_node("DRAFT-05", "收口记录占位", "离线记录草案状态，不写入 n8n 或外部系统", "local_draft_only"),
    ]
    static_scan_expectations = guard_copy(
        {
            "required_flags": {
                "disabled": True,
                "active": False,
                "webhook_enabled": False,
                "real_trigger": False,
                "credential_values_present": False,
                "import_allowed": False,
                "activation_allowed": False,
            },
            "forbidden_material": [
                "真实 URL",
                "真实密钥值",
                "真实凭据值",
                "启用态触发器",
                "外部网络动作",
                "真实企业微信发送动作",
            ],
            "error_count": 0,
        }
    )
    return guard_copy(
        {
            "name": "n8n禁用态离线导入包草案",
            "version": "offline-disabled-import-draft-static-scan-v1",
            "generated_at": now_text(),
            "status": "draft_disabled_static_scan_ready",
            "draft_only": True,
            "source_summary": source_summary,
            "workflow": {
                "name": "离线禁用态导入草案工作流",
                "disabled": True,
                "active": False,
                "webhook_enabled": False,
                "real_trigger": False,
                "credential_values_present": False,
                "import_allowed": False,
                "activation_allowed": False,
                "nodes": nodes,
                "connections": [],
                "settings": {
                    "execution_order": "disabled_manual_review_only",
                    "save_runtime_data": False,
                    "register_webhook": False,
                    "runtime_effect": "none",
                },
                "error_count": 0,
            },
            "static_scan_expectations": static_scan_expectations,
            "redlines": [
                "不接 n8n",
                "不触发 webhook",
                "不请求网络",
                "不改配置",
                "不重载服务",
                "不真实发送企业微信",
            ],
            "error_count": 0,
        }
    )


def build_scan_rules() -> dict[str, Any]:
    rules = [
        ("SCAN-01", "禁用态完整", "disabled=true 且 active=false"),
        ("SCAN-02", "触发禁用", "webhook_enabled=false 且 real_trigger=false"),
        ("SCAN-03", "凭据隔离", "credential_values_present=false 且无真实凭据值字段"),
        ("SCAN-04", "导入启用双禁", "import_allowed=false 且 activation_allowed=false"),
        ("SCAN-05", "无真实外部地址或密钥形态", "草案文本不得包含真实 URL 或密钥赋值形态"),
        ("SCAN-06", "无外部网络动作", "节点动作不得声明外部网络执行"),
        ("SCAN-07", "无真实企业微信发送动作", "节点不得声明真实企业微信发送执行"),
    ]
    return guard_copy(
        {
            "name": "n8n离线导入包静态扫描规则",
            "generated_at": now_text(),
            "rule_count": len(rules),
            "rules": [
                guard_copy(
                    {
                        "rule_id": rule_id,
                        "title": title,
                        "expectation": expectation,
                        "severity": "blocker",
                        "error_count": 0,
                    }
                )
                for rule_id, title, expectation in rules
            ],
            "error_count": 0,
        }
    )


def build_package(source_summary: dict[str, Any], draft: dict[str, Any], scan_rules: dict[str, Any]) -> dict[str, Any]:
    return guard_copy(
        {
            "name": "n8n离线导入包静态扫描与禁用态导出草案包",
            "version": "offline-disabled-import-static-scan-package-v1",
            "generated_at": now_text(),
            "status": "ready_for_offline_static_scan",
            "source_summary": source_summary,
            "draft_import_package": draft,
            "scan_rules": scan_rules,
            "acceptance_requirements": {
                "draft_json_exists": True,
                "draft_markdown_exists": True,
                "disabled": True,
                "active": False,
                "webhook_enabled": False,
                "real_trigger": False,
                "credential_values_present": False,
                "import_allowed": False,
                "activation_allowed": False,
                "scan_error_count": 0,
                "error_count": 0,
            },
            "outputs": {
                "package_json": str(PACKAGE_JSON),
                "package_markdown": str(PACKAGE_MD),
                "draft_json": str(DRAFT_JSON),
                "draft_markdown": str(DRAFT_MD),
                "scan_rules_json": str(SCAN_RULES_JSON),
                "source_summary_json": str(SOURCE_SUMMARY_JSON),
            },
            "error_count": 0,
        }
    )


def build_draft_md(draft: dict[str, Any]) -> str:
    workflow = draft["workflow"]
    lines = [
        "# n8n 禁用态离线导入包草案",
        "",
        f"- 生成时间：{draft['generated_at']}",
        f"- 状态：{draft['status']}",
        "- disabled=true",
        "- active=false",
        "- webhook_enabled=false",
        "- real_trigger=false",
        "- credential_values_present=false",
        "- import_allowed=false",
        "- activation_allowed=false",
        "- error_count=0",
        "",
        "| 节点 | 类型 | 动作 | disabled | active |",
        "| --- | --- | --- | --- | --- |",
    ]
    for node in workflow["nodes"]:
        lines.append(f"| {node['name']} | {node['type']} | {node['operation']} | {node['disabled']} | {node['active']} |")
    lines.append("")
    lines.append("红线：不接 n8n；不触发 webhook；不请求网络；不改配置；不重载服务；不真实发送企业微信。")
    lines.append("")
    return "\n".join(lines)


def build_package_md(package: dict[str, Any]) -> str:
    lines = [
        "# n8n 离线导入包静态扫描与禁用态导出草案包",
        "",
        f"- 生成时间：{package['generated_at']}",
        f"- 状态：{package['status']}",
        "- disabled=true",
        "- active=false",
        "- webhook_enabled=false",
        "- real_trigger=false",
        "- credential_values_present=false",
        "- import_allowed=false",
        "- activation_allowed=false",
        "- scan_error_count=0",
        "- error_count=0",
        "",
        "## 产物",
        "",
        f"- 草案 JSON：{package['outputs']['draft_json']}",
        f"- 草案 MD：{package['outputs']['draft_markdown']}",
        f"- 扫描规则：{package['outputs']['scan_rules_json']}",
        f"- 第84包承接摘要：{package['outputs']['source_summary_json']}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    source_summary = build_source_summary()
    draft = build_draft_package(source_summary)
    scan_rules = build_scan_rules()
    package = build_package(source_summary, draft, scan_rules)

    write_json(SOURCE_SUMMARY_JSON, source_summary)
    write_json(DRAFT_JSON, draft)
    write_text(DRAFT_MD, build_draft_md(draft))
    write_json(SCAN_RULES_JSON, scan_rules)
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, build_package_md(package))

    print(
        json.dumps(
            {
                "status": package["status"],
                "disabled": package["disabled"],
                "active": package["active"],
                "webhook_enabled": package["webhook_enabled"],
                "real_trigger": package["real_trigger"],
                "credential_values_present": package["credential_values_present"],
                "import_allowed": package["import_allowed"],
                "activation_allowed": package["activation_allowed"],
                "error_count": package["error_count"],
                "output": str(PACKAGE_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
