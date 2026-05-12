# -*- coding: utf-8 -*-
"""
名称：生成L8X综合候选池.py
作用：合并L8指数基底池、L8B扩展战略样本池和用户增强观察池标记，生成L7统一入口。
审计说明：本脚本实现《分层股票池L8-L5规则与施工方案_v1.0_20260501》中的“分层结构”和L8X综合候选入口部分。
触发方式：python 生成L8X综合候选池.py
依赖：03数据/130指数基底池/L8指数基底池_最新.json；03数据/130B扩展战略样本池/L8B扩展战略样本池_最新.json；03数据/131用户增强观察池/用户增强观察池_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读L8A/L8B/L8U；只写03数据/130X综合候选池与04日志/数据源；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-05-01 创建L8X综合候选池生成脚本。
标识：stock-l8x-comprehensive-candidate-pool-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SOURCE_PRIORITY = {"user_enhance": 3, "strategic": 2, "index_base": 1}


def module_root() -> Path:
    # 本脚本约定放在 股票研究系统/02脚本 下，因此 parents[1] 为股票研究系统根目录。
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


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if not text:
        return ""
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


def display_code(code: Any) -> str:
    norm = normalize_code(code)
    if norm.startswith("sh"):
        return f"{norm[2:]}.SH"
    if norm.startswith("sz"):
        return f"{norm[2:]}.SZ"
    if norm.startswith("bj"):
        return f"{norm[2:]}.BJ"
    return str(code or "").upper()


def choose_nonempty(current: Any, candidate: Any) -> Any:
    if candidate not in (None, "", [], {}, "待补充"):
        return candidate
    return current


def add_source(record: dict[str, Any], source: str) -> None:
    sources = record.setdefault("sources", [])
    if source not in sources:
        sources.append(source)
    sources.sort(key=lambda item: SOURCE_PRIORITY.get(item, 0), reverse=True)
    record["来源优先级"] = sources[0] if sources else ""
    record["是否指数基底"] = "index_base" in sources
    record["是否战略样本"] = "strategic" in sources
    record["是否用户增强"] = "user_enhance" in sources


def ensure_record(pool: dict[str, dict[str, Any]], item: dict[str, Any]) -> dict[str, Any]:
    code = normalize_code(item.get("代码") or item.get("展示代码"))
    if code not in pool:
        pool[code] = {
            "代码": code,
            "展示代码": display_code(code),
            "名称": item.get("名称") or "",
            "市场": item.get("市场") or "",
            "指数类型": item.get("指数类型") or "",
            "指数代码": item.get("指数代码") or "",
            "指数归属": item.get("指数归属", []),
            "行业": item.get("行业") or "",
            "细分领域": item.get("细分领域") or "",
            "名单分类": item.get("名单分类") or "",
            "标签": item.get("标签") if isinstance(item.get("标签"), list) else [],
            "sources": [],
            "是否指数基底": False,
            "是否战略样本": False,
            "是否用户增强": False,
            "来源优先级": "",
            "是否启用": item.get("是否启用", True) is not False,
        }
    return pool[code]


def merge_item(pool: dict[str, dict[str, Any]], item: dict[str, Any], source: str) -> None:
    code = normalize_code(item.get("代码") or item.get("展示代码"))
    if not code:
        return
    record = ensure_record(pool, item)
    add_source(record, source)

    # 信息优先级：用户增强 > 战略样本 > 指数基底。按调用顺序覆盖非空字段。
    for key in ("名称", "市场", "行业", "细分领域", "名单分类"):
        record[key] = choose_nonempty(record.get(key), item.get(key))

    if item.get("指数类型"):
        record["指数类型"] = choose_nonempty(record.get("指数类型"), item.get("指数类型"))
    if item.get("指数代码"):
        record["指数代码"] = choose_nonempty(record.get("指数代码"), item.get("指数代码"))
    if item.get("指数归属"):
        record["指数归属"] = item.get("指数归属")

    tags = record.setdefault("标签", [])
    if isinstance(item.get("标签"), list):
        for tag in item.get("标签", []):
            if tag and tag not in tags:
                tags.append(tag)

    if source == "user_enhance":
        record["用户增强权重加成"] = item.get("权重加成", 0.2)
        record["用户增强来源"] = item.get("来源") or ""
        record["关注级别"] = item.get("关注级别") or ""
    if source == "strategic":
        record["战略入池理由"] = item.get("入池理由") or ""
        record["战略证据来源"] = item.get("证据来源") or ""
        record["复核状态"] = item.get("复核状态") or "待月度复核"


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    today = now.strftime("%Y-%m-%d")

    l8a_path = root / "03数据" / "130指数基底池" / "L8指数基底池_最新.json"
    l8b_path = root / "03数据" / "130B扩展战略样本池" / "L8B扩展战略样本池_最新.json"
    l8u_path = root / "03数据" / "131用户增强观察池" / "用户增强观察池_最新.json"

    output_dir = root / "03数据" / "130X综合候选池"
    output_path = output_dir / f"L8X综合候选池_{stamp}.json"
    latest_path = output_dir / "L8X综合候选池_最新.json"
    log_dir = root / "04日志" / "数据源"
    log_path = log_dir / f"L8X综合候选池生成日志_{stamp}.json"
    log_latest_path = log_dir / "L8X综合候选池生成日志_最新.json"

    l8a_data = load_json(l8a_path, required=True)
    l8b_data = load_json(l8b_path, required=False)
    l8u_data = load_json(l8u_path, required=True)
    l8a_stocks = l8a_data.get("股票池", [])
    l8b_stocks = l8b_data.get("股票池", [])
    l8u_stocks = l8u_data.get("股票池", [])

    pool: dict[str, dict[str, Any]] = {}
    invalid_records: list[dict[str, Any]] = []

    for source, stocks in (
        ("index_base", l8a_stocks),
        ("strategic", l8b_stocks),
        ("user_enhance", l8u_stocks),
    ):
        for item in stocks:
            code = normalize_code(item.get("代码") or item.get("展示代码"))
            if not code:
                invalid_records.append({"来源": source, "名称": item.get("名称", ""), "原始记录": item})
                continue
            if item.get("是否启用") is False:
                continue
            merge_item(pool, item, source)

    output_stocks = sorted(pool.values(), key=lambda item: item.get("代码", ""))
    user_enhance_count = sum(1 for item in output_stocks if item.get("是否用户增强"))
    strategic_count = sum(1 for item in output_stocks if item.get("是否战略样本"))
    index_count = sum(1 for item in output_stocks if item.get("是否指数基底"))
    user_outside_index_count = sum(
        1 for item in output_stocks if item.get("是否用户增强") and not item.get("是否指数基底")
    )

    report = {
        "名称": "L8X综合候选池",
        "版本": "2026-05-01",
        "定位": "股票分层系统统一候选入口，合并指数基底、扩展战略样本和用户增强标记，再交由L7可交易过滤池处理。",
        "用户可见口径": "综合样本池",
        "数据日期": today,
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成L8X综合候选池.py",
        "股票数量": len(output_stocks),
        "数据源": {
            "L8A指数基底池": str(l8a_path),
            "L8B扩展战略样本池": str(l8b_path),
            "L8U用户增强观察池": str(l8u_path),
        },
        "合并规则": {
            "唯一键": "代码",
            "来源标记": ["index_base", "strategic", "user_enhance"],
            "来源优先级": "user_enhance > strategic > index_base，仅用于解释与字段补齐，不直接改变评分。",
            "L7入口": "后续L7优先读取本文件；本文件缺失时回退L8指数基底池。",
        },
        "字段规则": {
            "代码": "内部代码，sh/sz/bj + 六位数字",
            "展示代码": "外部展示代码，如600519.SH",
            "sources": "股票来源列表，用于追溯和复盘。",
        },
        "数据健康度": {
            "L8A输入股票数": len(l8a_stocks),
            "L8B输入股票数": len(l8b_stocks),
            "L8U输入股票数": len(l8u_stocks),
            "输出股票数": len(output_stocks),
            "指数基底标记股票数": index_count,
            "战略样本标记股票数": strategic_count,
            "用户增强标记股票数": user_enhance_count,
            "用户增强且不在指数基底数量": user_outside_index_count,
            "无效记录数": len(invalid_records),
            "是否完整": len(l8a_stocks) > 0 and len(l8u_stocks) > 0 and len(output_stocks) >= len(l8a_stocks),
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
            "读取L8指数基底池": True,
            "读取L8B扩展战略样本池": bool(l8b_data),
            "读取用户增强观察池": True,
            "写入03数据": True,
            "写入04日志": True,
            "修改源文件": False,
            "触发n8n": False,
            "企业微信真实发送": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "输出文件": {
            "时间戳文件": str(output_path),
            "最新文件": str(latest_path),
        },
        "股票池": output_stocks,
        "异常记录": {
            "无效记录": invalid_records,
        },
    }

    write_json(output_path, report)
    write_json(latest_path, report)
    write_json(log_path, {
        "名称": "L8X综合候选池生成日志",
        "生成时间": report["生成时间"],
        "数据源": report["数据源"],
        "数据健康度": report["数据健康度"],
        "输出文件": str(output_path),
        "最新文件": str(latest_path),
        "安全边界": report["安全边界"],
        "实际动作": report["实际动作"],
    })
    write_json(log_latest_path, load_json(log_path, required=True))

    print(json.dumps({
        "状态": "完成",
        "L8X股票数": len(output_stocks),
        "用户增强且不在指数基底数量": user_outside_index_count,
        "是否完整": report["数据健康度"]["是否完整"],
        "输出": str(output_path),
        "最新": str(latest_path),
        "日志": str(log_path),
    }, ensure_ascii=False))
    return 0 if report["数据健康度"]["是否完整"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
