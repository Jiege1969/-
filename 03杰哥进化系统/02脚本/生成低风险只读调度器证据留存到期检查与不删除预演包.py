# -*- coding: utf-8 -*-
"""生成低风险只读调度器证据留存到期检查与不删除预演包。
本脚本只读取本地证据索引并生成到期检查策略、样本清单和不删除队列；不删除、不移动、不归档历史包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = EVOLUTION_ROOT / "03数据" / "100低风险只读调度运行台账与证据归档预演包"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "118低风险只读调度器证据留存到期检查与不删除预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器证据留存到期检查与不删除预演包验收"

SOURCE_PACKAGE_JSON = SOURCE_DIR / "低风险只读调度运行台账与证据归档预演包_最新.json"
SOURCE_ARCHIVE_REPORT_JSON = SOURCE_DIR / "证据归档预演报告_最新.json"
SOURCE_LEDGER_JSON = SOURCE_DIR / "调度预演台账_最新.json"

POLICY_JSON = DATA_DIR / "证据留存到期检查策略_最新.json"
POLICY_MD = DATA_DIR / "证据留存到期检查策略_最新.md"
INVENTORY_JSON = DATA_DIR / "证据留存样本清单_最新.json"
INVENTORY_MD = DATA_DIR / "证据留存样本清单_最新.md"
QUEUE_JSON = DATA_DIR / "到期不删除处理队列_最新.json"
QUEUE_MD = DATA_DIR / "到期不删除处理队列_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器证据留存到期检查与不删除预演包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器证据留存到期检查与不删除预演包_最新.md"
GENERATE_LOG = LOG_DIR / "low-risk-readonly-scheduler-evidence-retention-expiry-generate-最新.json"


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


def safety_flags() -> dict[str, bool]:
    return {
        "read_only": True,
        "delete_file": False,
        "remove_directory": False,
        "move_history_package": False,
        "overwrite_history_package": False,
        "external_call": False,
        "send_notification": False,
        "connect_n8n": False,
        "reload_service": False,
        "promote_to_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
        "write_scope_is_118_only": True,
    }


def source_summary() -> dict[str, Any]:
    summary: dict[str, Any] = {
        "source_dir": str(SOURCE_DIR),
        "source_package_exists": SOURCE_PACKAGE_JSON.exists(),
        "source_archive_report_exists": SOURCE_ARCHIVE_REPORT_JSON.exists(),
        "source_ledger_exists": SOURCE_LEDGER_JSON.exists(),
    }
    for key, path in [
        ("source_package", SOURCE_PACKAGE_JSON),
        ("source_archive_report", SOURCE_ARCHIVE_REPORT_JSON),
        ("source_ledger", SOURCE_LEDGER_JSON),
    ]:
        if path.exists():
            data = read_json(path)
            summary[key] = {
                "path": str(path),
                "top_level_keys": sorted(data.keys()) if isinstance(data, dict) else [],
                "type": type(data).__name__,
            }
    return summary


def build_policy(generated_at: str) -> dict[str, Any]:
    rules = [
        {
            "id": "RET-POL-001",
            "name": "到期只登记不删除",
            "trigger": "证据留存时间达到检查窗口或疑似超过保留期。",
            "decision": "标记为到期候选，进入不删除处理队列。",
            "delete_allowed": False,
            "requires_supervisor_confirmation": True,
            "dry_run_only": True,
        },
        {
            "id": "RET-POL-002",
            "name": "历史包编号保护",
            "trigger": "路径位于已有历史编号包，例如 114 或其他已占用编号。",
            "decision": "只记录引用，不清空、不覆盖、不迁移。",
            "delete_allowed": False,
            "requires_supervisor_confirmation": True,
            "dry_run_only": True,
        },
        {
            "id": "RET-POL-003",
            "name": "证据链完整性优先",
            "trigger": "证据被台账、验收日志、调度报告或回传索引引用。",
            "decision": "保留原件，追加候选说明，等待人工复核。",
            "delete_allowed": False,
            "requires_supervisor_confirmation": True,
            "dry_run_only": True,
        },
        {
            "id": "RET-POL-004",
            "name": "缺失元数据不删除",
            "trigger": "留存起算时间、来源包、验收日志或引用关系缺失。",
            "decision": "标记元数据缺口，不删除证据。",
            "delete_allowed": False,
            "requires_supervisor_confirmation": True,
            "dry_run_only": True,
        },
        {
            "id": "RET-POL-005",
            "name": "本地预演不触发外部动作",
            "trigger": "需要通知、n8n、服务刷新、外部归档或真实清理。",
            "decision": "全部禁止，只生成本地草案和验收日志。",
            "delete_allowed": False,
            "requires_supervisor_confirmation": True,
            "dry_run_only": True,
        },
    ]
    return {
        "name": "证据留存到期检查策略",
        "generated_at": generated_at,
        "target_data_dir": str(DATA_DIR),
        "protected_history_dir_hint": str(EVOLUTION_ROOT / "03数据" / "114并行自主施工分片护栏与抢占处理包"),
        "readonly_dry_run_only": True,
        "delete_allowed": False,
        "rule_count": len(rules),
        "rules": rules,
        "safety_confirmation": safety_flags(),
    }


def build_inventory(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    samples = [
        {
            "id": "RET-SAMPLE-001",
            "source": str(SOURCE_PACKAGE_JSON),
            "source_exists": SOURCE_PACKAGE_JSON.exists(),
            "retention_status": "到期候选-需人工复核",
            "delete_allowed": False,
            "planned_action": "保留原件，仅记录到期候选。",
            "reason": "源包为调度运行台账与证据归档预演总包，属于证据链入口。",
        },
        {
            "id": "RET-SAMPLE-002",
            "source": str(SOURCE_ARCHIVE_REPORT_JSON),
            "source_exists": SOURCE_ARCHIVE_REPORT_JSON.exists(),
            "retention_status": "到期候选-需人工复核",
            "delete_allowed": False,
            "planned_action": "保留原件，仅记录到期候选。",
            "reason": "归档预演报告可证明证据链生成过程，不做删除预演外的动作。",
        },
        {
            "id": "RET-SAMPLE-003",
            "source": str(SOURCE_LEDGER_JSON),
            "source_exists": SOURCE_LEDGER_JSON.exists(),
            "retention_status": "到期候选-需人工复核",
            "delete_allowed": False,
            "planned_action": "保留原件，仅记录到期候选。",
            "reason": "调度预演台账是后续只读调度复核来源。",
        },
        {
            "id": "RET-SAMPLE-004",
            "source": str(EVOLUTION_ROOT / "03数据" / "114并行自主施工分片护栏与抢占处理包"),
            "source_exists": (EVOLUTION_ROOT / "03数据" / "114并行自主施工分片护栏与抢占处理包").exists(),
            "retention_status": "历史包编号保护",
            "delete_allowed": False,
            "planned_action": "不删除、不覆盖、不迁移，只在 118 包中记录边界。",
            "reason": "114 已被历史包占用，必须视为只读历史内容。",
        },
    ]
    return {
        "name": "证据留存样本清单",
        "generated_at": generated_at,
        "source_summary": summary,
        "sample_count": len(samples),
        "delete_allowed": False,
        "readonly_dry_run_only": True,
        "samples": samples,
        "safety_confirmation": safety_flags(),
    }


def build_queue(generated_at: str, inventory: dict[str, Any]) -> dict[str, Any]:
    items = []
    for sample in inventory["samples"]:
        items.append(
            {
                "id": sample["id"].replace("RET-SAMPLE", "RET-Q"),
                "sample_id": sample["id"],
                "source": sample["source"],
                "status": "待总管人工复核",
                "decision": "不删除",
                "delete_allowed": False,
                "dry_run_only": True,
                "requires_supervisor_confirmation": True,
                "planned_action": sample["planned_action"],
                "evidence_retained": True,
                "history_content_untouched": True,
            }
        )
    return {
        "name": "到期不删除处理队列",
        "generated_at": generated_at,
        "queue_count": len(items),
        "default_decision": "不删除",
        "delete_allowed": False,
        "readonly_dry_run_only": True,
        "items": items,
        "safety_confirmation": safety_flags(),
    }


def md_table(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return lines


def policy_md(policy: dict[str, Any]) -> str:
    rows = md_table(policy["rules"], ["id", "name", "delete_allowed", "requires_supervisor_confirmation", "dry_run_only"])
    return "\n".join([
        "# 证据留存到期检查策略",
        "",
        f"- 生成时间: {policy['generated_at']}",
        "- 结论: 到期检查只登记候选，不删除任何证据。",
        "- 写入范围: 仅 118 包目录与固定验收日志目录。",
        "",
        *rows,
        "",
    ])


def inventory_md(inventory: dict[str, Any]) -> str:
    rows = md_table(inventory["samples"], ["id", "source_exists", "retention_status", "delete_allowed", "planned_action"])
    return "\n".join([
        "# 证据留存样本清单",
        "",
        f"- 生成时间: {inventory['generated_at']}",
        f"- 样本数: {inventory['sample_count']}",
        "- 结论: 全部样本均为只读检查样本。",
        "",
        *rows,
        "",
    ])


def queue_md(queue: dict[str, Any]) -> str:
    rows = md_table(queue["items"], ["id", "sample_id", "status", "decision", "delete_allowed", "dry_run_only"])
    return "\n".join([
        "# 到期不删除处理队列",
        "",
        f"- 生成时间: {queue['generated_at']}",
        f"- 队列数: {queue['queue_count']}",
        "- 默认决策: 不删除",
        "",
        *rows,
        "",
    ])


def package_md(package: dict[str, Any]) -> str:
    return "\n".join([
        "# 低风险只读调度器证据留存到期检查与不删除预演包",
        "",
        f"- 生成时间: {package['generated_at']}",
        "- 数据目录: 118低风险只读调度器证据留存到期检查与不删除预演包",
        "- 结论: 本包仅做只读到期检查与不删除预演。",
        "- delete_allowed: false",
        "- history_content_untouched: true",
        "",
        "## 产物",
        "",
        f"- {POLICY_JSON.name}",
        f"- {INVENTORY_JSON.name}",
        f"- {QUEUE_JSON.name}",
        "",
    ])


def main() -> int:
    generated_at = now()
    summary = source_summary()
    policy = build_policy(generated_at)
    inventory = build_inventory(generated_at, summary)
    queue = build_queue(generated_at, inventory)
    package = {
        "name": "低风险只读调度器证据留存到期检查与不删除预演包",
        "generated_at": generated_at,
        "target_data_dir": str(DATA_DIR),
        "log_dir": str(LOG_DIR),
        "source_dir": str(SOURCE_DIR),
        "readonly_dry_run_only": True,
        "delete_allowed": False,
        "history_content_untouched": True,
        "write_scope_is_118_only": True,
        "metrics": {
            "policy_rule_count": policy["rule_count"],
            "inventory_sample_count": inventory["sample_count"],
            "queue_count": queue["queue_count"],
        },
        "artifacts": {
            "policy_json": str(POLICY_JSON),
            "policy_md": str(POLICY_MD),
            "inventory_json": str(INVENTORY_JSON),
            "inventory_md": str(INVENTORY_MD),
            "queue_json": str(QUEUE_JSON),
            "queue_md": str(QUEUE_MD),
        },
        "safety_confirmation": safety_flags(),
    }
    write_json(POLICY_JSON, policy)
    write_text(POLICY_MD, policy_md(policy))
    write_json(INVENTORY_JSON, inventory)
    write_text(INVENTORY_MD, inventory_md(inventory))
    write_json(QUEUE_JSON, queue)
    write_text(QUEUE_MD, queue_md(queue))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))
    write_json(GENERATE_LOG, package)
    print(json.dumps({"pass": True, "error_count": 0, "target_data_dir": str(DATA_DIR), "queue_count": queue["queue_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
