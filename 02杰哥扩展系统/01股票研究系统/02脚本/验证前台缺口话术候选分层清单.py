from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
REPORT_JSON = DATA_DIR / "前台缺口话术候选分层清单_最新.json"
RESULT_JSON = DATA_DIR / "前台缺口话术候选分层清单验收_最新.json"
RESULT_MD = DATA_DIR / "前台缺口话术候选分层清单验收_最新.md"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_candidate(item: dict) -> list[str]:
    errors = []
    stock = item.get("stock", {}).get("name", "<unknown>")
    for key in ["candidate_text", "layer", "action_type", "reason", "can_implement_now", "next_gate"]:
        if key not in item:
            errors.append(f"{stock}: 缺少字段 {key}")
    if item.get("layer") == "W3_blocked":
        if item.get("can_implement_now") is not False:
            errors.append(f"{stock}: W3_blocked必须can_implement_now=false")
        if "总管" not in item.get("next_gate", "") and "正式" not in item.get("next_gate", ""):
            errors.append(f"{stock}: W3阻断必须标明总管或正式闸口")
    if item.get("layer") == "W1_rule_draft":
        if item.get("can_implement_now") is not True:
            errors.append(f"{stock}: W1_rule_draft应允许继续形成草案")
        if "适配器代码" in item.get("candidate_text", "") or "真实企业微信入口" in item.get("candidate_text", ""):
            errors.append(f"{stock}: W1_rule_draft不得包含正式入口/适配器写入")
    return errors


def render_md(result: dict) -> str:
    lines = [
        "# 前台缺口话术候选分层清单验收",
        "",
        f"- 验收时间：{result['validated_at']}",
        f"- 验收结果：{result['status']}",
        f"- 候选总数：{result['candidate_count']}",
        f"- 错误数量：{len(result['errors'])}",
        "",
        "## 统计",
        "",
        f"- W1话术规则草案：{result['summary']['w1_rule_draft_count']}",
        f"- W3阻断：{result['summary']['w3_blocked_count']}",
        f"- 待复核：{result['summary']['review_needed_count']}",
        "",
        "## 边界",
        "",
        "- 未修改短答适配器",
        "- 未修改企业微信入口",
        "- 未发送企业微信",
        "- 未重启服务",
        "- 未接n8n",
        "- 未接券商接口",
        "- 未自动交易"
    ]
    if result["errors"]:
        lines.extend(["", "## 错误", ""])
        lines.extend([f"- {err}" for err in result["errors"]])
    return "\n".join(lines) + "\n"


def main() -> None:
    report = read_json(REPORT_JSON)
    candidates = report.get("candidates", [])
    errors = []
    for key in ["not_formal_config", "not_entrypoint", "not_external_send", "not_adapter_write", "not_score_write"]:
        if report.get(key) is not True:
            errors.append(f"report.{key} 必须为true")
    for key in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_adapter_write", "not_score_write", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if report.get("safety_boundary", {}).get(key) is not True:
            errors.append(f"safety_boundary.{key} 必须为true")
    for item in candidates:
        errors.extend(validate_candidate(item))
    summary = report.get("summary", {})
    if summary.get("candidate_count") != len(candidates):
        errors.append("summary.candidate_count与实际数量不一致")
    if summary.get("w1_rule_draft_count", 0) <= 0:
        errors.append("必须至少有一条W1话术规则草案")
    if summary.get("w3_blocked_count", 0) <= 0:
        errors.append("必须登记W3阻断项")

    result = {
        "名称": "前台缺口话术候选分层清单验收",
        "validated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "passed" if not errors else "failed",
        "candidate_count": len(candidates),
        "summary": summary,
        "errors": errors,
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_adapter_write": True,
            "not_score_write": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True
        }
    }
    write_json(RESULT_JSON, result)
    RESULT_MD.write_text(render_md(result), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "candidate_count": len(candidates),
        "errors": len(errors),
        "result_json": str(RESULT_JSON),
        "result_md": str(RESULT_MD)
    }, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
