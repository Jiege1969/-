from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
PREVIEW_JSON = DATA_DIR / "五样本前台缺口压缩预演_最新.json"
RESULT_JSON = DATA_DIR / "五样本前台缺口压缩预演验收_最新.json"
RESULT_MD = DATA_DIR / "五样本前台缺口压缩预演验收_最新.md"

FORBIDDEN_PHRASES = [
    "可以买入",
    "可以卖出",
    "建议加仓",
    "建议减仓",
    "下单",
    "自动交易",
    "仓位调整",
    "资金明显流入",
    "机构持续加仓",
    "趋势已经确认",
    "未入库政策利好"
]


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_preview(item: dict) -> list[str]:
    errors = []
    name = item.get("stock", {}).get("name", "<unknown>")
    fp = item.get("front_preview", {})
    required = ["first_line", "conclusion_line", "action_line", "one_line_gap", "why_not_higher", "do_not_say"]
    for key in required:
        if key not in fp:
            errors.append(f"{name}: 缺少front_preview.{key}")
    if item.get("stock", {}).get("name", "") not in fp.get("first_line", ""):
        errors.append(f"{name}: first_line未包含股票名称")
    if item.get("stock", {}).get("code", "") not in fp.get("first_line", ""):
        errors.append(f"{name}: first_line未包含股票代码")
    combined = " ".join(str(fp.get(key, "")) for key in ["conclusion_line", "action_line", "one_line_gap", "why_not_higher"])
    for phrase in FORBIDDEN_PHRASES:
        if phrase in combined:
            errors.append(f"{name}: 前台预演正文出现禁用词 {phrase}")
    gap = fp.get("one_line_gap", "")
    for keyword in ["价格", "政策", "资金"]:
        if keyword not in gap:
            errors.append(f"{name}: one_line_gap缺少{keyword}信息")
    status = item.get("evidence_status", {})
    if status.get("policy_score_allowed") is False and "政策项不能加分" not in gap and "政策证据待补" not in gap and "未发现" not in gap:
        errors.append(f"{name}: 无政策分时缺口话术未说明政策限制")
    boundary = item.get("safety_boundary", {})
    for key in ["not_formal_config", "not_entrypoint", "not_external_send", "not_service_restart", "not_n8n", "not_broker_interface", "not_auto_trade"]:
        if boundary.get(key) is not True:
            errors.append(f"{name}: safety_boundary.{key} 必须为 true")
    return errors


def render_md(result: dict) -> str:
    lines = [
        "# 五样本前台缺口压缩预演验收",
        "",
        f"- 验收时间：{result['validated_at']}",
        f"- 验收结果：{result['status']}",
        f"- 覆盖预演：{result['preview_count']}",
        f"- 错误数量：{len(result['errors'])}",
        "",
        "## 明细",
        "",
        "| 股票 | 结论 | 政策分允许 | 价格点 | 资金状态 |",
        "|---|---|---|---:|---|"
    ]
    for item in result["items"]:
        allowed = "是" if item["policy_score_allowed"] else "否"
        lines.append(f"| {item['stock']} | {item['conclusion']} | {allowed} | {item['price_observation_count']} | {item['capital_score_status']} |")
    if result["errors"]:
        lines.extend(["", "## 错误", ""])
        lines.extend([f"- {err}" for err in result["errors"]])
    lines.extend([
        "",
        "## 边界",
        "",
        "- 未改企业微信入口",
        "- 未发送企业微信",
        "- 未改L3评分",
        "- 未接n8n",
        "- 未重启服务",
        "- 未接券商接口",
        "- 未自动交易"
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    preview = read_json(PREVIEW_JSON)
    previews = preview.get("previews", [])
    errors = []
    if len(previews) != 5:
        errors.append("previews数量必须为5")
    for key in ["not_formal_config", "not_entrypoint", "not_external_send", "not_score_write"]:
        if preview.get(key) is not True:
            errors.append(f"preview.{key} 必须为 true")
    for key in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_score_write", "not_broker_interface", "not_auto_trade"]:
        if preview.get("safety_boundary", {}).get(key) is not True:
            errors.append(f"safety_boundary.{key} 必须为 true")
    for item in previews:
        errors.extend(validate_preview(item))

    result = {
        "名称": "五样本前台缺口压缩预演验收",
        "validated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "passed" if not errors else "failed",
        "preview_count": len(previews),
        "errors": errors,
        "items": [
            {
                "stock": item.get("stock", {}).get("name", ""),
                "code": item.get("stock", {}).get("code", ""),
                "conclusion": item.get("source_conclusion", ""),
                "policy_score_allowed": item.get("evidence_status", {}).get("policy_score_allowed", False),
                "price_observation_count": item.get("evidence_status", {}).get("price_observation_count", 0),
                "capital_score_status": item.get("evidence_status", {}).get("capital_score_status", "")
            }
            for item in previews
        ],
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_score_write": True,
            "not_broker_interface": True,
            "not_auto_trade": True
        }
    }
    write_json(RESULT_JSON, result)
    RESULT_MD.write_text(render_md(result), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "preview_count": len(previews),
        "errors": len(errors),
        "result_json": str(RESULT_JSON),
        "result_md": str(RESULT_MD)
    }, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
