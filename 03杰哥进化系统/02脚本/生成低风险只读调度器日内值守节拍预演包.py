# -*- coding: utf-8 -*-
"""生成低风险只读调度器日内值守节拍预演包。

只生成本地 JSON/MD 预演材料，不注册系统计划任务，不接外部系统，
不真实发送企业微信，不执行调度任务，不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "108低风险只读调度器日内值守节拍预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器日内值守节拍预演包验收"

CONFIG_JSON = DATA_DIR / "日内值守节拍配置_最新.json"
CONFIG_MD = DATA_DIR / "日内值守节拍配置_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器日内值守节拍预演包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器日内值守节拍预演包_最新.md"
GENERATE_LOG = LOG_DIR / "low-risk-readonly-scheduler-daily-rhythm-preview-generate-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safety_flags() -> dict[str, bool]:
    return {
        "preview_only": True,
        "auto_schedule": False,
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
        "register_system_scheduled_task": False,
        "reload_service": False,
    }


def source_packages() -> dict[str, str]:
    return {
        "package104_three_round_dryrun": str(
            EVOLUTION_ROOT / "03数据" / "104低风险只读调度器连续三轮干跑预演包" / "三轮干跑结果_最新.json"
        ),
        "package105_drift_idempotency": str(
            EVOLUTION_ROOT
            / "03数据"
            / "105低风险只读调度干跑结果漂移复核与幂等校验包"
            / "幂等校验报告_最新.json"
        ),
        "package106_redline_pause": str(
            EVOLUTION_ROOT
            / "03数据"
            / "106低风险只读调度红线失败注入与自动暂停演练包"
            / "自动暂停演练报告_最新.json"
        ),
        "package107_round13_index": str(
            EVOLUTION_ROOT
            / "03数据"
            / "107第十三轮只读调度连续干跑并行调度索引包"
            / "第十三轮只读调度连续干跑并行调度索引包_最新.json"
        ),
    }


def build_rhythms() -> list[dict[str, Any]]:
    specs = [
        (
            "RHYTHM-001",
            "早间巡检",
            "09:00",
            "09:10",
            ["读取104连续三轮干跑结果摘要", "读取105幂等校验通过状态", "确认106红线暂停演练无放行项"],
        ),
        (
            "RHYTHM-002",
            "午间快照",
            "12:10",
            "12:20",
            ["读取早间巡检计划证据路径", "读取104任务排序稳定摘要", "生成午间本地快照计划"],
        ),
        (
            "RHYTHM-003",
            "收盘复核",
            "15:10",
            "15:25",
            ["读取午间快照计划证据路径", "读取105漂移复核通过状态", "生成收盘只读复核计划"],
        ),
        (
            "RHYTHM-004",
            "晚间归档",
            "18:30",
            "18:45",
            ["读取收盘复核计划证据路径", "读取107第十三轮并行调度索引", "生成晚间归档计划"],
        ),
        (
            "RHYTHM-005",
            "异常复验",
            "20:00",
            "20:15",
            ["读取106红线失败注入与自动暂停演练报告", "读取当日全部节拍计划证据路径", "生成异常复验计划"],
        ),
    ]
    rhythms: list[dict[str, Any]] = []
    for order, (rhythm_id, name, start, end, dependencies) in enumerate(specs, start=1):
        evidence_path = DATA_DIR / "证据路径预留" / f"{order:02d}_{name}_计划证据.json"
        item = {
            "order": order,
            "rhythm_id": rhythm_id,
            "rhythm_name": name,
            "planned_window": {"start": start, "end": end, "timezone": "Asia/Shanghai"},
            "plan_only": True,
            "dependencies": dependencies,
            "evidence_path": str(evidence_path),
            "script_to_execute": None,
            "execution_adapter": "none",
            "system_schedule_name": None,
            "manual_review_required": name == "异常复验",
        }
        item.update(safety_flags())
        rhythms.append(item)
    return rhythms


def build_config(generated_at: str) -> dict[str, Any]:
    rhythms = build_rhythms()
    config = {
        "name": "低风险只读调度器日内值守节拍配置",
        "generated_at": generated_at,
        "based_on_packages": source_packages(),
        "rhythm_count": len(rhythms),
        "timezone": "Asia/Shanghai",
        "scheduler_mode": "daily_rhythm_preview_plan_only",
        "preview_only": True,
        "auto_schedule": False,
        "auto_execute": False,
        "actual_execution": False,
        "external_call": False,
        "reload_service": False,
        "register_system_scheduled_task": False,
        "rhythms": rhythms,
        "hard_red_line_confirmation": safety_flags(),
    }
    config.update(safety_flags())
    return config


def config_md(config: dict[str, Any]) -> str:
    rows = [
        f"| {item['order']} | {item['rhythm_id']} | {item['rhythm_name']} | {item['planned_window']['start']}-{item['planned_window']['end']} | {item['plan_only']} | {item['auto_schedule']} | {item['actual_execution']} |"
        for item in config["rhythms"]
    ]
    return "\n".join(
        [
            "# 低风险只读调度器日内值守节拍配置",
            "",
            f"- 生成时间: {config['generated_at']}",
            f"- rhythm_count: {config['rhythm_count']}",
            "- preview_only: true",
            "- auto_schedule: false",
            "- actual_execution: false",
            "- external_call: false",
            "- reload_service: false",
            "",
            "| order | rhythm_id | rhythm_name | window | plan_only | auto_schedule | actual_execution |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def package_md(package: dict[str, Any]) -> str:
    output_rows = [f"- {key}: `{value}`" for key, value in package["outputs"].items()]
    return "\n".join(
        [
            "# 低风险只读调度器日内值守节拍预演包",
            "",
            f"- 生成时间: {package['generated_at']}",
            f"- rhythm_count: {package['rhythm_count']}",
            "- preview_only: true",
            "- auto_schedule: false",
            "- actual_execution: false",
            "- external_call: false",
            "- reload_service: false",
            "",
            "## 输出",
            "",
            *output_rows,
        ]
    )


def main() -> int:
    generated_at = now()
    config = build_config(generated_at)
    package = {
        "name": "低风险只读调度器日内值守节拍预演包",
        "generated_at": generated_at,
        "status": "generated_preview_only",
        "rhythm_count": config["rhythm_count"],
        "preview_only": True,
        "auto_schedule": False,
        "auto_execute": False,
        "actual_execution": False,
        "external_call": False,
        "reload_service": False,
        "register_system_scheduled_task": False,
        "outputs": {
            "config_json": str(CONFIG_JSON),
            "config_md": str(CONFIG_MD),
            "preview_result_json": str(DATA_DIR / "值守节拍预演结果_最新.json"),
            "preview_result_md": str(DATA_DIR / "值守节拍预演结果_最新.md"),
            "conflict_check_json": str(DATA_DIR / "节拍冲突检查_最新.json"),
            "conflict_check_md": str(DATA_DIR / "节拍冲突检查_最新.md"),
            "package_json": str(PACKAGE_JSON),
            "package_md": str(PACKAGE_MD),
            "verify_log_json": str(LOG_DIR / "low-risk-readonly-scheduler-daily-rhythm-preview-verify-最新.json"),
        },
        "hard_red_line_confirmation": safety_flags(),
    }
    package.update(safety_flags())
    write_json(CONFIG_JSON, config)
    write_text(CONFIG_MD, config_md(config))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))
    write_json(GENERATE_LOG, package | {"log_type": "generate"})
    print(json.dumps({"pass": True, "error_count": 0, "rhythm_count": config["rhythm_count"], "output": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
