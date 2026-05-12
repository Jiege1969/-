from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
REPORT_JSON = DATA_DIR / "五样本前台缺口压缩差异对照_最新.json"
RESULT_JSON = DATA_DIR / "五样本前台缺口压缩差异对照验收_最新.json"
RESULT_MD = DATA_DIR / "五样本前台缺口压缩差异对照验收_最新.md"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_item(item: dict) -> list[str]:
    errors = []
    name = item.get("stock", {}).get("name", "<unknown>")
    for key in ["current_why_line", "current_missing_line", "preview_gap_line", "alignment_findings", "blocked_formal_changes"]:
        if key not in item:
            errors.append(f"{name}: 缺少字段 {key}")
    if item.get("current_reply_status") != "available":
        errors.append(f"{name}: 当前短答不可用")
    if not item.get("adapter_passed"):
        errors.append(f"{name}: 当前适配器样本未通过")
    if not item.get("alignment_findings"):
        errors.append(f"{name}: 差异发现不能为空")
    blocked = " ".join(item.get("blocked_formal_changes", []))
    for phrase in ["正式候选脚本变更", "真实企业微信入口", "本轮只登记不实施"]:
        if phrase not in blocked:
            errors.append(f"{name}: 阻断登记缺少 {phrase}")
    return errors


def render_md(result: dict) -> str:
    lines = [
        "# 五样本前台缺口压缩差异对照验收",
        "",
        f"- 验收时间：{result['validated_at']}",
        f"- 验收结果：{result['status']}",
        f"- 覆盖样本：{result['sample_count']}",
        f"- 错误数量：{len(result['errors'])}",
        "",
        "## 明细",
        "",
        "| 股票 | 当前短答 | 适配器通过 | 差异发现数 | 阻断登记数 |",
        "|---|---|---|---:|---:|"
    ]
    for item in result["items"]:
        lines.append(
            f"| {item['stock']} | {item['current_reply_status']} | {item['adapter_passed']} | "
            f"{item['finding_count']} | {item['blocked_count']} |"
        )
    if result["errors"]:
        lines.extend(["", "## 错误", ""])
        lines.extend([f"- {err}" for err in result["errors"]])
    lines.extend([
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
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    report = read_json(REPORT_JSON)
    items = report.get("items", [])
    errors = []
    if len(items) != 5:
        errors.append("items数量必须为5")
    for key in ["not_formal_config", "not_entrypoint", "not_external_send", "not_score_write", "not_adapter_write"]:
        if report.get(key) is not True:
            errors.append(f"report.{key} 必须为true")
    for key in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_score_write", "not_adapter_write", "not_entrypoint", "not_broker_interface", "not_auto_trade"]:
        if report.get("safety_boundary", {}).get(key) is not True:
            errors.append(f"safety_boundary.{key} 必须为true")
    for item in items:
        errors.extend(validate_item(item))

    result = {
        "名称": "五样本前台缺口压缩差异对照验收",
        "validated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "passed" if not errors else "failed",
        "sample_count": len(items),
        "errors": errors,
        "items": [
            {
                "stock": item.get("stock", {}).get("name", ""),
                "code": item.get("stock", {}).get("code", ""),
                "current_reply_status": item.get("current_reply_status", ""),
                "adapter_passed": item.get("adapter_passed", False),
                "finding_count": len(item.get("alignment_findings", [])),
                "blocked_count": len(item.get("blocked_formal_changes", []))
            }
            for item in items
        ],
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_score_write": True,
            "not_adapter_write": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True
        }
    }
    write_json(RESULT_JSON, result)
    RESULT_MD.write_text(render_md(result), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "sample_count": len(items),
        "errors": len(errors),
        "result_json": str(RESULT_JSON),
        "result_md": str(RESULT_MD)
    }, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
