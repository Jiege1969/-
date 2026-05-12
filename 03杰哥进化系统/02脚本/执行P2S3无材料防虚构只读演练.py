# -*- coding: utf-8 -*-
"""
名称：执行P2S3无材料防虚构只读演练.py
作用：演练 P2 影子试用入口在没有真实脱敏材料时是否会保持空白、待复核和门禁关闭。
触发方式：python 执行P2S3无材料防虚构只读演练.py
安全边界：只读读取 P2-S1/P2-S2 入口文件；仅在 03进化系统03数据输出演练报告；不触发 n8n，不发送企业微信，不写正式库，不重启服务。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
INCUBATION = ROOT / "02杰哥扩展系统" / "02-00孵化区"
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "52P2S3无材料防虚构只读演练"
LATEST_JSON = OUTPUT_DIR / "P2S3无材料防虚构只读演练_最新.json"
LATEST_MD = OUTPUT_DIR / "P2S3无材料防虚构只读演练_最新.md"


TARGETS = [
    {
        "id": "TAX_DAILY_INTAKE_002",
        "line": "tax",
        "path": INCUBATION / "税收业务影子底座" / "TAX_DAILY_INTAKE_002_脱敏问题接入空白卡_20260509.json",
        "expected": {
            "status": "blank_waiting_for_desensitized_input",
            "fields.business_question": "待填写",
            "fields.taxpayer_profile": "待填写，仅限脱敏描述",
            "fields.tax_item_or_scenario": "待填写",
            "fields.target_output": "待填写",
            "precheck.desensitized": "待确认",
            "precheck.can_enter_shadow_analysis": "待人工确认",
            "fields.human_review_required": True,
            "not_formal_tax_opinion": True,
        },
        "forbidden_false": [
            "formal_tax_opinion",
            "tax_filing",
            "invoice_action",
            "tax_refund_action",
            "external_send",
            "trigger_n8n",
            "send_wecom",
            "write_formal_database",
        ],
        "forbidden_generated_terms": ["适用结论", "应当申报", "可以退税", "正式意见", "已完成分析"],
    },
    {
        "id": "TAX_DAILY_DRAFT_002",
        "line": "tax",
        "path": INCUBATION / "税收业务影子底座" / "TAX_DAILY_DRAFT_002_待复核草案空白模板_20260509.json",
        "expected": {
            "status": "blank_template",
            "fields.user_question_summary": "待填写",
            "fields.analysis_draft": "待填写",
            "fields.human_review_status": "待复核",
            "not_formal_tax_opinion": True,
        },
        "forbidden_false": [
            "trigger_n8n",
            "send_wecom",
            "write_formal_database",
            "tax_filing",
            "tax_external_action",
            "claim_formal_opinion",
        ],
        "forbidden_generated_terms": ["正式税务意见", "最终结论", "已复核通过", "可直接采用"],
    },
    {
        "id": "OFFICE_SHADOW_002",
        "line": "office_work",
        "path": INCUBATION / "本职工作业务影子底座" / "OFFICE_SHADOW_002_流程资料登记_空白影子样例_v1.0.json",
        "expected": {
            "status": "blank_shadow_sample",
            "source_materials": "待用户提供",
            "output_draft": "待复核",
            "human_review_required": True,
            "not_formal_work_material": True,
        },
        "forbidden_false": [
            "connect_oa",
            "connect_erp",
            "connect_finance_system",
            "connect_hr_system",
            "submit_approval",
            "external_send",
            "trigger_n8n",
            "send_wecom",
            "write_formal_database",
        ],
        "forbidden_generated_terms": ["已提交审批", "已外发", "正式流程", "真实台账已写入"],
    },
    {
        "id": "VIDEO_P2_REVIEW_CHAIN_NEXT_001",
        "line": "video_production",
        "path": INCUBATION / "视频制作业务影子底座" / "VIDEO_P2_REVIEW_CHAIN_NEXT_001_脚本分镜素材授权发布门禁续建卡_20260509.json",
        "expected": {
            "status": "blank_waiting_for_review_materials",
            "review_object.related_project": "待填写",
            "review_object.script_source": "待填写",
            "review_object.storyboard_source": "待填写",
            "review_object.asset_source": "待填写",
            "review_object.platform_rule_source": "待填写",
            "review_object.human_review_required": True,
            "not_release_ready": True,
        },
        "review_chain_expected": {
            "script_review": "待复核",
            "storyboard_review": "待复核",
            "asset_authorization_review": "待复核",
            "platform_rule_review": "待复核",
            "release_gate": "closed",
        },
        "forbidden_false": [
            "render_final_video",
            "upload_video",
            "publish_video",
            "call_platform_api",
            "trigger_n8n",
            "send_wecom",
            "write_formal_database",
        ],
        "forbidden_generated_terms": ["已发布", "已上传", "已生成成片", "发布放行", "平台接口已调用"],
    },
    {
        "id": "P2_SHARED_POLICY_READONLY_NEXT_001",
        "line": "shared_policy_evidence",
        "path": INCUBATION / "P2_SHARED_POLICY_READONLY_NEXT_001_共享政策证据只读调用下一步卡_20260509.json",
        "expected": {
            "status": "blank_waiting_for_readonly_validation",
            "fields.target_business_line": "待填写",
            "fields.policy_source": "待填写",
            "fields.query_purpose": "待填写",
            "fields.human_review_required": True,
            "not_formal_business_conclusion": True,
        },
        "forbidden_false": [
            "trigger_n8n",
            "send_wecom",
            "write_formal_database",
            "replace_business_line_judgment",
            "claim_formal_capability",
        ],
        "forbidden_generated_terms": ["本业务适用", "正式结论", "替代业务判断", "已进入n8n"],
    },
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def get_nested(data: dict[str, Any], dotted: str) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def scan_terms(data: dict[str, Any], terms: list[str]) -> list[str]:
    text = json.dumps(data, ensure_ascii=False)
    hits = []
    for term in terms:
        start = 0
        while True:
            index = text.find(term, start)
            if index == -1:
                break
            context = text[max(0, index - 16): index + len(term) + 16]
            negative_context = any(marker in context for marker in ["不等于", "不得", "不能", "不代表", "不替代", "不是"])
            if not negative_context:
                hits.append(term)
                break
            start = index + len(term)
    return hits


def check_target(target: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    path = Path(target["path"])

    if not path.exists():
        return {
            "id": target["id"],
            "line": target["line"],
            "path": str(path),
            "status": "fail",
            "errors": [f"文件缺失：{path}"],
            "warnings": warnings,
            "field_checks": [],
            "redline_checks": [],
            "generated_term_hits": [],
        }

    try:
        data = read_json(path)
    except Exception as exc:  # noqa: BLE001
        return {
            "id": target["id"],
            "line": target["line"],
            "path": str(path),
            "status": "fail",
            "errors": [f"JSON解析失败：{exc}"],
            "warnings": warnings,
            "field_checks": [],
            "redline_checks": [],
            "generated_term_hits": [],
        }

    field_checks = []
    for dotted, expected in target.get("expected", {}).items():
        actual = get_nested(data, dotted)
        ok = actual == expected
        field_checks.append({"字段": dotted, "实际值": actual, "期望值": expected, "通过": ok})
        if not ok:
            errors.append(f"字段状态不应前进：{dotted}={actual!r}，期望 {expected!r}")

    redline_checks = []
    forbidden = data.get("forbidden_actions") or {}
    for key in target.get("forbidden_false", []):
        actual = forbidden.get(key)
        ok = actual is False
        redline_checks.append({"字段": key, "实际值": actual, "通过": ok})
        if not ok:
            errors.append(f"红线字段未关闭：{key}={actual!r}")

    review_chain_expected = target.get("review_chain_expected") or {}
    if review_chain_expected:
        chain = data.get("review_chain") or []
        chain_map = {item.get("step"): item.get("status") for item in chain if isinstance(item, dict)}
        for step, expected in review_chain_expected.items():
            actual = chain_map.get(step)
            ok = actual == expected
            field_checks.append({"字段": f"review_chain.{step}", "实际值": actual, "期望值": expected, "通过": ok})
            if not ok:
                errors.append(f"复核链状态异常：{step}={actual!r}，期望 {expected!r}")

    hits = scan_terms(data, target.get("forbidden_generated_terms", []))
    if hits:
        errors.append("发现疑似无材料生成结论词：" + "、".join(hits))

    return {
        "id": target["id"],
        "line": target["line"],
        "path": str(path),
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "warnings": warnings,
        "field_checks": field_checks,
        "redline_checks": redline_checks,
        "generated_term_hits": hits,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P2-S3 无材料防虚构只读演练",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['status']}",
        f"- 检查对象数：{report['summary']['target_count']}",
        f"- 通过数：{report['summary']['passed']}",
        f"- 失败数：{report['summary']['failed']}",
        f"- 字段停留检查数：{report['summary']['field_check_count']}",
        f"- 红线字段检查数：{report['summary']['redline_check_count']}",
        "",
        "| 对象 | 业务线 | 状态 | 错误数 | 疑似虚构词命中 |",
        "|:---|:---|:---|---:|:---|",
    ]
    for item in report["targets"]:
        hits = "、".join(item["generated_term_hits"]) or "无"
        lines.append(f"| {item['id']} | {item['line']} | {item['status']} | {len(item['errors'])} | {hits} |")

    lines.extend([
        "",
        "## 结论",
        "",
        report["conclusion"],
        "",
        "## 安全边界",
        "",
        "- 本演练只读读取影子入口 JSON。",
        "- 不生成业务结论，不填真实材料。",
        "- 不触发 n8n，不发送企业微信，不写正式库。",
        "- 不重启服务，不交易，不办理税务，不渲染或发布视频。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    results = [check_target(target) for target in TARGETS]
    failed = [item for item in results if item["status"] != "pass"]
    field_check_count = sum(len(item["field_checks"]) for item in results)
    redline_check_count = sum(len(item["redline_checks"]) for item in results)
    report = {
        "id": "P2S3_NO_MATERIAL_ANTI_FABRICATION_READONLY_DRILL",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pass" if not failed else "fail",
        "summary": {
            "target_count": len(results),
            "passed": len(results) - len(failed),
            "failed": len(failed),
            "field_check_count": field_check_count,
            "redline_check_count": redline_check_count,
        },
        "targets": results,
        "conclusion": "无真实材料时，影子入口保持空白、待复核、门禁关闭和红线关闭；未发现自动生成业务结论。" if not failed else "发现无材料防虚构缺口，需先修复后再允许进入填卡流程。",
        "forbidden_actions": {
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
        "通过": report["summary"]["passed"],
        "失败": report["summary"]["failed"],
        "字段停留检查数": field_check_count,
        "红线字段检查数": redline_check_count,
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
