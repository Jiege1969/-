# -*- coding: utf-8 -*-
"""
名称：生成L6行业主题观察池.py
作用：读取L7可交易过滤池，生成L6行业主题观察池。
触发方式：python 生成L6行业主题观察池.py
依赖：L7可交易过滤池_最新.json；用户增强观察池_最新.json；L6行业主题观察池规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读L7和用户增强池；只读公开行业信息；只写03数据/133行业主题观察池与04日志/数据源；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易；不重启服务。
标识：stock-layered-pool-l6-industry-observation
"""

from __future__ import annotations

import argparse
import json
import math
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"必需文件不存在: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "None"):
            return default
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except (TypeError, ValueError):
        return default


def normalize_code(code: str) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        suffix = suffix.upper()
        if suffix == "SH":
            return f"sh{num}"
        if suffix == "SZ":
            return f"sz{num}"
        if suffix == "BJ":
            return f"bj{num}"
    if len(text) == 6 and text.isdigit():
        if text.startswith(("6", "9")):
            return f"sh{text}"
        if text.startswith(("4", "8")):
            return f"bj{text}"
        return f"sz{text}"
    return text


def display_code(code: str) -> str:
    norm = normalize_code(code)
    if norm.startswith("sh"):
        return f"{norm[2:]}.SH"
    if norm.startswith("sz"):
        return f"{norm[2:]}.SZ"
    if norm.startswith("bj"):
        return f"{norm[2:]}.BJ"
    return str(code or "").upper()


def strip_industry_level(raw: str) -> str:
    text = str(raw or "").strip()
    if not text or text == "待补充":
        return "待映射"
    text = re.sub(r"^[A-Z]\d+", "", text).strip()
    text = re.sub(r"[ⅠⅡⅢIVX]+$", "", text).strip()
    text = re.sub(r"\s+", "", text)
    return text or "待映射"


def percentile_scores(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    sorted_items = sorted(values.items(), key=lambda item: item[1])
    total = len(sorted_items)
    if total == 1:
        return {sorted_items[0][0]: 5.0}
    output: dict[str, float] = {}
    for rank, (key, _value) in enumerate(sorted_items):
        output[key] = round(rank / (total - 1) * 5, 4)
    return output


def load_user_enhance(path: Path) -> dict[str, dict[str, Any]]:
    data = load_json(path, required=False)
    result: dict[str, dict[str, Any]] = {}
    for item in data.get("股票池", []):
        code = normalize_code(item.get("代码") or item.get("展示代码") or "")
        if code:
            result[code] = item
    return result


def fetch_industry_one(code: str, name: str, retry_count: int) -> dict[str, Any]:
    try:
        import akshare as ak  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return {
            "代码": code,
            "展示代码": display_code(code),
            "名称": name,
            "行业原始": "",
            "行业": "待映射",
            "状态": "失败",
            "错误": f"akshare不可用:{exc}",
            "数据源": "AKShare stock_individual_info_em",
        }

    symbol = normalize_code(code)[2:]
    errors: list[str] = []
    for attempt in range(1, max(1, retry_count) + 1):
        try:
            df = ak.stock_individual_info_em(symbol=symbol)
            industry = ""
            for row in df.to_dict("records"):
                if str(row.get("item")) == "行业":
                    industry = str(row.get("value") or "").strip()
                    break
            normalized = strip_industry_level(industry)
            return {
                "代码": code,
                "展示代码": display_code(code),
                "名称": name,
                "行业原始": industry,
                "行业": normalized,
                "状态": "成功" if normalized != "待映射" else "待映射",
                "错误": "",
                "数据源": "AKShare stock_individual_info_em",
            }
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))
            if attempt < retry_count:
                time.sleep(0.3 * attempt)
    return {
        "代码": code,
        "展示代码": display_code(code),
        "名称": name,
        "行业原始": "",
        "行业": "待映射",
        "状态": "失败",
        "错误": "；".join(errors),
        "数据源": "AKShare stock_individual_info_em",
    }


def fetch_baostock_industry_bulk() -> tuple[dict[str, dict[str, Any]], str]:
    try:
        import baostock as bs  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return {}, f"baostock不可用:{exc}"

    result: dict[str, dict[str, Any]] = {}
    error = ""
    login = bs.login()
    try:
        if getattr(login, "error_code", "1") != "0":
            return {}, f"baostock登录失败:{getattr(login, 'error_msg', '')}"
        rs = bs.query_stock_industry()
        if getattr(rs, "error_code", "1") != "0":
            return {}, f"baostock行业查询失败:{getattr(rs, 'error_msg', '')}"
        fields = list(getattr(rs, "fields", []))
        while rs.next():
            row = dict(zip(fields, rs.get_row_data()))
            code = normalize_code(str(row.get("code", "")).replace(".", ""))
            raw_industry = row.get("industry", "")
            industry = strip_industry_level(raw_industry)
            if code and industry != "待映射":
                result[code] = {
                    "代码": code,
                    "展示代码": display_code(code),
                    "名称": row.get("code_name", ""),
                    "行业原始": raw_industry,
                    "行业": industry,
                    "状态": "成功",
                    "错误": "",
                    "数据源": "baostock query_stock_industry",
                    "更新日期": row.get("updateDate", ""),
                    "分类标准": row.get("industryClassification", ""),
                }
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
    finally:
        try:
            bs.logout()
        except Exception:  # noqa: BLE001
            pass
    return result, error


def build_industry_map(
    stocks: list[dict[str, Any]],
    user_map: dict[str, dict[str, Any]],
    cache_path: Path,
    workers: int,
    retry_count: int,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    cache = load_json(cache_path, required=False)
    cached_items = cache.get("行业映射", {}) if isinstance(cache.get("行业映射", {}), dict) else {}
    industry_map: dict[str, dict[str, Any]] = dict(cached_items)
    baostock_map, baostock_error = fetch_baostock_industry_bulk()
    fetch_targets: list[dict[str, Any]] = []

    for stock in stocks:
        code = normalize_code(stock.get("代码") or stock.get("展示代码") or "")
        if not code:
            continue
        enhanced = user_map.get(code, {})
        enhanced_industry = strip_industry_level(enhanced.get("行业", ""))
        if enhanced_industry != "待映射":
            industry_map[code] = {
                "代码": code,
                "展示代码": display_code(code),
                "名称": stock.get("名称", ""),
                "行业原始": enhanced.get("行业"),
                "行业": enhanced_industry,
                "状态": "成功",
                "错误": "",
                "数据源": "用户增强观察池",
            }
        elif code in baostock_map:
            item = dict(baostock_map[code])
            item["名称"] = stock.get("名称", "") or item.get("名称", "")
            industry_map[code] = item
        elif code in industry_map and industry_map.get(code, {}).get("行业") not in ("", "待映射") and industry_map.get(code, {}).get("状态") == "成功":
            continue
        elif code not in industry_map or industry_map.get(code, {}).get("行业") in ("", "待映射"):
            fetch_targets.append(stock)

    fetched: list[dict[str, Any]] = []
    if fetch_targets:
        with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
            future_map = {
                executor.submit(
                    fetch_industry_one,
                    normalize_code(stock.get("代码") or stock.get("展示代码") or ""),
                    stock.get("名称", ""),
                    retry_count,
                ): stock
                for stock in fetch_targets
            }
            for future in as_completed(future_map):
                item = future.result()
                fetched.append(item)
                industry_map[item["代码"]] = item

    write_json(cache_path, {
        "名称": "行业映射缓存",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "说明": "供L6行业主题观察池使用。优先用户增强池，其次baostock行业分类，再次公开个股资料接口。",
        "baostock获取数量": len(baostock_map),
        "baostock错误": baostock_error,
        "行业映射": industry_map,
    })
    fetched.extend([item for code, item in baostock_map.items() if code in {normalize_code(stock.get("代码") or stock.get("展示代码") or "") for stock in stocks}])
    return industry_map, fetched


def average(values: list[float]) -> float:
    values = [value for value in values if value is not None]
    return sum(values) / len(values) if values else 0.0


def build_l6(
    l7_data: dict[str, Any],
    user_map: dict[str, dict[str, Any]],
    industry_map: dict[str, dict[str, Any]],
    rule: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    stocks = list(l7_data.get("股票池", []))
    if args.limit and args.limit > 0:
        stocks = stocks[: args.limit]

    weights = rule.get("评分权重", {})
    target = int(rule.get("目标规模", {}).get("L6默认数量", 80))
    if args.limit and args.limit > 0:
        target = min(target, len(stocks))
    strong_ratio = float(rule.get("行业规则", {}).get("强势行业比例", 0.3))
    user_bonus = float(weights.get("用户增强加分", 0.2))

    for stock in stocks:
        code = normalize_code(stock.get("代码") or "")
        mapping = industry_map.get(code, {})
        stock["行业"] = mapping.get("行业") or "待映射"
        stock["行业原始"] = mapping.get("行业原始") or ""
        stock["行业映射状态"] = mapping.get("状态") or "待映射"
        stock["是否用户增强"] = code in user_map and bool(user_map.get(code, {}).get("是否启用", True))
        stock["用户增强标签"] = user_map.get(code, {}).get("标签", [])
        avg5 = safe_float(stock.get("近5日日均成交额"))
        avg20 = safe_float(stock.get("近20日日均成交额"))
        stock["资金放量率"] = round(avg5 / avg20 - 1, 4) if avg20 > 0 else 0.0

    industry_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for stock in stocks:
        industry_groups[str(stock.get("行业") or "待映射")].append(stock)

    market_20 = average([safe_float(stock.get("近20日涨跌幅")) for stock in stocks])
    industry_stats: dict[str, dict[str, Any]] = {}
    industry_strength_raw: dict[str, float] = {}
    for industry, members in industry_groups.items():
        pct1 = average([safe_float(item.get("涨跌幅")) for item in members])
        pct5 = average([safe_float(item.get("近5日涨跌幅")) for item in members])
        pct20 = average([safe_float(item.get("近20日涨跌幅")) for item in members])
        relative20 = pct20 - market_20
        strength = pct1 * 0.4 + pct5 * 0.4 + relative20 * 0.2
        industry_strength_raw[industry] = strength
        industry_stats[industry] = {
            "行业": industry,
            "成分数": len(members),
            "当日平均涨跌幅": round(pct1, 4),
            "近5日平均涨跌幅": round(pct5, 4),
            "近20日平均涨跌幅": round(pct20, 4),
            "近20日相对强弱": round(relative20, 4),
            "行业强度原始值": round(strength, 4),
        }

    industry_score_map = percentile_scores(industry_strength_raw)
    amount_scores = percentile_scores({stock["代码"]: safe_float(stock.get("近20日日均成交额")) for stock in stocks})
    volume_scores = percentile_scores({stock["代码"]: safe_float(stock.get("资金放量率")) for stock in stocks})
    tech_scores = percentile_scores({stock["代码"]: safe_float(stock.get("近5日涨跌幅")) + safe_float(stock.get("近20日涨跌幅")) * 0.5 for stock in stocks})

    for industry, score in industry_score_map.items():
        industry_stats[industry]["行业强度分"] = score

    sorted_industries = sorted(industry_stats.values(), key=lambda item: item.get("行业强度分", 0), reverse=True)
    strong_count = max(1, math.ceil(len(sorted_industries) * strong_ratio))
    strong_industries = {item["行业"] for item in sorted_industries[:strong_count]}

    candidates: list[dict[str, Any]] = []
    for stock in stocks:
        code = stock["代码"]
        industry = stock.get("行业") or "待映射"
        industry_score = industry_score_map.get(industry, 0.0)
        fund_score = volume_scores.get(code, 0.0) * 0.6 + amount_scores.get(code, 0.0) * 0.4
        tech_score = tech_scores.get(code, 0.0)
        raw_score = (
            industry_score * float(weights.get("行业强度", 0.4))
            + fund_score * float(weights.get("资金活跃度", 0.3))
            + tech_score * float(weights.get("技术面", 0.2))
        )
        adjusted_score = raw_score + (user_bonus if stock.get("是否用户增强") else 0.0)
        channel = "强势行业资金活跃" if industry in strong_industries else "总排序补位"
        abnormal = (
            safe_float(stock.get("资金放量率")) >= float(rule.get("资金活跃度指标", {}).get("异常强势放量率", 1.0))
            and safe_float(stock.get("近20日日均成交额")) >= float(rule.get("资金活跃度指标", {}).get("最低近20日日均成交额_亿元", 1.0)) * 100000000
        )
        if abnormal and industry not in strong_industries:
            channel = "异常强势个股"
        if stock.get("是否用户增强") and channel == "总排序补位":
            channel = "用户增强观察池"
        candidates.append({
            **stock,
            "行业强度分": round(industry_score, 4),
            "资金活跃度分": round(fund_score, 4),
            "技术面分": round(tech_score, 4),
            "原始分": round(raw_score, 4),
            "调整分": round(adjusted_score, 4),
            "用户增强加分": user_bonus if stock.get("是否用户增强") else 0.0,
            "入选通道": channel,
            "入选理由": [
                f"行业强度分{round(industry_score, 2)}",
                f"资金活跃度分{round(fund_score, 2)}",
                f"近5/20日成交额放量率{round(safe_float(stock.get('资金放量率')) * 100, 2)}%",
            ],
        })

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_from(rows: list[dict[str, Any]], count: int) -> None:
        for row in sorted(rows, key=lambda item: item.get("调整分", 0), reverse=True):
            if len(selected) >= target or count <= 0:
                break
            code = row.get("代码")
            if code in seen:
                continue
            selected.append(row)
            seen.add(code)
            count -= 1

    ratio = rule.get("组成配比", {})
    add_from([row for row in candidates if row.get("入选通道") == "强势行业资金活跃"], math.ceil(target * float(ratio.get("强势行业资金活跃", 0.7))))
    add_from([row for row in candidates if row.get("是否用户增强")], math.ceil(target * float(ratio.get("用户增强观察池", 0.2))))
    add_from([row for row in candidates if row.get("入选通道") == "异常强势个股"], math.ceil(target * float(ratio.get("异常强势个股", 0.1))))
    add_from(candidates, target - len(selected))

    selected = sorted(selected, key=lambda item: item.get("调整分", 0), reverse=True)[:target]
    now = datetime.now()
    return {
        "名称": "L6行业主题观察池",
        "版本": "2026-05-01",
        "定位": "L7可交易过滤池基础上的行业主题观察池，供L5深度研究池继续筛选。",
        "数据日期": l7_data.get("数据日期"),
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(module_root() / "01配置" / "L6行业主题观察池规则.json"),
        "上游文件": "03数据/132可交易过滤池/L7可交易过滤池_最新.json",
        "行业强度方法": rule.get("行业规则", {}).get("行业强度方法"),
        "数据健康度": {
            "L7输入股票数": len(stocks),
            "行业已映射数": sum(1 for item in stocks if item.get("行业") != "待映射"),
            "行业待映射数": sum(1 for item in stocks if item.get("行业") == "待映射"),
            "L6输出股票数": len(selected),
            "强势行业数量": len(strong_industries),
            "是否完整": len(selected) >= int(rule.get("目标规模", {}).get("最小数量", 50)),
        },
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写旧系统": False,
            "是否写正式库": False,
        },
        "实际动作": {
            "读取L7可交易过滤池": True,
            "读取用户增强观察池": True,
            "读取公开行业信息": True,
            "写入03数据": True,
            "写入04日志": True,
            "触发n8n": False,
            "企业微信真实发送": False,
            "调用券商接口": False,
            "自动交易": False,
            "重启服务": False,
        },
        "行业强度排行": sorted_industries,
        "强势行业": sorted(strong_industries),
        "股票池": selected,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成L6行业主题观察池")
    parser.add_argument("--limit", type=int, default=0, help="仅处理前N只股票，用于调试；0表示全量。")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = module_root()
    rule_path = root / "01配置" / "L6行业主题观察池规则.json"
    rule = load_json(rule_path, required=True)
    l7_path = root / "03数据" / "132可交易过滤池" / "L7可交易过滤池_最新.json"
    user_path = root / "03数据" / "131用户增强观察池" / "用户增强观察池_最新.json"
    l7_data = load_json(l7_path, required=True)
    user_map = load_user_enhance(user_path)

    source_rule = rule.get("数据源", {})
    workers = int(source_rule.get("行业获取并发线程数", 4))
    retry_count = int(source_rule.get("失败重试次数", 2))
    cache_path = root / rule.get("行业规则", {}).get("行业缓存文件", "03数据/133行业主题观察池/行业映射缓存_最新.json")
    stocks = list(l7_data.get("股票池", []))
    if args.limit and args.limit > 0:
        stocks = stocks[: args.limit]
    industry_map, fetched = build_industry_map(stocks, user_map, cache_path, workers, retry_count)
    limited_l7 = {**l7_data, "股票池": stocks}
    report = build_l6(limited_l7, user_map, industry_map, rule, args)
    report["行业映射本次获取"] = {
        "获取数量": len(fetched),
        "成功数量": sum(1 for item in fetched if item.get("状态") == "成功"),
        "失败数量": sum(1 for item in fetched if item.get("状态") == "失败"),
        "待映射数量": sum(1 for item in fetched if item.get("状态") == "待映射"),
        "失败样本": [item for item in fetched if item.get("状态") == "失败"][:20],
    }

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = root / "03数据" / "133行业主题观察池"
    output_path = output_dir / f"L6行业主题观察池_{stamp}.json"
    latest_path = output_dir / "L6行业主题观察池_最新.json"
    log_dir = root / "04日志" / "数据源"
    log_path = log_dir / f"L6行业主题观察池数据源日志_{stamp}.json"
    log_latest_path = log_dir / "L6行业主题观察池数据源日志_最新.json"

    write_json(output_path, report)
    write_json(latest_path, report)
    log = {
        "名称": "L6行业主题观察池数据源日志",
        "生成时间": report["生成时间"],
        "数据健康度": report["数据健康度"],
        "行业映射本次获取": report["行业映射本次获取"],
        "输出文件": str(output_path),
        "最新文件": str(latest_path),
        "安全边界": report["安全边界"],
        "实际动作": report["实际动作"],
    }
    write_json(log_path, log)
    write_json(log_latest_path, log)

    print(json.dumps({
        "状态": "完成",
        "L7输入股票数": report["数据健康度"]["L7输入股票数"],
        "L6输出股票数": report["数据健康度"]["L6输出股票数"],
        "行业待映射数": report["数据健康度"]["行业待映射数"],
        "是否完整": report["数据健康度"]["是否完整"],
        "输出": str(output_path),
        "最新": str(latest_path),
        "日志": str(log_path),
    }, ensure_ascii=False))
    return 0 if report["数据健康度"]["是否完整"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
