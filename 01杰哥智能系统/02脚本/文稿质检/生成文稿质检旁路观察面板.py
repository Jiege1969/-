# -*- coding: utf-8 -*-
"""
名称：生成文稿质检旁路观察面板.py
作用：读取 review_records.jsonl，生成第一阶段旁路审稿观察面板，并明确用户确认进度。
触发方式：python 生成文稿质检旁路观察面板.py
依赖：01杰哥智能系统/03数据/文稿质检/review_records.jsonl。
所属系统：01杰哥智能系统/文稿质检
输出：03数据/文稿质检/观察面板/文稿质检旁路观察面板_最新.md|json。
安全边界：只读审稿记录；不调用模型、不触发 n8n、不发送企业微信、不替换原文、不固化模板。
创建/修改记录：2026-05-03 创建；2026-05-03 增加用户确认进度字段。
标识：text-reviewer-sidecar-observation-panel-generate
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
SMART = ROOT / "01杰哥智能系统"
DATA_DIR = SMART / "03数据" / "文稿质检"
RECORDS = DATA_DIR / "review_records.jsonl"
OUT_DIR = DATA_DIR / "观察面板"
OUT_JSON = OUT_DIR / "文稿质检旁路观察面板_最新.json"
OUT_MD = OUT_DIR / "文稿质检旁路观察面板_最新.md"

STOCK_DOC_TYPES = {
    "stock_daily": "每日推荐",
    "stock_daily_recommendation": "每日推荐",
    "stock_single_report": "单股查询",
    "stock_position_diagnosis": "持仓诊断",
}
REQUIRED_TYPES = ["stock_daily", "stock_single_report", "stock_position_diagnosis"]


def read_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def equivalent_doc_type(doc_type: str) -> str:
    if doc_type == "stock_daily_recommendation":
        return "stock_daily"
    return doc_type


def bool_value(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def build_panel(records: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    type_counter: Counter[str] = Counter(equivalent_doc_type(str(item.get("doc_type", ""))) for item in records)
    status_counter: Counter[str] = Counter(str(item.get("status", "")) for item in records)
    stock_records = [item for item in records if equivalent_doc_type(str(item.get("doc_type", ""))) in STOCK_DOC_TYPES]
    model_records = [item for item in records if item.get("model")]
    forbidden_records = [item for item in records if item.get("forbidden_modified")]
    adopted_records = [item for item in records if item.get("status") == "adopted"]
    passed_records = [item for item in records if bool_value(item.get("review", {}).get("pass"))]

    required_progress = []
    for doc_type in REQUIRED_TYPES:
        count = type_counter.get(doc_type, 0)
        required_progress.append({
            "文稿类型": doc_type,
            "名称": STOCK_DOC_TYPES[doc_type],
            "样本数": count,
            "是否已有样本": count > 0,
        })

    five_useful_ready = len(adopted_records) >= 5
    three_types_ready = all(item["是否已有样本"] for item in required_progress)
    second_stage_allowed = five_useful_ready and three_types_ready
    useful_threshold = 5
    useful_confirmed = len(adopted_records)
    useful_remaining = max(useful_threshold - useful_confirmed, 0)

    recent = []
    for item in records[-10:]:
        recent.append({
            "id": item.get("id", ""),
            "时间": item.get("created_at", ""),
            "类型": item.get("doc_type", ""),
            "来源": item.get("draft_source", ""),
            "是否通过": item.get("review", {}).get("pass"),
            "评分": item.get("review", {}).get("total_score"),
            "模型": item.get("model") or "未调用",
            "禁止字段改动数": len(item.get("forbidden_modified") or []),
            "状态": item.get("status", ""),
        })

    next_actions = []
    if not three_types_ready:
        missing = [item["名称"] for item in required_progress if not item["是否已有样本"]]
        next_actions.append(f"补齐股票三类报告样本：{', '.join(missing)}。")
    if not five_useful_ready:
        next_actions.append("继续旁路观察；只有累计 5 次用户明确采用或确认有价值后，才评估第二阶段。")
    if forbidden_records:
        next_actions.append("已有审稿触发禁止字段改动回退，继续保留脚本硬防线，不允许模型自动替换原文。")
    if not next_actions:
        next_actions.append("样本和采用观察已满足最低条件；仍需人工复核后才能讨论第二阶段。")

    return {
        "生成时间": now,
        "结论": "继续第一阶段旁路观察" if not second_stage_allowed else "达到第二阶段评估前置条件，但仍需人工复核",
        "是否允许进入第二阶段": False,
        "说明": "本面板只判断观察进度，不授权接入正式推送链路。",
        "统计": {
            "审稿记录总数": len(records),
            "股票类记录数": len(stock_records),
            "调用模型记录数": len(model_records),
            "规则-only记录数": len(records) - len(model_records),
            "通过记录数": len(passed_records),
            "采用记录数": len(adopted_records),
            "废弃记录数": status_counter.get("discarded", 0),
            "禁止字段改动记录数": len(forbidden_records),
        },
        "用户确认进度": {
            "第二阶段评估最低确认次数": useful_threshold,
            "已采用或确认有价值次数": useful_confirmed,
            "仍需确认次数": useful_remaining,
            "三类股票样本是否齐全": three_types_ready,
            "是否达到第二阶段评估前置条件": second_stage_allowed,
            "口径": "只有累计5次用户明确采用或确认有价值，且三类股票文稿均有样本，才允许讨论第二阶段；本字段仍不授权接入正式推送。",
        },
        "股票三类报告样本进度": required_progress,
        "文稿类型分布": dict(type_counter),
        "状态分布": dict(status_counter),
        "最近记录": recent,
        "下一步": next_actions,
        "安全边界": {
            "调用模型": False,
            "触发n8n": False,
            "发送企业微信": False,
            "替换原文": False,
            "固化正式模板": False,
            "接入正式推送": False,
        },
    }


def build_md(panel: dict[str, Any]) -> str:
    lines = [
        f"# 文稿质检旁路观察面板 - {panel['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 结论：{panel['结论']}",
        f"- 是否允许进入第二阶段：{panel['是否允许进入第二阶段']}",
        f"- 说明：{panel['说明']}",
        "",
        "## 二、统计",
        "",
    ]
    for key, value in panel["统计"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、用户确认进度", ""])
    for key, value in panel["用户确认进度"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 四、股票三类报告样本进度", ""])
    for item in panel["股票三类报告样本进度"]:
        state = "已有样本" if item["是否已有样本"] else "缺样本"
        lines.append(f"- {item['名称']}（{item['文稿类型']}）：{item['样本数']}，{state}")
    lines.extend(["", "## 五、最近记录", ""])
    for item in panel["最近记录"]:
        lines.append(
            f"- {item['id']}｜{item['类型']}｜评分 {item['评分']}｜通过 {item['是否通过']}｜模型 {item['模型']}｜禁止字段改动 {item['禁止字段改动数']}｜状态 {item['状态']}"
        )
    lines.extend(["", "## 六、下一步", ""])
    for item in panel["下一步"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 七、安全边界", ""])
    for key, value in panel["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    records = read_records(RECORDS)
    panel = build_panel(records)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(panel, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(build_md(panel), encoding="utf-8")
    print(json.dumps({
        "状态": "完成",
        "结论": panel["结论"],
        "审稿记录总数": panel["统计"]["审稿记录总数"],
        "股票类记录数": panel["统计"]["股票类记录数"],
        "报告": str(OUT_MD),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
