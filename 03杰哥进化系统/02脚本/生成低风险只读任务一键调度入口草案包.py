# -*- coding: utf-8 -*-
"""生成低风险只读任务一键调度入口草案包。

本脚本只生成本地 JSON/MD 草案材料，不注册入口，不接入总管面板，不写一键接续包，
不调用 n8n/企业微信/券商/税局/财税软件，不执行任何任务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "99低风险只读任务一键调度入口草案包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读任务一键调度入口草案包验收"

SOURCE_PACKAGE_DIR = EVOLUTION_ROOT / "03数据" / "96低风险自主任务本地只读调度预演包"
SOURCE_SCHEDULE_JSON = SOURCE_PACKAGE_DIR / "本地只读调度计划_最新.json"
SOURCE_RULES_JSON = SOURCE_PACKAGE_DIR / "调度预演规则_最新.json"
SOURCE_REPORT_JSON = SOURCE_PACKAGE_DIR / "调度预演报告_最新.json"

ENTRY_JSON = DATA_DIR / "一键调度入口草案_最新.json"
ENTRY_MD = DATA_DIR / "一键调度入口草案_最新.md"
CONFIG_JSON = DATA_DIR / "本地预演配置_最新.json"
CONFIG_MD = DATA_DIR / "本地预演配置_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读任务一键调度入口草案包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读任务一键调度入口草案包_最新.md"
GEN_LOG = LOG_DIR / "low-risk-readonly-one-click-scheduler-entry-generate-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json_if_exists(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safety_flags() -> dict[str, bool]:
    return {
        "enabled": False,
        "preview_only": True,
        "auto_execute": False,
        "external_call": False,
        "real_send": False,
        "real_wecom_send": False,
        "trigger_n8n": False,
        "broker_connection": False,
        "trade_order": False,
        "tax_bureau_login": False,
        "finance_tax_software_connection": False,
        "write_formal_rule": False,
        "reload_service": False,
        "modify_supervisor_panel": False,
        "modify_one_click_pack": False,
        "modify_one_click_continuation_package": False,
        "task_executed": False,
    }


def output_paths() -> dict[str, str]:
    return {
        "entry_json": str(ENTRY_JSON),
        "entry_md": str(ENTRY_MD),
        "preview_config_json": str(CONFIG_JSON),
        "preview_config_md": str(CONFIG_MD),
        "preview_report_json": str(DATA_DIR / "一键入口本地预演报告_最新.json"),
        "preview_report_md": str(DATA_DIR / "一键入口本地预演报告_最新.md"),
        "package_json": str(PACKAGE_JSON),
        "package_md": str(PACKAGE_MD),
        "verify_log_json": str(LOG_DIR / "low-risk-readonly-one-click-scheduler-entry-verify-最新.json"),
    }


def source_task_names() -> list[str]:
    source = read_json_if_exists(SOURCE_SCHEDULE_JSON) or {}
    names = []
    for item in source.get("tasks", []):
        name = str(item.get("name") or "").strip()
        if name:
            names.append(name)
    return names[:8]


def build_tasks(generated_at: str) -> list[dict[str, Any]]:
    fallback_names = [
        "读取第96包调度计划快照",
        "检查只读安全字段",
        "解析暂停闸口条件",
        "整理入口前置检查清单",
        "生成候选任务预览顺序",
        "生成候选任务依赖关系预览",
        "复核红线禁触达项",
        "汇总本地预演报告输入",
    ]
    names = source_task_names() or fallback_names
    while len(names) < 8:
        names.append(fallback_names[len(names)])

    task_ids = [
        "LRRO-ENTRY-001",
        "LRRO-ENTRY-002",
        "LRRO-ENTRY-003",
        "LRRO-ENTRY-004",
        "LRRO-ENTRY-005",
        "LRRO-ENTRY-006",
        "LRRO-ENTRY-007",
        "LRRO-ENTRY-008",
    ]
    objectives = [
        "只读取第96包本地只读调度预演产物是否存在，不加载业务执行器。",
        "只检查 enabled/preview_only/auto_execute/external_call 等安全字段。",
        "只把暂停条件转为入口草案的解析项，不触发暂停动作之外的流程。",
        "只列出执行前检查项，不改总管面板和一键接续包。",
        "只生成预览排序，不运行任务。",
        "只生成依赖关系预览，不调用任务适配器。",
        "只复核企业微信、n8n、券商、税局、财税软件、服务重载等禁触达项。",
        "只为本地预演报告准备结构化输入，不真实发送、不交易、不登录。",
    ]

    tasks: list[dict[str, Any]] = []
    for index, task_id in enumerate(task_ids):
        depends_on = [] if index == 0 else [task_ids[index - 1]]
        task = {
            "id": task_id,
            "name": names[index],
            "objective": objectives[index],
            "source_package": "96低风险自主任务本地只读调度预演包",
            "preview_order": index + 1,
            "depends_on": depends_on,
            "enabled": False,
            "preview_only": True,
            "auto_execute": False,
            "external_call": False,
            "real_send": False,
            "reload_service": False,
            "modify_supervisor_panel": False,
            "modify_one_click_pack": False,
            "task_executed": False,
            "execution_adapter": "none",
            "generated_at": generated_at,
            "allowed_action": "entry_parse_and_plan_generation_only",
        }
        task.update({k: v for k, v in safety_flags().items() if k not in task})
        tasks.append(task)
    return tasks


def build_entry(generated_at: str, tasks: list[dict[str, Any]]) -> dict[str, Any]:
    paths = output_paths()
    return {
        "entry_name": "低风险只读任务一键调度入口草案",
        "generated_at": generated_at,
        "status": "draft_only_not_connected",
        "based_on": {
            "package": "96低风险自主任务本地只读调度预演包",
            "source_schedule_json": str(SOURCE_SCHEDULE_JSON),
            "source_rules_json": str(SOURCE_RULES_JSON),
            "source_report_json": str(SOURCE_REPORT_JSON),
            "source_schedule_exists": SOURCE_SCHEDULE_JSON.exists(),
            "source_rules_exists": SOURCE_RULES_JSON.exists(),
            "source_report_exists": SOURCE_REPORT_JSON.exists(),
        },
        "scope": "one_click_entry_draft_and_local_preview_only",
        "allowed_task_list": [
            {
                "id": task["id"],
                "name": task["name"],
                "enabled": task["enabled"],
                "preview_only": task["preview_only"],
                "auto_execute": task["auto_execute"],
                "external_call": task["external_call"],
                "allowed_action": task["allowed_action"],
            }
            for task in tasks
        ],
        "pre_execution_checks": [
            "确认入口处于 draft_only_not_connected 状态",
            "确认本地预演配置 defaults.enabled=false",
            "确认所有任务 enabled=false",
            "确认 preview_only=true",
            "确认 auto_execute=false",
            "确认 external_call=false",
            "确认 real_send=false",
            "确认 reload_service=false",
            "确认 modify_supervisor_panel=false",
            "确认 modify_one_click_pack=false",
            "确认 execution_adapter=none",
        ],
        "pause_conditions": [
            "任一任务 enabled 不为 false",
            "任一任务 preview_only 不为 true",
            "任一任务 auto_execute/external_call/real_send/reload_service 不为 false",
            "出现企业微信真实发送、n8n触发、券商连接、交易下单、税局登录、财税软件连接意图",
            "出现写正式规则、修改总管面板、修改一键接续包、重载服务意图",
            "第96包来源文件缺失时只记录为预演输入不足，不补接真实系统",
        ],
        "output_paths": paths,
        "hard_red_line_confirmation": safety_flags(),
        "auto_execute": False,
        "external_call": False,
        "real_send": False,
        "reload_service": False,
        "modify_supervisor_panel": False,
        "modify_one_click_pack": False,
    }


def build_config(generated_at: str, tasks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "config_name": "低风险只读任务一键调度入口本地预演配置",
        "generated_at": generated_at,
        "based_on": "96低风险自主任务本地只读调度预演包",
        "defaults": {
            "enabled": False,
            "preview_only": True,
            "auto_execute": False,
            "external_call": False,
            "real_send": False,
            "reload_service": False,
            "modify_supervisor_panel": False,
            "modify_one_click_pack": False,
            "task_executed": False,
            "execution_adapter": "none",
        },
        "task_count": len(tasks),
        "tasks": tasks,
        "plan_generation_mode": "parse_entry_and_generate_disabled_preview_plan_only",
        "hard_red_line_confirmation": safety_flags(),
        "auto_execute": False,
        "external_call": False,
        "real_send": False,
        "reload_service": False,
        "modify_supervisor_panel": False,
        "modify_one_click_pack": False,
    }


def entry_md(entry: dict[str, Any]) -> str:
    allowed_rows = [
        f"| {item['id']} | {item['name']} | {item['enabled']} | {item['preview_only']} | {item['auto_execute']} | {item['external_call']} |"
        for item in entry["allowed_task_list"]
    ]
    checks = "\n".join(f"- {item}" for item in entry["pre_execution_checks"])
    pauses = "\n".join(f"- {item}" for item in entry["pause_conditions"])
    outputs = "\n".join(f"- {key}: {value}" for key, value in entry["output_paths"].items())
    return "\n".join(
        [
            "# 低风险只读任务一键调度入口草案",
            "",
            f"- 生成时间: {entry['generated_at']}",
            f"- 状态: {entry['status']}",
            "- 范围: 只做入口草案与本地预演，不接入总管面板，不写一键接续包，不真实执行任务。",
            "",
            "## 允许任务列表",
            "",
            "| id | name | enabled | preview_only | auto_execute | external_call |",
            "| --- | --- | --- | --- | --- | --- |",
            *allowed_rows,
            "",
            "## 执行前检查",
            "",
            checks,
            "",
            "## 暂停条件",
            "",
            pauses,
            "",
            "## 输出路径",
            "",
            outputs,
        ]
    )


def config_md(config: dict[str, Any]) -> str:
    rows = [
        f"| {task['preview_order']} | {task['id']} | {task['name']} | {task['enabled']} | {task['preview_only']} | {task['auto_execute']} | {task['external_call']} |"
        for task in config["tasks"]
    ]
    return "\n".join(
        [
            "# 本地预演配置",
            "",
            f"- 生成时间: {config['generated_at']}",
            "- 默认: enabled=false, preview_only=true, auto_execute=false, external_call=false",
            "- 说明: 所有任务均禁用，只允许入口解析和计划生成预演。",
            "",
            "| order | id | name | enabled | preview_only | auto_execute | external_call |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def package_md(package: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 低风险只读任务一键调度入口草案包",
            "",
            f"- 生成时间: {package['generated_at']}",
            f"- 入口草案: {package['files']['entry_json']}",
            f"- 本地预演配置: {package['files']['config_json']}",
            "- 红线确认: auto_execute=false, external_call=false, real_send=false, reload_service=false, modify_supervisor_panel=false, modify_one_click_pack=false",
            "- 状态: 草案包已生成，未接入任何真实系统。",
        ]
    )


def main() -> int:
    generated_at = now()
    tasks = build_tasks(generated_at)
    entry = build_entry(generated_at, tasks)
    config = build_config(generated_at, tasks)
    package = {
        "package_name": "低风险只读任务一键调度入口草案包",
        "generated_at": generated_at,
        "based_on": "96低风险自主任务本地只读调度预演包",
        "files": {
            "entry_json": str(ENTRY_JSON),
            "entry_md": str(ENTRY_MD),
            "config_json": str(CONFIG_JSON),
            "config_md": str(CONFIG_MD),
            "package_json": str(PACKAGE_JSON),
            "package_md": str(PACKAGE_MD),
        },
        "entry_name": entry["entry_name"],
        "task_count": len(tasks),
        "auto_execute": False,
        "external_call": False,
        "real_send": False,
        "reload_service": False,
        "modify_supervisor_panel": False,
        "modify_one_click_pack": False,
        "hard_red_line_confirmation": safety_flags(),
    }

    write_json(ENTRY_JSON, entry)
    write_text(ENTRY_MD, entry_md(entry))
    write_json(CONFIG_JSON, config)
    write_text(CONFIG_MD, config_md(config))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))

    log = {
        "name": "低风险只读任务一键调度入口草案包生成日志",
        "generated_at": generated_at,
        "pass": True,
        "error_count": 0,
        "outputs": output_paths(),
        "auto_execute": False,
        "external_call": False,
        "real_send": False,
        "reload_service": False,
        "modify_supervisor_panel": False,
        "modify_one_click_pack": False,
    }
    write_json(GEN_LOG, log)
    print(json.dumps({"pass": True, "error_count": 0, "output": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
