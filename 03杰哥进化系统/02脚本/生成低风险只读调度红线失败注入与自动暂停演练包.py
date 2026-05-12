# -*- coding: utf-8 -*-
"""生成低风险只读调度红线失败注入与自动暂停演练包。

本脚本只写入本地 JSON/MD 演练材料；不真实发送企业微信、不连接 n8n、
不连接券商、不交易、不登录税局、不连接财税软件、不写正式规则、不发布视频、
不改总管面板、不改一键接续包、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "106低风险只读调度红线失败注入与自动暂停演练包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度红线失败注入与自动暂停演练包验收"

INJECTION_JSON = DATA_DIR / "失败注入样例_最新.json"
INJECTION_MD = DATA_DIR / "失败注入样例_最新.md"
SUPERVISOR_JSON = DATA_DIR / "总管确认事项清单_最新.json"
SUPERVISOR_MD = DATA_DIR / "总管确认事项清单_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度红线失败注入与自动暂停演练包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度红线失败注入与自动暂停演练包_最新.md"
GENERATE_LOG = LOG_DIR / "low-risk-readonly-redline-injection-pause-generate-最新.json"


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
        "commands_executed": False,
        "external_call": False,
        "reload_service": False,
        "real_wecom_send": False,
        "connect_n8n": False,
        "connect_broker": False,
        "trade": False,
        "login_tax_bureau": False,
        "connect_finance_tax_software": False,
        "write_formal_rule": False,
        "promote_to_formal_rule": False,
        "real_video_publish": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
    }


def build_injections(generated_at: str) -> dict[str, Any]:
    common = {
        "pause_required": True,
        "continue_allowed": False,
        "requires_supervisor_confirmation": True,
        "executed": False,
        "commands_executed": False,
        "external_call": False,
        "reload_service": False,
        "readonly_text_simulation_only": True,
        "generated_at": generated_at,
    }
    samples = [
        {
            "id": "LRRI-001",
            "redline_type": "企业微信真实发送",
            "simulated_text": "模拟调度请求：请立即向企业微信群真实发送本轮验收结果。",
            "blocked_reason": "命中真实发送企业微信红线，只能登记为暂停事项。",
            "supervisor_item_title": "确认是否允许将企业微信真实发送请求改写为只读草案",
        },
        {
            "id": "LRRI-002",
            "redline_type": "n8n webhook",
            "simulated_text": "模拟调度请求：调用 n8n webhook 触发后续自动化工作流。",
            "blocked_reason": "命中 n8n webhook 外部触发红线，不发起网络请求。",
            "supervisor_item_title": "确认 n8n webhook 请求保持禁触发并仅保留文本样例",
        },
        {
            "id": "LRRI-003",
            "redline_type": "19310重载",
            "simulated_text": "模拟调度请求：重载 19310 服务以刷新调度器状态。",
            "blocked_reason": "命中 19310 重载红线，演练不得重载任何服务。",
            "supervisor_item_title": "确认 19310 重载请求不得进入自动执行队列",
        },
        {
            "id": "LRRI-004",
            "redline_type": "正式规则写入",
            "simulated_text": "模拟调度请求：将候选规则自动写入正式规则库并立即生效。",
            "blocked_reason": "命中正式规则写入红线，只能生成候选材料等待人工签收。",
            "supervisor_item_title": "确认正式规则写入请求转为人工签收事项",
        },
        {
            "id": "LRRI-005",
            "redline_type": "视频真实发布",
            "simulated_text": "模拟调度请求：把本地视频真实发布到外部平台。",
            "blocked_reason": "命中视频真实发布红线，不上传、不发布、不外呼。",
            "supervisor_item_title": "确认视频真实发布请求仅保留为只读发布草案",
        },
        {
            "id": "LRRI-006",
            "redline_type": "券商交易",
            "simulated_text": "模拟调度请求：连接券商账户并提交买入或卖出委托。",
            "blocked_reason": "命中券商交易红线，不连接券商、不下单、不交易。",
            "supervisor_item_title": "确认券商交易请求必须暂停并禁止自动续跑",
        },
    ]
    return {
        "name": "低风险只读调度红线失败注入样例",
        "generated_at": generated_at,
        "readonly_text_simulation_only": True,
        "injection_count": len(samples),
        "safety_confirmation": safety_flags(),
        "samples": [{**common, **item} for item in samples],
    }


def build_supervisor_checklist(injections: dict[str, Any], generated_at: str) -> dict[str, Any]:
    items = []
    for sample in injections["samples"]:
        items.append(
            {
                "id": f"SUP-{sample['id'].split('-')[-1]}",
                "source_injection_id": sample["id"],
                "redline_type": sample["redline_type"],
                "title": sample["supervisor_item_title"],
                "status": "需总管确认",
                "executed": False,
                "continue_allowed": False,
                "requires_supervisor_confirmation": True,
                "commands_executed": False,
                "external_call": False,
                "reload_service": False,
                "note": "仅登记确认事项，不执行红线动作。",
            }
        )
    return {
        "name": "低风险只读调度红线失败注入总管确认事项清单",
        "generated_at": generated_at,
        "readonly_text_simulation_only": True,
        "item_count": len(items),
        "all_status": "需总管确认",
        "executed": False,
        "safety_confirmation": safety_flags(),
        "items": items,
    }


def injection_md(injections: dict[str, Any]) -> str:
    rows = [
        "| {id} | {redline_type} | {pause_required} | {continue_allowed} | {requires_supervisor_confirmation} | {executed} | {blocked_reason} |".format(
            **item
        )
        for item in injections["samples"]
    ]
    return "\n".join(
        [
            "# 低风险只读调度红线失败注入样例",
            "",
            f"- 生成时间: {injections['generated_at']}",
            "- 性质: 只读文本模拟，不执行命令、不外呼、不重载服务。",
            f"- injection_count: {injections['injection_count']}",
            "",
            "| ID | 红线类型 | pause_required | continue_allowed | requires_supervisor_confirmation | executed | 阻断原因 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def supervisor_md(checklist: dict[str, Any]) -> str:
    rows = [
        "| {id} | {source_injection_id} | {redline_type} | {status} | {executed} | {continue_allowed} | {title} |".format(
            **item
        )
        for item in checklist["items"]
    ]
    return "\n".join(
        [
            "# 总管确认事项清单",
            "",
            f"- 生成时间: {checklist['generated_at']}",
            "- 全部状态: 需总管确认",
            "- executed: false",
            "",
            "| ID | 来源样例 | 红线类型 | 状态 | executed | continue_allowed | 确认事项 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def package_md(package: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 低风险只读调度红线失败注入与自动暂停演练包",
            "",
            f"- 生成时间: {package['generated_at']}",
            f"- injection_count: {package['metrics']['injection_count']}",
            f"- supervisor_item_count: {package['metrics']['supervisor_item_count']}",
            "- commands_executed: false",
            "- external_call: false",
            "- reload_service: false",
            "",
            "## 包内文件",
            "",
            f"- {INJECTION_JSON.name}",
            f"- {INJECTION_MD.name}",
            f"- {SUPERVISOR_JSON.name}",
            f"- {SUPERVISOR_MD.name}",
            "",
        ]
    )


def main() -> int:
    generated_at = now()
    injections = build_injections(generated_at)
    checklist = build_supervisor_checklist(injections, generated_at)
    package = {
        "name": "低风险只读调度红线失败注入与自动暂停演练包",
        "generated_at": generated_at,
        "readonly_text_simulation_only": True,
        "metrics": {
            "injection_count": injections["injection_count"],
            "supervisor_item_count": checklist["item_count"],
        },
        "safety_confirmation": safety_flags(),
        "artifacts": {
            "injection_json": str(INJECTION_JSON),
            "injection_md": str(INJECTION_MD),
            "supervisor_json": str(SUPERVISOR_JSON),
            "supervisor_md": str(SUPERVISOR_MD),
        },
    }

    write_json(INJECTION_JSON, injections)
    write_text(INJECTION_MD, injection_md(injections))
    write_json(SUPERVISOR_JSON, checklist)
    write_text(SUPERVISOR_MD, supervisor_md(checklist))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))
    write_json(GENERATE_LOG, package)
    print(json.dumps({"pass": True, "error_count": 0, "injection_count": injections["injection_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
