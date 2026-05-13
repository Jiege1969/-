# -*- coding: utf-8 -*-
"""生成股票前台报告实样影子门禁。

这个脚本只读取本地单股报告样本，不触发真实发送、不触碰 n8n、不改正式入口。
目标是把“前台少讲技术过程、多给结论和算好的条件”变成可检查的影子关口。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
REPORT_DIR = BASE_DIR / "03数据" / "135分层日报"
OUT_DIR = BASE_DIR / "03数据" / "289股票前台报告实样影子门禁"
JSON_OUT = OUT_DIR / "股票前台报告实样影子门禁_最新.json"
MD_OUT = OUT_DIR / "股票前台报告实样影子门禁_最新.md"

MAX_REPORTS = 8
CONCLUSION_WORDS = ["强烈关注", "重点关注", "可纳入观察", "继续观察", "暂不建议关注", "取消关注", "风险复核"]
HARD_FORBIDDEN_WORDS = ["真实发送", "真实n8n", "Webhook", "自动交易", "券商接口", "下单", "保证收益"]
TECH_PROCESS_WORDS = ["MACD", "RSI", "K线", "均线", "量比", "金叉", "死叉", "item_scores", "计算过程"]
NEGATION_PREFIXES = ["不", "未", "无", "没有", "不触发", "不调用", "不支持", "不接入", "不执行", "禁止"]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def latest_report_paths() -> list[Path]:
    paths = sorted(
        REPORT_DIR.glob("单股标准报告v2*_最新.md"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    unique: list[Path] = []
    seen_text: set[str] = set()
    for path in paths:
        text = read_text(path)
        # 单股标准报告v2_最新.md 通常是某只股票的镜像，避免同一内容重复计数。
        digest = text[:600]
        if digest in seen_text:
            continue
        seen_text.add(digest)
        unique.append(path)
        if len(unique) >= MAX_REPORTS:
            break
    return unique


def has_stock_identity(text: str, path: Path) -> bool:
    if re.search(r"(sh|sz|bj)\d{6}|\b\d{6}\b", text, re.IGNORECASE):
        return True
    return bool(re.search(r"(sh|sz|bj)\d{6}", path.name, re.IGNORECASE))


def first_lines(text: str, limit: int = 18) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:limit])


def has_front_conclusion(text: str) -> bool:
    head = first_lines(text)
    return any(word in head for word in CONCLUSION_WORDS) or bool(re.search(r"结论|当前判断|当前状态", head))


def has_concrete_price_condition(text: str) -> bool:
    return bool(
        re.search(
            r"(站稳|跌破|风险线|失效|转强|承接|区间|上方|下方|高于|低于|当前价)[^。\n]{0,40}\d+(?:\.\d+)?\s*元",
            text,
        )
        or re.search(
            r"\d+(?:\.\d+)?\s*元[^。\n]{0,40}(站稳|跌破|风险线|失效|转强|承接|区间|上方|下方|高于|低于)",
            text,
        )
    )


def mentions_volume_logic(text: str) -> bool:
    return any(word in text for word in ["成交量", "成交额", "放量", "缩量", "量能", "资金活跃"])


def has_computed_volume_condition(text: str) -> bool:
    if not mentions_volume_logic(text):
        return False
    return bool(
        re.search(r"(成交量|成交额|放量|量能|资金活跃)[^。\n]{0,60}\d+(?:\.\d+)?\s*(万手|手|亿|万元|元)", text)
        or re.search(r"\d+(?:\.\d+)?\s*(万手|手|亿|万元|元)[^。\n]{0,60}(成交量|成交额|放量|量能|资金活跃)", text)
    )


def has_evidence_boundary(text: str) -> bool:
    return any(word in text for word in ["证据缺口", "待核验", "证据边界", "置信度", "数据缺口"])


def has_follow_watch_items(text: str) -> bool:
    return any(word in text for word in ["后续只盯", "后续观察", "下一步", "只盯", "重点看"])


def positive_forbidden_hits(text: str) -> list[str]:
    hits: list[str] = []
    for word in HARD_FORBIDDEN_WORDS:
        for match in re.finditer(re.escape(word), text):
            start = max(0, match.start() - 12)
            prefix = text[start : match.start()]
            if any(neg in prefix for neg in NEGATION_PREFIXES):
                continue
            hits.append(word)
            break
    return hits


def inspect_report(path: Path) -> dict:
    text = read_text(path)
    hard_hits = positive_forbidden_hits(text)
    tech_hits = [word for word in TECH_PROCESS_WORDS if word in text]
    checks = {
        "对象和代码明确": has_stock_identity(text, path),
        "前18行有结论或当前判断": has_front_conclusion(text),
        "价格/风险/失效条件有具体元值": has_concrete_price_condition(text),
        "证据边界或缺口明确": has_evidence_boundary(text),
        "后续观察事项明确": has_follow_watch_items(text),
        "未出现真实外发或交易执行硬禁词": not hard_hits,
    }
    volume_review = {
        "提到成交量或资金活跃": mentions_volume_logic(text),
        "成交量/成交额条件已给出计算后数值": has_computed_volume_condition(text),
    }
    missing = [name for name, passed in checks.items() if not passed]
    review_items: list[str] = []
    if volume_review["提到成交量或资金活跃"] and not volume_review["成交量/成交额条件已给出计算后数值"]:
        review_items.append("提到了成交量/资金活跃，但没有给出计算后的具体数值")
    if len(tech_hits) >= 3:
        review_items.append("后台技术过程词偏多，前台表达需要再翻译")
    return {
        "file": str(path),
        "passed": not missing and not review_items,
        "must_fix": missing,
        "review_items": review_items,
        "hard_forbidden_hits": hard_hits,
        "technical_process_hits": tech_hits,
        "volume_review": volume_review,
        "head_preview": first_lines(text, 8),
    }


def build_asset() -> dict:
    reports = [inspect_report(path) for path in latest_report_paths()]
    must_fix_total = sum(len(item["must_fix"]) for item in reports)
    review_total = sum(len(item["review_items"]) for item in reports)
    passed_count = sum(1 for item in reports if item["passed"])
    return {
        "name": "股票前台报告实样影子门禁",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "shadow_gate_only",
        "purpose": "检查真实单股报告是否已经把前台结论、具体价量条件、风险线、证据边界和后续观察事项说清楚。",
        "report_count": len(reports),
        "passed_count": passed_count,
        "must_fix_total": must_fix_total,
        "review_total": review_total,
        "overall_passed": bool(reports) and must_fix_total == 0 and review_total == 0,
        "reports": reports,
        "next_rule": "后续生成前台报告时，不把计算题留给使用者；出现倍数、区间、站稳、跌破、放量等表达时，必须同时给出已算好的具体数值。",
        "safety_boundary": {
            "not_real_send": True,
            "not_n8n": True,
            "not_webhook": True,
            "not_formal_entry": True,
            "not_service_restart": True,
            "not_formal_database_write": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }


def write_markdown(asset: dict) -> None:
    lines = [
        "# 股票前台报告实样影子门禁",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 检查报告数：{asset['report_count']}",
        f"- 通过报告数：{asset['passed_count']}",
        f"- 必改缺口数：{asset['must_fix_total']}",
        f"- 复核提示数：{asset['review_total']}",
        f"- 总体通过：{'是' if asset['overall_passed'] else '否'}",
        "",
        "## 固化规则",
        "",
        f"- {asset['next_rule']}",
        "- 这是影子门禁，只读本地报告，不触发真实发送、真实n8n、Webhook、正式入口或服务重启。",
        "",
        "## 实样检查结果",
        "",
    ]
    for item in asset["reports"]:
        lines.extend(
            [
                f"### {Path(item['file']).name}",
                "",
                f"- 是否通过：{'是' if item['passed'] else '否'}",
                f"- 必改：{'; '.join(item['must_fix']) if item['must_fix'] else '无'}",
                f"- 复核：{'; '.join(item['review_items']) if item['review_items'] else '无'}",
                f"- 硬禁词：{'; '.join(item['hard_forbidden_hits']) if item['hard_forbidden_hits'] else '无'}",
                f"- 技术过程词：{'; '.join(item['technical_process_hits']) if item['technical_process_hits'] else '无'}",
                "",
            ]
        )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    asset = build_asset()
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({
        "status": "ok",
        "report_count": asset["report_count"],
        "overall_passed": asset["overall_passed"],
        "must_fix_total": asset["must_fix_total"],
        "review_total": asset["review_total"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
