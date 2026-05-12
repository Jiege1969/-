# -*- coding: utf-8 -*-
"""
名称：执行P2S5真实材料接入分流门场景干跑.py
作用：用内置脱敏虚拟样例演练 P2-S4 分流门的路由和暂停判断。
触发方式：python 执行P2S5真实材料接入分流门场景干跑.py
安全边界：不读取真实材料，不扫描用户目录；仅在 03进化系统03数据输出干跑报告；不触发 n8n，不发送企业微信，不写正式库，不重启服务。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
INCUBATION = ROOT / "02杰哥扩展系统" / "02-00孵化区"
GATE_JSON = INCUBATION / "P2_REAL_MATERIAL_INTAKE_GATE_001_真实材料接入分流门_20260509.json"
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "54P2S5真实材料接入分流门场景干跑"
LATEST_JSON = OUTPUT_DIR / "P2S5真实材料接入分流门场景干跑_最新.json"
LATEST_MD = OUTPUT_DIR / "P2S5真实材料接入分流门场景干跑_最新.md"


SCENARIOS = [
    {
        "case_id": "P2S5-CASE-001",
        "name": "脱敏涉税问题进入税收影子入口",
        "material": {
            "source_type": "用户提供",
            "authorization_status": "已授权",
            "sensitivity": "无敏感",
            "desensitized_status": "已脱敏",
            "material_type": "涉税业务分析材料",
            "request_text": "请分析某类软件产品增值税政策适用条件，信息已脱敏，仅需待复核草案。",
        },
        "expected_target_line": "tax",
        "expected_next_allowed_action": "登记资料",
        "expected_can_enter_shadow": "是",
    },
    {
        "case_id": "P2S5-CASE-002",
        "name": "制度流程资料进入本职工作影子入口",
        "material": {
            "source_type": "用户提供",
            "authorization_status": "已授权",
            "sensitivity": "无敏感",
            "desensitized_status": "已脱敏",
            "material_type": "制度流程",
            "request_text": "请整理一份已脱敏的内部流程资料字段，供影子样例复核。",
        },
        "expected_target_line": "office_work",
        "expected_next_allowed_action": "登记资料",
        "expected_can_enter_shadow": "是",
    },
    {
        "case_id": "P2S5-CASE-003",
        "name": "视频脚本分镜素材进入视频复核链",
        "material": {
            "source_type": "用户提供",
            "authorization_status": "已授权",
            "sensitivity": "素材版权",
            "desensitized_status": "已脱敏",
            "material_type": "脚本分镜素材授权",
            "request_text": "请复核一份脱敏脚本、分镜和素材授权说明，不生成不发布。",
        },
        "expected_target_line": "video_production",
        "expected_next_allowed_action": "登记资料",
        "expected_can_enter_shadow": "是",
    },
    {
        "case_id": "P2S5-CASE-004",
        "name": "公开政策来源进入共享政策证据入口",
        "material": {
            "source_type": "官方公开",
            "authorization_status": "仅参考",
            "sensitivity": "无敏感",
            "desensitized_status": "不适用",
            "material_type": "政策依据候选",
            "request_text": "请登记一个公开政策来源作为依据候选，不替代业务线判断。",
        },
        "expected_target_line": "shared_policy_evidence",
        "expected_next_allowed_action": "登记资料",
        "expected_can_enter_shadow": "是",
    },
    {
        "case_id": "P2S5-CASE-005",
        "name": "未脱敏财务资料暂停",
        "material": {
            "source_type": "用户提供",
            "authorization_status": "待确认",
            "sensitivity": "财务",
            "desensitized_status": "未脱敏",
            "material_type": "涉税业务分析材料",
            "request_text": "资料含未脱敏财务明细，请直接分析。",
        },
        "expected_target_line": "pause",
        "expected_next_allowed_action": "暂停",
        "expected_can_enter_shadow": "否",
    },
    {
        "case_id": "P2S5-CASE-006",
        "name": "真实执行请求暂停",
        "material": {
            "source_type": "用户提供",
            "authorization_status": "已授权",
            "sensitivity": "无敏感",
            "desensitized_status": "已脱敏",
            "material_type": "视频发布请求",
            "request_text": "请上传并发布这个视频，同时发送企业微信通知。",
        },
        "expected_target_line": "pause",
        "expected_next_allowed_action": "暂停",
        "expected_can_enter_shadow": "否",
    },
    {
        "case_id": "P2S5-CASE-007",
        "name": "来源不清材料暂停",
        "material": {
            "source_type": "待核验",
            "authorization_status": "待确认",
            "sensitivity": "待判",
            "desensitized_status": "待确认",
            "material_type": "未知材料",
            "request_text": "这是一份来源不清的材料，请先帮我处理。",
        },
        "expected_target_line": "pause",
        "expected_next_allowed_action": "暂停",
        "expected_can_enter_shadow": "否",
    },
]


REAL_ACTION_TERMS = [
    "申报",
    "开票",
    "退税",
    "交易",
    "审批",
    "发布",
    "外发",
    "发送企业微信",
    "触发n8n",
    "触发 n8n",
    "写正式库",
]

NEGATIVE_CONTEXT_MARKERS = ["不", "不再", "不得", "不能", "不允许", "不生成", "不上传", "不发布", "不外发", "不触发", "不发送"]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def route_material(material: dict[str, Any]) -> dict[str, Any]:
    text = material.get("request_text", "")
    material_type = material.get("material_type", "")
    source_type = material.get("source_type", "")
    authorization = material.get("authorization_status", "")
    sensitivity = material.get("sensitivity", "")
    desensitized = material.get("desensitized_status", "")

    pause_reasons: list[str] = []
    if source_type == "待核验":
        pause_reasons.append("来源不清")
    if authorization in {"禁止使用", "待确认"}:
        pause_reasons.append("授权未确认")
    if sensitivity in {"财务", "人事", "合同", "客户", "账号", "素材版权", "待判"} and desensitized not in {"已脱敏", "不适用"}:
        pause_reasons.append("敏感内容未脱敏")
    real_action_hit = False
    for term in REAL_ACTION_TERMS:
        start = 0
        while True:
            index = text.find(term, start)
            if index == -1:
                break
            context = text[max(0, index - 6): index + len(term) + 6]
            if not any(marker in context for marker in NEGATIVE_CONTEXT_MARKERS):
                real_action_hit = True
                break
            start = index + len(term)
        if real_action_hit:
            break
    if real_action_hit:
        pause_reasons.append("命中真实执行请求")

    if pause_reasons:
        can_enter = "待确认" if "来源不清" in pause_reasons and len(pause_reasons) == 1 else "否"
        return {
            "target_line": "pause",
            "entry": "gap_or_redline_record",
            "can_enter_shadow": can_enter,
            "next_allowed_action": "暂停",
            "pause_reasons": pause_reasons,
            "human_review_required": True,
        }

    if "涉税" in material_type or "税" in text:
        target = "tax"
    elif "制度" in material_type or "流程" in material_type or "办公" in text:
        target = "office_work"
    elif "视频" in material_type or "脚本" in material_type or "分镜" in material_type or "素材" in material_type:
        target = "video_production"
    elif "政策" in material_type or source_type == "官方公开":
        target = "shared_policy_evidence"
    else:
        target = "pause"

    return {
        "target_line": target,
        "entry": target,
        "can_enter_shadow": "是" if target != "pause" else "待确认",
        "next_allowed_action": "登记资料" if target != "pause" else "暂停",
        "pause_reasons": [],
        "human_review_required": True,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P2-S5 真实材料接入分流门场景干跑",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['status']}",
        f"- 场景数：{report['summary']['case_count']}",
        f"- 通过数：{report['summary']['passed']}",
        f"- 失败数：{report['summary']['failed']}",
        "",
        "| 场景 | 期望路由 | 实际路由 | 状态 | 暂停原因 |",
        "|:---|:---|:---|:---|:---|",
    ]
    for item in report["cases"]:
        reasons = "、".join(item["actual"]["pause_reasons"]) or "无"
        lines.append(
            f"| {item['case_id']} {item['name']} | {item['expected']['target_line']} | "
            f"{item['actual']['target_line']} | {item['status']} | {reasons} |"
        )
    lines.extend([
        "",
        "## 结论",
        "",
        report["conclusion"],
        "",
        "## 安全边界",
        "",
        "- 本干跑使用内置脱敏虚拟样例。",
        "- 不读取真实材料，不扫描用户目录。",
        "- 不触发 n8n，不发送企业微信，不写正式库。",
        "- 不重启服务，不交易，不办理税务，不渲染或发布视频。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    gate = read_json(GATE_JSON)
    route_names = {route.get("target_line") for route in gate.get("routes", []) if isinstance(route, dict)}
    cases = []
    errors = []
    for scenario in SCENARIOS:
        actual = route_material(scenario["material"])
        expected = {
            "target_line": scenario["expected_target_line"],
            "next_allowed_action": scenario["expected_next_allowed_action"],
            "can_enter_shadow": scenario["expected_can_enter_shadow"],
        }
        checks = {
            "target_line": actual["target_line"] == expected["target_line"],
            "next_allowed_action": actual["next_allowed_action"] == expected["next_allowed_action"],
            "can_enter_shadow": actual["can_enter_shadow"] == expected["can_enter_shadow"],
            "human_review_required": actual["human_review_required"] is True,
            "target_route_registered": actual["target_line"] in route_names,
        }
        status = "pass" if all(checks.values()) else "fail"
        if status != "pass":
            errors.append({"case_id": scenario["case_id"], "checks": checks, "actual": actual, "expected": expected})
        cases.append({
            "case_id": scenario["case_id"],
            "name": scenario["name"],
            "material": scenario["material"],
            "expected": expected,
            "actual": actual,
            "checks": checks,
            "status": status,
        })

    failed = [case for case in cases if case["status"] != "pass"]
    report = {
        "id": "P2S5_REAL_MATERIAL_INTAKE_GATE_SCENARIO_DRYRUN",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pass" if not failed else "fail",
        "summary": {
            "case_count": len(cases),
            "passed": len(cases) - len(failed),
            "failed": len(failed),
            "registered_routes": sorted(route_names),
        },
        "cases": cases,
        "errors": errors,
        "conclusion": "分流门场景干跑通过；税收、本职工作、视频、共享政策证据和暂停路径均按预期路由。" if not failed else "分流门场景干跑存在失败场景，需修复后再接入真实材料。",
        "forbidden_actions": {
            "read_real_material": False,
            "scan_user_directory": False,
            "trigger_n8n": False,
            "send_wecom": False,
            "write_formal_database": False,
            "restart_service": False,
            "trade": False,
            "tax_filing": False,
            "render_or_publish_video": False,
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "总体状态": report["status"],
        "场景数": report["summary"]["case_count"],
        "通过": report["summary"]["passed"],
        "失败": report["summary"]["failed"],
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
