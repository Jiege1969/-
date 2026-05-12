from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
PRIORITY_REPORT = DATA_DIR / "L3五样本证据缺口优先级报告_最新.json"
POLICY_EVENTS = DATA_DIR / "policy_events_v1.0.json"
POLICY_EXPOSURES = DATA_DIR / "stock_policy_exposures_v1.0.json"
QUEUE_JSON = DATA_DIR / "五样本政策事件缺口队列_最新.json"
QUEUE_MD = DATA_DIR / "五样本政策事件缺口队列_最新.md"


CANDIDATE_HINTS = {
    "sz002466": {
        "classification": "no_direct_structured_policy",
        "review_focus": "锂盐、新能源材料或矿产资源政策是否存在直接、可量化、可暴露度映射的事件。",
        "candidate_action": "先确认无直接政策；如后续发现官方政策，必须单独建立事件和暴露度，不得借用泛新能源口径加分。",
        "front_wording": "未匹配到直接结构化政策，政策项不能加分。"
    },
    "sh688347": {
        "classification": "candidate_policy_needed",
        "review_focus": "半导体国产替代、集成电路产业政策、晶圆代工产能与先进制程限制等是否能形成结构化事件。",
        "candidate_action": "可建立半导体政策候选复核任务，但在官方事件、影响方向、影响强度和公司暴露度明确前不得入库计分。",
        "front_wording": "半导体政策背景存在，但尚未结构化到单股政策事件，前台只能写政策证据待补。"
    },
    "sz000906": {
        "classification": "no_direct_structured_policy",
        "review_focus": "供应链、大宗商品流通、国企改革或物流政策是否与公司主营形成直接映射。",
        "candidate_action": "目前只登记为待观察，不把宏观供应链口号写成政策加分。",
        "front_wording": "未发现可直接映射到公司的结构化政策事件。"
    },
    "sz300641": {
        "classification": "no_direct_structured_policy",
        "review_focus": "精细化工、TMA、环保、安全生产或出口政策是否直接影响公司产品价格与产能。",
        "candidate_action": "仅在找到官方来源、产品范围和公司暴露度后建立候选事件；当前不得给政策分。",
        "front_wording": "未匹配到直接结构化政策，化工品景气需由价格和财报证据验证。"
    }
}


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalized_stock_code(code: str) -> str:
    if code.startswith(("sz", "sh")):
        return code[2:]
    return code


def build_indexes(events: list[dict], exposures: list[dict]) -> tuple[dict, dict]:
    events_by_id = {event.get("event_id"): event for event in events}
    exposures_by_stock: dict[str, list[dict]] = {}
    for exposure in exposures:
        stock_code = exposure.get("stock_code", "")
        exposures_by_stock.setdefault(stock_code, []).append(exposure)
    return events_by_id, exposures_by_stock


def build_task(sample: dict, events_by_id: dict, exposures_by_stock: dict) -> dict:
    stock = sample["stock"]
    code = stock["code"]
    plain_code = normalized_stock_code(code)
    matches = []
    for exposure in exposures_by_stock.get(plain_code, []):
        event = events_by_id.get(exposure.get("event_id"), {})
        if not event:
            continue
        matches.append({
            "event_id": exposure.get("event_id"),
            "title": event.get("title", ""),
            "source_name": event.get("source_name", ""),
            "source_level": event.get("source_level", ""),
            "event_status": event.get("status", ""),
            "impact_direction": event.get("impact_direction", ""),
            "impact_strength": event.get("impact_strength", 0),
            "event_confidence": event.get("event_confidence", 0),
            "exposure": exposure.get("exposure", 0),
            "exposure_direction": exposure.get("exposure_direction", ""),
            "exposure_reason": exposure.get("exposure_reason", "")
        })

    if matches:
        classification = "structured_policy_ready"
        priority = "P2"
        action = "保留既有结构化政策事件；后续只需复核是否重复计分、是否需要时效说明。"
        front_wording = "已匹配结构化政策事件，政策只能作为分项依据，不能单因子强推。"
        missing = []
    else:
        hint = CANDIDATE_HINTS.get(code, {})
        classification = hint.get("classification", "no_direct_structured_policy")
        priority = "P1" if classification == "candidate_policy_needed" else "P2"
        action = hint.get("candidate_action", "确认无直接结构化政策；不得凭空给政策分。")
        front_wording = hint.get("front_wording", "未匹配到直接结构化政策事件。")
        missing = [
            item for item in sample.get("missing", [])
            if "政策" in item
        ] or ["未匹配到该股票的结构化政策事件暴露度。"]

    return {
        "stock": stock,
        "classification": classification,
        "priority": priority,
        "matched_policy_events": matches,
        "matched_event_count": len(matches),
        "policy_score_allowed": bool(matches),
        "policy_score_action": action,
        "review_focus": CANDIDATE_HINTS.get(code, {}).get("review_focus", "复核是否存在官方来源清晰、影响方向明确、公司暴露度可量化的直接政策事件。"),
        "missing": missing,
        "front_wording": front_wording,
        "redline_blocking": [
            "未入库政策不得参与L3政策分。",
            "无股票暴露度映射不得给单股政策分。",
            "宏观背景、行业口号、新闻热词不得替代结构化政策事件。",
            "不得凭空补政策强度、暴露度或时效衰减。",
            "不得生成买卖、仓位、下单或交易建议。"
        ]
    }


def render_md(queue: dict) -> str:
    lines = [
        "# 五样本政策事件缺口队列",
        "",
        f"- 生成时间：{queue['generated_at']}",
        "- 资产身份：W1政策缺口队列，不是政策事件正式入库，不改L3评分。",
        "- 安全边界：未触发外部抓取、未发送企业微信、未重启服务、未调用券商接口、未自动交易。",
        "",
        "## 队列明细",
        "",
        "| 股票 | 分类 | 已匹配事件数 | 是否允许政策分 | 优先级 | 前台口径 |",
        "|---|---|---:|---|---|---|"
    ]
    for task in queue["tasks"]:
        allowed = "是" if task["policy_score_allowed"] else "否"
        lines.append(
            f"| {task['stock']['name']} | {task['classification']} | {task['matched_event_count']} | "
            f"{allowed} | {task['priority']} | {task['front_wording']} |"
        )
    lines.extend([
        "",
        "## 红线阻断",
        "",
        "- 未入库政策不得参与L3政策分。",
        "- 无股票暴露度映射不得给单股政策分。",
        "- 宏观背景、行业口号、新闻热词不得替代结构化政策事件。",
        "- 不得凭空补政策强度、暴露度或时效衰减。",
        "- 不得生成买卖、仓位、下单或交易建议。"
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    priority_report = read_json(PRIORITY_REPORT)
    events = read_json(POLICY_EVENTS)
    exposures = read_json(POLICY_EXPOSURES)
    events_by_id, exposures_by_stock = build_indexes(events, exposures)
    tasks = [build_task(sample, events_by_id, exposures_by_stock) for sample in priority_report.get("samples", [])]
    queue = {
        "名称": "五样本政策事件缺口队列",
        "generated_at": now,
        "asset_identity": "W1政策缺口队列",
        "status": "ready",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_external_fetch": True,
        "not_policy_event_write": True,
        "not_score_write": True,
        "tasks": tasks,
        "source_state": {
            "policy_event_count": len(events),
            "stock_policy_exposure_count": len(exposures)
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_external_fetch": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_delete_or_move_old_assets": True,
            "not_formal_database_write": True,
            "not_policy_event_write": True,
            "not_score_write": True,
            "not_broker_interface": True,
            "not_auto_trade": True
        }
    }
    write_json(QUEUE_JSON, queue)
    QUEUE_MD.write_text(render_md(queue), encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "task_count": len(tasks),
        "queue_json": str(QUEUE_JSON),
        "queue_md": str(QUEUE_MD)
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
