# -*- coding: utf-8 -*-
"""
名称：更新指数样本学习账_从L8数据.py
作用：从L8指数基底池和L8X综合候选池生成指数样本学习账。
触发方式：python 更新指数样本学习账_从L8数据.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地L8/L8X JSON；只写03数据/169指数样本学习账；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不自动修改规则。
标识：stock-index-sample-learning-refresh
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
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
            return suffix + num
    if text.isdigit():
        if text.startswith(("6", "9")):
            return "sh" + text.zfill(6)
        if text.startswith(("4", "8")):
            return "bj" + text.zfill(6)
        return "sz" + text.zfill(6)
    return text


def by_code(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        code = normalize_code(item.get("代码") or item.get("原始代码"))
        if code:
            result[code] = item
    return result


def stock_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ["股票池", "成分股", "候选池", "stocks"]:
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def index_membership(item: dict[str, Any]) -> list[str]:
    names: list[str] = []
    if item.get("指数类型"):
        names.append(str(item.get("指数类型")))
    for belong in item.get("指数归属") or []:
        if isinstance(belong, dict) and belong.get("指数类型"):
            names.append(str(belong.get("指数类型")))
    return sorted(set(names))


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 指数样本学习账 - {report['生成时间']}",
        "",
        "## 样本概况",
        "",
        f"- 指数基底股票数：{report['样本统计']['指数基底股票数']}",
        f"- 综合候选池股票数：{report['样本统计']['综合候选池股票数']}",
        f"- 指数外重点/战略样本数：{report['样本统计']['指数外重点样本数']}",
        "",
        "## 指数类型分布",
        "",
    ]
    for key, value in report["指数类型分布"].items():
        lines.append(f"- {key}：{value}")
    lines.extend([
        "",
        "## 行业分布TOP20",
        "",
    ])
    for key, value in list(report["行业分布"].items())[:20]:
        lines.append(f"- {key}：{value}")
    lines.extend([
        "",
        "## 学习提示",
        "",
        "- 指数基底用于学习市场核心资产的稳定特征。",
        "- 指数外重点样本用于观察新锐、龙头和用户重点关注标的是否有进入核心指数的潜力。",
        "- 本账本只提供样本学习资料，不自动改变L8/L7/L6/L5规则。",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    data_dir = root / "03数据"
    l8_path = data_dir / "130指数基底池" / "L8指数基底池_最新.json"
    l8x_path = data_dir / "130X综合候选池" / "L8X综合候选池_最新.json"
    old_path = data_dir / "169指数样本学习账" / "指数样本学习账_最新.json"

    l8_data = load_json(l8_path, {})
    l8x_data = load_json(l8x_path, {})
    old_data = load_json(old_path, {})
    l8_items = stock_items(l8_data)
    l8x_items = stock_items(l8x_data)
    l8_by_code = by_code(l8_items)
    l8x_by_code = by_code(l8x_items)

    index_type_counter: Counter[str] = Counter()
    industry_counter: Counter[str] = Counter()
    members: list[dict[str, Any]] = []
    for code, item in sorted(l8_by_code.items()):
        memberships = index_membership(item) or ["指数基底"]
        for idx in memberships:
            index_type_counter[idx] += 1
        industry = item.get("行业") or item.get("申万一级行业") or "待补充"
        industry_counter[str(industry)] += 1
        members.append({
            "代码": code,
            "展示代码": item.get("展示代码") or item.get("原始代码") or code,
            "名称": item.get("名称", ""),
            "指数归属": memberships,
            "行业": industry,
            "数据日期": item.get("数据日期") or l8_data.get("数据日期"),
        })

    outside_focus: list[dict[str, Any]] = []
    for code, item in sorted(l8x_by_code.items()):
        sources = item.get("sources") or []
        if code not in l8_by_code and ("user_enhance" in sources or "strategic" in sources or item.get("是否用户增强") or item.get("是否战略样本")):
            outside_focus.append({
                "代码": code,
                "展示代码": item.get("展示代码") or code,
                "名称": item.get("名称", ""),
                "行业": item.get("行业") or "待补充",
                "细分领域": item.get("细分领域") or "待补充",
                "sources": sources,
                "学习用途": "观察指数外重点样本是否具备后续进入核心指数或持续跟踪价值",
            })

    previous_events = old_data.get("指数调仓事件", []) if isinstance(old_data, dict) else []
    report = {
        "名称": "指数样本学习账",
        "版本": "v1.0",
        "定位": "学习沪深300、中证500等指数成分股与指数外重点样本的结构特征，为L8B扩展和规则复盘提供资料，不自动改规则。",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "更新指数样本学习账_从L8数据.py",
        "数据来源": {
            "L8指数基底池": str(l8_path),
            "L8X综合候选池": str(l8x_path),
        },
        "样本统计": {
            "指数基底股票数": len(l8_by_code),
            "综合候选池股票数": len(l8x_by_code),
            "指数外重点样本数": len(outside_focus),
        },
        "指数类型分布": dict(index_type_counter.most_common()),
        "行业分布": dict(industry_counter.most_common()),
        "指数成分股历史": members,
        "指数外重点样本": outside_focus,
        "指数调仓事件": previous_events,
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否自动修改规则": False,
        },
    }

    latest_path = data_dir / "169指数样本学习账" / "指数样本学习账_最新.json"
    stamp_path = data_dir / "169指数样本学习账" / f"指数样本学习账_{stamp}.json"
    latest_md = data_dir / "169指数样本学习账" / "指数样本学习账_最新.md"
    stamp_md = data_dir / "169指数样本学习账" / f"指数样本学习账_{stamp}.md"
    write_json(latest_path, report)
    write_json(stamp_path, report)
    markdown = build_markdown(report)
    write_text(latest_md, markdown)
    write_text(stamp_md, markdown)

    print(json.dumps({
        "状态": "完成",
        "指数基底股票数": len(l8_by_code),
        "综合候选池股票数": len(l8x_by_code),
        "指数外重点样本数": len(outside_focus),
        "输出": str(latest_path),
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
