# -*- coding: utf-8 -*-
"""
名称：执行P2S2影子试用入口只读准入检查.py
作用：检查 P2-S1 新增影子试用入口是否具备受控试用准入条件。
触发方式：python 执行P2S2影子试用入口只读准入检查.py
安全边界：只读读取文件、索引和 JSON 字段；仅在 03进化系统03数据输出检查报告；不触发 n8n，不发送企业微信，不写正式库，不重启服务。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
INCUBATION = ROOT / "02杰哥扩展系统" / "02-00孵化区"
STABLE_CLOSEOUT = ROOT / "00杰哥系统总管" / "03数据" / "稳定版正式收口_20260509"
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "51P2S2影子试用入口只读准入检查"
LATEST_JSON = OUTPUT_DIR / "P2S2影子试用入口只读准入检查_最新.json"
LATEST_MD = OUTPUT_DIR / "P2S2影子试用入口只读准入检查_最新.md"


ARTIFACTS = [
    {
        "id": "P2-S1-PACKAGE",
        "line": "governor",
        "md": STABLE_CLOSEOUT / "P2_S1_三线影子续建执行包_20260509.md",
        "json": STABLE_CLOSEOUT / "P2_S1_三线影子续建执行包_20260509.json",
        "index_files": [],
        "required_false_keys": [
            "trigger_n8n",
            "send_wecom",
            "write_formal_database",
            "call_broker_or_trade_api",
            "tax_filing_or_tax_external_action",
            "render_upload_or_publish_video",
            "claim_formal_capability",
        ],
    },
    {
        "id": "TAX_DAILY_INTAKE_002",
        "line": "tax",
        "md": INCUBATION / "税收业务影子底座" / "TAX_DAILY_INTAKE_002_脱敏问题接入空白卡_20260509.md",
        "json": INCUBATION / "税收业务影子底座" / "TAX_DAILY_INTAKE_002_脱敏问题接入空白卡_20260509.json",
        "index_files": [
            INCUBATION / "税收业务影子底座" / "税收影子底座索引_最新.md",
            INCUBATION / "税收业务影子底座" / "税收影子底座索引_最新.json",
            INCUBATION / "孵化区影子底座总索引_最新.md",
            INCUBATION / "孵化区影子底座总索引_最新.json",
        ],
        "required_false_keys": [
            "formal_tax_opinion",
            "tax_filing",
            "invoice_action",
            "tax_refund_action",
            "external_send",
            "trigger_n8n",
            "send_wecom",
            "write_formal_database",
        ],
        "must_have": {"fields.human_review_required": True},
    },
    {
        "id": "TAX_DAILY_DRAFT_002",
        "line": "tax",
        "md": INCUBATION / "税收业务影子底座" / "TAX_DAILY_DRAFT_002_待复核草案空白模板_20260509.md",
        "json": INCUBATION / "税收业务影子底座" / "TAX_DAILY_DRAFT_002_待复核草案空白模板_20260509.json",
        "index_files": [
            INCUBATION / "税收业务影子底座" / "税收影子底座索引_最新.md",
            INCUBATION / "税收业务影子底座" / "税收影子底座索引_最新.json",
            INCUBATION / "孵化区影子底座总索引_最新.md",
            INCUBATION / "孵化区影子底座总索引_最新.json",
        ],
        "required_false_keys": [
            "trigger_n8n",
            "send_wecom",
            "write_formal_database",
            "tax_filing",
            "tax_external_action",
            "claim_formal_opinion",
        ],
    },
    {
        "id": "OFFICE_SHADOW_002",
        "line": "office_work",
        "md": INCUBATION / "本职工作业务影子底座" / "OFFICE_SHADOW_002_流程资料登记_空白影子样例_v1.0.md",
        "json": INCUBATION / "本职工作业务影子底座" / "OFFICE_SHADOW_002_流程资料登记_空白影子样例_v1.0.json",
        "index_files": [
            INCUBATION / "本职工作业务影子底座" / "本职工作影子底座索引_最新.md",
            INCUBATION / "本职工作业务影子底座" / "本职工作影子底座索引_最新.json",
            INCUBATION / "孵化区影子底座总索引_最新.md",
            INCUBATION / "孵化区影子底座总索引_最新.json",
        ],
        "required_false_keys": [
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
        "must_have": {"human_review_required": True},
    },
    {
        "id": "VIDEO_P2_REVIEW_CHAIN_NEXT_001",
        "line": "video_production",
        "md": INCUBATION / "视频制作业务影子底座" / "VIDEO_P2_REVIEW_CHAIN_NEXT_001_脚本分镜素材授权发布门禁续建卡_20260509.md",
        "json": INCUBATION / "视频制作业务影子底座" / "VIDEO_P2_REVIEW_CHAIN_NEXT_001_脚本分镜素材授权发布门禁续建卡_20260509.json",
        "index_files": [
            INCUBATION / "视频制作业务影子底座" / "视频制作影子底座索引_最新.md",
            INCUBATION / "视频制作业务影子底座" / "视频制作影子底座索引_最新.json",
            INCUBATION / "孵化区影子底座总索引_最新.md",
            INCUBATION / "孵化区影子底座总索引_最新.json",
        ],
        "required_false_keys": [
            "render_final_video",
            "upload_video",
            "publish_video",
            "call_platform_api",
            "trigger_n8n",
            "send_wecom",
            "write_formal_database",
        ],
        "must_have": {"review_object.human_review_required": True},
        "release_gate_required": "closed",
    },
    {
        "id": "P2_SHARED_POLICY_READONLY_NEXT_001",
        "line": "shared_policy_evidence",
        "md": INCUBATION / "P2_SHARED_POLICY_READONLY_NEXT_001_共享政策证据只读调用下一步卡_20260509.md",
        "json": INCUBATION / "P2_SHARED_POLICY_READONLY_NEXT_001_共享政策证据只读调用下一步卡_20260509.json",
        "index_files": [
            INCUBATION / "孵化区影子底座总索引_最新.md",
            INCUBATION / "孵化区影子底座总索引_最新.json",
        ],
        "required_false_keys": [
            "trigger_n8n",
            "send_wecom",
            "write_formal_database",
            "replace_business_line_judgment",
            "claim_formal_capability",
        ],
        "must_have": {"fields.human_review_required": True},
    },
]


INDEX_FORMAL_CAPABILITY_CHECKS = [
    INCUBATION / "税收业务影子底座" / "税收影子底座索引_最新.json",
    INCUBATION / "本职工作业务影子底座" / "本职工作影子底座索引_最新.json",
    INCUBATION / "视频制作业务影子底座" / "视频制作影子底座索引_最新.json",
]


def read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")), None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def get_nested(data: dict[str, Any], dotted: str) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def check_artifact(item: dict[str, Any]) -> dict[str, Any]:
    md = Path(item["md"])
    json_path = Path(item["json"])
    errors: list[str] = []
    warnings: list[str] = []

    if not md.exists():
        errors.append(f"MD缺失：{md}")
    if not json_path.exists():
        errors.append(f"JSON缺失：{json_path}")

    data: dict[str, Any] | None = None
    if json_path.exists():
        data, parse_error = read_json(json_path)
        if parse_error:
            errors.append(f"JSON解析失败：{parse_error}")

    index_hits: list[dict[str, Any]] = []
    for index_path in item.get("index_files", []):
        index_path = Path(index_path)
        hit = False
        if index_path.exists():
            text = index_path.read_text(encoding="utf-8", errors="ignore")
            hit = json_path.name in text or md.name in text or item["id"] in text
        else:
            errors.append(f"索引缺失：{index_path}")
        index_hits.append({"索引": str(index_path), "命中": hit})
        if index_path.exists() and not hit:
            errors.append(f"索引未命中 {item['id']}：{index_path}")

    false_checks: list[dict[str, Any]] = []
    if data is not None:
        forbidden = data.get("forbidden_actions") or {}
        for key in item.get("required_false_keys", []):
            value = forbidden.get(key)
            ok = value is False
            false_checks.append({"字段": key, "值": value, "通过": ok})
            if not ok:
                errors.append(f"红线字段未保持 false：{key}={value}")

        for key, expected in item.get("must_have", {}).items():
            value = get_nested(data, key)
            if value != expected:
                errors.append(f"必备字段不符合：{key}={value}，期望 {expected}")

        gate_required = item.get("release_gate_required")
        if gate_required:
            chain = data.get("review_chain") or []
            release_gate = next((node for node in chain if node.get("step") == "release_gate"), None)
            actual = release_gate.get("status") if release_gate else None
            if actual != gate_required:
                errors.append(f"发布门禁状态异常：{actual}，期望 {gate_required}")

    if md.exists():
        md_text = md.read_text(encoding="utf-8", errors="ignore")
        boundary_keywords = ["不触发 n8n", "不发送企业微信", "不写正式库"]
        missing_boundary = [word for word in boundary_keywords if word not in md_text]
        if missing_boundary:
            warnings.append("MD边界提示不完整：" + "、".join(missing_boundary))

    return {
        "id": item["id"],
        "line": item["line"],
        "md": str(md),
        "json": str(json_path),
        "md_exists": md.exists(),
        "json_exists": json_path.exists(),
        "index_hits": index_hits,
        "redline_false_checks": false_checks,
        "warnings": warnings,
        "errors": errors,
        "status": "pass" if not errors else "fail",
    }


def check_index_formal_claims() -> list[dict[str, Any]]:
    results = []
    for path in INDEX_FORMAL_CAPABILITY_CHECKS:
        data, parse_error = read_json(path)
        if parse_error or data is None:
            results.append({"path": str(path), "status": "fail", "error": parse_error})
            continue
        claim = data.get("formal_capability_claim")
        results.append({
            "path": str(path),
            "formal_capability_claim": claim,
            "status": "pass" if claim is False else "fail",
        })
    return results


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P2-S2 影子试用入口只读准入检查",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['status']}",
        f"- 检查入口数：{report['summary']['artifact_count']}",
        f"- 通过数：{report['summary']['passed']}",
        f"- 失败数：{report['summary']['failed']}",
        f"- 红线字段检查数：{report['summary']['redline_false_check_count']}",
        "",
        "| 入口 | 业务线 | 状态 | 错误数 | 提醒数 |",
        "|:---|:---|:---|---:|---:|",
    ]
    for item in report["artifacts"]:
        lines.append(
            f"| {item['id']} | {item['line']} | {item['status']} | "
            f"{len(item['errors'])} | {len(item['warnings'])} |"
        )

    lines.extend([
        "",
        "## 准入结论",
        "",
        report["conclusion"],
        "",
        "## 安全边界",
        "",
        "- 本检查只读读取文件、索引和 JSON 字段。",
        "- 不触发 n8n，不发送企业微信，不写正式库。",
        "- 不重启服务，不交易，不办理税务，不渲染或发布视频。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    artifacts = [check_artifact(item) for item in ARTIFACTS]
    index_claims = check_index_formal_claims()
    failed = [item for item in artifacts if item["status"] != "pass"]
    index_failed = [item for item in index_claims if item["status"] != "pass"]
    redline_count = sum(len(item["redline_false_checks"]) for item in artifacts)
    status = "pass" if not failed and not index_failed else "fail"
    report = {
        "id": "P2S2_SHADOW_TRIAL_ENTRY_READONLY_ADMISSION_CHECK",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "summary": {
            "artifact_count": len(artifacts),
            "passed": len(artifacts) - len(failed),
            "failed": len(failed),
            "index_formal_claim_failed": len(index_failed),
            "redline_false_check_count": redline_count,
        },
        "artifacts": artifacts,
        "index_formal_capability_claims": index_claims,
        "conclusion": "P2-S1 影子试用入口可进入受控试用填卡前置阶段。" if status == "pass" else "存在准入缺口，需先修复后再进入受控试用。",
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
        "总体状态": status,
        "通过": report["summary"]["passed"],
        "失败": report["summary"]["failed"],
        "红线字段检查数": redline_count,
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
