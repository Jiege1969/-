# -*- coding: utf-8 -*-
"""
名称：验证01股票池全A基础链路.py
作用：校验全A基础股票池、全市场行情快照、2000样本池、重点关注池之间的基础口径一致性。
边界：只读本地数据并写校验报告；不触发n8n；不发送企业微信；不接券商；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
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
        if suffix == "sh":
            return f"sh{num.zfill(6)}"
        if suffix == "sz":
            return f"sz{num.zfill(6)}"
        if suffix == "bj":
            return f"bj{num.zfill(6)}"
    if text.isdigit():
        text = text.zfill(6)
        if text.startswith(("4", "8", "920")):
            return f"bj{text}"
        if text.startswith(("6", "9")):
            return f"sh{text}"
        return f"sz{text}"
    return text


def code_set(rows: list[dict[str, Any]]) -> set[str]:
    return {normalize_code(row.get("代码")) for row in rows if normalize_code(row.get("代码"))}


def duplicate_codes(rows: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    dup: set[str] = set()
    for row in rows:
        code = normalize_code(row.get("代码"))
        if not code:
            continue
        if code in seen:
            dup.add(code)
        seen.add(code)
    return sorted(dup)


def market_count(rows: list[dict[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        market = str(row.get("市场") or "未知")
        result[market] = result.get(market, 0) + 1
    return dict(sorted(result.items(), key=lambda kv: (-kv[1], kv[0])))


def missing_from_base(base_codes: set[str], rows: list[dict[str, Any]], limit: int = 30) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for row in rows:
        code = normalize_code(row.get("代码"))
        if code and code not in base_codes:
            missing.append({
                "代码": code,
                "名称": row.get("名称", ""),
                "展示代码": row.get("展示代码", ""),
            })
        if len(missing) >= limit:
            break
    return missing


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 01股票池全A基础链路校验",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 严重问题数：{len(report['严重问题'])}",
        f"- 提示数：{len(report['提示'])}",
        "",
        "## 关键计数",
        "",
    ]
    for key, value in report["关键计数"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 严重问题", ""])
    if report["严重问题"]:
        for item in report["严重问题"]:
            lines.append(f"- {item}")
    else:
        lines.append("- 无")
    lines.extend(["", "## 提示", ""])
    if report["提示"]:
        for item in report["提示"]:
            lines.append(f"- {item}")
    else:
        lines.append("- 无")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    data_dir = root / "03数据"
    output_dir = data_dir / "01股票池"
    full_a_path = output_dir / "全A基础股票池_最新.json"
    seed_snapshot_path = data_dir / "04数据快照" / "全市场源头股票池基础行情统一快照_最新.json"
    sample_path = output_dir / "2000只样本股票池_最新.json"
    focus_path = root / "01配置" / "重点关注股票池.json"

    full_a = load_json(full_a_path)
    seed_snapshot = load_json(seed_snapshot_path)
    sample = load_json(sample_path)
    focus = load_json(focus_path)

    full_rows = list(full_a.get("股票池", []))
    snapshot_rows = list(seed_snapshot.get("行情", []))
    sample_rows = list(sample.get("股票列表", []))
    focus_rows = list(focus.get("股票池", []))

    full_codes = code_set(full_rows)
    snapshot_codes = code_set(snapshot_rows)
    sample_missing = missing_from_base(full_codes, sample_rows)
    focus_missing = missing_from_base(full_codes, focus_rows)
    severe: list[str] = []
    hints: list[str] = []

    if len(full_rows) < 5000:
        severe.append(f"全A基础股票池数量不足5000：{len(full_rows)}")
    if len(snapshot_rows) != len(full_rows):
        severe.append(f"全市场行情快照数量与全A基础池不一致：快照{len(snapshot_rows)} / 基础池{len(full_rows)}")
    if len(snapshot_codes - full_codes) > 0:
        severe.append(f"全市场行情快照存在不属于全A基础池的代码：{len(snapshot_codes - full_codes)}")
    if duplicate_codes(full_rows):
        severe.append(f"全A基础池存在重复代码：{len(duplicate_codes(full_rows))}")
    if not any(row.get("市场") == "北交所" for row in full_rows):
        severe.append("全A基础池未识别北交所股票")
    if not any(normalize_code(row.get("代码")).startswith("bj") for row in snapshot_rows):
        severe.append("全市场行情快照未包含北交所行情")
    if sample_missing:
        severe.append(f"2000样本池存在不属于全A基础池的代码：{len(sample_missing)}")
    if focus_missing:
        severe.append(f"重点关注池存在不属于全A基础池的代码：{len(focus_missing)}")

    conflict_count = int((seed_snapshot.get("复核状态统计") or {}).get("多源冲突待复核") or 0)
    single_count = int((seed_snapshot.get("复核状态统计") or {}).get("单源可用") or 0)
    if conflict_count:
        hints.append(f"全市场行情快照存在多源冲突待复核：{conflict_count}，报告层不得把冲突行情当强结论。")
    if single_count:
        hints.append(f"全市场行情快照存在单源可用：{single_count}，应继续等待复核源恢复。")

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not severe else "阻断",
        "严重问题": severe,
        "提示": hints,
        "关键计数": {
            "全A基础股票池数量": len(full_rows),
            "全市场行情快照数量": len(snapshot_rows),
            "基础池市场统计": market_count(full_rows),
            "快照北交所数量": len([row for row in snapshot_rows if normalize_code(row.get("代码")).startswith("bj")]),
            "2000样本池数量": len(sample_rows),
            "重点关注池数量": len(focus_rows),
            "全市场行情多源一致": int((seed_snapshot.get("复核状态统计") or {}).get("多源一致") or 0),
            "全市场行情多源冲突待复核": conflict_count,
            "全市场行情单源可用": single_count,
        },
        "缺口样本": {
            "2000样本池缺口样本": sample_missing,
            "重点关注池缺口样本": focus_missing,
        },
        "输入": {
            "全A基础股票池": str(full_a_path),
            "全市场行情快照": str(seed_snapshot_path),
            "2000样本池": str(sample_path),
            "重点关注池": str(focus_path),
        },
        "安全边界": {
            "是否触发n8n": False,
            "是否真实发送企业微信": False,
            "是否接券商": False,
            "是否交易": False,
        },
    }

    json_path = output_dir / "全A基础链路校验_最新.json"
    md_path = output_dir / "全A基础链路校验_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "严重问题数": len(severe),
        "提示数": len(hints),
        "报告": str(md_path),
        "数据": str(json_path),
    }, ensure_ascii=False))
    return 0 if not severe else 1


if __name__ == "__main__":
    raise SystemExit(main())
