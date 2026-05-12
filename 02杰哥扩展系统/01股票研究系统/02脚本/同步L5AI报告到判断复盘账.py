# -*- coding: utf-8 -*-
"""
名称：同步L5AI报告到判断复盘账.py
作用：将L5批量AI分析报告中的股票判断同步到轻量学习闭环的判断复盘账。
审计说明：本脚本实现《股票分析报告v2与轻量学习闭环施工方案》中的“判断主因规则”“样本池优化”“成长股向核心指数迁移观察”复盘记录入口。
触发方式：python 同步L5AI报告到判断复盘账.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读L5/AI报告本地JSON；只写04日志/复盘判断复盘账；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不自动修改规则。
标识：stock-sync-l5-ai-report-to-replay-ledger
"""

from __future__ import annotations

import json
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
    except ValueError as exc:
        raise ValueError(f"JSON文件损坏，停止同步：{path}") from exc


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


def collect_dicts(value: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(value, dict):
        rows.append(value)
        for child in value.values():
            rows.extend(collect_dicts(child))
    elif isinstance(value, list):
        for child in value:
            rows.extend(collect_dicts(child))
    return rows


def stock_rows(value: Any) -> list[dict[str, Any]]:
    rows = []
    for item in collect_dicts(value):
        if item.get("代码") and item.get("名称"):
            rows.append(item)
    return rows


def l5_map(l5_data: Any) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for item in stock_rows(l5_data):
        code = normalize_code(item.get("代码"))
        if code and code not in mapping:
            mapping[code] = item
    return mapping


def ai_analysis_rows(ai_data: Any) -> list[dict[str, Any]]:
    rows = []
    for item in stock_rows(ai_data):
        if "analysis_text" in item or "model_used" in item or "调整分" in item:
            rows.append(item)
    return rows


def main_reason(item: dict[str, Any], l5_item: dict[str, Any]) -> tuple[str, list[str]]:
    text = "；".join(str(value) for value in [
        item.get("入选原因"),
        item.get("analysis_text"),
        l5_item.get("入选理由"),
        l5_item.get("主因"),
        l5_item.get("行业"),
    ] if value)
    if "风险" in text:
        return "风险复核", ["技术/资金信号"]
    if "行业" in text or item.get("行业") or l5_item.get("行业"):
        return "行业景气", ["技术/资金信号"]
    return "技术/资金信号", []


def periods(reason: str) -> list[str]:
    if reason == "行业景气":
        return ["T20", "T60"]
    if reason == "风险复核":
        return ["T5", "T20"]
    return ["T5", "T20"]


def append_records(ledger_path: Path, records: list[dict[str, Any]]) -> tuple[int, int]:
    ledger = load_json(ledger_path, [])
    if not isinstance(ledger, list):
        ledger = []
    existing = {
        (
            item.get("股票代码"),
            item.get("报告日期"),
            item.get("报告类型"),
        )
        for item in ledger
    }
    added = 0
    skipped = 0
    for record in records:
        key = (record.get("股票代码"), record.get("报告日期"), record.get("报告类型"))
        if key in existing:
            skipped += 1
            continue
        ledger.append(record)
        existing.add(key)
        added += 1
    write_json(ledger_path, ledger)
    return added, skipped


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# L5 AI报告同步判断复盘账 - {result['生成时间']}",
        "",
        f"- AI报告：`{result['AI报告']}`",
        f"- L5池：`{result['L5深度研究池']}`",
        f"- 判断复盘账：`{result['判断复盘账']}`",
        f"- 新增记录：{result['新增记录数']}",
        f"- 跳过重复：{result['跳过重复数']}",
        "",
        "## 同步股票",
        "",
    ]
    for item in result["同步记录预览"]:
        lines.append(f"- {item.get('股票名称')}({item.get('股票代码')})：{item.get('判断主因')}，{item.get('关注等级')}")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 不触发 n8n。",
        "- 不发送企业微信。",
        "- 不调用券商接口。",
        "- 不自动交易。",
        "- 不自动修改规则。",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    now = datetime.now()
    ai_path = root / "03数据" / "135分层日报" / "AI分析报告_最新.json"
    ai_md_path = root / "03数据" / "135分层日报" / "AI分析报告_最新.md"
    l5_path = root / "03数据" / "134深度研究池" / "L5深度研究池_最新.json"
    ledger_path = root / "04日志" / "复盘" / "判断复盘账_最新.json"
    out_dir = root / "04日志" / "复盘"

    ai_data = load_json(ai_path, {})
    l5_data = load_json(l5_path, {})
    l5_by_code = l5_map(l5_data)
    data_date = ai_data.get("数据日期") or datetime.now().strftime("%Y-%m-%d")
    if isinstance(data_date, str) and len(data_date) == 8 and data_date.isdigit():
        data_date = f"{data_date[:4]}-{data_date[4:6]}-{data_date[6:]}"

    records: list[dict[str, Any]] = []
    for item in ai_analysis_rows(ai_data):
        code = normalize_code(item.get("代码"))
        if not code:
            continue
        l5_item = l5_by_code.get(code, {})
        reason, sub_reasons = main_reason(item, l5_item)
        adjusted_score = item.get("调整分") or l5_item.get("调整分")
        record = {
            "股票代码": code,
            "股票名称": item.get("名称") or l5_item.get("名称"),
            "报告日期": data_date,
            "报告类型": "L5批量AI分析报告",
            "报告触发原因": "L5人工确认后AI分析",
            "判断主因": reason,
            "辅因": sub_reasons,
            "关注等级": "高优先级研究对象" if adjusted_score and float(adjusted_score) >= 4.5 else "常规跟踪对象",
            "系统评分": None,
            "分层状态": "L5深度研究池",
            "L5调整分": adjusted_score,
            "证据完整度": "中",
            "公司品质档位": "待核验",
            "原始报告路径": str(ai_md_path),
            "应验证周期": periods(reason),
            "验证结果_T5": None,
            "验证结果_T20": None,
            "验证结果_T60": None,
            "验证结果_T120": None,
            "人工评价": None,
            "备注": "由L5批量AI分析报告同步写入；不自动修改规则。",
            "记录时间": now.strftime("%Y-%m-%d %H:%M:%S"),
            "model_used": item.get("model_used"),
            "is_fallback": item.get("is_fallback"),
        }
        records.append(record)

    added, skipped = append_records(ledger_path, records)
    result = {
        "名称": "L5 AI报告同步判断复盘账",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "AI报告": str(ai_path),
        "L5深度研究池": str(l5_path),
        "判断复盘账": str(ledger_path),
        "识别记录数": len(records),
        "新增记录数": added,
        "跳过重复数": skipped,
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否自动修改规则": False,
        },
        "同步记录预览": records[:20],
    }
    latest_json = out_dir / "L5AI报告同步判断复盘账_最新.json"
    latest_md = out_dir / "L5AI报告同步判断复盘账_最新.md"
    write_json(latest_json, result)
    markdown = build_markdown(result)
    write_text(latest_md, markdown)
    print(json.dumps({
        "状态": "完成",
        "识别记录数": len(records),
        "新增记录数": added,
        "跳过重复数": skipped,
        "输出": str(latest_json),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
