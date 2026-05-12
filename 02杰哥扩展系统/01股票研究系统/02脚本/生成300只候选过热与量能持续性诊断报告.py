# -*- coding: utf-8 -*-
"""
名称：生成300只候选过热与量能持续性诊断报告.py
作用：诊断推送前候选的短线过热和量能连续性；只生成报告，不改评分、不发送。
触发方式：python 生成300只候选过热与量能持续性诊断报告.py
依赖：Python标准库；300只候选过热与量能持续性诊断规则.json；94历史K线和技术指标；96推送前候选包；110评分因子拆解。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写111诊断报告；不修改评分规则；不修改候选清单；不触发发送链路；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选过热与量能持续性诊断报告脚本。
标识：stock-trial-pool-300-overheat-volume-continuity-diagnosis
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


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", "-", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def index_by_code(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("代码", "")).lower(): item for item in items if item.get("代码")}


def avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def sum_percent(kline: list[dict[str, Any]], days: int) -> float:
    return round(sum(as_float(item.get("涨跌幅")) for item in kline[-days:]), 4) if len(kline) >= days else 0.0


def volume_avg(kline: list[dict[str, Any]], days: int) -> float:
    return avg([as_float(item.get("成交量")) for item in kline[-days:]]) if len(kline) >= days else 0.0


def consecutive_volume_up(kline: list[dict[str, Any]]) -> int:
    count = 0
    tail = kline[-6:]
    for idx in range(len(tail) - 1, 0, -1):
        if as_float(tail[idx].get("成交量")) > as_float(tail[idx - 1].get("成交量")):
            count += 1
        else:
            break
    return count


def overheat_level(rsi: float, pct3: float, pct5: float, ma20_deviation: float) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if rsi > 75:
        reasons.append("RSI14>75")
    elif rsi >= 70:
        reasons.append("RSI14接近偏热区")
    if pct3 >= 8:
        reasons.append("3日累计涨幅>=8%")
    elif pct3 >= 5:
        reasons.append("3日累计涨幅>=5%")
    if pct5 >= 12:
        reasons.append("5日累计涨幅>=12%")
    if ma20_deviation >= 15:
        reasons.append("收盘价偏离MA20>=15%")
    elif ma20_deviation >= 10:
        reasons.append("收盘价偏离MA20>=10%")
    if rsi > 75 and (pct3 >= 8 or ma20_deviation >= 15):
        return "高", reasons
    if rsi > 75 or pct3 >= 6 or pct5 >= 12 or ma20_deviation >= 10:
        return "中", reasons
    return "低", reasons or ["未触发明显短线过热条件"]


def volume_level(ratio3_10: float, ratio5_20: float, up_days: int) -> tuple[str, list[str]]:
    reasons: list[str] = []
    reasons.append(f"3日均量/10日均量={ratio3_10}")
    reasons.append(f"5日均量/20日均量={ratio5_20}")
    reasons.append(f"连续放量天数={up_days}")
    if ratio3_10 >= 1.2 and ratio5_20 >= 1.05:
        return "强", reasons
    if ratio3_10 >= 0.9 and ratio5_20 >= 0.85:
        return "一般", reasons
    return "弱", reasons


def diagnose(item: dict[str, Any], kline_item: dict[str, Any], tech_item: dict[str, Any], score_item: dict[str, Any]) -> dict[str, Any]:
    kline = kline_item.get("K线", [])
    tech = item.get("技术指标摘要", {}) or tech_item
    ma20 = as_float(tech.get("均线", {}).get("MA20"))
    close = as_float(tech.get("最新收盘"))
    rsi = as_float(tech.get("RSI14"), -1)
    pct3 = sum_percent(kline, 3)
    pct5 = sum_percent(kline, 5)
    pct10 = sum_percent(kline, 10)
    ma20_deviation = round(((close / ma20) - 1) * 100, 4) if close and ma20 else 0.0
    vol3 = volume_avg(kline, 3)
    vol5 = volume_avg(kline, 5)
    vol10 = volume_avg(kline, 10)
    vol20 = volume_avg(kline, 20)
    ratio3_10 = round(vol3 / vol10, 4) if vol10 else 0.0
    ratio5_20 = round(vol5 / vol20, 4) if vol20 else 0.0
    up_days = consecutive_volume_up(kline)
    hot_level, hot_reasons = overheat_level(rsi, pct3, pct5, ma20_deviation)
    vol_level, vol_reasons = volume_level(ratio3_10, ratio5_20, up_days)
    tags = []
    if hot_level in ("中", "高"):
        tags.append(f"短线过热{hot_level}")
    if vol_level != "强":
        tags.append(f"量能持续性{vol_level}")
    if "事件待核验" in score_item.get("风险标签", []):
        tags.append("事件待核验")
    if hot_level == "高":
        action = "优先等待复盘验证，不因单日强势直接提高权重。"
    elif vol_level == "弱":
        action = "保留观察，但需要后续量能重新转强再提高置信度。"
    else:
        action = "保持候选观察，等待事件核验和T+1/T+3/T+5复盘。"
    return {
        "代码": item.get("代码"),
        "名称": item.get("名称"),
        "现有推送前评分": item.get("推送前评分"),
        "短线过热等级": hot_level,
        "量能持续等级": vol_level,
        "关键指标": {
            "RSI14": rsi,
            "3日累计涨跌幅": pct3,
            "5日累计涨跌幅": pct5,
            "10日累计涨跌幅": pct10,
            "收盘价相对MA20偏离度": ma20_deviation,
            "3日均量/10日均量": ratio3_10,
            "5日均量/20日均量": ratio5_20,
            "连续放量天数": up_days
        },
        "判断依据": {
            "过热依据": hot_reasons,
            "量能依据": vol_reasons
        },
        "观察标签": list(dict.fromkeys(tags)) or ["未发现111层新增观察标签"],
        "下一步观察动作": action
    }


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    high_or_mid = [row["名称"] for row in rows if row.get("短线过热等级") in ("中", "高")]
    weak_volume = [row["名称"] for row in rows if row.get("量能持续等级") == "弱"]
    normal_volume = [row["名称"] for row in rows if row.get("量能持续等级") == "一般"]
    return {
        "候选数量": len(rows),
        "短线过热中高候选": high_or_mid,
        "量能持续性弱候选": weak_volume,
        "量能持续性一般候选": normal_volume,
        "结论": "111层用于补充短线风险和量能连续性观察，不改变当前评分和候选排序。"
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选过热与量能持续性诊断报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 总结",
        "",
        f"- 候选数量：{report['摘要']['候选数量']}",
        f"- 短线过热中高候选：{('、'.join(report['摘要']['短线过热中高候选']) or '无')}",
        f"- 量能持续性弱候选：{('、'.join(report['摘要']['量能持续性弱候选']) or '无')}",
        f"- 量能持续性一般候选：{('、'.join(report['摘要']['量能持续性一般候选']) or '无')}",
        f"- 当前结论：{report['摘要']['结论']}",
        "",
        "## 候选诊断",
        ""
    ]
    for row in report.get("候选诊断", []):
        metrics = row["关键指标"]
        lines.append(
            f"- {row['名称']}（{row['代码']}）：过热{row['短线过热等级']}，量能{row['量能持续等级']}；"
            f"RSI{metrics['RSI14']}，3日涨跌{metrics['3日累计涨跌幅']}%，MA20偏离{metrics['收盘价相对MA20偏离度']}%，"
            f"3日/10日量比{metrics['3日均量/10日均量']}；标签：{'、'.join(row['观察标签'])}"
        )
    lines.extend([
        "",
        "## 下一步",
        "",
        "- 先补齐事件正文人工核验，再运行108联动刷新。",
        "- T+1/T+3/T+5到期后用107回填复盘结果，再判断是否调整过热和量能权重。",
        "- 本报告不生成买卖建议，不替换原评分。",
        "",
        "## 安全边界",
        ""
    ])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选过热与量能持续性诊断规则.json"
    rule = load_json(rule_path)
    kline_path = root / "03数据" / "94候选历史K线技术指标" / "300只候选历史K线_最新.json"
    tech_path = root / "03数据" / "94候选历史K线技术指标" / "300只候选技术指标_最新.json"
    package_path = root / "03数据" / "96推送前候选包" / "300只候选推送前候选包_最新.json"
    score_path = root / "03数据" / "110评分因子拆解" / "300只候选评分因子拆解报告_最新.json"
    kline_map = index_by_code(load_json(kline_path).get("历史K线", []))
    tech_map = index_by_code(load_json(tech_path).get("技术指标", []))
    package = load_json(package_path)
    score_map = index_by_code(load_json(score_path).get("候选评分拆解", []))
    rows = [
        diagnose(
            item,
            kline_map.get(str(item.get("代码", "")).lower(), {}),
            tech_map.get(str(item.get("代码", "")).lower(), {}),
            score_map.get(str(item.get("代码", "")).lower(), {})
        )
        for item in package.get("推送前候选", [])
    ]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "94历史K线": str(kline_path),
            "94技术指标": str(tech_path),
            "96推送前候选包": str(package_path),
            "110评分因子拆解": str(score_path)
        },
        "摘要": build_summary(rows),
        "候选诊断": rows,
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选过热与量能持续性诊断报告_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只候选过热与量能持续性诊断报告_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"候选数量": len(rows), "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
