# -*- coding: utf-8 -*-
"""
名称：生成2000只样本股票池.py
作用：用中证全指成分股作为母池，按申万一级行业与中证权重分层抽样，生成2000只样本股票池和行业代表性验证报告。
审计说明：本脚本实现《2000只标准大股票池主动研究执行方案》中的“分层规模”部分，以及2000只标准样本地基。
触发方式：python 生成2000只样本股票池.py
安全边界：只通过 akshare 读取公开市场数据，只写股票研究系统本地样本池和只读索引；不触发 n8n；不发送企业微信；不接券商；不交易；不重载 19310/19302。
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import akshare as ak
import pandas as pd


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(r"D:\杰哥智能化系统")
STOCK_ROOT = ROOT / "02杰哥扩展系统" / "01股票研究系统"
POOL_DIR = STOCK_ROOT / "03数据" / "01股票池"
PACKAGE_DIR = STOCK_ROOT / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
INDEX_JSON = PACKAGE_DIR / "股票池只读总索引_最新.json"
INDEX_MD = PACKAGE_DIR / "股票池只读总索引_最新.md"
INDEX_CSV = PACKAGE_DIR / "股票池只读总索引_完整名单_最新.csv"

TARGET_SIZE = 2000
CSI_SYMBOL = "000985"
MIN_AMOUNT = 5_000_000


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return default
        return float(value)
    except Exception:
        return default


def market_from_exchange(exchange: str, code: str) -> str:
    text = str(exchange)
    if "深圳" in text:
        return "深交所"
    if "上海" in text:
        return "上交所"
    if code.startswith(("83", "87", "88", "92")):
        return "北交所"
    return text or "未知"


def display_code(code: str, market: str) -> str:
    if market == "上交所":
        return f"{code}.SH"
    if market == "深交所":
        return f"{code}.SZ"
    if market == "北交所":
        return f"{code}.BJ"
    return code


def normalized_spot_code(value: str) -> str:
    text = str(value)
    if text.startswith(("sh", "sz", "bj")):
        return text[2:]
    return text


def latest_total_market_cap() -> tuple[float, str]:
    data = ak.macro_china_stock_market_cap()
    for _, row in data.iterrows():
        sh = safe_float(row.get("市价总值-上海"))
        sz = safe_float(row.get("市价总值-深圳"))
        if sh > 0 and sz > 0:
            return (sh + sz) * 100_000_000, str(row.get("数据日期", ""))
    return 0.0, ""


def build_sw_first_mapping() -> tuple[dict[str, str], dict[str, int]]:
    first = ak.sw_index_first_info()
    mapping: dict[str, str] = {}
    industry_member_count: dict[str, int] = {}
    for _, row in first.iterrows():
        code = str(row.iloc[0]).split(".")[0]
        industry = str(row.iloc[1])
        try:
            members = ak.index_component_sw(symbol=code)
        except Exception:
            members = pd.DataFrame()
        industry_member_count[industry] = int(len(members))
        if members.empty:
            continue
        for stock_code in members.get("证券代码", []):
            mapping[str(stock_code).zfill(6)] = industry
    return mapping, industry_member_count


def load_market_data() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[str, Any]], dict[str, str], dict[str, int], float, str]:
    cons = ak.index_stock_cons_csindex(symbol=CSI_SYMBOL)
    weights = ak.index_stock_cons_weight_csindex(symbol=CSI_SYMBOL)
    spot = ak.stock_zh_a_spot()
    sw_map, sw_counts = build_sw_first_mapping()
    total_cap, cap_date = latest_total_market_cap()
    spot_map: dict[str, dict[str, Any]] = {}
    for _, row in spot.iterrows():
        code = normalized_spot_code(row.get("代码", ""))
        spot_map[code] = {
            "名称": row.get("名称", ""),
            "最新价": safe_float(row.get("最新价")),
            "成交额": safe_float(row.get("成交额")),
            "时间戳": row.get("时间戳", ""),
        }
    return cons, weights, spot_map, sw_map, sw_counts, total_cap, cap_date


def build_mother_pool() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cons, weights, spot_map, sw_map, sw_counts, total_cap, cap_date = load_market_data()
    weight_map = {str(row.get("成分券代码")).zfill(6): safe_float(row.get("权重")) for _, row in weights.iterrows()}
    rows: list[dict[str, Any]] = []
    counters = defaultdict(int)
    for _, row in cons.iterrows():
        code = str(row.get("成分券代码")).zfill(6)
        name = str(row.get("成分券名称") or "")
        market = market_from_exchange(str(row.get("交易所") or ""), code)
        industry = sw_map.get(code, "")
        spot = spot_map.get(code, {})
        latest_amount = safe_float(spot.get("成交额"))
        weight = weight_map.get(code, 0.0)
        counters["中证全指成分"] += 1
        if not industry:
            counters["申万未匹配"] += 1
            continue
        if any(flag in name for flag in ["ST", "*ST", "退"]):
            counters["ST或退市名称剔除"] += 1
            continue
        if latest_amount < MIN_AMOUNT:
            counters["最新成交额低于500万剔除"] += 1
            continue
        rows.append({
            "代码": f"{'sh' if market == '上交所' else 'sz' if market == '深交所' else 'bj'}{code}",
            "展示代码": display_code(code, market),
            "名称": name,
            "行业": industry,
            "市场": market,
            "市值": round(total_cap * weight / 100, 2) if total_cap else None,
            "中证全指权重": weight,
            "最新成交额": latest_amount,
            "纳入日期": datetime.now().strftime("%Y-%m-%d"),
            "数据来源": "中证全指成分股+中证权重+申万一级行业+新浪A股实时行情",
        })
    meta = {
        "中证全指成分日期": str(cons["日期"].iloc[0]) if "日期" in cons.columns and len(cons) else "",
        "中证权重日期": str(weights["日期"].iloc[0]) if "日期" in weights.columns and len(weights) else "",
        "估算总市值日期": cap_date,
        "估算总市值": total_cap,
        "过滤统计": dict(counters),
        "申万一级行业成分数量": sw_counts,
    }
    return rows, meta


def allocate_quota(rows: list[dict[str, Any]]) -> dict[str, int]:
    by_industry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_industry[row["行业"]].append(row)
    industry_weight = {industry: sum(item["中证全指权重"] for item in items) for industry, items in by_industry.items()}
    total_weight = sum(industry_weight.values())
    raw = {industry: TARGET_SIZE * weight / total_weight for industry, weight in industry_weight.items()}
    quota = {industry: min(len(by_industry[industry]), int(math.floor(value))) for industry, value in raw.items()}
    remaining = TARGET_SIZE - sum(quota.values())
    while remaining > 0:
        candidates = [
            (
                raw[industry] - quota[industry],
                industry_weight[industry],
                industry,
            )
            for industry in by_industry
            if quota[industry] < len(by_industry[industry])
        ]
        if not candidates:
            break
        _, _, industry = sorted(candidates, reverse=True)[0]
        quota[industry] += 1
        remaining -= 1
    return quota


def sample_pool(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    quota = allocate_quota(rows)
    selected: list[dict[str, Any]] = []
    by_industry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_industry[row["行业"]].append(row)
    for industry, items in by_industry.items():
        ranked = sorted(items, key=lambda item: (item["中证全指权重"], item["最新成交额"]), reverse=True)
        selected.extend(ranked[:quota.get(industry, 0)])
    selected = sorted(selected, key=lambda item: item["中证全指权重"], reverse=True)
    return selected, quota


def industry_distribution(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    total_count = len(rows)
    total_weight = sum(item["中证全指权重"] for item in rows)
    result: dict[str, dict[str, float]] = {}
    for row in rows:
        item = result.setdefault(row["行业"], {"数量": 0, "权重": 0.0})
        item["数量"] += 1
        item["权重"] += row["中证全指权重"]
    for item in result.values():
        item["数量占比"] = item["数量"] / total_count if total_count else 0
        item["权重占比"] = item["权重"] / total_weight if total_weight else 0
    return result


def representative_report(selected: list[dict[str, Any]], mother_rows: list[dict[str, Any]], meta: dict[str, Any]) -> tuple[dict[str, Any], str]:
    selected_dist = industry_distribution(selected)
    mother_dist = industry_distribution(mother_rows)
    rows = []
    abs_deviation_sum = 0.0
    for industry in sorted(mother_dist):
        target_weight = mother_dist[industry]["权重占比"]
        sample_weight = selected_dist.get(industry, {}).get("数量占比", 0.0)
        deviation = sample_weight - target_weight
        abs_deviation_sum += abs(deviation)
        available = int(mother_dist[industry]["数量"])
        selected_count = int(selected_dist.get(industry, {}).get("数量", 0))
        rows.append({
            "行业": industry,
            "样本数量": selected_count,
            "样本数量占比": round(sample_weight * 100, 2),
            "中证全指行业权重": round(target_weight * 100, 2),
            "偏离度": round(deviation * 100, 2),
            "可选母池数量": available,
            "行业覆盖率": round(selected_count / available * 100, 2) if available else 0,
        })
    representative_score = max(0.0, 100.0 - abs_deviation_sum * 100)
    largest_gaps = sorted(rows, key=lambda item: abs(item["偏离度"]), reverse=True)[:5]
    report = {
        "名称": "2000只样本池行业代表性验证",
        "生成时间": now_text(),
        "目标样本数": TARGET_SIZE,
        "实际样本数": len(selected),
        "覆盖行业数": len(selected_dist),
        "代表性总评分": round(representative_score, 2),
        "最大缺口行业": largest_gaps,
        "行业分布": rows,
        "数据口径": {
            "母池": "中证全指成分股 000985",
            "行业": "申万一级行业",
            "抽样": "按中证全指行业权重分配名额，各行业内按中证权重和最新成交额排序",
            "流动性过滤": "本轮使用最新交易日成交额>=500万作为流动性先验；20日均成交额批量补验待后续稳定数据接口补齐",
            "市值字段": "按最近可用沪深总市值与中证全指成分权重反推的估算市值，用于分层代表性，不作为财务精确市值",
            **meta,
        },
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否接券商": False,
            "是否交易": False,
            "是否重载19310或19302": False,
        },
    }
    lines = [
        f"# 2000只样本池行业代表性验证 - {report['生成时间']}",
        "",
        f"- 实际样本数：{report['实际样本数']}",
        f"- 覆盖行业数：{report['覆盖行业数']}",
        f"- 代表性总评分：{report['代表性总评分']}",
        f"- 母池：{report['数据口径']['母池']}",
        f"- 中证全指成分日期：{meta.get('中证全指成分日期')}",
        f"- 中证权重日期：{meta.get('中证权重日期')}",
        f"- 流动性过滤口径：{report['数据口径']['流动性过滤']}",
        "",
        "## 行业分布与偏离度",
        "",
        "| 行业 | 样本数量 | 样本占比 | 中证全指行业权重 | 偏离度 | 可选母池 | 覆盖率 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in rows:
        lines.append(
            f"| {item['行业']} | {item['样本数量']} | {item['样本数量占比']}% | {item['中证全指行业权重']}% | {item['偏离度']}% | {item['可选母池数量']} | {item['行业覆盖率']}% |"
        )
    lines.extend(["", "## 缺口最大的行业", ""])
    for item in largest_gaps:
        direction = "超配" if item["偏离度"] > 0 else "低配"
        lines.append(f"- {item['行业']}：{direction} {abs(item['偏离度'])}%（样本 {item['样本数量']} 只，中证权重 {item['中证全指行业权重']}%）。")
    lines.extend([
        "",
        "## 验证结论",
        "",
        f"- 2000只样本地基已生成，覆盖 {report['覆盖行业数']} 个申万一级行业。",
        "- 当前池子可作为 L8X 上游大样本底座，但不直接产生买卖建议。",
        "- 下一轮建议补齐 20日均成交额批量校验与精确个股总市值字段。",
        "",
        "## 安全边界",
        "",
        "- 未触发 n8n。",
        "- 未真实发送企业微信。",
        "- 未接券商、不交易。",
    ])
    return report, "\n".join(lines) + "\n"


def write_pool(selected: list[dict[str, Any]], report: dict[str, Any], markdown: str) -> dict[str, str]:
    POOL_DIR.mkdir(parents=True, exist_ok=True)
    latest_json = POOL_DIR / "2000只样本股票池_最新.json"
    latest_csv = POOL_DIR / "2000只样本股票池_最新.csv"
    report_md = POOL_DIR / "2000只样本池行业代表性验证_最新.md"
    stamp = stamp_text()
    archive_json = POOL_DIR / f"2000只样本股票池_{stamp}.json"
    archive_csv = POOL_DIR / f"2000只样本股票池_{stamp}.csv"
    archive_report_md = POOL_DIR / f"2000只样本池行业代表性验证_{stamp}.md"
    package = {
        "名称": "2000只样本股票池",
        "生成时间": now_text(),
        "数量": len(selected),
        "字段": ["代码", "展示代码", "名称", "行业", "市场", "市值", "中证全指权重", "最新成交额", "纳入日期"],
        "股票列表": selected,
        "行业代表性验证": report,
        "安全边界": report["安全边界"],
    }
    for path in [latest_json, archive_json]:
        path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    fieldnames = package["字段"]
    for path in [latest_csv, archive_csv]:
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(selected)
    for path in [report_md, archive_report_md]:
        path.write_text(markdown, encoding="utf-8")
    return {
        "json": str(latest_json),
        "csv": str(latest_csv),
        "report": str(report_md),
    }


def update_readonly_index(selected: list[dict[str, Any]], report: dict[str, Any]) -> None:
    index = json.loads(INDEX_JSON.read_text(encoding="utf-8-sig")) if INDEX_JSON.exists() else {}
    stock_pools = index.get("股票池索引", [])
    stock_pools = [item for item in stock_pools if item.get("池ID") != "sample_2000_pool"]
    top10 = sorted(
        [{"行业": item["行业"], "数量": int(item["样本数量"])} for item in report["行业分布"]],
        key=lambda item: item["数量"],
        reverse=True,
    )[:10]
    pool_entry = {
        "池ID": "sample_2000_pool",
        "名称": "2000只样本股票池",
        "角色": "中证全指母池+申万一级行业分层抽样形成的大样本地基",
        "源文件": str(POOL_DIR / "2000只样本股票池_最新.json"),
        "数量": len(selected),
        "阶段用途": ["L8X上游地基", "行业代表性验证", "后续指标扩面目标"],
        "字段": ["代码", "展示代码", "名称", "行业", "市场", "市值", "纳入日期"],
        "行业分布TOP10": top10,
        "完整股票名单": [
            {
                "代码": item["代码"],
                "展示代码": item["展示代码"],
                "名称": item["名称"],
                "市场": item["市场"],
                "行业": item["行业"],
                "细分领域": "",
                "名单分类": "2000只样本池",
                "来源": "中证全指+申万一级分层抽样",
                "入池理由": "按行业权重代表性与流动性先验纳入",
                "评分": "",
                "所属池": "2000只样本股票池",
                "阶段用途": "L8X上游地基；行业代表性验证；后续指标扩面目标",
            }
            for item in selected
        ],
    }
    stock_pools.append(pool_entry)
    index["生成时间"] = now_text()
    index["统计"] = index.get("统计", {})
    index["统计"]["2000只样本股票池数量"] = len(selected)
    index["统计"]["2000只样本股票池覆盖行业数"] = report["覆盖行业数"]
    index["统计"]["2000只样本股票池代表性总评分"] = report["代表性总评分"]
    index["股票池索引"] = stock_pools
    unique: dict[str, dict[str, Any]] = {}
    for pool in stock_pools:
        for item in pool.get("完整股票名单", []):
            unique.setdefault(item.get("代码") or item.get("展示代码"), item)
    index["统计"]["去重股票数"] = len(unique)
    index["跨池去重总表"] = list(unique.values())
    INDEX_JSON.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 股票池只读总索引",
        "",
        f"- 生成时间：{index['生成时间']}",
        "- 定位：只读派生索引，用于统一股票池入口和三阶段报告输入绑定；不修改任何正式规则。",
        "- 安全边界：未触发 n8n，未真实发送企业微信，未接券商，不交易，未重载 19310/19302。",
        f"- 去重股票数：{index['统计'].get('去重股票数')}",
        f"- 2000只样本股票池：{len(selected)}只，覆盖{report['覆盖行业数']}个申万一级行业，代表性总评分{report['代表性总评分']}。",
        "",
        "## 一、股票池总览",
        "",
        "| 股票池 | 数量 | 角色 | 三阶段用途 | 行业分布TOP5 |",
        "|---|---:|---|---|---|",
    ]
    for pool in stock_pools:
        top5 = "；".join(f"{item['行业']} {item['数量']}" for item in pool.get("行业分布TOP10", [])[:5])
        lines.append(
            f"| {pool.get('名称')} | {pool.get('数量')} | {pool.get('角色')} | {'；'.join(pool.get('阶段用途', []))} | {top5} |"
        )
    lines.extend([
        "",
        "## 二、三阶段输入绑定",
        "",
        "### 收盘短线观察",
        "- 主输入池：300只试运行池、300只盘后轻扫描候选",
        "- 上游地基：2000只样本股票池用于后续指标扩面和行业代表性校验，不直接扫全市场生成报告。",
        "",
        "### 深度三维研究",
        "- 主输入池：L6行业主题观察池、L5深度研究池",
        "- 上游地基：2000只样本股票池用于行业分布、主题覆盖和L8X扩展。",
        "",
        "### 盘前出击排序",
        "- 主输入池：前一晚深度三维研究、收盘短线观察候选",
        "- 上游地基：2000只样本池不直接生成买卖指令，只提供样本代表性底座。",
        "",
        "## 三、完整名单入口",
        "",
        "- 机器读取：`股票池只读总索引_最新.json`，包含每个池的完整股票名单和跨池去重总表。",
        "- 表格核验：`股票池只读总索引_完整名单_最新.csv`，每行是一只股票在某个池中的成员关系。",
        "- 2000只样本池：`D:\\杰哥智能化系统\\02杰哥扩展系统\\01股票研究系统\\03数据\\01股票池\\2000只样本股票池_最新.json`。",
        "",
        "## 四、验收判断",
        "",
        "- 已把2000只样本股票池注册进只读总索引。",
        "- 已补齐申万一级行业分布与代表性评分。",
        "- 流动性过滤本轮使用最新交易日成交额，20日均成交额批量补验列为下一轮升级项。",
    ])
    INDEX_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    rows = []
    for pool in stock_pools:
        for item in pool.get("完整股票名单", []):
            row = dict(item)
            row["所属池"] = pool.get("名称")
            rows.append(row)
    fieldnames = ["所属池", "代码", "展示代码", "名称", "市场", "行业", "细分领域", "名单分类", "来源", "入池理由", "评分", "阶段用途"]
    with INDEX_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    mother_rows, meta = build_mother_pool()
    selected, _quota = sample_pool(mother_rows)
    if len(selected) < TARGET_SIZE:
        raise RuntimeError(f"可选母池不足，目标{TARGET_SIZE}，实际{len(selected)}")
    selected = selected[:TARGET_SIZE]
    report, markdown = representative_report(selected, mother_rows, meta)
    outputs = write_pool(selected, report, markdown)
    update_readonly_index(selected, report)
    print(json.dumps({
        "状态": "完成",
        "样本数量": len(selected),
        "覆盖行业数": report["覆盖行业数"],
        "代表性总评分": report["代表性总评分"],
        "最大缺口行业": report["最大缺口行业"],
        "输出": outputs,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
