# -*- coding: utf-8 -*-
"""
生成股票 L3 统一刷新验收执行记录样例。

只基于本地资产状态生成影子执行记录，不执行真实刷新、不抓取数据、不外发。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
TEMPLATE_PATH = DATA_DIR / "股票L3统一刷新验收执行记录模板_最新.json"
JSON_OUT = DATA_DIR / "股票L3统一刷新验收执行记录样例_最新.json"
MD_OUT = DATA_DIR / "股票L3统一刷新验收执行记录样例_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_record_from_template(template: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records = []
    missing = []
    for item in template.get("asset_check_records", []):
        path = Path(item.get("path", ""))
        exists = path.exists()
        if not exists:
            missing.append(item.get("display_name"))
        records.append(
            {
                **item,
                "actual_exists": exists,
                "check_result": "pass" if exists else "blocked",
                "blocking_issue": None if exists else f"缺少资产：{item.get('display_name')}",
                "review_note": "本地资产存在，影子执行记录检查通过。" if exists else "缺失，禁止生成 L3 完整前台报告。",
            }
        )

    allow_front = len(missing) == 0
    return {
        "name": "股票L3统一刷新验收执行记录样例",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W1影子执行记录样例",
        "status": "shadow_record",
        "source_assets": {
            "execution_template": str(TEMPLATE_PATH),
            "execution_template_exists": bool(template),
        },
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "not_real_refresh": True,
        "execution_header": {
            "execution_id": f"STOCK_L3_REFRESH_SHADOW_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "execution_time": now,
            "operator": "codex_shadow_builder",
            "trigger_source": "shadow_local_validation",
            "scope": "五样本L3统一刷新验收",
            "real_refresh_performed": False,
            "external_send_performed": False,
            "formal_database_write_performed": False,
        },
        "asset_check_records": records,
        "decision_section": {
            "all_required_assets_ready": allow_front,
            "allow_front_answer_generation": allow_front,
            "allow_l3_complete_claim": False,
            "blocked_reasons": [f"缺少资产：{item}" for item in missing],
            "missing_summary": "本地关键资产齐备；但未执行真实数据刷新，不能声称正式 L3 完整。" if allow_front else "存在缺失资产，禁止生成完整前台报告。",
            "next_action": "可继续做影子前台短答刷新验收；正式入口或真实刷新仍需 W3 判断。",
        },
        "front_answer_gate": template.get("front_answer_gate", {}),
        "prohibited_actions": template.get("prohibited_actions", []),
        "summary": {
            "asset_record_count": len(records),
            "pass_count": sum(1 for item in records if item["check_result"] == "pass"),
            "blocked_count": sum(1 for item in records if item["check_result"] == "blocked"),
            "real_refresh_performed": False,
            "external_send_performed": False,
            "formal_database_write_performed": False,
        },
        "safety_boundary": template.get("safety_boundary", {}),
    }


def write_markdown(asset: dict[str, Any]) -> None:
    lines = [
        "# 股票L3统一刷新验收执行记录样例",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：W1 影子执行记录，不真实刷新，不抓取数据，不外发，不写正式库。",
        "",
        "## 执行头",
        "",
    ]
    for key, value in asset["execution_header"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 检查汇总", ""])
    for key, value in asset["summary"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 决策区", ""])
    for key, value in asset["decision_section"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 资产检查记录", ""])
    for item in asset["asset_check_records"]:
        lines.extend(
            [
                f"### {item['display_name']}",
                "",
                f"- asset_key：{item['asset_key']}",
                f"- actual_exists：{item['actual_exists']}",
                f"- check_result：{item['check_result']}",
                f"- review_note：{item['review_note']}",
                "",
            ]
        )
    lines.extend(["## 下一步自动推进", ""])
    lines.append("- 继续生成“影子前台短答刷新验收样例”，用本影子执行记录检查是否允许生成前台短答样例。")
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    template = load_json(TEMPLATE_PATH)
    asset = build_record_from_template(template)
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({"status": "ok", "json": str(JSON_OUT), "md": str(MD_OUT), "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
