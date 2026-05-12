from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"

L3_GAP_REPORT = DATA_DIR / "L3五样本证据缺口优先级报告_最新.json"
POLICY_QUEUE = DATA_DIR / "五样本政策事件缺口队列_最新.json"
PRICE_QUEUE = DATA_DIR / "五样本行业价格连续观测补数队列_最新.json"
CAPITAL_CARDS = DATA_DIR / "五样本资金机构解禁证据卡候选_最新.json"

OUTPUT_JSON = DATA_DIR / "五样本前台缺口压缩预演_最新.json"
OUTPUT_MD = DATA_DIR / "五样本前台缺口压缩预演_最新.md"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def index_by_code(items: list[dict], stock_key: str = "stock") -> dict[str, dict]:
    out = {}
    for item in items:
        stock = item.get(stock_key, {})
        code = stock.get("code", "")
        if code:
            out[code] = item
    return out


def derive_action_phrase(conclusion: str, confidence: str) -> str:
    if conclusion == "重点关注" and confidence in {"medium", "high"}:
        return "可重点跟踪，但仍以证据复核为前提"
    if conclusion == "可纳入观察":
        return "先纳入观察，等关键证据补齐后再提高判断等级"
    return "暂时只适合观察，不适合给强结论"


def build_preview(sample: dict, policy: dict, price: dict, capital: dict) -> dict:
    stock = sample["stock"]
    name = stock["name"]
    code = stock["code"]
    conclusion = sample.get("conclusion", "暂不建议关注")
    confidence = sample.get("confidence", "low")
    score = sample.get("total_score", 0)

    price_name = price.get("product_name", "行业价格/景气")
    price_count = price.get("current_observation_count", 0)
    price_target = price.get("target_min_observation_count", 5)
    if price_count >= price_target:
        price_sentence = f"{price_name}价格/景气已有连续观测，可作为行业景气证据。"
    elif price_count > 0:
        price_sentence = f"{price_name}价格/景气只有{price_count}个观测点，只能弱参考，不能写趋势确认。"
    else:
        price_sentence = f"{price_name}价格/景气还没有观测点入账，行业景气仍是关键缺口。"

    if policy.get("policy_score_allowed"):
        policy_sentence = policy.get("front_wording", "已匹配结构化政策，但不能单因子强推。")
    else:
        policy_sentence = policy.get("front_wording", "未匹配直接结构化政策，政策项不能加分。")
        if all(marker not in policy_sentence for marker in ["政策项不能加分", "政策证据待补", "未发现"]):
            policy_sentence = f"{policy_sentence} 政策项不能加分。"

    capital_score = capital.get("capital_institution_shadow_score", {})
    capital_sentence = capital.get("front_output_compression", {}).get(
        "one_sentence",
        "资金、机构和解禁减持证据仍待采集，不能作为强化结论依据。"
    )
    if capital_score.get("score_status") != "not_scored":
        capital_sentence = "资金、机构和解禁减持已有评分状态，需复核后才可进入前台。"

    one_line_gap = f"{price_sentence} {policy_sentence} {capital_sentence}"
    user_first_answer = (
        f"{name}（{code}）：{conclusion}。{derive_action_phrase(conclusion, confidence)}；"
        f"主要卡点是行业价格、政策映射和资金/机构/解禁证据。"
    )
    why_not_higher = (
        f"不是更高评级，主要因为：{price_sentence}"
        f"{' ' if policy_sentence else ''}{policy_sentence}"
        f" {capital_sentence}"
    )

    return {
        "stock": stock,
        "source_score": score,
        "source_conclusion": conclusion,
        "source_confidence": confidence,
        "front_preview": {
            "first_line": f"{name}（{code}）",
            "conclusion_line": f"结论：{conclusion}",
            "action_line": f"现在怎么处理：{derive_action_phrase(conclusion, confidence)}。",
            "one_line_gap": one_line_gap,
            "why_not_higher": why_not_higher,
            "do_not_say": [
                "可以买入",
                "可以卖出",
                "建议加仓",
                "建议减仓",
                "资金明显流入",
                "机构持续加仓",
                "趋势已经确认",
                "未入库政策利好"
            ]
        },
        "evidence_status": {
            "price_status": price.get("current_status", ""),
            "price_observation_count": price_count,
            "policy_classification": policy.get("classification", ""),
            "policy_score_allowed": policy.get("policy_score_allowed", False),
            "capital_score_status": capital_score.get("score_status", ""),
            "capital_confidence": capital_score.get("confidence", "")
        },
        "safety_boundary": {
            "not_formal_config": True,
            "not_entrypoint": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_n8n": True,
            "not_broker_interface": True,
            "not_auto_trade": True
        }
    }


def render_md(result: dict) -> str:
    lines = [
        "# 五样本前台缺口压缩预演",
        "",
        f"- 生成时间：{result['generated_at']}",
        "- 资产身份：W1前台话术预演，不是正式企业微信入口，不外发。",
        "- 用途：把后台证据缺口压缩成用户能看懂的结论型短答依据。",
        "",
        "## 预演结果",
        ""
    ]
    for item in result["previews"]:
        fp = item["front_preview"]
        lines.extend([
            f"### {fp['first_line']}",
            "",
            f"- {fp['conclusion_line']}",
            f"- {fp['action_line']}",
            f"- 缺口：{fp['one_line_gap']}",
            f"- 为什么不是更高评级：{fp['why_not_higher']}",
            ""
        ])
    lines.extend([
        "## 边界",
        "",
        "- 本预演不改企业微信入口。",
        "- 本预演不发送企业微信。",
        "- 本预演不改L3评分。",
        "- 本预演不接n8n、不重启服务、不接券商接口、不生成交易动作。"
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    gaps = read_json(L3_GAP_REPORT)
    policies = index_by_code(read_json(POLICY_QUEUE).get("tasks", []))
    prices = index_by_code(read_json(PRICE_QUEUE).get("tasks", []))
    capitals = index_by_code(read_json(CAPITAL_CARDS).get("cards", []))

    previews = []
    for sample in gaps.get("samples", []):
        code = sample.get("stock", {}).get("code", "")
        previews.append(build_preview(
            sample,
            policies.get(code, {}),
            prices.get(code, {}),
            capitals.get(code, {})
        ))

    result = {
        "名称": "五样本前台缺口压缩预演",
        "generated_at": now,
        "asset_identity": "W1前台话术预演",
        "status": "ready",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_score_write": True,
        "previews": previews,
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
    write_json(OUTPUT_JSON, result)
    OUTPUT_MD.write_text(render_md(result), encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "preview_count": len(previews),
        "json": str(OUTPUT_JSON),
        "md": str(OUTPUT_MD)
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
