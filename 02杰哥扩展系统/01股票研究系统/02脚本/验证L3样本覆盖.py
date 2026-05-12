# -*- coding: utf-8 -*-
"""
名称：验证L3样本覆盖.py
作用：验收L3五样本是否都有评分、财报证据、前台短答验收和企业微信桥接dry-run覆盖。
触发方式：python 验证L3样本覆盖.py
安全边界：只读本地L3样本资产和验收报告；只写验收报告；不发送企业微信；不触发n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SAMPLES = [
    {"name": "云南锗业", "code": "sz002428", "require_industry_price": True},
    {"name": "天齐锂业", "code": "sz002466", "require_industry_price": True},
    {"name": "华虹公司", "code": "sh688347", "require_industry_price": False},
    {"name": "浙商中拓", "code": "sz000906", "require_industry_price": False},
    {"name": "正丹股份", "code": "sz300641", "require_industry_price": True},
]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def base_dir(root: Path) -> Path:
    return root / "03数据" / "245L3评分基础资产"


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


def any_file(paths: list[Path]) -> str:
    existing = [p for p in paths if p.exists()]
    if not existing:
        return ""
    existing.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return str(existing[0])


def sample_in_validation(report: dict[str, Any], name: str, code: str) -> dict[str, Any]:
    for item in report.get("samples", []) if isinstance(report.get("samples"), list) else []:
        text = json.dumps(item, ensure_ascii=False)
        if name in text and code in text:
            return item
    return {}


def validate_sample(root: Path, sample: dict[str, Any], short_report: dict[str, Any], bridge_report: dict[str, Any]) -> dict[str, Any]:
    base = base_dir(root)
    score_dir = base / "单股L3评分"
    name = sample["name"]
    code = sample["code"]
    digits = code[2:]
    blocking: list[str] = []
    warnings: list[str] = []

    score_path = any_file(list(score_dir.glob(f"{name}_{code}_*.json")) + list(score_dir.glob(f"{name}_*{digits}*.json")))
    fundamental_path = any_file(list(base.glob(f"{name}_财报基本面证据卡_*.json")))
    industry_price_path = any_file(list(base.glob(f"{name}_行业价格证据卡_*latest.json")) + list(base.glob(f"{name}_行业价格证据卡_*.json")))
    short_item = sample_in_validation(short_report, name, code)
    bridge_item = sample_in_validation(bridge_report, name, code)

    if not score_path:
        blocking.append("缺少单股L3评分报告")
    if not fundamental_path:
        blocking.append("缺少财报基本面证据卡")
    if sample.get("require_industry_price") and not industry_price_path:
        blocking.append("强制跟踪行业价格的样本缺少行业价格证据卡")
    if not sample.get("require_industry_price") and not industry_price_path:
        warnings.append("未强制要求行业价格卡；前台不得把行业价格写成已入账")
    if not short_item:
        blocking.append("短答适配器验收未覆盖")
    elif not short_item.get("passed"):
        blocking.append("短答适配器验收未通过")
    if not bridge_item:
        blocking.append("企业微信桥接dry-run未覆盖")
    elif not bridge_item.get("passed"):
        blocking.append("企业微信桥接dry-run未通过")

    for label, item in (("short", short_item), ("bridge", bridge_item)):
        if item:
            if item.get("reply_length") and int(item["reply_length"]) > 560:
                blocking.append(f"{label}回复超过560字")
            if item.get("line_count") and int(item["line_count"]) > 10:
                blocking.append(f"{label}回复超过10行")
            if item.get("why_line_length") and int(item["why_line_length"]) > 150:
                blocking.append(f"{label}为什么行超过150字")

    return {
        "name": name,
        "code": code,
        "require_industry_price": bool(sample.get("require_industry_price")),
        "score_report": score_path,
        "fundamental_card": fundamental_path,
        "industry_price_card": industry_price_path,
        "short_answer_validation": bool(short_item),
        "bridge_dry_run_validation": bool(bridge_item),
        "short_reply_length": short_item.get("reply_length") if short_item else None,
        "bridge_reply_length": bridge_item.get("reply_length") if bridge_item else None,
        "blocking": blocking,
        "warnings": warnings,
        "passed": not blocking,
    }


def build_markdown(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['name']} | {item['code']} | {item['passed']} | {bool(item['score_report'])} | {bool(item['fundamental_card'])} | {bool(item['industry_price_card'])} | {item['short_answer_validation']} | {item['bridge_dry_run_validation']} |"
        for item in report["samples"]
    ]
    lines = [
        "# L3样本覆盖验收",
        "",
        f"生成时间：{report['generated_at']}",
        f"总体状态：{report['status']}",
        "",
        "| 股票 | 代码 | 通过 | L3评分 | 财报卡 | 行业价格卡 | 短答验收 | 桥接dry-run |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
        *rows,
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in report["blocking"]] or ["- 无"])
    lines.extend(["", "## 提醒项", ""])
    lines.extend([f"- {item}" for item in report["warnings"]] or ["- 无"])
    lines.extend([
        "",
        "## 边界",
        "",
        "- 不真实发送企业微信",
        "- 不触发 n8n",
        "- 不调用券商接口",
        "- 不自动交易",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    base = base_dir(root)
    short_report = load_json(base / "L3企业微信短答适配器自动验收_20260507.json", {}) or {}
    bridge_report = load_json(base / "L3企业微信短答桥接dry_run验收_20260507.json", {}) or {}
    sample_rows = [validate_sample(root, sample, short_report, bridge_report) for sample in SAMPLES]
    blocking = [f"{item['name']}：{problem}" for item in sample_rows for problem in item["blocking"]]
    warnings = [f"{item['name']}：{warning}" for item in sample_rows for warning in item["warnings"]]
    status = "passed" if not blocking else "failed"
    report = {
        "名称": "L3样本覆盖验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "自动验收报告",
        "status": status,
        "summary": {
            "sample_count": len(sample_rows),
            "passed_count": sum(1 for item in sample_rows if item["passed"]),
            "blocking_count": len(blocking),
            "warning_count": len(warnings),
        },
        "samples": sample_rows,
        "blocking": blocking,
        "warnings": warnings,
        "safety_boundary": {
            "not_external_send": True,
            "not_n8n": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }
    json_path = base / "L3样本覆盖验收_最新.json"
    md_path = base / "L3样本覆盖验收_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({"status": status, "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
