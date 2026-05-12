# -*- coding: utf-8 -*-
"""
名称：生成重点关注池候选池.py
作用：根据重点关注池技术指标生成L5深度研究、L6轻度关注和L7过滤候选池。
触发方式：python 生成重点关注池候选池.py
依赖：Python标准库；候选池生成规则.json；重点关注池技术指标_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读新系统技术指标；只写新系统候选池和报告；不调用大模型；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建重点关注池候选池生成脚本。
标识：stock-focus-candidate-pool-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def choose_layer(score: int, thresholds: list[dict[str, Any]]) -> dict[str, Any]:
    for item in sorted(thresholds, key=lambda row: int(row.get("最低分", 0)), reverse=True):
        if score >= int(item.get("最低分", 0)):
            return item
    return {"层级": "L7系统过滤", "动作": "记录过滤原因"}


def score_item(item: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    score_rules = rules.get("评分规则", {})
    score = int(score_rules.get("基础分", 50))
    basis: list[str] = []
    risks: list[str] = []
    if item.get("状态") != "成功":
        score += int(score_rules.get("数据不足", -30))
        risks.append("历史K线或指标不足，暂不进入深度研究。")
        layer = choose_layer(score, rules.get("分层阈值", []))
        return build_result(item, score, layer, basis, risks)

    close = item.get("最新收盘")
    ma = item.get("均线", {})
    ma5 = ma.get("MA5")
    ma10 = ma.get("MA10")
    ma20 = ma.get("MA20")
    ma60 = ma.get("MA60")
    rsi = item.get("RSI14")
    macd = item.get("MACD", {})
    volume_ratio = item.get("量比5日")

    if close is not None and ma60 is not None:
        if close > ma60:
            score += int(score_rules.get("站上MA60", 0))
            basis.append("收盘价站上MA60，中期趋势仍有支撑。")
        else:
            score += int(score_rules.get("低于MA60", 0))
            risks.append("收盘价低于MA60，中期趋势仍需修复。")
    if ma5 is not None and ma10 is not None and ma5 > ma10:
        score += int(score_rules.get("MA5大于MA10", 0))
        basis.append("MA5大于MA10，短线均线改善。")
    if ma10 is not None and ma20 is not None and ma10 > ma20:
        score += int(score_rules.get("MA10大于MA20", 0))
        basis.append("MA10大于MA20，中短期结构改善。")
    if rsi is not None:
        if 40 <= rsi <= 70:
            score += int(score_rules.get("RSI40到70", 0))
            basis.append(f"RSI14为{rsi}，处于可观察强弱区间。")
        elif rsi > 70:
            score += int(score_rules.get("RSI大于70", 0))
            risks.append(f"RSI14为{rsi}，存在短线过热风险。")
        else:
            score += int(score_rules.get("RSI小于40", 0))
            risks.append(f"RSI14为{rsi}，弱势或修复不足。")
    if macd.get("DIF") is not None and macd.get("DEA") is not None:
        if macd["DIF"] > macd["DEA"]:
            score += int(score_rules.get("MACD强", 0))
            basis.append("MACD DIF高于DEA，动能偏强。")
        else:
            score += int(score_rules.get("MACD弱", 0))
            risks.append("MACD DIF低于DEA，动能偏弱。")
    if volume_ratio is not None:
        if 1.1 <= volume_ratio <= 2.5:
            score += int(score_rules.get("量比1点1到2点5", 0))
            basis.append(f"5日量比{volume_ratio}，量能活跃但未明显过热。")
        elif volume_ratio > 3.5:
            score += int(score_rules.get("量比大于3点5", 0))
            risks.append(f"5日量比{volume_ratio}，短线异动过强。")

    layer = choose_layer(max(0, min(100, score)), rules.get("分层阈值", []))
    return build_result(item, max(0, min(100, score)), layer, basis, risks)


def build_result(item: dict[str, Any], score: int, layer: dict[str, Any], basis: list[str], risks: list[str]) -> dict[str, Any]:
    return {
        "代码": item.get("代码"),
        "名称": item.get("名称"),
        "系统评分": score,
        "层级": layer.get("层级"),
        "动作": layer.get("动作"),
        "依据": basis or ["未触发足够正向条件。"],
        "风险": risks or ["未发现技术指标层面的突出风险，仍需结合公告、财务和行业。"],
        "指标摘要": {
            "最新日期": item.get("最新日期"),
            "最新收盘": item.get("最新收盘"),
            "均线": item.get("均线", {}),
            "RSI14": item.get("RSI14"),
            "MACD": item.get("MACD", {}),
            "量比5日": item.get("量比5日")
        }
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 重点关注池候选池报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "说明：本报告只用于研究辅助，不构成投资建议，不自动交易。",
        "",
        "## L5深度研究候选",
        "",
    ]
    for item in report["候选池"]["L5深度研究"]:
        lines.append(f"- {item['名称']}（{item['代码']}）：评分{item['系统评分']}。依据：{'；'.join(item['依据'])}")
    if not report["候选池"]["L5深度研究"]:
        lines.append("- 暂无。")
    lines.extend(["", "## L6轻度关注", ""])
    for item in report["候选池"]["L6轻度关注"]:
        lines.append(f"- {item['名称']}（{item['代码']}）：评分{item['系统评分']}。风险：{'；'.join(item['风险'])}")
    if not report["候选池"]["L6轻度关注"]:
        lines.append("- 暂无。")
    lines.extend(["", "## L7系统过滤", ""])
    for item in report["候选池"]["L7系统过滤"]:
        lines.append(f"- {item['名称']}（{item['代码']}）：评分{item['系统评分']}。原因：{'；'.join(item['风险'])}")
    if not report["候选池"]["L7系统过滤"]:
        lines.append("- 暂无。")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rules = load_json(root / "01配置" / "候选池生成规则.json")
    indicators_path = root / "03数据" / "12技术指标" / "重点关注池技术指标_最新.json"
    indicators = load_json(indicators_path)
    scored = [score_item(item, rules) for item in indicators.get("技术指标", [])]
    candidate_pool = {
        "L5深度研究": [item for item in scored if item["层级"] == "L5深度研究"],
        "L6轻度关注": [item for item in scored if item["层级"] == "L6轻度关注"],
        "L7系统过滤": [item for item in scored if item["层级"] == "L7系统过滤"],
    }
    for group in candidate_pool.values():
        group.sort(key=lambda row: row["系统评分"], reverse=True)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(root / "01配置" / "候选池生成规则.json"),
        "技术指标文件": str(indicators_path),
        "股票数量": len(scored),
        "候选池": candidate_pool,
        "安全边界": {
            "是否调用大模型": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False
        }
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = root / rules.get("输出路径", {}).get("候选池", "03数据/14候选池")
    report_dir = root / rules.get("输出路径", {}).get("候选报告", "03数据/03研究报告")
    output = output_dir / f"重点关注池候选池_{timestamp}.json"
    latest = output_dir / "重点关注池候选池_最新.json"
    markdown = report_dir / f"重点关注池候选池报告_{timestamp}.md"
    markdown_latest = report_dir / "重点关注池候选池报告_最新.md"
    write_json(output, report)
    write_json(latest, report)
    text = build_markdown(report)
    write_text(markdown, text)
    write_text(markdown_latest, text)
    print(json.dumps({"股票数量": len(scored), "L5数量": len(candidate_pool["L5深度研究"]), "输出": str(output)}, ensure_ascii=False))
    return 0 if scored else 1


if __name__ == "__main__":
    raise SystemExit(main())
