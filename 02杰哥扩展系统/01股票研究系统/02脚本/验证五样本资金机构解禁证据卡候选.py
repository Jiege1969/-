from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
SUMMARY_PATH = DATA_DIR / "五样本资金机构解禁证据卡候选_最新.json"
RESULT_JSON = DATA_DIR / "五样本资金机构解禁证据卡候选验收_最新.json"
RESULT_MD = DATA_DIR / "五样本资金机构解禁证据卡候选验收_最新.md"

REQUIRED_TOP = [
    "名称",
    "版本",
    "生成日期",
    "所属系统",
    "资产身份",
    "状态",
    "stock",
    "evidence_scope",
    "source_requirements",
    "evidence_slots",
    "capital_institution_shadow_score",
    "front_output_compression",
    "safety_boundary",
]

REQUIRED_BOUNDARIES = [
    "only_for_research",
    "not_investment_advice",
    "not_buy_sell_signal",
    "not_position_adjustment",
    "not_broker_interface",
    "not_auto_trade",
    "not_external_send",
]


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_card(card: dict) -> list[str]:
    errors = []
    name = card.get("stock", {}).get("name", "<unknown>")

    for key in REQUIRED_TOP:
        if key not in card:
            errors.append(f"{name}: 缺少顶层字段 {key}")

    if card.get("资产身份") != "W1证据候选卡":
        errors.append(f"{name}: 资产身份不是W1证据候选卡")
    if card.get("状态") != "source_requirements_ready":
        errors.append(f"{name}: 状态不是source_requirements_ready")
    for flag in ["not_formal_config", "not_entrypoint", "not_external_send"]:
        if card.get(flag) is not True:
            errors.append(f"{name}: {flag} 必须为 true")

    stock = card.get("stock", {})
    for key in ["name", "code", "display_code"]:
        if not stock.get(key):
            errors.append(f"{name}: stock.{key} 不能为空")

    source_requirements = card.get("source_requirements", [])
    if len(source_requirements) < 4:
        errors.append(f"{name}: source_requirements 不足4项")
    for idx, item in enumerate(source_requirements, start=1):
        for key in ["source_name", "source_type", "required_fields", "status", "usage_boundary"]:
            if key not in item:
                errors.append(f"{name}: source_requirements[{idx}] 缺少 {key}")
        if item.get("status") not in {"candidate_source_registered", "not_collected", "collected_pending_review", "reviewed"}:
            errors.append(f"{name}: source_requirements[{idx}] status 非法")

    slots = card.get("evidence_slots", [])
    required_slots = {"capital_flow", "institutional_holding", "unlock_schedule", "reduction_plan", "public_trading_disclosure"}
    slot_names = {item.get("slot") for item in slots}
    missing_slots = sorted(required_slots - slot_names)
    if missing_slots:
        errors.append(f"{name}: evidence_slots 缺少 {','.join(missing_slots)}")
    for item in slots:
        if item.get("status") not in {"missing", "candidate_source_registered", "partial", "evidence_ready", "not_applicable"}:
            errors.append(f"{name}: {item.get('slot')} status 非法")
        if item.get("status") != "evidence_ready" and not item.get("missing"):
            errors.append(f"{name}: {item.get('slot')} 未ready时必须写missing")

    score = card.get("capital_institution_shadow_score", {})
    if score.get("score_status") != "not_scored":
        errors.append(f"{name}: 当前候选卡不得提前评分")
    if score.get("score") != 0:
        errors.append(f"{name}: 当前候选卡score必须为0")
    if score.get("confidence") != "low":
        errors.append(f"{name}: 当前候选卡confidence必须为low")
    if not score.get("missing"):
        errors.append(f"{name}: capital_institution_shadow_score.missing 不能为空")

    front = card.get("front_output_compression", {})
    for key in ["one_sentence", "user_facing_reason", "missing_sentence", "do_not_say"]:
        if key not in front:
            errors.append(f"{name}: front_output_compression 缺少 {key}")

    boundary = card.get("safety_boundary", {})
    for key in REQUIRED_BOUNDARIES:
        if boundary.get(key) is not True:
            errors.append(f"{name}: safety_boundary.{key} 必须为 true")

    return errors


def render_md(result: dict) -> str:
    lines = [
        "# 五样本资金机构解禁证据卡候选验收",
        "",
        f"- 验收时间：{result['validated_at']}",
        f"- 验收结果：{result['status']}",
        f"- 覆盖卡片：{result['card_count']}",
        f"- 错误数量：{len(result['errors'])}",
        "",
        "## 边界",
        "",
        "- 未触发n8n",
        "- 未发送企业微信",
        "- 未重启服务",
        "- 未调用券商接口",
        "- 未自动交易",
        "",
        "## 结果明细",
        "",
        "| 股票 | 状态 | 评分状态 | 缺口数 |",
        "|---|---|---|---:|"
    ]
    for item in result["cards"]:
        lines.append(f"| {item['stock']} | {item['status']} | {item['score_status']} | {item['missing_count']} |")
    if result["errors"]:
        lines.extend(["", "## 错误", ""])
        lines.extend([f"- {err}" for err in result["errors"]])
    return "\n".join(lines) + "\n"


def main() -> None:
    summary = read_json(SUMMARY_PATH)
    cards = summary.get("cards", [])
    errors = []
    if summary.get("card_count") != 5:
        errors.append("summary.card_count 必须为5")
    if len(cards) != 5:
        errors.append("cards 实际数量必须为5")
    for key in ["not_formal_config", "not_entrypoint", "not_external_send"]:
        if summary.get(key) is not True:
            errors.append(f"summary.{key} 必须为 true")
    for key in ["not_n8n", "not_external_send", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_broker_interface", "not_auto_trade"]:
        if summary.get("safety_boundary", {}).get(key) is not True:
            errors.append(f"summary.safety_boundary.{key} 必须为 true")

    for card in cards:
        errors.extend(validate_card(card))

    result = {
        "名称": "五样本资金机构解禁证据卡候选验收",
        "validated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "passed" if not errors else "failed",
        "card_count": len(cards),
        "errors": errors,
        "cards": [
            {
                "stock": card.get("stock", {}).get("name", ""),
                "code": card.get("stock", {}).get("display_code", ""),
                "status": card.get("状态", ""),
                "score_status": card.get("capital_institution_shadow_score", {}).get("score_status", ""),
                "missing_count": len(card.get("capital_institution_shadow_score", {}).get("missing", []))
            }
            for card in cards
        ],
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_delete_or_move_old_assets": True,
            "not_formal_database_write": True,
            "not_broker_interface": True,
            "not_auto_trade": True
        }
    }
    write_json(RESULT_JSON, result)
    RESULT_MD.write_text(render_md(result), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "card_count": result["card_count"],
        "errors": len(errors),
        "result_json": str(RESULT_JSON),
        "result_md": str(RESULT_MD)
    }, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
