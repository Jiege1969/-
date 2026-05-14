# -*- coding: utf-8 -*-
"""
名称：生成中信样本学习闭环.py
作用：用中信本机vipdoc日线为样本池建立持续跟踪账，记录T+1/T+3/T+5/T+10/T+20效果。
边界：只读股票系统数据和中信本机归档日线；只写03数据/286中信样本学习闭环；不登录券商；不调用券商接口；不交易；不发送企业微信。
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


WINDOWS = [1, 3, 5, 10, 20]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        suffix = suffix.lower()
        if suffix in {"sh", "sz", "bj"}:
            return f"{suffix}{num.zfill(6)}"
    if text.isdigit():
        text = text.zfill(6)
        if text.startswith(("4", "8", "920")):
            return f"bj{text}"
        if text.startswith(("6", "9")):
            return f"sh{text}"
        return f"sz{text}"
    return text


def display_code(code: str) -> str:
    if code.startswith("sh"):
        return f"{code[2:]}.SH"
    if code.startswith("sz"):
        return f"{code[2:]}.SZ"
    if code.startswith("bj"):
        return f"{code[2:]}.BJ"
    return code.upper()


def market_dir(code: str) -> str:
    if code.startswith("bj"):
        return "bj"
    if code.startswith("sh"):
        return "sh"
    return "sz"


def stock_history_path(root: Path, code: str) -> Path:
    return root / "03数据" / "013券商本机历史日线" / "中信证券" / "按股票" / market_dir(code) / f"{code}.json"


def latest_rows(root: Path, code: str) -> list[dict[str, Any]]:
    data = load_json(stock_history_path(root, code), {})
    rows = data.get("日线", []) if isinstance(data, dict) else []
    return rows if isinstance(rows, list) else []


def close_value(row: dict[str, Any]) -> float | None:
    try:
        value = row.get("收盘")
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def row_date(row: dict[str, Any]) -> str:
    return str(row.get("日期") or "")


def existing_by_code(path: Path) -> dict[str, dict[str, Any]]:
    data = load_json(path, {})
    records = data.get("样本记录", []) if isinstance(data, dict) else []
    result: dict[str, dict[str, Any]] = {}
    for item in records:
        if isinstance(item, dict) and item.get("代码"):
            result[normalize_code(item.get("代码"))] = item
    return result


def add_candidate(pool: dict[str, dict[str, Any]], stock: dict[str, Any], source: str, level: str) -> None:
    code = normalize_code(stock.get("代码") or stock.get("展示代码") or stock.get("原始代码"))
    if not code:
        return
    item = pool.setdefault(code, {
        "代码": code,
        "展示代码": stock.get("展示代码") or stock.get("原始代码") or display_code(code),
        "名称": stock.get("名称") or "",
        "行业": stock.get("行业") or stock.get("名单分类") or "未分类",
        "细分领域": stock.get("细分领域") or "",
        "样本来源": [],
        "观察层级": level,
        "入池理由": [],
    })
    if source not in item["样本来源"]:
        item["样本来源"].append(source)
    if level == "核心验证样本":
        item["观察层级"] = level
    reasons = stock.get("入选理由") if isinstance(stock.get("入选理由"), list) else []
    for reason in reasons[:3]:
        if reason not in item["入池理由"]:
            item["入池理由"].append(reason)


def build_candidates(root: Path) -> list[dict[str, Any]]:
    pool: dict[str, dict[str, Any]] = {}
    l5 = load_json(root / "03数据" / "134深度研究池" / "L5深度研究池_最新.json", {})
    for stock in (l5.get("股票池", []) if isinstance(l5, dict) else [])[:15]:
        if isinstance(stock, dict):
            add_candidate(pool, stock, "L5深度研究池", "核心验证样本")

    named = load_json(root / "01配置" / "19名单股票池.json", {})
    for stock in (named.get("股票池", []) if isinstance(named, dict) else []):
        if isinstance(stock, dict):
            add_candidate(pool, stock, "19名单长期样本池", "长期对照样本")

    return list(pool.values())


def outcome_for(rows: list[dict[str, Any]], baseline_date: str, baseline_close: float | None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if not rows or not baseline_date or baseline_close is None:
        return result
    dates = [row_date(row) for row in rows]
    try:
        start_index = dates.index(baseline_date)
    except ValueError:
        return result
    for window in WINDOWS:
        idx = start_index + window
        key = f"T+{window}"
        if idx >= len(rows):
            result[key] = {"状态": "待验证", "目标序号": idx, "可用交易日数": len(rows) - start_index - 1}
            continue
        close = close_value(rows[idx])
        if close is None:
            result[key] = {"状态": "缺收盘价", "日期": row_date(rows[idx])}
            continue
        result[key] = {
            "状态": "已验证",
            "日期": row_date(rows[idx]),
            "收盘价": close,
            "相对入池涨跌幅": round((close - baseline_close) / baseline_close * 100, 4),
        }
    return result


def make_record(root: Path, candidate: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    code = normalize_code(candidate.get("代码"))
    rows = latest_rows(root, code)
    latest = rows[-1] if rows else {}
    latest_date = row_date(latest)
    latest_close = close_value(latest)
    baseline_date = previous.get("基准日期") or latest_date
    baseline_close = previous.get("基准收盘价")
    if baseline_close is None:
        baseline_close = latest_close
    try:
        baseline_close = float(baseline_close) if baseline_close is not None else None
    except (TypeError, ValueError):
        baseline_close = latest_close
    outcomes = outcome_for(rows, str(baseline_date), baseline_close)
    verified_count = sum(1 for item in outcomes.values() if item.get("状态") == "已验证")
    pending_count = sum(1 for item in outcomes.values() if item.get("状态") == "待验证")
    return {
        "代码": code,
        "展示代码": candidate.get("展示代码") or display_code(code),
        "名称": candidate.get("名称") or previous.get("名称") or "",
        "行业": candidate.get("行业") or previous.get("行业") or "未分类",
        "细分领域": candidate.get("细分领域") or previous.get("细分领域") or "",
        "观察层级": candidate.get("观察层级") or previous.get("观察层级") or "常规样本",
        "样本来源": sorted(set((previous.get("样本来源") or []) + (candidate.get("样本来源") or []))),
        "入池理由": list(dict.fromkeys((previous.get("入池理由") or []) + (candidate.get("入池理由") or [])))[:8],
        "基准日期": baseline_date,
        "基准收盘价": baseline_close,
        "最新日期": latest_date,
        "最新收盘价": latest_close,
        "中信日线记录数": len(rows),
        "中信数据可用": bool(rows),
        "验证窗口": outcomes,
        "已验证窗口数": verified_count,
        "待验证窗口数": pending_count,
        "学习状态": "已有验证结果" if verified_count else "等待T周期验证",
    }


def experience_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for record in records:
        for key in ("T+3", "T+5", "T+10", "T+20"):
            outcome = (record.get("验证窗口") or {}).get(key) or {}
            if outcome.get("状态") != "已验证":
                continue
            pct = float(outcome.get("相对入池涨跌幅") or 0)
            if pct >= 5:
                result.append({
                    "类型": "正向经验候选",
                    "股票": f"{record['名称']}({record['展示代码']})",
                    "窗口": key,
                    "涨跌幅": pct,
                    "候选经验": "入池后对应窗口表现较强，后续复盘其入池理由是否可沉淀为加分条件。",
                    "是否自动改规则": False,
                })
            elif pct <= -5:
                result.append({
                    "类型": "失效经验候选",
                    "股票": f"{record['名称']}({record['展示代码']})",
                    "窗口": key,
                    "涨跌幅": pct,
                    "候选经验": "入池后对应窗口回撤较大，后续复盘风险线、过热量能或行业退潮条件是否应提前提示。",
                    "是否自动改规则": False,
                })
    return result[:50]


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 中信样本学习闭环 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 总体状态：{report['总体状态']}",
        f"- 样本总数：{report['样本统计']['样本总数']}",
        f"- 中信数据可用：{report['样本统计']['中信数据可用数']}",
        f"- 已有验证结果样本：{report['样本统计']['已有验证结果样本数']}",
        f"- 经验候选：{report['样本统计']['经验候选数']}",
        f"- 最新中信日线日期：{report['样本统计']['最新中信日线日期'] or '未提取'}",
        "",
        "## 二、样本来源",
        "",
    ]
    for name, count in report["来源统计"].items():
        lines.append(f"- {name}：{count}")
    lines.extend(["", "## 三、核心验证样本", ""])
    for item in report["核心样本预览"]:
        lines.append(
            f"- {item['名称']}({item['展示代码']})：{item['学习状态']}，"
            f"基准 {item['基准日期']} / 最新 {item['最新日期']}"
        )
    lines.extend(["", "## 四、经验候选", ""])
    if report["经验候选"]:
        for item in report["经验候选"][:20]:
            lines.append(f"- [{item['类型']}] {item['股票']} {item['窗口']} {item['涨跌幅']}%：{item['候选经验']}")
    else:
        lines.append("- 暂无，等待T周期验证。")
    lines.extend([
        "",
        "## 五、安全边界",
        "",
        "- 不登录券商。",
        "- 不调用券商接口。",
        "- 不交易。",
        "- 不自动改评分、排序或规则。",
        "- 只把经验写入候选账，等待复盘确认。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "286中信样本学习闭环"
    latest_json = out_dir / "中信样本学习闭环_最新.json"
    previous = existing_by_code(latest_json)
    candidates = build_candidates(root)
    records = [make_record(root, item, previous.get(normalize_code(item.get("代码")), {})) for item in candidates]
    source_counter: Counter[str] = Counter()
    for record in records:
        for source in record.get("样本来源") or []:
            source_counter[source] += 1
    exp = experience_candidates(records)
    core = [item for item in records if item.get("观察层级") == "核心验证样本"][:20]
    report = {
        "名称": "中信样本学习闭环",
        "版本": "2026-05-14",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "样本账已建立，等待T周期滚动验证" if not exp else "已有经验候选，等待复盘确认",
        "数据口径": {
            "主数据源": "中信证券本机vipdoc归档日线",
            "用途": "验证分析效果、沉淀经验候选、辅助后续分析表达和规则复盘",
            "不做事项": "不登录券商、不交易、不自动改评分权重",
        },
        "样本统计": {
            "样本总数": len(records),
            "中信数据可用数": sum(1 for item in records if item.get("中信数据可用")),
            "已有验证结果样本数": sum(1 for item in records if item.get("已验证窗口数", 0) > 0),
            "经验候选数": len(exp),
            "最新中信日线日期": max([str(item.get("最新日期") or "") for item in records] or [""]),
        },
        "来源统计": dict(source_counter),
        "核心样本预览": core,
        "经验候选": exp,
        "样本记录": records,
        "安全边界": {
            "是否登录券商": False,
            "是否调用券商接口": False,
            "是否交易": False,
            "是否企业微信真实发送": False,
            "是否自动改规则": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = out_dir / f"中信样本学习闭环_{stamp}.json"
    output_md = out_dir / f"中信样本学习闭环_{stamp}.md"
    latest_md = out_dir / "中信样本学习闭环_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({
        "状态": "完成",
        "样本总数": len(records),
        "中信数据可用数": report["样本统计"]["中信数据可用数"],
        "经验候选数": len(exp),
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
