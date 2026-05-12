# -*- coding: utf-8 -*-
"""生成 n8n 离线导入前凭据隔离与启用禁入包。

只读取离线样例或本包内置蓝图；不连接 n8n，不启用 webhook，不请求网络，
不写 n8n 配置，不重载服务，不真实发送企业微信。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "84n8n离线导入前凭据隔离与启用禁入包"
SOURCE_81_DIR = ROOT / "03数据" / "81n8n离线闸口失败演练与回滚剧本包"
SOURCE_81_PACKAGE = SOURCE_81_DIR / "n8n离线闸口失败演练与回滚剧本包_最新.json"

PACKAGE_JSON = DATA_DIR / "n8n离线导入前凭据隔离与启用禁入包_最新.json"
PACKAGE_MD = DATA_DIR / "n8n离线导入前凭据隔离与启用禁入包_最新.md"
CREDENTIAL_ISOLATION_JSON = DATA_DIR / "凭据字段隔离清单_最新.json"
CREDENTIAL_ISOLATION_MD = DATA_DIR / "凭据字段隔离清单_最新.md"
WEBHOOK_DISABLED_JSON = DATA_DIR / "webhook禁用清单_最新.json"
IMPORT_BAN_JSON = DATA_DIR / "导入前禁入条件_最新.json"
ACTIVATION_CONFIRM_JSON = DATA_DIR / "启用前总管确认项_最新.json"
ROLLBACK_REQUIREMENTS_JSON = DATA_DIR / "回滚要求_最新.json"

MODE = "offline/import_precheck"

GLOBAL_GUARD = {
    "mode": MODE,
    "offline": True,
    "read_only": True,
    "dry_run": True,
    "import_allowed": False,
    "activation_allowed": False,
    "credential_values_present": False,
    "webhook_enabled": False,
    "real_trigger": False,
    "network_request_enabled": False,
    "n8n_connection_enabled": False,
    "n8n_config_write_enabled": False,
    "service_reload_enabled": False,
    "enterprise_wechat_send_enabled": False,
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
    source81 = read_json_if_exists(SOURCE_81_PACKAGE)
    return guard_copy(
        {
            "source_package": "第81包离线闸口失败演练与回滚剧本包",
            "source_exists": SOURCE_81_PACKAGE.exists(),
            "source_status": source81.get("status", ""),
            "source_scenario_count": source81.get("scenario_count", 0),
            "source_error_count": source81.get("error_count", 0) if source81 else 0,
            "fallback_used_when_missing": "本包内置离线蓝图",
        }
    )


def sensitive_slot(slot_id: str, display_name: str, owner: str, reason: str) -> dict[str, Any]:
    return guard_copy(
        {
            "slot_id": slot_id,
            "display_name": display_name,
            "owner": owner,
            "reason": reason,
            "value_present": False,
            "value_storage": "not_collected",
            "value_source": "not_read",
            "import_behavior": "strip_before_import",
            "activation_behavior": "blocked_before_supervisor_confirmation",
            "required_action": "仅保留字段名和隔离理由，不保留真实值",
            "error_count": 0,
        }
    )


def build_credential_isolation() -> dict[str, Any]:
    slots = [
        sensitive_slot("CRED01", "企业微信发送凭据", "notification", "第81包失败演练要求真实发送保持禁入"),
        sensitive_slot("CRED02", "n8n webhook 鉴权凭据", "n8n_webhook", "离线导入前不得携带 webhook 鉴权值"),
        sensitive_slot("CRED03", "外部接口访问凭据", "external_api", "导入前禁止外部请求和外部访问能力"),
        sensitive_slot("CRED04", "数据库连接凭据", "storage", "本包不读取、不迁移、不写入任何连接值"),
        sensitive_slot("CRED05", "人工确认人身份凭据", "supervisor", "总管确认只能作为人工步骤，不允许自动伪造"),
    ]
    return guard_copy(
        {
            "name": "凭据字段隔离清单",
            "generated_at": now_text(),
            "credential_values_present": False,
            "isolation_policy": "field_names_only_no_values",
            "slot_count": len(slots),
            "slots": slots,
            "required_assertions": {
                "no_plain_values": True,
                "no_runtime_lookup": True,
                "no_env_read": True,
                "no_n8n_credential_write": True,
                "manual_fill_required_after_acceptance": True,
            },
            "error_count": 0,
        }
    )


def build_webhook_disabled_list() -> dict[str, Any]:
    items = [
        {
            "webhook_id": "WH01",
            "name": "入队触发 webhook",
            "enabled": False,
            "registered_in_n8n": False,
            "real_trigger": False,
            "ban_reason": "离线导入前只允许蓝图检查，不允许触发入队",
        },
        {
            "webhook_id": "WH02",
            "name": "企业微信反馈 webhook",
            "enabled": False,
            "registered_in_n8n": False,
            "real_trigger": False,
            "ban_reason": "禁止真实发送或接收企业微信链路",
        },
        {
            "webhook_id": "WH03",
            "name": "总管确认 webhook",
            "enabled": False,
            "registered_in_n8n": False,
            "real_trigger": False,
            "ban_reason": "总管确认必须由人工离线确认，不允许 webhook 代替",
        },
    ]
    return guard_copy(
        {
            "name": "webhook禁用清单",
            "generated_at": now_text(),
            "webhook_enabled": False,
            "real_trigger": False,
            "item_count": len(items),
            "items": [guard_copy({**item, "error_count": 0}) for item in items],
            "error_count": 0,
        }
    )


def ban_condition(condition_id: str, title: str, evidence: str, blocks: list[str]) -> dict[str, Any]:
    return guard_copy(
        {
            "condition_id": condition_id,
            "title": title,
            "evidence_required": evidence,
            "decision": "ban_import_and_activation",
            "blocks": blocks,
            "resolved": False,
            "error_count": 0,
        }
    )


def build_import_bans() -> dict[str, Any]:
    conditions = [
        ban_condition("BAN01", "存在凭据真实值", "credential_values_present 必须为 false", ["import", "activation"]),
        ban_condition("BAN02", "存在启用中的 webhook", "webhook_enabled 必须为 false", ["import", "activation"]),
        ban_condition("BAN03", "存在真实触发标识", "real_trigger 必须为 false", ["import", "activation"]),
        ban_condition("BAN04", "存在网络或 n8n 连接动作", "network_request_enabled 与 n8n_connection_enabled 必须为 false", ["import", "activation"]),
        ban_condition("BAN05", "缺少总管启用前确认", "supervisor_confirmed 必须由人工在离线验收后补齐", ["activation"]),
        ban_condition("BAN06", "缺少回滚要求", "rollback_requirements_ready 必须为 true", ["import", "activation"]),
    ]
    return guard_copy(
        {
            "name": "导入前禁入条件",
            "generated_at": now_text(),
            "import_allowed": False,
            "activation_allowed": False,
            "condition_count": len(conditions),
            "conditions": conditions,
            "error_count": 0,
        }
    )


def build_activation_confirmations() -> dict[str, Any]:
    items = [
        "总管确认本包仅为离线导入前检查产物",
        "总管确认凭据值未出现、未读取、未写入",
        "总管确认 webhook 全部保持禁用",
        "总管确认导入动作仍被禁止",
        "总管确认启用动作仍被禁止",
        "总管确认企业微信真实发送仍被禁止",
        "总管确认回滚要求已具备",
    ]
    return guard_copy(
        {
            "name": "启用前总管确认项",
            "generated_at": now_text(),
            "supervisor_confirmed": False,
            "activation_allowed": False,
            "item_count": len(items),
            "items": [
                guard_copy(
                    {
                        "confirm_id": f"SUP{index:02d}",
                        "title": title,
                        "required_before_activation": True,
                        "confirmed": False,
                        "error_count": 0,
                    }
                )
                for index, title in enumerate(items, start=1)
            ],
            "error_count": 0,
        }
    )


def build_rollback_requirements() -> dict[str, Any]:
    requirements = [
        ("RB01", "发现凭据值时立即废弃离线导入候选", "删除候选副本中的值字段，仅保留隔离清单说明"),
        ("RB02", "发现 webhook 启用意图时冻结候选", "把候选状态退回 blocked_offline_precheck"),
        ("RB03", "发现真实触发意图时停止交接", "要求总管人工复核后重新生成离线样例"),
        ("RB04", "发现网络或 n8n 调用意图时废弃检查结果", "重新运行生成脚本和只读检查脚本"),
        ("RB05", "发现企业微信真实发送意图时升级红线", "记录为禁止启用项，禁止进入导入队列"),
    ]
    return guard_copy(
        {
            "name": "回滚要求",
            "generated_at": now_text(),
            "rollback_requirements_ready": True,
            "requirements": [
                guard_copy(
                    {
                        "requirement_id": req_id,
                        "title": title,
                        "rollback_action": action,
                        "runtime_change_required": False,
                        "error_count": 0,
                    }
                )
                for req_id, title, action in requirements
            ],
            "error_count": 0,
        }
    )


def build_package(
    credential_isolation: dict[str, Any],
    webhook_disabled: dict[str, Any],
    import_bans: dict[str, Any],
    confirmations: dict[str, Any],
    rollback_requirements: dict[str, Any],
) -> dict[str, Any]:
    return guard_copy(
        {
            "name": "n8n离线导入前凭据隔离与启用禁入包",
            "version": "offline-import-credential-isolation-no-activate-v1",
            "generated_at": now_text(),
            "status": "blocked_offline_precheck_ready",
            "source_summary": build_source_summary(),
            "credential_isolation": credential_isolation,
            "webhook_disabled_list": webhook_disabled,
            "import_ban_conditions": import_bans,
            "activation_supervisor_confirmations": confirmations,
            "rollback_requirements": rollback_requirements,
            "acceptance_requirements": {
                "import_allowed": False,
                "activation_allowed": False,
                "credential_values_present": False,
                "webhook_enabled": False,
                "real_trigger": False,
                "error_count": 0,
            },
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


def build_credential_md(data: dict[str, Any]) -> str:
    lines = [
        "# 凭据字段隔离清单",
        "",
        f"- 生成时间：{data['generated_at']}",
        "- credential_values_present=false",
        "- import_allowed=false",
        "- activation_allowed=false",
        "",
        "| 槽位 | 名称 | 是否有值 | 导入行为 |",
        "| --- | --- | --- | --- |",
    ]
    for slot in data["slots"]:
        lines.append(f"| {slot['slot_id']} | {slot['display_name']} | {slot['value_present']} | {slot['import_behavior']} |")
    lines.append("")
    return "\n".join(lines)


def build_package_md(package: dict[str, Any]) -> str:
    lines = [
        "# n8n 离线导入前凭据隔离与启用禁入包",
        "",
        f"- 生成时间：{package['generated_at']}",
        f"- 状态：{package['status']}",
        "- import_allowed=false",
        "- activation_allowed=false",
        "- credential_values_present=false",
        "- webhook_enabled=false",
        "- real_trigger=false",
        "- error_count=0",
        "",
        "## 清单",
        "",
        f"- 凭据隔离槽位数：{package['credential_isolation']['slot_count']}",
        f"- webhook禁用项数：{package['webhook_disabled_list']['item_count']}",
        f"- 导入前禁入条件数：{package['import_ban_conditions']['condition_count']}",
        f"- 启用前总管确认项数：{package['activation_supervisor_confirmations']['item_count']}",
        f"- 回滚要求数：{len(package['rollback_requirements']['requirements'])}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    credential_isolation = build_credential_isolation()
    webhook_disabled = build_webhook_disabled_list()
    import_bans = build_import_bans()
    confirmations = build_activation_confirmations()
    rollback_requirements = build_rollback_requirements()
    package = build_package(credential_isolation, webhook_disabled, import_bans, confirmations, rollback_requirements)

    write_json(CREDENTIAL_ISOLATION_JSON, credential_isolation)
    write_text(CREDENTIAL_ISOLATION_MD, build_credential_md(credential_isolation))
    write_json(WEBHOOK_DISABLED_JSON, webhook_disabled)
    write_json(IMPORT_BAN_JSON, import_bans)
    write_json(ACTIVATION_CONFIRM_JSON, confirmations)
    write_json(ROLLBACK_REQUIREMENTS_JSON, rollback_requirements)
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, build_package_md(package))

    print(
        json.dumps(
            {
                "status": package["status"],
                "import_allowed": package["import_allowed"],
                "activation_allowed": package["activation_allowed"],
                "credential_values_present": package["credential_values_present"],
                "webhook_enabled": package["webhook_enabled"],
                "real_trigger": package["real_trigger"],
                "error_count": package["error_count"],
                "output": str(PACKAGE_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
