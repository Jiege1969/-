# -*- coding: utf-8 -*-
"""生成低风险自主任务失败暂停与恢复演练包。

本脚本只生成本地演练资产，不发送企业微信，不连接 n8n/券商/税局/财税软件，
不写正式规则，不改总管面板或一键接续包，不重载服务，不执行恢复动作。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "97低风险自主任务失败暂停与恢复演练包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险自主任务失败暂停与恢复演练包验收"

SCENARIO_JSON = DATA_DIR / "失败暂停场景矩阵_最新.json"
SCENARIO_MD = DATA_DIR / "失败暂停场景矩阵_最新.md"
RECOVERY_JSON = DATA_DIR / "恢复申请模板_最新.json"
RECOVERY_MD = DATA_DIR / "恢复申请模板_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险自主任务失败暂停与恢复演练包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险自主任务失败暂停与恢复演练包_最新.md"
GEN_LOG = LOG_DIR / "low-risk-autonomous-failure-pause-recovery-generate-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_scenarios(generated_at: str) -> dict[str, Any]:
    base = {
        "pause_required": True,
        "auto_continue_after_failure": False,
        "continue_dispatch_allowed": False,
        "recovery_requested": False,
        "recovery_executed": False,
        "external_call": False,
        "reload_service": False,
        "requires_supervisor_confirmation": True,
        "readonly_drill_only": True,
        "generated_at": generated_at,
    }
    scenarios = [
        {
            "id": "LRF-001",
            "scenario": "验收失败",
            "trigger": "本地验收脚本返回失败、error_count 大于 0 或关键断言不通过",
            "pause_reason": "验收未通过时禁止低风险自主任务继续调度，等待人工复核失败项",
            "registration_required": ["验收脚本路径", "失败断言", "错误数量", "最后一次只读输出"],
            "recovery_request_note": "只能提交复验申请，不自动复跑真实业务动作",
        },
        {
            "id": "LRF-002",
            "scenario": "证据缺失",
            "trigger": "指定 JSON/MD/日志证据不存在、不可解析或字段缺失",
            "pause_reason": "证据链不完整时不能继续推进，避免把不完整产物当成已完成",
            "registration_required": ["缺失文件", "缺失字段", "期望证据", "补证责任说明"],
            "recovery_request_note": "只能申请补齐证据后再验收，不补做外部动作",
        },
        {
            "id": "LRF-003",
            "scenario": "红线词命中",
            "trigger": "命中真实发送企业微信、接 n8n、券商、交易、登录税局、财税软件等红线词",
            "pause_reason": "任何红线词命中都进入暂停，不继续调度、不尝试替代执行",
            "registration_required": ["命中词", "命中文本来源", "影响范围", "人工确认建议"],
            "recovery_request_note": "只能申请总管确认是否改写为只读候选说明",
        },
        {
            "id": "LRF-004",
            "scenario": "需服务重载",
            "trigger": "任务要求重载服务、刷新进程、重启端口或 reload 运行组件",
            "pause_reason": "服务重载超出低风险自主范围，必须停止调度并登记",
            "registration_required": ["重载对象", "触发原因", "关联端口或服务", "未执行证明"],
            "recovery_request_note": "只能提交重载申请，不自动重载服务",
        },
        {
            "id": "LRF-005",
            "scenario": "正式规则影响",
            "trigger": "任务会写入、覆盖、启用或自动转正式规则",
            "pause_reason": "正式规则变更需要人工确认，演练只保留候选草案",
            "registration_required": ["规则名称", "影响模块", "候选差异", "人工签收要求"],
            "recovery_request_note": "只能申请人工签收，不能自动转正式规则",
        },
        {
            "id": "LRF-006",
            "scenario": "外部接口需求",
            "trigger": "任务需要调用企业微信、n8n、券商、税局、财税软件或其他外部接口",
            "pause_reason": "外部接口调用不属于只读演练，必须暂停并登记接口需求",
            "registration_required": ["接口名称", "请求目的", "请求数据", "只读替代方案"],
            "recovery_request_note": "只能申请人工授权，不发起接口请求",
        },
    ]
    return {
        "name": "低风险自主任务失败暂停场景矩阵",
        "generated_at": generated_at,
        "readonly_drill_only": True,
        "scenario_count": len(scenarios),
        "global_policy": {
            "auto_continue_after_failure": False,
            "recovery_executed": False,
            "external_call": False,
            "reload_service": False,
            "real_wecom_send": False,
            "connect_n8n": False,
            "connect_broker": False,
            "trade": False,
            "login_tax_bureau": False,
            "connect_finance_tax_software": False,
            "promote_to_formal_rule": False,
            "modify_master_panel": False,
            "modify_one_click_continuation_package": False,
        },
        "scenarios": [{**base, **item} for item in scenarios],
    }


def build_recovery_template(generated_at: str) -> dict[str, Any]:
    return {
        "name": "低风险自主任务恢复申请模板",
        "generated_at": generated_at,
        "template_version": "readonly-drill-v1",
        "recovery_requested": False,
        "recovery_executed": False,
        "requires_supervisor_confirmation": True,
        "external_call": False,
        "reload_service": False,
        "auto_continue_after_failure": False,
        "readonly_drill_only": True,
        "allowed_status": ["draft", "submitted_for_supervisor_confirmation", "rejected", "approved_for_manual_handling"],
        "default_status": "draft",
        "fields": {
            "request_id": "",
            "source_scenario_id": "",
            "source_scenario": "",
            "failure_summary": "",
            "evidence_paths": [],
            "pause_registration_path": "",
            "requested_recovery_scope": "仅申请人工复核或只读复验",
            "supervisor_confirmation": {
                "required": True,
                "confirmed": False,
                "confirmed_by": "",
                "confirmed_at": "",
            },
            "execution_confirmation": {
                "recovery_executed": False,
                "executor": "",
                "executed_at": "",
                "execution_note": "本模板默认不执行恢复动作",
            },
        },
        "forbidden_recovery_actions": [
            "真实发送企业微信",
            "连接或触发 n8n",
            "连接券商或交易",
            "登录税局",
            "连接财税软件",
            "自动转正式规则",
            "修改总管面板",
            "修改一键接续包",
            "重载服务",
        ],
    }


def scenario_md(matrix: dict[str, Any]) -> str:
    rows = [
        "| {id} | {scenario} | {trigger} | {pause_required} | {continue_dispatch_allowed} | {recovery_executed} |".format(**item)
        for item in matrix["scenarios"]
    ]
    return "\n".join(
        [
            "# 低风险自主任务失败暂停场景矩阵",
            "",
            f"- 生成时间：{matrix['generated_at']}",
            "- 性质：只读演练矩阵，不执行恢复动作。",
            "- 统一策略：失败后不自动继续调度，恢复只能申请人工确认。",
            "",
            "| ID | 场景 | 触发条件 | pause_required | continue_dispatch_allowed | recovery_executed |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def recovery_md(template: dict[str, Any]) -> str:
    forbidden = "\n".join(f"- {item}" for item in template["forbidden_recovery_actions"])
    return "\n".join(
        [
            "# 低风险自主任务恢复申请模板",
            "",
            f"- 生成时间：{template['generated_at']}",
            f"- recovery_requested：{template['recovery_requested']}",
            f"- recovery_executed：{template['recovery_executed']}",
            f"- requires_supervisor_confirmation：{template['requires_supervisor_confirmation']}",
            f"- auto_continue_after_failure：{template['auto_continue_after_failure']}",
            f"- external_call：{template['external_call']}",
            f"- reload_service：{template['reload_service']}",
            "",
            "## 禁止恢复动作",
            "",
            forbidden,
            "",
            "## 使用口径",
            "",
            "- 本模板只登记恢复申请，不代表允许恢复。",
            "- 未取得总管确认前，recovery_requested 与 recovery_executed 均保持 false。",
            "",
        ]
    )


def package_md(package: dict[str, Any]) -> str:
    outputs = "\n".join(f"- {name}：{path}" for name, path in package["outputs"].items())
    return "\n".join(
        [
            "# 低风险自主任务失败暂停与恢复演练包",
            "",
            f"- 生成时间：{package['generated_at']}",
            f"- 状态：{package['status']}",
            "- 结论：只读演练资产已生成；失败暂停场景不继续调度，恢复动作不执行。",
            "",
            "## 安全确认",
            "",
            f"- auto_continue_after_failure：{package['safety_confirmation']['auto_continue_after_failure']}",
            f"- recovery_executed：{package['safety_confirmation']['recovery_executed']}",
            f"- external_call：{package['safety_confirmation']['external_call']}",
            f"- reload_service：{package['safety_confirmation']['reload_service']}",
            "",
            "## 输出文件",
            "",
            outputs,
            "",
        ]
    )


def main() -> int:
    generated_at = now()
    matrix = build_scenarios(generated_at)
    template = build_recovery_template(generated_at)
    package = {
        "name": "低风险自主任务失败暂停与恢复演练包",
        "generated_at": generated_at,
        "status": "readonly_failure_pause_recovery_drill_ready",
        "readonly_drill_only": True,
        "scenario_count": matrix["scenario_count"],
        "recovery_template_defaults": {
            "recovery_requested": template["recovery_requested"],
            "recovery_executed": template["recovery_executed"],
            "requires_supervisor_confirmation": template["requires_supervisor_confirmation"],
        },
        "safety_confirmation": {
            "auto_continue_after_failure": False,
            "recovery_executed": False,
            "external_call": False,
            "reload_service": False,
            "real_wecom_send": False,
            "connect_n8n": False,
            "connect_broker": False,
            "trade": False,
            "login_tax_bureau": False,
            "connect_finance_tax_software": False,
            "promote_to_formal_rule": False,
            "modify_master_panel": False,
            "modify_one_click_continuation_package": False,
        },
        "outputs": {
            "失败暂停场景矩阵JSON": str(SCENARIO_JSON),
            "失败暂停场景矩阵Markdown": str(SCENARIO_MD),
            "恢复申请模板JSON": str(RECOVERY_JSON),
            "恢复申请模板Markdown": str(RECOVERY_MD),
            "演练包JSON": str(PACKAGE_JSON),
            "演练包Markdown": str(PACKAGE_MD),
        },
    }

    write_json(SCENARIO_JSON, matrix)
    write_text(SCENARIO_MD, scenario_md(matrix))
    write_json(RECOVERY_JSON, template)
    write_text(RECOVERY_MD, recovery_md(template))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))
    write_json(
        GEN_LOG,
        {
            "name": "生成低风险自主任务失败暂停与恢复演练包",
            "generated_at": now(),
            "pass": True,
            "error_count": 0,
            "outputs": package["outputs"],
            "safety_confirmation": package["safety_confirmation"],
        },
    )
    print(json.dumps({"pass": True, "error_count": 0, "output": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
