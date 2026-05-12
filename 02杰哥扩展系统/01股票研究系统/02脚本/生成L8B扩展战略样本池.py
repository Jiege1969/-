# -*- coding: utf-8 -*-
"""
名称：生成L8B扩展战略样本池.py
作用：从用户增强观察池中筛出未纳入L8指数基底池的重点股票，生成L8B扩展战略样本池。
触发方式：python 生成L8B扩展战略样本池.py
依赖：03数据/130指数基底池/L8指数基底池_最新.json；03数据/131用户增强观察池/用户增强观察池_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读L8指数基底池和用户增强观察池；只写03数据/130B扩展战略样本池与04日志/数据源；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-05-01 创建L8B扩展战略样本池生成脚本。
标识：stock-l8b-strategic-extension-pool-generate
"""

from __future__ import annotations

import json
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


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    today = now.strftime("%Y-%m-%d")

    l8a_path = root / "03数据" / "130指数基底池" / "L8指数基底池_最新.json"
    l8u_path = root / "03数据" / "131用户增强观察池" / "用户增强观察池_最新.json"

    output_dir = root / "03数据" / "130B扩展战略样本池"
    output_path = output_dir / f"L8B扩展战略样本池_{stamp}.json"
    latest_path = output_dir / "L8B扩展战略样本池_最新.json"
    log_dir = root / "04日志" / "数据源"
    log_path = log_dir / f"L8B扩展战略样本池生成日志_{stamp}.json"
    log_latest_path = log_dir / "L8B扩展战略样本池生成日志_最新.json"

    l8a_data = load_json(l8a_path, required=True)
    l8u_data = load_json(l8u_path, required=True)
    l8a_stocks = l8a_data.get("股票池", [])
    l8u_stocks = l8u_data.get("股票池", [])

    l8a_codes = {
        normalize_code(item.get("代码") or item.get("展示代码"))
        for item in l8a_stocks
        if normalize_code(item.get("代码") or item.get("展示代码"))
    }

    output_stocks: list[dict[str, Any]] = []
    invalid_user_codes: list[dict[str, Any]] = []
    disabled_user_codes: list[str] = []

    for item in l8u_stocks:
        code = normalize_code(item.get("代码") or item.get("展示代码"))
        if not code:
            invalid_user_codes.append({"名称": item.get("名称", ""), "原始记录": item})
            continue
        if item.get("是否启用") is False:
            disabled_user_codes.append(code)
            continue
        if code in l8a_codes:
            continue

        source = item.get("来源") or "用户增强观察池"
        sub_field = item.get("细分领域") or "待补充"
        category = item.get("名单分类") or "用户增强"
        reason_parts = ["用户增强观察池重点关注", "未纳入L8指数基底池"]
        if category and category not in {"历史重点关注", "其他"}:
            reason_parts.append(str(category))
        if sub_field and sub_field != "待补充":
            reason_parts.append(str(sub_field))

        output_stocks.append({
            "代码": code,
            "展示代码": display_code(code),
            "名称": item.get("名称") or "",
            "市场": item.get("市场") or "",
            "行业": item.get("行业") or "待补充",
            "细分领域": sub_field,
            "名单分类": category,
            "标签": item.get("标签") if isinstance(item.get("标签"), list) else [],
            "指数类型": "扩展战略样本",
            "指数代码": "",
            "入池日期": item.get("加入日期") or today,
            "入池理由": "；".join(reason_parts),
            "证据来源": source,
            "复核状态": "待月度复核",
            "是否启用": True,
            "来源用户增强权重加成": item.get("权重加成", 0.2),
        })

    report = {
        "名称": "L8B扩展战略样本池",
        "版本": "2026-05-01",
        "定位": "由用户增强观察池中未纳入L8指数基底池的重点股票派生，负责让指数外重点股进入主流程候选入口。",
        "数据日期": today,
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成L8B扩展战略样本池.py",
        "生成方式": "由用户增强观察池中不在L8指数基底池的股票派生；每次运行基于当前L8A和L8U重新生成。",
        "股票数量": len(output_stocks),
        "数据源": {
            "L8A指数基底池": str(l8a_path),
            "L8U用户增强观察池": str(l8u_path),
        },
        "字段规则": {
            "代码": "内部代码，sh/sz/bj + 六位数字",
            "展示代码": "外部展示代码，如600519.SH",
            "复核状态": "初期统一为待月度复核，不自动出池。",
        },
        "数据健康度": {
            "L8A股票数": len(l8a_stocks),
            "L8U股票数": len(l8u_stocks),
            "输出股票数": len(output_stocks),
            "用户增强中已在L8A数量": len(l8u_stocks) - len(output_stocks) - len(invalid_user_codes) - len(disabled_user_codes),
            "用户增强无效代码数": len(invalid_user_codes),
            "用户增强停用数量": len(disabled_user_codes),
            "是否完整": len(l8a_stocks) > 0 and len(l8u_stocks) > 0 and len(invalid_user_codes) == 0,
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
            "用户增强无效代码": invalid_user_codes,
            "用户增强停用代码": disabled_user_codes,
        },
    }

    write_json(output_path, report)
    write_json(latest_path, report)
    write_json(log_path, {
        "名称": "L8B扩展战略样本池生成日志",
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
        "L8B股票数": len(output_stocks),
        "是否完整": report["数据健康度"]["是否完整"],
        "输出": str(output_path),
        "最新": str(latest_path),
        "日志": str(log_path),
    }, ensure_ascii=False))
    return 0 if report["数据健康度"]["是否完整"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
