# -*- coding: utf-8 -*-
"""生成政策事件真实来源替换准备清单。

本脚本只生成只读准备清单，不抓取真实来源、不写正式配置、不更新政策事件库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "政策事件真实来源替换准备清单_最新.json"
MD_OUT = DATA_DIR / "政策事件真实来源替换准备清单_最新.md"


SOURCE_PREP = [
    {
        "source_group": "official_policy",
        "display_name": "部委/交易所/地方政府公开政策",
        "priority": "P0",
        "candidate_sources": ["国务院/部委官网", "交易所公告", "地方政府公开文件"],
        "required_fields": ["来源名称", "发布日期", "标题", "链接或人工记录路径", "政策对象", "影响方向", "人工复核状态"],
        "replacement_gate": "无原文链接或人工记录路径时，不得替换样例事件。",
    },
    {
        "source_group": "industry_policy",
        "display_name": "行业协会与产业政策解读",
        "priority": "P1",
        "candidate_sources": ["行业协会公告", "产业白皮书", "监管公开解读"],
        "required_fields": ["行业标签", "政策主题", "影响链条", "适用股票范围", "证据强度", "人工复核状态"],
        "replacement_gate": "仅有媒体解读时，只能作为线索，不得作为政策事件主来源。",
    },
    {
        "source_group": "company_policy_exposure",
        "display_name": "单股政策暴露映射",
        "priority": "P1",
        "candidate_sources": ["公司公告", "主营业务说明", "年报行业段落"],
        "required_fields": ["股票代码", "主营业务关联", "受益/受压方向", "证据字段", "缺口字段", "下一次复核日期"],
        "replacement_gate": "缺少主营业务关联证据时，不得把宏观政策直接映射到单股。",
    },
]


CHECKLIST = [
    "先保留样例政策事件库，不做覆盖替换。",
    "真实来源只允许登记为候选，必须经过人工复核后再进入正式替换讨论。",
    "每条政策事件必须区分来源原文、解读材料、单股暴露映射。",
    "缺少来源日期或链接时，前台只能提示政策线索待核验。",
    "政策事件不得触发交易指令、买卖建议或仓位建议。",
]


def build_markdown(asset: dict) -> str:
    lines = [
        "# 政策事件真实来源替换准备清单",
        "",
        f"- 生成时间：{asset['generated_at']}",
        "- 资产身份：W2 只读准备清单",
        "- 替换正式政策事件库：否",
        "- 正式配置：否",
        "",
        "## 来源准备",
        "",
        "| 来源组 | 优先级 | 候选来源 | 必备字段 | 替换门禁 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in asset["source_preparation"]:
        lines.append(
            f"| {item['display_name']} | {item['priority']} | {'；'.join(item['candidate_sources'])} | "
            f"{'、'.join(item['required_fields'])} | {item['replacement_gate']} |"
        )
    lines.extend(["", "## 替换前检查清单", ""])
    lines.extend([f"- {item}" for item in asset["checklist"]])
    return "\n".join(lines)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "政策事件真实来源替换准备清单",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W2_readonly_preparation_checklist",
        "status": "candidate_only_not_replaced",
        "purpose": "为政策事件库从样例走向真实来源建立替换前字段、来源和人工复核门禁。",
        "source_preparation": SOURCE_PREP,
        "checklist": CHECKLIST,
        "acceptance_rules": [
            "必须覆盖官方政策、行业政策解读、单股政策暴露映射三层。",
            "必须登记来源字段、人工复核状态和替换门禁。",
            "不得抓取真实来源，不得替换正式政策事件库。",
            "不得产生交易化表达或买卖建议。",
        ],
        "summary": {
            "source_group_count": len(SOURCE_PREP),
            "checklist_count": len(CHECKLIST),
            "candidate_only": True,
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_formal_database_write": True,
            "not_formal_config": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
            "not_order": True,
            "not_position_adjustment": True,
        },
    }
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_OUT.write_text(build_markdown(asset), encoding="utf-8")
    print(json.dumps({"status": "ok", "path": str(JSON_OUT), "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
