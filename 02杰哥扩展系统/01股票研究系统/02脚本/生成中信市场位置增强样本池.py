# -*- coding: utf-8 -*-
"""
名称：生成中信市场位置增强样本池.py
作用：读取现有 L6/L5 样本池和中信市场位置表，生成不改核心评分的市场位置增强排序。
边界：只读股票系统本地数据；只写 03数据/293；不修改 L6/L5 原始产物；不触发 n8n；不发送企业微信；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
DATA = ROOT / "03数据"
L6_PATH = DATA / "133行业主题观察池" / "L6行业主题观察池_最新.json"
L5_PATH = DATA / "134深度研究池" / "L5深度研究池_最新.json"
MARKET_POSITION_PATH = DATA / "292中信概念板块成分映射" / "中信股票市场位置_最新.csv"
OUT_DIR = DATA / "293中信市场位置增强样本池"


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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        suffix = suffix.lower()
        if suffix in {"sh", "sz", "bj"}:
            return suffix + num.zfill(6)
    if text.isdigit():
        if text.startswith(("6", "9")):
            return "sh" + text.zfill(6)
        if text.startswith(("4", "8")):
            return "bj" + text.zfill(6)
        return "sz" + text.zfill(6)
    return text


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def split_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        raw = value
    else:
        raw = str(value or "").replace(",", "、").split("、")
    result: list[str] = []
    seen: set[str] = set()
    for item in raw:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def load_market_positions() -> dict[str, dict[str, Any]]:
    if not MARKET_POSITION_PATH.exists():
        return {}
    positions: dict[str, dict[str, Any]] = {}
    with MARKET_POSITION_PATH.open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            code = normalize_code(row.get("股票代码"))
            if not code:
                continue
            item = dict(row)
            item["概念列表"] = split_tags(row.get("概念板块"))
            item["风格列表"] = split_tags(row.get("风格板块"))
            item["指数列表"] = split_tags(row.get("指数板块"))
            item["特殊列表"] = split_tags(row.get("特殊板块"))
            item["板块总数"] = int(safe_float(row.get("板块总数"), 0))
            positions[code] = item
    return positions


def stock_code(item: dict[str, Any]) -> str:
    return normalize_code(item.get("代码") or item.get("展示代码") or item.get("股票代码") or item.get("code"))


def position_signal(position: dict[str, Any]) -> dict[str, Any]:
    concepts = position.get("概念列表", [])
    styles = position.get("风格列表", [])
    indices = position.get("指数列表", [])
    specials = position.get("特殊列表", [])
    concept_score = min(len(concepts) / 12 * 5, 5)
    style_score = min(len(styles) / 8 * 5, 5)
    index_score = min(len(indices) / 8 * 5, 5)
    special_score = min(len(specials) / 6 * 5, 5)
    return {
        "概念数量": len(concepts),
        "风格数量": len(styles),
        "指数数量": len(indices),
        "特殊板块数量": len(specials),
        "概念交叉分": round(concept_score, 4),
        "风格确认分": round(style_score, 4),
        "指数归属分": round(index_score, 4),
        "交易属性分": round(special_score, 4),
    }


def build_hot_theme_counter(items: list[dict[str, Any]], positions: dict[str, dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for item in items:
        code = stock_code(item)
        position = positions.get(code, {})
        weight = max(safe_float(item.get("调整分"), 0), safe_float(item.get("行业强度分"), 0), 1)
        for concept in position.get("概念列表", []):
            counter[concept] += weight
    return counter


def enhance_items(
    items: list[dict[str, Any]],
    positions: dict[str, dict[str, Any]],
    hot_themes: set[str],
    pool_name: str,
) -> list[dict[str, Any]]:
    enhanced: list[dict[str, Any]] = []
    for item in items:
        code = stock_code(item)
        position = positions.get(code, {})
        signal = position_signal(position)
        base_score = safe_float(item.get("调整分"), safe_float(item.get("行业强度分"), 0))
        concepts = position.get("概念列表", [])
        hot_hits = [theme for theme in concepts if theme in hot_themes]
        hot_score = min(len(hot_hits) / 5 * 5, 5)
        market_position_score = (
            base_score * 0.45
            + signal["概念交叉分"] * 0.25
            + signal["风格确认分"] * 0.10
            + signal["指数归属分"] * 0.10
            + signal["交易属性分"] * 0.05
            + hot_score * 0.05
        )
        source_reasons = [str(x) for x in item.get("入选理由", []) if str(x).strip()]
        if hot_hits:
            source_reasons.append(f"命中当前高频主题：{'、'.join(hot_hits[:5])}")
        if position:
            source_reasons.append(f"市场位置：{position.get('行业名称', '')}/{position.get('细分行业名称', '')}")
        row = {
            **item,
            "股票代码": code,
            "增强池": pool_name,
            "中信市场位置状态": "已匹配" if position else "未匹配",
            "行业名称_中信": position.get("行业名称", ""),
            "细分行业名称_中信": position.get("细分行业名称", ""),
            "概念板块Top": "、".join(concepts[:8]),
            "风格板块Top": "、".join(position.get("风格列表", [])[:5]),
            "指数归属Top": "、".join(position.get("指数列表", [])[:5]),
            "特殊板块Top": "、".join(position.get("特殊列表", [])[:5]),
            "市场位置摘要": position.get("市场位置摘要", ""),
            "概念数量": signal["概念数量"],
            "风格数量": signal["风格数量"],
            "指数数量": signal["指数数量"],
            "特殊板块数量": signal["特殊板块数量"],
            "高频主题命中": "、".join(hot_hits[:8]),
            "高频主题命中数": len(hot_hits),
            "市场位置增强分": round(market_position_score, 4),
            "市场位置增强理由": source_reasons[:8],
            "是否改变原始评分": False,
        }
        enhanced.append(row)
    enhanced.sort(key=lambda x: safe_float(x.get("市场位置增强分")), reverse=True)
    for index, row in enumerate(enhanced, start=1):
        row["市场位置增强排名"] = index
    return enhanced


def compact_csv_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        output.append(
            {
                "市场位置增强排名": row.get("市场位置增强排名"),
                "股票代码": row.get("股票代码"),
                "名称": row.get("名称"),
                "原行业": row.get("行业"),
                "中信行业": row.get("行业名称_中信"),
                "中信细分行业": row.get("细分行业名称_中信"),
                "原调整分": row.get("调整分"),
                "市场位置增强分": row.get("市场位置增强分"),
                "概念数量": row.get("概念数量"),
                "高频主题命中数": row.get("高频主题命中数"),
                "高频主题命中": row.get("高频主题命中"),
                "概念板块Top": row.get("概念板块Top"),
                "市场位置摘要": row.get("市场位置摘要"),
            }
        )
    return output


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 中信市场位置增强样本池 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- {report['结论']}",
        f"- L6增强样本数：{report['统计']['L6增强样本数']}，匹配中信市场位置：{report['统计']['L6市场位置匹配数']}。",
        f"- L5增强样本数：{report['统计']['L5增强样本数']}，匹配中信市场位置：{report['统计']['L5市场位置匹配数']}。",
        f"- 高频主题数量：{len(report['高频主题Top30'])}。",
        "",
        "## 二、当前高频主题Top20",
        "",
    ]
    for item in report["高频主题Top30"][:20]:
        lines.append(f"- {item['主题']}：{item['权重']}")
    lines.extend(["", "## 三、L5市场位置增强排序", ""])
    for item in report["L5市场位置增强排序"][:10]:
        lines.append(
            f"- {item['市场位置增强排名']}. {item.get('名称')}（{item['股票代码']}）："
            f"增强分 {item['市场位置增强分']}；{item.get('市场位置摘要') or '市场位置待补齐'}"
        )
    lines.extend(["", "## 四、L6市场位置增强排序Top20", ""])
    for item in report["L6市场位置增强排序"][:20]:
        lines.append(
            f"- {item['市场位置增强排名']}. {item.get('名称')}（{item['股票代码']}）："
            f"增强分 {item['市场位置增强分']}；高频主题 {item.get('高频主题命中') or '无'}"
        )
    lines.extend(
        [
            "",
            "## 五、使用原则",
            "",
            "- 本增强层不修改 L6/L5 原始评分，只给样本池多一层“市场位置解释”和“主题交叉排序”。",
            "- 后续可把 L5报告、盘后短线观察、专家总览读取本增强层，优先解释高频主题命中和市场位置。",
            "- 只有复盘证明有效后，才考虑把其中稳定因子吸收到正式评分规则。",
            "",
            "## 六、安全边界",
            "",
            "- 不触发 n8n，不发送企业微信，不调用券商接口，不自动交易。",
            "- 不修改中信软件目录，不修改 L6/L5 原始产物。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    l6 = load_json(L6_PATH, {}) or {}
    l5 = load_json(L5_PATH, {}) or {}
    positions = load_market_positions()
    l6_items = list(l6.get("股票池", []))
    l5_items = list(l5.get("股票池", []))
    hot_counter = build_hot_theme_counter(l6_items, positions)
    hot_theme_top = [{"主题": key, "权重": round(value, 4)} for key, value in hot_counter.most_common(30)]
    hot_themes = {item["主题"] for item in hot_theme_top[:30]}
    l6_enhanced = enhance_items(l6_items, positions, hot_themes, "L6行业主题观察池")
    l5_enhanced = enhance_items(l5_items, positions, hot_themes, "L5深度研究池")
    report = {
        "名称": "中信市场位置增强样本池",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "已把中信行业、概念、风格、指数、特殊板块位置接到L6/L5样本池解释层；本轮不改变原始评分。",
        "输入文件": {
            "L6": str(L6_PATH),
            "L5": str(L5_PATH),
            "中信市场位置": str(MARKET_POSITION_PATH),
        },
        "统计": {
            "中信市场位置股票数": len(positions),
            "L6增强样本数": len(l6_enhanced),
            "L6市场位置匹配数": sum(1 for item in l6_enhanced if item.get("中信市场位置状态") == "已匹配"),
            "L5增强样本数": len(l5_enhanced),
            "L5市场位置匹配数": sum(1 for item in l5_enhanced if item.get("中信市场位置状态") == "已匹配"),
        },
        "评分说明": {
            "原始评分权重": "45%",
            "概念交叉": "25%",
            "风格确认": "10%",
            "指数归属": "10%",
            "交易属性": "5%",
            "高频主题命中": "5%",
            "是否改变原始评分": False,
        },
        "高频主题Top30": hot_theme_top,
        "L6市场位置增强排序": l6_enhanced,
        "L5市场位置增强排序": l5_enhanced,
        "安全边界": {
            "是否修改L6L5原始产物": False,
            "是否修改中信目录": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    write_json(OUT_DIR / "中信市场位置增强样本池_最新.json", report)
    write_text(OUT_DIR / "中信市场位置增强样本池_最新.md", build_markdown(report))
    csv_fields = [
        "市场位置增强排名",
        "股票代码",
        "名称",
        "原行业",
        "中信行业",
        "中信细分行业",
        "原调整分",
        "市场位置增强分",
        "概念数量",
        "高频主题命中数",
        "高频主题命中",
        "概念板块Top",
        "市场位置摘要",
    ]
    write_csv(OUT_DIR / "L6市场位置增强排序_最新.csv", compact_csv_rows(l6_enhanced), csv_fields)
    write_csv(OUT_DIR / "L5市场位置增强排序_最新.csv", compact_csv_rows(l5_enhanced), csv_fields)
    print(
        json.dumps(
            {
                "状态": "完成",
                "L6增强样本数": len(l6_enhanced),
                "L5增强样本数": len(l5_enhanced),
                "L6匹配数": report["统计"]["L6市场位置匹配数"],
                "L5匹配数": report["统计"]["L5市场位置匹配数"],
                "报告": str(OUT_DIR / "中信市场位置增强样本池_最新.md"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
