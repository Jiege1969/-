# -*- coding: utf-8 -*-
"""
生成股票 L3 五样本统一刷新验收清单。

只生成 W1 验收清单，不触发真实刷新、不抓取数据、不外发、不改正式配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "股票L3五样本统一刷新验收清单_最新.json"
MD_OUT = DATA_DIR / "股票L3五样本统一刷新验收清单_最新.md"


ASSETS = [
    {
        "asset_key": "l3_gap_priority",
        "display_name": "L3五样本证据缺口优先级报告",
        "path": DATA_DIR / "L3五样本证据缺口优先级报告_最新.json",
        "refresh_role": "确认当前最重要证据缺口和补齐顺序。",
        "required_before_front_answer": True,
    },
    {
        "asset_key": "policy_gap_queue",
        "display_name": "五样本政策事件缺口队列",
        "path": DATA_DIR / "五样本政策事件缺口队列_最新.json",
        "refresh_role": "确认政策事件是否结构化、是否允许政策项加分。",
        "required_before_front_answer": True,
    },
    {
        "asset_key": "industry_price_queue",
        "display_name": "五样本行业价格连续观测补数队列",
        "path": DATA_DIR / "五样本行业价格连续观测补数队列_最新.json",
        "refresh_role": "确认行业价格/景气观测是否足以写趋势。",
        "required_before_front_answer": True,
    },
    {
        "asset_key": "financial_capital_template",
        "display_name": "五样本财报资金证据采集模板草案",
        "path": DATA_DIR / "五样本财报资金证据采集模板草案_最新.json",
        "refresh_role": "确认财报、估值、资金、机构、解禁字段是否 ready。",
        "required_before_front_answer": True,
    },
    {
        "asset_key": "front_answer_samples",
        "display_name": "五样本前台结论型短答修订样例",
        "path": DATA_DIR / "五样本前台结论型短答修订样例_最新.json",
        "refresh_role": "确认前台回答保持对象明确、结论先行、缺口明确。",
        "required_before_front_answer": True,
    },
    {
        "asset_key": "backend_front_mapping",
        "display_name": "后台证据链到前台短答字段映射草案",
        "path": DATA_DIR / "后台证据链到前台短答字段映射草案_最新.json",
        "refresh_role": "确认后台 evidence/missing/confidence 到前台字段的映射契约。",
        "required_before_front_answer": True,
    },
    {
        "asset_key": "sample_mapping_acceptance",
        "display_name": "五样本后台到前台字段映射验收样例",
        "path": DATA_DIR / "五样本后台到前台字段映射验收样例_最新.json",
        "refresh_role": "确认五样本字段映射验收是否通过。",
        "required_before_front_answer": True,
    },
]


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def inspect_asset(item: dict) -> dict:
    data = read_json(item["path"])
    exists = item["path"].exists()
    passed = None
    summary = {}
    status = None
    if isinstance(data, dict):
        passed = data.get("passed")
        summary = data.get("summary") or data.get("metrics") or {}
        status = data.get("status")
    return {
        "asset_key": item["asset_key"],
        "display_name": item["display_name"],
        "path": str(item["path"]),
        "exists": exists,
        "status": status,
        "passed": passed,
        "summary": summary,
        "refresh_role": item["refresh_role"],
        "required_before_front_answer": item["required_before_front_answer"],
        "refresh_check": "pass" if exists else "missing",
        "blocking_if_missing": "缺少该资产时，不得生成声称 L3 完整的前台报告。",
    }


def build_asset() -> dict:
    checks = [inspect_asset(item) for item in ASSETS]
    return {
        "name": "股票L3五样本统一刷新验收清单",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1统一刷新验收清单",
        "status": "draft",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "not_real_refresh": True,
        "asset_checks": checks,
        "refresh_order": [item["asset_key"] for item in ASSETS],
        "refresh_contract": [
            "先验收结构化证据资产，再生成前台短答。",
            "政策、市场风格、行业价格、财报资金任一关键证据缺失时，前台必须写缺口。",
            "统一刷新只检查资产状态，不抓取真实数据、不写正式库。",
            "通过统一刷新不等于正式上线，不等于真实外发，不等于投资建议。",
        ],
        "summary": {
            "asset_count": len(checks),
            "exists_count": sum(1 for item in checks if item["exists"]),
            "missing_count": sum(1 for item in checks if not item["exists"]),
            "required_count": sum(1 for item in checks if item["required_before_front_answer"]),
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_adapter_write": True,
            "not_score_write": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
            "not_real_refresh": True,
        },
    }


def write_markdown(asset: dict) -> None:
    lines = [
        "# 股票L3五样本统一刷新验收清单",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：W1 验收清单，不真实刷新，不抓取数据，不外发，不改正式配置。",
        "",
        "## 汇总",
        "",
        f"- 资产数：{asset['summary']['asset_count']}",
        f"- 已存在：{asset['summary']['exists_count']}",
        f"- 缺失：{asset['summary']['missing_count']}",
        "",
        "## 刷新顺序",
        "",
    ]
    for idx, key in enumerate(asset["refresh_order"], start=1):
        lines.append(f"{idx}. {key}")
    lines.extend(["", "## 资产检查", ""])
    for item in asset["asset_checks"]:
        lines.extend(
            [
                f"### {item['display_name']}",
                "",
                f"- key：{item['asset_key']}",
                f"- exists：{item['exists']}",
                f"- refresh_check：{item['refresh_check']}",
                f"- 作用：{item['refresh_role']}",
                f"- 缺失阻断：{item['blocking_if_missing']}",
                "",
            ]
        )
    lines.extend(["## 刷新契约", ""])
    lines.extend([f"- {item}" for item in asset["refresh_contract"]])
    lines.extend(["", "## 下一步自动推进", ""])
    lines.append("- 可继续生成“统一刷新验收执行记录模板”，用于每次刷新后记录通过/缺口/阻断。")
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    asset = build_asset()
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({"status": "ok", "json": str(JSON_OUT), "md": str(MD_OUT), "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
