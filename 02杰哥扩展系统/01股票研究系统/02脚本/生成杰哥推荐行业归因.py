# -*- coding: utf-8 -*-
"""
名称：生成杰哥推荐行业归因.py
作用：基于【杰哥推荐】量价特征，生成行业强势归因、失败归因和行业权重建议。
触发方式：python 生成杰哥推荐行业归因.py
依赖：03数据/272杰哥推荐量价特征/全候选量价特征_最新.json；强势成功样本量价特征_最新.json；失败对照样本量价特征_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地量价特征，只写03数据/273杰哥推荐行业归因；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不输出买卖指令。
创建修改记录：2026-05-10 创建，用于把【杰哥推荐】从量价强弱扩展到行业解释层。
标识：jiege-recommendation-industry-attribution-v1
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
FEATURE_DIR = ROOT / "03数据" / "272杰哥推荐量价特征"
ALL_FEATURE_PATH = FEATURE_DIR / "全候选量价特征_最新.json"
STRONG_FEATURE_PATH = FEATURE_DIR / "强势成功样本量价特征_最新.json"
FAILURE_FEATURE_PATH = FEATURE_DIR / "失败对照样本量价特征_最新.json"
OUT_DIR = ROOT / "03数据" / "273杰哥推荐行业归因"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_industry(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else "未知"


def avg(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [safe_float(row.get(key)) for row in rows if row.get(key) not in (None, "")]
    return round(mean(values), 4) if values else None


def med(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [safe_float(row.get(key)) for row in rows if row.get(key) not in (None, "")]
    return round(median(values), 4) if values else None


def ratio(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def industry_groups(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if isinstance(row, dict):
            groups[clean_industry(row.get("行业"))].append(row)
    return dict(groups)


def top_tags(rows: list[dict[str, Any]], limit: int = 8) -> list[list[Any]]:
    counter = Counter()
    for row in rows:
        tags = row.get("量价模式标签", [])
        if isinstance(tags, list):
            counter.update(str(item) for item in tags if item)
    return [[key, value] for key, value in counter.most_common(limit)]


def top_stocks(rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    sorted_rows = sorted(rows, key=lambda item: safe_float(item.get("杰哥推荐相似度分")), reverse=True)
    return [
        {
            "名称": item.get("名称"),
            "展示代码": item.get("展示代码"),
            "杰哥推荐相似度分": item.get("杰哥推荐相似度分"),
            "识别结论": item.get("识别结论"),
            "60日涨跌幅": item.get("60日涨跌幅"),
            "250日涨跌幅": item.get("250日涨跌幅"),
            "量价模式标签": item.get("量价模式标签", []),
        }
        for item in sorted_rows[:limit]
    ]


def attribution_label(stats: dict[str, Any]) -> str:
    if stats["强势样本数"] >= 8 and stats["强势过度代表指数"] >= 1.4 and stats["平均杰哥推荐分"] >= 82:
        return "强势共振行业"
    if stats["强势样本数"] >= 4 and stats["强势过度代表指数"] >= 1.0:
        return "结构活跃行业"
    if stats["失败样本数"] >= 8 and stats["失败过度代表指数"] >= 1.3:
        return "弱势/失败集中行业"
    if stats["候选数"] >= 60 and stats["优先研究数"] <= 2:
        return "样本多但强势不足行业"
    return "中性观察行业"


def build_industry_rows(all_rows: list[dict[str, Any]], strong_rows: list[dict[str, Any]], failure_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    all_groups = industry_groups(all_rows)
    strong_groups = industry_groups(strong_rows)
    failure_groups = industry_groups(failure_rows)
    total_count = len(all_rows)
    strong_total = len(strong_rows)
    failure_total = len(failure_rows)
    industries = sorted(set(all_groups) | set(strong_groups) | set(failure_groups))
    rows: list[dict[str, Any]] = []
    for industry in industries:
        universe = all_groups.get(industry, [])
        strong = strong_groups.get(industry, [])
        failure = failure_groups.get(industry, [])
        priority = [row for row in universe if row.get("识别结论") == "优先研究"]
        observe = [row for row in universe if row.get("识别结论") == "观察验证"]
        universe_share = ratio(len(universe), total_count)
        strong_share = ratio(len(strong), strong_total)
        failure_share = ratio(len(failure), failure_total)
        stats = {
            "行业": industry,
            "候选数": len(universe),
            "候选占比": universe_share,
            "强势样本数": len(strong),
            "强势样本占比": strong_share,
            "强势过度代表指数": round(strong_share / universe_share, 4) if universe_share else 0.0,
            "失败样本数": len(failure),
            "失败样本占比": failure_share,
            "失败过度代表指数": round(failure_share / universe_share, 4) if universe_share else 0.0,
            "优先研究数": len(priority),
            "观察验证数": len(observe),
            "平均杰哥推荐分": avg(universe, "杰哥推荐相似度分"),
            "中位杰哥推荐分": med(universe, "杰哥推荐相似度分"),
            "强势平均60日涨跌幅": avg(strong, "60日涨跌幅"),
            "强势平均120日涨跌幅": avg(strong, "120日涨跌幅"),
            "强势平均250日涨跌幅": avg(strong, "250日涨跌幅"),
            "强势成交额20_60比": avg(strong, "成交额20_60比"),
            "强势近60日放量天数": avg(strong, "近60日放量天数"),
            "强势250日距高点": avg(strong, "250日距高点"),
            "失败平均60日涨跌幅": avg(failure, "60日涨跌幅"),
            "失败平均250日涨跌幅": avg(failure, "250日涨跌幅"),
            "强势模式标签Top": top_tags(strong),
            "失败模式标签Top": top_tags(failure),
            "代表强势股票": top_stocks(strong),
            "代表当前候选": top_stocks(priority or observe or universe),
        }
        stats["归因标签"] = attribution_label(stats)
        stats["行业权重建议"] = industry_weight_suggestion(stats)
        stats["归因说明"] = attribution_reason(stats)
        rows.append(stats)
    rows.sort(key=lambda item: (
        item["归因标签"] == "强势共振行业",
        item["强势过度代表指数"],
        item["强势样本数"],
        safe_float(item.get("平均杰哥推荐分")),
    ), reverse=True)
    return rows


def industry_weight_suggestion(stats: dict[str, Any]) -> str:
    label = stats.get("归因标签")
    if label == "强势共振行业":
        return "提高行业解释权重，但仍需个股量价确认"
    if label == "结构活跃行业":
        return "保持观察权重，优先寻找量价同步个股"
    if label == "弱势/失败集中行业":
        return "降低推荐权重，除非出现明确反转证据"
    if label == "样本多但强势不足行业":
        return "只做覆盖，不作为杰哥推荐主要方向"
    return "中性权重"


def attribution_reason(stats: dict[str, Any]) -> str:
    return (
        f"候选{stats['候选数']}只，强势样本{stats['强势样本数']}只，失败样本{stats['失败样本数']}只；"
        f"强势过度代表指数{stats['强势过度代表指数']}，失败过度代表指数{stats['失败过度代表指数']}；"
        f"优先研究{stats['优先研究数']}只，观察验证{stats['观察验证数']}只。"
    )


def build_report(rows: list[dict[str, Any]], all_rows: list[dict[str, Any]], strong_rows: list[dict[str, Any]], failure_rows: list[dict[str, Any]]) -> dict[str, Any]:
    label_counter = Counter(row["归因标签"] for row in rows)
    strong_industries = [row for row in rows if row["归因标签"] in {"强势共振行业", "结构活跃行业"}]
    weak_industries = [row for row in rows if row["归因标签"] in {"弱势/失败集中行业", "样本多但强势不足行业"}]
    return {
        "名称": "杰哥推荐行业归因报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "输入": {
            "全候选量价特征": str(ALL_FEATURE_PATH),
            "强势成功样本量价特征": str(STRONG_FEATURE_PATH),
            "失败对照样本量价特征": str(FAILURE_FEATURE_PATH),
        },
        "统计": {
            "候选数量": len(all_rows),
            "强势样本数量": len(strong_rows),
            "失败对照数量": len(failure_rows),
            "行业数量": len(rows),
            "归因标签分布": dict(label_counter),
        },
        "强势行业Top": strong_industries[:12],
        "弱势或降权行业Top": weak_industries[:12],
        "全部行业归因": rows,
        "方法边界": [
            "本报告只解释量价样本在行业上的分布，不等于行业基本面结论。",
            "行业强势必须回到个股量价和证据边界验证，不能单靠行业标签推荐。",
            "缺行业资金连续证据和板块指数长周期证据，后续应继续补强。",
        ],
        "安全边界": safety_boundary(),
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 杰哥推荐行业归因报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 候选数量：{report['统计']['候选数量']}",
        f"- 强势样本：{report['统计']['强势样本数量']}",
        f"- 失败对照：{report['统计']['失败对照数量']}",
        f"- 行业数量：{report['统计']['行业数量']}",
        f"- 归因标签分布：{report['统计']['归因标签分布']}",
        "",
        "## 一、强势行业Top",
        "",
        "| 排名 | 行业 | 标签 | 候选数 | 强势样本 | 强势代表指数 | 平均推荐分 | 权重建议 |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for index, row in enumerate(report["强势行业Top"][:12], start=1):
        lines.append(
            f"| {index} | {row['行业']} | {row['归因标签']} | {row['候选数']} | {row['强势样本数']} | "
            f"{row['强势过度代表指数']} | {row['平均杰哥推荐分']} | {row['行业权重建议']} |"
        )
    lines.extend([
        "",
        "## 二、弱势或降权行业Top",
        "",
        "| 排名 | 行业 | 标签 | 候选数 | 失败样本 | 失败代表指数 | 优先研究数 | 权重建议 |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ])
    for index, row in enumerate(report["弱势或降权行业Top"][:12], start=1):
        lines.append(
            f"| {index} | {row['行业']} | {row['归因标签']} | {row['候选数']} | {row['失败样本数']} | "
            f"{row['失败过度代表指数']} | {row['优先研究数']} | {row['行业权重建议']} |"
        )
    lines.extend([
        "",
        "## 三、方法边界",
        "",
    ])
    for item in report["方法边界"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_rows = load_json(ALL_FEATURE_PATH, [])
    strong_rows = load_json(STRONG_FEATURE_PATH, [])
    failure_rows = load_json(FAILURE_FEATURE_PATH, [])
    industry_rows = build_industry_rows(all_rows, strong_rows, failure_rows)
    report = build_report(industry_rows, all_rows, strong_rows, failure_rows)
    write_json(OUT_DIR / f"杰哥推荐行业归因明细_{stamp}.json", industry_rows)
    write_json(OUT_DIR / "杰哥推荐行业归因明细_最新.json", industry_rows)
    write_json(OUT_DIR / f"杰哥推荐行业归因报告_{stamp}.json", report)
    write_json(OUT_DIR / "杰哥推荐行业归因报告_最新.json", report)
    write_text(OUT_DIR / f"杰哥推荐行业归因报告_{stamp}.md", build_markdown(report))
    write_text(OUT_DIR / "杰哥推荐行业归因报告_最新.md", build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "候选数量": len(all_rows),
        "强势样本数量": len(strong_rows),
        "失败对照数量": len(failure_rows),
        "行业数量": len(industry_rows),
        "输出目录": str(OUT_DIR),
        "安全边界": safety_boundary(),
    }, ensure_ascii=False))
    return 0 if len(industry_rows) > 0 and len(strong_rows) >= 100 and len(failure_rows) >= 100 else 1


def safety_boundary() -> dict[str, bool]:
    return {
        "真实发送企业微信": False,
        "触发n8n": False,
        "调用券商接口": False,
        "自动交易": False,
        "输出交易指令": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
