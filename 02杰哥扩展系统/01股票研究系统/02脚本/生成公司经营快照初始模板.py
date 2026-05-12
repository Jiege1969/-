# -*- coding: utf-8 -*-
"""
名称：生成公司经营快照初始模板.py
作用：为标准报告 v2 建立公司经营快照JSON骨架，先覆盖当前L5与用户增强池，字段缺失处明确标记待接入/人工核验。
触发方式：python 生成公司经营快照初始模板.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读03数据；只写03数据/166公司经营快照；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-company-snapshot-template-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    code = item.get("代码") or item.get("原始代码") or ""
    name = item.get("名称") or ""
    return {
        "代码": code,
        "展示代码": item.get("展示代码") or "",
        "名称": name,
        "申万一级行业": item.get("行业") or "待补充",
        "细分行业": item.get("细分领域") or "待补充",
        "用户标记": {
            "是否用户关注": bool(item.get("是否用户增强") or item.get("是否启用")),
            "是否战略样本": bool(item.get("是否战略样本")),
            "是否指数基底": bool(item.get("是否指数基底")),
        },
        "公司概况": {
            "核心业务": "待接入",
            "行业地位": "待接入",
            "主营产品": "待接入",
            "主要客户或下游": "待接入",
            "未来方向": "待接入",
        },
        "财报快照": {
            "最新报告期": "待接入",
            "营业收入_亿元": None,
            "营业收入同比": None,
            "归母或扣非净利润_亿元": None,
            "利润同比": None,
            "毛利率": None,
            "净利率": None,
            "ROE": None,
            "经营现金流净额_亿元": None,
            "现金流质量说明": "待接入",
        },
        "证据状态": {
            "公司概况": "待接入",
            "财报指标": "待接入",
            "行业地位": "人工核验",
            "未来方向": "人工核验",
        },
        "数据来源": [],
        "人工备注": "",
    }


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    data_dir = root / "03数据"

    l5 = load_json(data_dir / "134深度研究池" / "L5深度研究池_最新.json")
    user_pool = load_json(data_dir / "131用户增强观察池" / "用户增强观察池_最新.json")

    merged: dict[str, dict[str, Any]] = {}
    source_map: dict[str, list[str]] = {}

    for item in user_pool.get("股票池", []):
        code = item.get("代码")
        if not code:
            continue
        merged[code] = normalize_item(item)
        source_map.setdefault(code, []).append("用户增强观察池")

    for item in l5.get("股票池", []):
        code = item.get("代码")
        if not code:
            continue
        base = merged.get(code, normalize_item(item))
        # L5数据优先补充当前分层标记和行业口径。
        base["申万一级行业"] = item.get("行业") or base.get("申万一级行业")
        base["细分行业"] = item.get("细分领域") or base.get("细分行业")
        base["用户标记"] = {
            "是否用户关注": bool(item.get("是否用户增强")),
            "是否战略样本": bool(item.get("是否战略样本")),
            "是否指数基底": bool(item.get("是否指数基底")),
        }
        merged[code] = base
        source_map.setdefault(code, []).append("当前L5深度研究池")

    for code, sources in source_map.items():
        if code in merged:
            merged[code]["数据来源"] = sorted(set(sources))

    stocks = sorted(merged.values(), key=lambda x: (x.get("申万一级行业", ""), x.get("代码", "")))
    report = {
        "名称": "公司经营快照初始模板",
        "版本": "2026-05-02",
        "定位": "股票标准报告v2的P0数据源骨架。先不编造财报，缺失字段明确标记待接入/人工核验。",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成公司经营快照初始模板.py",
        "覆盖范围": {
            "用户增强池股票数": len(user_pool.get("股票池", [])),
            "当前L5股票数": len(l5.get("股票池", [])),
            "输出股票数": len(stocks),
        },
        "字段状态说明": {
            "待接入": "系统尚无自动数据源。",
            "人工核验": "需要人工或可信材料确认后填写。",
            "已接入": "系统可自动生成且可追溯。",
        },
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写旧系统": False,
            "是否写正式库": False,
        },
        "股票快照": stocks,
    }

    output_dir = data_dir / "166公司经营快照"
    latest = output_dir / "公司经营快照_最新.json"
    stamped = output_dir / f"公司经营快照_{stamp}.json"
    write_json(latest, report)
    write_json(stamped, report)

    print(json.dumps({
        "状态": "完成",
        "输出股票数": len(stocks),
        "最新": str(latest),
        "时间戳": str(stamped),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
