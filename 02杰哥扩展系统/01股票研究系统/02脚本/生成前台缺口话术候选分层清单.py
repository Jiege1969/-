from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"

DIFF_JSON = DATA_DIR / "五样本前台缺口压缩差异对照_最新.json"
OUTPUT_JSON = DATA_DIR / "前台缺口话术候选分层清单_最新.json"
OUTPUT_MD = DATA_DIR / "前台缺口话术候选分层清单_最新.md"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def classify_candidate(text: str, stock: dict) -> dict:
    if "写入L3企业微信短答适配器" in text or "真实企业微信入口" in text or "服务刷新" in text:
        return {
            "stock": stock,
            "candidate_text": text,
            "layer": "W3_blocked",
            "action_type": "formal_change_blocked",
            "reason": "涉及正式候选脚本、企业微信入口或服务刷新，本轮只能登记阻断。",
            "can_implement_now": False,
            "next_gate": "回到总管判断，按正式脚本/正式入口变更处理。"
        }
    if "资金/机构/解禁" in text:
        return {
            "stock": stock,
            "candidate_text": text,
            "layer": "W1_rule_draft",
            "action_type": "front_wording_rule_candidate",
            "reason": "该项只固化前台缺口表达，不补数据、不改评分、不改入口。",
            "can_implement_now": True,
            "next_gate": "可进入W1话术规则草案；若要写入适配器代码则升级为W3阻断。"
        }
    if "政策项不能加分" in text or "政策背景存在" in text:
        return {
            "stock": stock,
            "candidate_text": text,
            "layer": "W1_rule_draft",
            "action_type": "policy_wording_rule_candidate",
            "reason": "该项收紧政策缺口表达，防止无结构化政策时凭空加分。",
            "can_implement_now": True,
            "next_gate": "可进入W1话术规则草案；如需入库政策事件或改L3政策分则另走政策事件闸口。"
        }
    if "价格/景气观测点不足" in text or "趋势确认" in text:
        return {
            "stock": stock,
            "candidate_text": text,
            "layer": "W1_rule_draft",
            "action_type": "industry_price_wording_rule_candidate",
            "reason": "该项统一行业价格/景气缺口表达，不写观测账本、不生成趋势结论。",
            "can_implement_now": True,
            "next_gate": "可进入W1话术规则草案；真实补价格点需另走行业价格观测入账闸口。"
        }
    return {
        "stock": stock,
        "candidate_text": text,
        "layer": "W1_review_needed",
        "action_type": "manual_review_candidate",
        "reason": "候选含义不够明确，需人工复核后再决定是否进入话术规则草案。",
        "can_implement_now": False,
        "next_gate": "人工复核。"
    }


def dedupe(items: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for item in items:
        key = (item.get("stock", {}).get("code", ""), item.get("candidate_text", ""), item.get("layer", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def render_md(result: dict) -> str:
    lines = [
        "# 前台缺口话术候选分层清单",
        "",
        f"- 生成时间：{result['generated_at']}",
        "- 资产身份：W1候选分层清单，不改短答适配器，不改企业微信入口。",
        "- 用途：把差异对照中的候选项拆成可继续草拟、需阻断、需补证据三层。",
        "",
        "## 总览",
        "",
        f"- 候选总数：{result['summary']['candidate_count']}",
        f"- W1话术规则草案：{result['summary']['w1_rule_draft_count']}",
        f"- W3阻断：{result['summary']['w3_blocked_count']}",
        f"- 待复核：{result['summary']['review_needed_count']}",
        "",
        "## W1话术规则草案",
        ""
    ]
    for item in result["candidates"]:
        if item["layer"] != "W1_rule_draft":
            continue
        lines.extend([
            f"- {item['stock'].get('name')}：{item['candidate_text']}",
            f"  - 理由：{item['reason']}",
            f"  - 下一闸口：{item['next_gate']}"
        ])
    lines.extend(["", "## W3阻断登记", ""])
    for item in result["candidates"]:
        if item["layer"] != "W3_blocked":
            continue
        lines.extend([
            f"- {item['stock'].get('name')}：{item['candidate_text']}",
            f"  - 阻断原因：{item['reason']}",
            f"  - 下一闸口：{item['next_gate']}"
        ])
    review_items = [item for item in result["candidates"] if item["layer"] == "W1_review_needed"]
    if review_items:
        lines.extend(["", "## 待复核", ""])
        for item in review_items:
            lines.append(f"- {item['stock'].get('name')}：{item['candidate_text']}")
    lines.extend([
        "",
        "## 边界",
        "",
        "- 本清单不修改短答适配器。",
        "- 本清单不修改企业微信入口。",
        "- 本清单不发送企业微信。",
        "- 本清单不改L3评分、不写正式库、不接n8n、不重启服务、不接券商接口、不自动交易。"
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    diff = read_json(DIFF_JSON)
    candidates = []
    for item in diff.get("items", []):
        stock = item.get("stock", {})
        for text in item.get("low_risk_candidates", []):
            candidates.append(classify_candidate(text, stock))
        for text in item.get("blocked_formal_changes", []):
            candidates.append(classify_candidate(text, stock))
    candidates = dedupe(candidates)
    result = {
        "名称": "前台缺口话术候选分层清单",
        "generated_at": now,
        "asset_identity": "W1候选分层清单",
        "status": "ready",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "candidates": candidates,
        "summary": {
            "candidate_count": len(candidates),
            "w1_rule_draft_count": sum(1 for item in candidates if item["layer"] == "W1_rule_draft"),
            "w3_blocked_count": sum(1 for item in candidates if item["layer"] == "W3_blocked"),
            "review_needed_count": sum(1 for item in candidates if item["layer"] == "W1_review_needed")
        },
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
    write_json(OUTPUT_JSON, result)
    OUTPUT_MD.write_text(render_md(result), encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "candidate_count": result["summary"]["candidate_count"],
        "w1_rule_draft_count": result["summary"]["w1_rule_draft_count"],
        "w3_blocked_count": result["summary"]["w3_blocked_count"],
        "json": str(OUTPUT_JSON),
        "md": str(OUTPUT_MD)
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
