# -*- coding: utf-8 -*-
"""
生成股票施工前本地检查。

作用：在动手施工前，把股票系统规则转成一次轻量风险分级判断：
低风险直接施工，中风险先影子走通，高风险只登记并等待确认。

安全边界：只读本模块规则与本地面板，只写 03数据/288股票施工前本地检查；
不触发 n8n，不发送企业微信，不调用 Webhook，不重启服务，不写正式库，
不调用券商接口，不自动交易。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "288股票施工前本地检查"
RULE_PATH = ROOT / "01配置" / "股票系统搭建闭环防误解规则_v1.0.json"
MAINLINE_GATE = ROOT / "03数据" / "287股票主线施工闸口面板" / "股票主线施工闸口面板_最新.json"
SAMPLE_ROOM_GATE = ROOT / "03数据" / "286股票样本房本地验收面板" / "股票样本房本地验收面板_最新.json"

HIGH_RISK_WORDS = [
    "真实发送",
    "真实n8n",
    "n8n启用",
    "Webhook",
    "正式入口",
    "服务重启",
    "重启",
    "正式库",
    "凭据",
    "token",
    "券商",
    "自动交易",
    "下单",
]
NEGATION_PREFIXES = [
    "不触发",
    "不发送",
    "不调用",
    "不重启",
    "不写",
    "不修改",
    "不切换",
    "不碰",
    "不接入",
    "不启用",
    "不实施",
    "不会涉及",
    "不涉及",
    "不是",
    "并非",
    "只登记",
    "除非",
    "除非要碰",
    "红线",
    "安全边界",
    "总原则",
    "禁止",
    "关闭",
]
MEDIUM_RISK_WORDS = [
    "前台",
    "报告",
    "结论",
    "评分",
    "推送",
    "样本",
    "证据",
    "降级",
    "机器人回复",
    "企业微信回复",
]
LOW_RISK_WORDS = [
    "文档",
    "规则表述",
    "整理",
    "合并",
    "删除旧规则",
    "路径",
    "字段",
    "样本同步",
]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def contains_any(text: str, words: list[str]) -> list[str]:
    return [word for word in words if word.lower() in text.lower()]


def split_action_clauses(text: str) -> list[str]:
    normalized = text.replace(",", "，").replace("；", "，").replace(";", "，").replace("。", "，")
    return [part.strip() for part in normalized.split("，") if part.strip()]


def is_negated_in_action(text: str, word: str) -> bool:
    for clause in split_action_clauses(text):
        if word.lower() not in clause.lower():
            continue
        if any(prefix in clause for prefix in NEGATION_PREFIXES):
            return True
    return False


def contains_positive_risk(text: str, words: list[str]) -> list[str]:
    return [
        word
        for word in words
        if word.lower() in text.lower() and not is_negated_in_action(text, word)
    ]


def classify_action(action: str) -> dict[str, Any]:
    high_hits = contains_positive_risk(action, HIGH_RISK_WORDS)
    medium_hits = contains_any(action, MEDIUM_RISK_WORDS)
    low_hits = contains_any(action, LOW_RISK_WORDS)
    boundary_hits = contains_any(action, ["除非", "红线", "安全边界", "总原则", "不会涉及", "不涉及", "不碰"])
    if high_hits:
        level = "高风险"
        decision = "只登记，不实施；必须影子走通、列出回滚和验收口径，并等待人工确认。"
        required_path = "影子验证 -> 人工确认 -> 主线固化 -> CircleCI后台守门"
        can_continue = False
        shadow_required = True
        circleci_wait_required = False
    elif medium_hits:
        level = "中风险"
        decision = "先影子走通，再主线固化；本地验证通过后再批量推送，CircleCI后台守门。"
        required_path = "影子验证 -> 主线固化 -> 本地轻量验证 -> CircleCI后台守门"
        can_continue = True
        shadow_required = True
        circleci_wait_required = False
    else:
        level = "低风险"
        decision = "可直接施工，做轻量本地验证；不机械要求影子，不等待CircleCI。"
        required_path = "直接施工 -> 轻量本地验证 -> 需要时批量提交"
        can_continue = True
        shadow_required = False
        circleci_wait_required = False
    return {
        "风险等级": level,
        "命中词": {
            "高风险": high_hits,
            "中风险": medium_hits,
            "低风险": low_hits,
            "边界声明": boundary_hits,
        },
        "红线解释": "红线是施工边界，不是停工口令；只有正向要求执行真实外发、真实n8n、Webhook、正式入口、服务重启、正式库、券商或自动交易时才阻断。否定说明、条件说明、总原则说明必须放行。",
        "施工判定": decision,
        "推荐路径": required_path,
        "可继续施工": can_continue,
        "必须影子验证": shadow_required,
        "必须等待CircleCI": circleci_wait_required,
    }


def build_report(action: str) -> dict[str, Any]:
    rule = load_json(RULE_PATH, {})
    mainline = load_json(MAINLINE_GATE, {})
    sample_room = load_json(SAMPLE_ROOM_GATE, {})
    decision = classify_action(action)
    blockers: list[str] = []
    if not rule:
        blockers.append("缺少股票系统搭建闭环防误解规则")
    if mainline and mainline.get("红线命中数", 0) not in (0, None):
        blockers.append("主线施工闸口存在红线命中")
    if sample_room and sample_room.get("红线命中数", 0) not in (0, None):
        blockers.append("样本房验收面板存在红线命中")
    if blockers:
        decision["可继续施工"] = False
        decision["施工判定"] = "先处理阻断项，再决定施工节奏。"
    return {
        "名称": "股票施工前本地检查",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查动作": action,
        "规则版本": rule.get("版本", "未知"),
        "规则来源": str(RULE_PATH),
        "主线闸口状态": mainline.get("结论", "未生成"),
        "样本房状态": sample_room.get("结论", "未生成"),
        "风险分级判定": decision,
        "阻断项": blockers,
        "事前预防闭环": [
            "先判定风险等级和影响面。",
            "低风险直接施工并轻量验证。",
            "中风险先做影子短答、影子报告、影子映射或本地预演。",
            "高风险只登记，等待人工确认前不实施。",
            "主线固化后再用本地验证和CircleCI做外层守门。",
        ],
        "安全边界": {
            "发送企业微信": False,
            "触发n8n": False,
            "触发Webhook": False,
            "重启服务": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    decision = report["风险分级判定"]
    lines = [
        "# 股票施工前本地检查",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 检查动作：{report['检查动作']}",
        f"- 风险等级：{decision['风险等级']}",
        f"- 施工判定：{decision['施工判定']}",
        f"- 推荐路径：{decision['推荐路径']}",
        f"- 可继续施工：{str(decision['可继续施工']).lower()}",
        f"- 必须影子验证：{str(decision['必须影子验证']).lower()}",
        f"- 必须等待CircleCI：{str(decision['必须等待CircleCI']).lower()}",
        "",
        "## 阻断项",
        "",
    ]
    if report["阻断项"]:
        lines.extend([f"- {item}" for item in report["阻断项"]])
    else:
        lines.append("- 无")
    lines.extend(["", "## 事前预防闭环", ""])
    lines.extend([f"- {item}" for item in report["事前预防闭环"]])
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{str(value).lower()}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="生成股票施工前本地检查")
    parser.add_argument("--action", default="继续股票分析系统主线搭建", help="本轮准备施工的动作描述")
    parser.add_argument("--no-write", action="store_true", help="只打印，不写文件")
    args = parser.parse_args()

    report = build_report(args.action)
    if not args.no_write:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        write_json(OUT_DIR / f"股票施工前本地检查_{stamp}.json", report)
        write_text(OUT_DIR / f"股票施工前本地检查_{stamp}.md", render_markdown(report))
        write_json(OUT_DIR / "股票施工前本地检查_最新.json", report)
        write_text(OUT_DIR / "股票施工前本地检查_最新.md", render_markdown(report))
    print(json.dumps({
        "风险等级": report["风险分级判定"]["风险等级"],
        "施工判定": report["风险分级判定"]["施工判定"],
        "可继续施工": report["风险分级判定"]["可继续施工"],
        "必须影子验证": report["风险分级判定"]["必须影子验证"],
        "阻断项": report["阻断项"],
    }, ensure_ascii=False))
    return 0 if report["风险分级判定"]["可继续施工"] or report["风险分级判定"]["风险等级"] == "高风险" else 1


if __name__ == "__main__":
    raise SystemExit(main())
