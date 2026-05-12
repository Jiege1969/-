# -*- coding: utf-8 -*-
"""生成低风险只读调度器连续三轮干跑预演包。

本脚本只写入本包 JSON/MD 预演材料，不真实发送企业微信，不接 n8n，
不接券商，不交易，不登录税局，不接财税软件，不自动转正式规则，
不改总管面板，不改一键接续包，不重载服务。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "104低风险只读调度器连续三轮干跑预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器连续三轮干跑预演包验收"

CONFIG_JSON = DATA_DIR / "三轮干跑配置_最新.json"
CONFIG_MD = DATA_DIR / "三轮干跑配置_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器连续三轮干跑预演包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器连续三轮干跑预演包_最新.md"
GENERATE_LOG = LOG_DIR / "low-risk-readonly-scheduler-three-round-dryrun-generate-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_json(data: Any) -> str:
    text = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safety_flags() -> dict[str, bool]:
    return {
        "preview_only": True,
        "auto_execute": False,
        "actual_execution": False,
        "external_call": False,
        "real_wecom_send": False,
        "connect_n8n": False,
        "trigger_n8n": False,
        "broker_connection": False,
        "trade_order": False,
        "tax_bureau_login": False,
        "finance_tax_software_connection": False,
        "write_formal_rule": False,
        "auto_promote_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
        "reload_service": False,
    }


def build_tasks() -> list[dict[str, Any]]:
    specs = [
        ("LRRO-3R-001", "读取第99包只读调度入口草案", "99低风险只读任务一键调度入口草案包"),
        ("LRRO-3R-002", "读取第100包台账字段定义预演", "100低风险只读调度运行台账与证据归档预演包"),
        ("LRRO-3R-003", "读取第100包证据索引清单预演", "100低风险只读调度运行台账与证据归档预演包"),
        ("LRRO-3R-004", "读取第101包命令白名单草案", "101低风险自主命令白名单与红线静态扫描包"),
        ("LRRO-3R-005", "读取第101包红线扫描规则草案", "101低风险自主命令白名单与红线静态扫描包"),
        ("LRRO-3R-006", "生成计划排序快照预演", "本包连续三轮干跑配置"),
        ("LRRO-3R-007", "生成暂停状态快照预演", "本包连续三轮干跑配置"),
        ("LRRO-3R-008", "生成台账登记快照预演", "本包连续三轮干跑配置"),
        ("LRRO-3R-009", "生成连续性汇总输入快照", "本包连续三轮干跑配置"),
    ]
    tasks: list[dict[str, Any]] = []
    for order, (task_id, name, source_package) in enumerate(specs, start=1):
        task = {
            "task_id": task_id,
            "task_name": name,
            "order": order,
            "source_package": source_package,
            "enabled": False,
            "preview_only": True,
            "auto_execute": False,
            "actual_execution": False,
            "external_call": False,
            "pause_state": "manual_review_not_required",
            "allowed_action": "plan_sort_ledger_preview_only",
            "execution_adapter": "none",
            "evidence_index_id": f"EVID-{task_id}",
            "command_scan_id": f"SCAN-{task_id}",
        }
        task.update({key: value for key, value in safety_flags().items() if key not in task})
        tasks.append(task)
    return tasks


def build_config(generated_at: str) -> dict[str, Any]:
    tasks = build_tasks()
    return {
        "name": "低风险只读调度器连续三轮干跑配置",
        "generated_at": generated_at,
        "based_on_packages": [
            "99低风险只读任务一键调度入口草案包",
            "100低风险只读调度运行台账与证据归档预演包",
            "101低风险自主命令白名单与红线静态扫描包",
        ],
        "round_count": 3,
        "task_count": len(tasks),
        "preview_only": True,
        "auto_execute": False,
        "actual_execution": False,
        "external_call": False,
        "scheduler_mode": "readonly_three_round_dryrun_preview",
        "sort_key": ["order", "task_id"],
        "ledger_preview_mode": "append_preview_rows_only_no_source_touch",
        "command_scan_mode": "static_whitelist_summary_only_no_command_execution",
        "rounds": [
            {
                "round_index": index,
                "round_name": f"readonly_dryrun_round_{index}",
                "preview_only": True,
                "auto_execute": False,
                "actual_execution": False,
                "external_call": False,
                "task_count": len(tasks),
                "expected_order_hash": sha256_json([task["task_id"] for task in tasks]),
            }
            for index in range(1, 4)
        ],
        "tasks": tasks,
        "hard_red_line_confirmation": safety_flags(),
    }


def config_md(config: dict[str, Any]) -> str:
    rows = [
        f"| {task['order']} | {task['task_id']} | {task['task_name']} | {task['enabled']} | {task['preview_only']} | {task['auto_execute']} | {task['actual_execution']} | {task['external_call']} |"
        for task in config["tasks"]
    ]
    return "\n".join(
        [
            "# 低风险只读调度器连续三轮干跑配置",
            "",
            f"- 生成时间: {config['generated_at']}",
            f"- round_count: {config['round_count']}",
            f"- task_count: {config['task_count']}",
            "- preview_only: true",
            "- auto_execute: false",
            "- actual_execution: false",
            "- external_call: false",
            "",
            "| order | task_id | task_name | enabled | preview_only | auto_execute | actual_execution | external_call |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def package_md(package: dict[str, Any]) -> str:
    outputs = "\n".join(f"- {key}: `{value}`" for key, value in package["outputs"].items())
    return "\n".join(
        [
            "# 低风险只读调度器连续三轮干跑预演包",
            "",
            f"- 生成时间: {package['generated_at']}",
            "- 状态: generated_preview_only",
            f"- round_count: {package['round_count']}",
            f"- task_count: {package['task_count']}",
            "- preview_only: true",
            "- auto_execute: false",
            "- actual_execution: false",
            "- external_call: false",
            "",
            "## 产物",
            outputs,
        ]
    )


def main() -> int:
    generated_at = now()
    config = build_config(generated_at)
    package = {
        "name": "低风险只读调度器连续三轮干跑预演包",
        "generated_at": generated_at,
        "status": "generated_preview_only",
        "round_count": config["round_count"],
        "task_count": config["task_count"],
        "preview_only": True,
        "auto_execute": False,
        "actual_execution": False,
        "external_call": False,
        "reload_service": False,
        "write_formal_rule": False,
        "hard_red_line_confirmation": safety_flags(),
        "outputs": {
            "config_json": str(CONFIG_JSON),
            "config_md": str(CONFIG_MD),
            "run_result_json": str(DATA_DIR / "三轮干跑结果_最新.json"),
            "run_result_md": str(DATA_DIR / "三轮干跑结果_最新.md"),
            "continuity_summary_json": str(DATA_DIR / "连续性汇总_最新.json"),
            "continuity_summary_md": str(DATA_DIR / "连续性汇总_最新.md"),
            "package_json": str(PACKAGE_JSON),
            "package_md": str(PACKAGE_MD),
            "verify_log_json": str(LOG_DIR / "low-risk-readonly-scheduler-three-round-dryrun-verify-最新.json"),
        },
    }

    write_json(CONFIG_JSON, config)
    write_text(CONFIG_MD, config_md(config))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))
    write_json(GENERATE_LOG, package)
    print(json.dumps({"pass": True, "error_count": 0, "output": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
