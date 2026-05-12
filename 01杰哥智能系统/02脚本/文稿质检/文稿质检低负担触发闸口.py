# -*- coding: utf-8 -*-
"""
名称：文稿质检低负担触发闸口.py
作用：根据触发词、文稿类型、重要性和时间窗判断是否允许文稿质检调用模型，防止审稿能力增加日常运行负担。
触发方式：python 文稿质检低负担触发闸口.py --trigger "#审稿" --doc-type stock_single_report
依赖：Python标准库；01配置/文稿质检低负担触发规则.json。
所属系统：01杰哥智能系统/文稿质检
输出：JSON触发决策；默认只打印，不写业务库。
安全边界：只读配置并输出决策；不调用模型，不触发n8n，不发送企业微信，不替换原文，不修改正式模板，不调用券商接口，不自动交易。
创建/修改记录：2026-05-03 创建低负担审稿触发闸口。
标识：text-review-low-load-gate
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, time
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def smart_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_policy_path() -> Path:
    return smart_root() / "01配置" / "文稿质检低负担触发规则.json"


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def parse_clock(value: str) -> time:
    hour, minute = [int(part) for part in value.split(":", 1)]
    return time(hour=hour, minute=minute)


def parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now()
    text = value.strip()
    if len(text) == 5 and ":" in text:
        today = datetime.now()
        clock = parse_clock(text)
        return today.replace(hour=clock.hour, minute=clock.minute, second=0, microsecond=0)
    return datetime.fromisoformat(text)


def in_time_window(now_clock: time, start_text: str, end_text: str) -> bool:
    start = parse_clock(start_text)
    end = parse_clock(end_text)
    if start <= end:
        return start <= now_clock <= end
    return now_clock >= start or now_clock <= end


def is_low_peak(now: datetime, policy: dict[str, Any]) -> bool:
    windows = (
        policy.get("触发类型", {})
        .get("low_peak_batch", {})
        .get("允许时间窗", [])
    )
    for item in windows:
        if not isinstance(item, dict):
            continue
        if in_time_window(now.time(), str(item.get("开始", "22:30")), str(item.get("结束", "06:30"))):
            return True
    return False


def trigger_contains(trigger: str, words: list[str]) -> bool:
    text = str(trigger or "").strip()
    return bool(text) and any(word and word in text for word in words)


def make_decision(args: argparse.Namespace) -> dict[str, Any]:
    policy_path = Path(args.policy) if args.policy else default_policy_path()
    policy = load_json(policy_path)
    now = parse_now(args.now)
    trigger = str(args.trigger or "")
    doc_type = str(args.doc_type or "generic")
    important = bool(args.important)
    low_peak = is_low_peak(now, policy)
    trigger_types = policy.get("触发类型", {}) if isinstance(policy.get("触发类型"), dict) else {}
    manual_words = trigger_types.get("manual_review", {}).get("触发词", ["#审稿", "审稿"])
    deep_words = trigger_types.get("manual_deep_review", {}).get("触发词", ["#深度审稿", "深度审稿"])
    important_docs = trigger_types.get("important_report", {}).get("适用文稿", [])

    action = policy.get("默认策略", {}).get("默认动作", "no_review")
    model = ""
    reason = "默认不调用模型审稿，保持正式链路快速稳定。"
    allowed = False

    if trigger_contains(trigger, [str(word) for word in deep_words]):
        action = "enhanced_model_review_candidate"
        model = ",".join(str(item) for item in trigger_types.get("manual_deep_review", {}).get("候选模型", []))
        reason = "用户手动触发深度审稿；只允许增强主编候选旁路审稿，不自动替换。"
        allowed = True
    elif trigger_contains(trigger, [str(word) for word in manual_words]):
        action = "light_model_review"
        model = str(trigger_types.get("manual_review", {}).get("默认模型", "qwen2.5:7b"))
        reason = "用户手动触发审稿；允许轻量主编模型旁路审稿。"
        allowed = True
    elif args.model_compare:
        action = "plan_only_or_manual_sample"
        model = ",".join(str(item) for item in trigger_types.get("model_compare", {}).get("候选模型", []))
        reason = "多模型同稿对比只做手动样本或预案，不进入日常链路。"
        allowed = False
    elif args.batch and low_peak:
        action = "light_model_review"
        model = str(trigger_types.get("manual_review", {}).get("默认模型", "qwen2.5:7b"))
        reason = "当前处于低峰时间窗，允许抽样轻量模型审稿。"
        allowed = True
    elif important or doc_type in important_docs:
        action = "rule_first_optional_light_model"
        reason = "重点报告先规则检查；未手动触发且非低峰时不调用模型。"
        allowed = False

    command_hint = ""
    if allowed and action == "light_model_review":
        command_hint = f"python text_reviewer.py review --doc-type {doc_type} --model {model}"
    elif allowed and action == "enhanced_model_review_candidate":
        command_hint = "手动选择一个候选模型运行 text_reviewer.py review；必须保留禁止字段硬比对。"

    return {
        "名称": "文稿质检低负担触发闸口决策",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "判定时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "配置": str(policy_path),
        "输入": {
            "trigger": trigger,
            "doc_type": doc_type,
            "important": important,
            "batch": bool(args.batch),
            "model_compare": bool(args.model_compare),
        },
        "低峰时间窗": low_peak,
        "允许调用模型": allowed,
        "动作": action,
        "模型": model,
        "原因": reason,
        "建议命令": command_hint,
        "安全边界": {
            "调用模型": allowed,
            "触发n8n": False,
            "发送企业微信": False,
            "替换原文": False,
            "写正式模板": False,
            "改变股票判断": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="文稿质检低负担触发闸口")
    parser.add_argument("--trigger", default="", help="触发词或用户指令，例如 #审稿")
    parser.add_argument("--doc-type", default="generic", help="文稿类型")
    parser.add_argument("--important", action="store_true", help="标记为重点报告")
    parser.add_argument("--batch", action="store_true", help="低峰批处理场景")
    parser.add_argument("--model-compare", action="store_true", help="多模型同稿对比场景")
    parser.add_argument("--now", default="", help="指定判定时间，支持 HH:MM 或 ISO 时间")
    parser.add_argument("--policy", default="", help="触发规则配置路径")
    args = parser.parse_args()
    print(json.dumps(make_decision(args), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
