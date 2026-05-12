# -*- coding: utf-8 -*-
"""
名称：生成用户增强观察池.py
作用：读取重点关注股票池和19名单股票池，生成标准化用户增强观察池。
触发方式：python 生成用户增强观察池.py
依赖：01配置/重点关注股票池.json；01配置/19名单股票池.json
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读配置文件；只写03数据目录；不触发n8n；不发送企业微信；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-05-01 创建用户增强观察池生成脚本。
标识：stock-user-enhance-pool-generate
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


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


def merge_text_values(*values: Any) -> str:
    """合并多个来源文本并去重；来源字段可能已经是中英文分号拼接文本。"""
    seen: list[str] = []
    for value in values:
        if not value:
            continue
        for part in re.split(r"[；;]+", str(value)):
            item = part.strip()
            if item and item not in seen:
                seen.append(item)
    return "；".join(seen)


def build_tags(industry: str, sub_field: str, category: str, existing: Any = None) -> list[str]:
    tags: list[str] = []

    def add(value: str) -> None:
        value = value.strip()
        if not value or value in {"待补充", "历史重点关注"}:
            return
        if value not in tags:
            tags.append(value)

    if isinstance(existing, list):
        for item in existing:
            add(str(item))

    for item in (category, industry):
        add(str(item or ""))

    for part in re.split(r"[、,/+()（）\s]+", str(sub_field or "")):
        add(part)

    return tags


def pending_reason(code: str, supplement_map: dict[str, dict[str, Any]]) -> str:
    if code not in supplement_map:
        return "不在19名单补充源中，且重点关注池未提供完整行业/细分领域"
    return "在19名单补充源中，但行业/细分领域仍缺失"


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    today = now.strftime("%Y-%m-%d")

    focus_path = root / "01配置" / "重点关注股票池.json"
    supplement_path = root / "01配置" / "19名单股票池.json"

    output_dir = root / "03数据" / "131用户增强观察池"
    output_path = output_dir / f"用户增强观察池_{stamp}.json"
    latest_path = output_dir / "用户增强观察池_最新.json"

    focus_data = load_json(focus_path, required=True)
    supplement_data = load_json(supplement_path, required=True)

    focus_stocks = focus_data.get("股票池", [])
    supplement_stocks = supplement_data.get("股票池", [])
    expected_count = int(focus_data.get("股票数量") or len(focus_stocks))

    supplement_map: dict[str, dict[str, Any]] = {}
    supplement_duplicates: list[str] = []
    invalid_supplement_code_count = 0

    for item in supplement_stocks:
        code = normalize_code(item.get("代码") or item.get("原始代码"))
        if not code:
            invalid_supplement_code_count += 1
            continue
        if code in supplement_map:
            supplement_duplicates.append(code)
        supplement_map[code] = item

    output_stocks: list[dict[str, Any]] = []
    seen_codes: set[str] = set()
    duplicate_focus_codes: list[str] = []
    invalid_focus_code_count = 0
    pending_fill: list[dict[str, Any]] = []

    for item in focus_stocks:
        code = normalize_code(item.get("代码") or item.get("原始代码"))
        if not code:
            invalid_focus_code_count += 1
            continue

        if code in seen_codes:
            duplicate_focus_codes.append(code)
            continue
        seen_codes.add(code)

        sup = supplement_map.get(code, {})

        industry = item.get("行业") or sup.get("行业") or "待补充"
        sub_field = item.get("细分领域") or sup.get("细分领域") or "待补充"
        category = item.get("名单分类") or sup.get("名单分类") or "历史重点关注"
        source = merge_text_values(item.get("来源"), sup.get("来源")) or "重点关注股票池"
        focus_level = item.get("关注级别") or sup.get("关注级别") or ""
        joined_date = item.get("加入日期") or sup.get("加入日期") or today

        stock = {
            "代码": code,
            "展示代码": display_code(code),
            "名称": item.get("名称") or sup.get("名称") or "",
            "市场": item.get("市场") or sup.get("市场") or "",
            "行业": industry,
            "细分领域": sub_field,
            "名单分类": category,
            "标签": build_tags(industry, sub_field, category, item.get("标签") or sup.get("标签")),
            "来源": source,
            "关注级别": focus_level,
            "是否启用": True,
            "权重加成": 0.2,
            "加入日期": joined_date,
        }
        output_stocks.append(stock)

        if industry == "待补充" or sub_field == "待补充":
            missing = [
                name
                for name, value in {"行业": industry, "细分领域": sub_field}.items()
                if value == "待补充"
            ]
            pending_fill.append(
                {
                    "代码": code,
                    "展示代码": stock["展示代码"],
                    "名称": stock["名称"],
                    "缺失字段": missing,
                    "原因": pending_reason(code, supplement_map),
                }
            )

    is_complete = (
        len(output_stocks) == expected_count
        and invalid_focus_code_count == 0
        and len(duplicate_focus_codes) == 0
        and len(output_stocks) > 0
    )

    report = {
        "名称": "用户增强观察池",
        "版本": "2026-05-01",
        "定位": "人工维护的重点观察池，不参与指数基底，仅用于L6/L5排序加权和报告标记。",
        "数据日期": today,
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成用户增强观察池.py",
        "股票数量": len(output_stocks),
        "数据源": {
            "主源": str(focus_path),
            "补充源": str(supplement_path),
            "主源说明": "重点关注股票池为用户增强观察池全集。",
            "补充源说明": "19名单股票池用于补齐行业、细分领域、名单分类等标签。",
        },
        "字段规则": {
            "代码": "内部代码，sh/sz/bj + 六位数字",
            "展示代码": "外部展示代码，如600519.SH",
            "权重加成": "默认+0.2，仅用于排序，不覆盖原始评分",
        },
        "数据健康度": {
            "预期股票数": expected_count,
            "主源股票数": len(focus_stocks),
            "补充源股票数": len(supplement_stocks),
            "输出股票数": len(output_stocks),
            "待补充股票数": len(pending_fill),
            "主源无效代码数": invalid_focus_code_count,
            "补充源无效代码数": invalid_supplement_code_count,
            "主源重复代码数": len(duplicate_focus_codes),
            "补充源重复代码数": len(supplement_duplicates),
            "是否完整": is_complete,
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
            "读取重点关注股票池": True,
            "读取19名单股票池": True,
            "写入03数据": True,
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
        "待补充字段股票": pending_fill,
        "重复代码记录": {
            "主源重复代码": duplicate_focus_codes,
            "补充源重复代码": supplement_duplicates,
        },
    }

    write_json(output_path, report)
    write_json(latest_path, report)

    print(
        json.dumps(
            {
                "状态": "完成",
                "输出股票数": len(output_stocks),
                "待补充股票数": len(pending_fill),
                "是否完整": is_complete,
                "输出": str(output_path),
                "最新": str(latest_path),
            },
            ensure_ascii=False,
        )
    )
    return 0 if is_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
